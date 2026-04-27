#!/usr/bin/env bash
# set -Eeuo pipefail

bucketName=$1

logPaths=($(gsutil ls "gs://${bucketName}/submissions/**/monitoring.log"))

if [ -f "data/logSummary.tsv" ]; then
    rm "data/logSummary.tsv" # delete for regenerating file
fi

if [ ! -d "data/logs" ]; then
    mkdir "data/logs"
fi

metrics=(cpu memgb mempct diskgb diskpct read write)

header=$'submission_id\tworkflow_name\tworkflow_id\ttask_name\tattempt\t'

for m in "${metrics[@]}"; do
    header+=$(printf "min_%s\tmax_%s\tavg_%s\t" "$m" "$m" "$m")
done

printf "%s\n" "${header%$'\t'}" > data/logSummary.tsv

for path in "${logPaths[@]}"; do
    if [[ $path =~ submissions/([^/]+)/([^/]+)/([^/]+)/([^/]+)/ ]]; then
        submission_id="${BASH_REMATCH[1]}"
        workflow_name="${BASH_REMATCH[2]}"
        workflow_id="${BASH_REMATCH[3]}"
        task_name="${BASH_REMATCH[4]}"
    fi

    # Default attempt
    attempt=1

    if [[ $path =~ attempt-([0-9]+) ]]; then
        attempt="${BASH_REMATCH[1]}"
    fi
    gsutil cat "$path" | 
        tail -n +8 |  
        awk -v submission_id="$submission_id" \
            -v workflow_name="$workflow_name" \
            -v workflow_id="$workflow_id" \
            -v task_name="$task_name" \
            -v attempt="$attempt" '
        {
            last_col1 = $1

            if (NF > max_nf) max_nf = NF

            for (i=2; i<=NF; i++) {
                val = $i + 0
                sum[i] += val

                if (!(i in min) || val < min[i]) min[i] = val
                if (!(i in max) || val > max[i]) max[i] = val
            }
            count++
        }
        END {
            # metadata first
            printf "%s\t%s\t%s\t%s\t%s\t",
                submission_id, workflow_name, workflow_id, task_name, attempt

            # stats
            printf "%s\t", last_col1

            for (i=2; i<=max_nf; i++) {
                mean = sum[i]/count
                printf "%f\t%f\t%f\t", min[i], max[i], mean
            }

            printf "\n"
        }' >> data/logSummary.tsv

done
