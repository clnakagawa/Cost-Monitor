#!/usr/bin/env bash
set -Eeuo pipefail

bucketName=$1
summaryFile="data/logSummary.tsv"
mkdir -p data

# 1. Discovery
logPaths=($(gcloud storage ls "gs://${bucketName}/submissions/**/monitoring.log"))
echo "Found ${#logPaths[@]} total logs in bucket."

# 2. Setup Headers & Filtering
metrics=(cpu memgb mempct diskgb diskpct read write)
header="submission_id\tlog_path\tworkflow_name\tworkflow_id\ttask_name\tattempt"
for m in "${metrics[@]}"; do
    header+="\tmin_${m}\tmax_${m}\tavg_${m}"
done

if [ -f "$summaryFile" ]; then
    # Filter out already processed logs to avoid duplicates
    loggedPaths=($(awk -F'\t' '{print $2}' "$summaryFile"))
    logPaths=($(comm -23 <(printf '%s\n' "${logPaths[@]}" | sort) <(printf '%s\n' "${loggedPaths[@]}" | sort)))
else
    echo -e "$header" > "$summaryFile"
fi

echo "Processing ${#logPaths[@]} new logs..."

# -----------------------------------------------------------------------------
# 3. Define the Worker Function
# This function handles the logic for a SINGLE log file.
# -----------------------------------------------------------------------------
process_log() {
    local path=$1
    
    # Regex extraction for metadata
    if [[ $path =~ submissions/([^/]+)/([^/]+)/([^/]+)/([^/]+)/ ]]; then
        submission_id="${BASH_REMATCH[1]}"
        workflow_name="${BASH_REMATCH[2]}"
        workflow_id="${BASH_REMATCH[3]}"
        task_name="${BASH_REMATCH[4]}"
    fi

    attempt=1
    [[ $path =~ attempt-([0-9]+) ]] && attempt="${BASH_REMATCH[1]}"

    # Stream log, skip header, and process with AWK
    # Note: We hardcode the metric count (7) to ensure output consistency
    gcloud storage cat "$path" 2>/dev/null | tail -n +8 | awk -v sid="$submission_id" \
        -v lp="$path" -v wn="$workflow_name" -v wid="$workflow_id" \
        -v tn="$task_name" -v att="$attempt" '
        BEGIN { FS="[ \t]+" }
        {
            # NF-1 because monitoring logs often have a trailing timestamp/empty col
            for (i=2; i<=8; i++) {
                val = $i + 0
                sum[i] += val
                if (!(i in min) || val < min[i]) min[i] = val
                if (!(i in max) || val > max[i]) max[i] = val
            }
            count++
        }
        END {
            if (count > 0) {
                printf "%s\t%s\t%s\t%s\t%s\t%s", sid, lp, wn, wid, tn, att
                for (i=2; i<=8; i++) {
                    printf "\t%f\t%f\t%f", min[i], max[i], (sum[i]/count)
                }
                printf "\n"
            }
        }'
}

# Export the function so 'parallel' can access it
export -f process_log

# -----------------------------------------------------------------------------
# 4. Execute in Parallel
# --jobs: Number of concurrent downloads (adjust based on your RAM/Network)
# --keep-order: Ensures output isn't scrambled if you care about sorting
# -----------------------------------------------------------------------------
if [ ${#logPaths[@]} -gt 0 ]; then
    printf '%s\n' "${logPaths[@]}" | \
        parallel --jobs 6 --progress --keep-order process_log {} >> "$summaryFile"
fi

echo -e "\nDone! Results saved to $summaryFile"