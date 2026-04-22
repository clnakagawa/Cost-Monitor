#!/usr/bin/env bash
set -Eeuo pipefail

bucketName=$1

logPaths=($(gsutil ls "gs://${bucketName}/submissions/**/monitoring.log"))

if [ -f "data/logSummary.tsv" ]; then
    rm "data/logSummary.tsv" # delete for regenerating file
fi

if [ ! -d "data/logs" ]; then
    mkdir "data/logs"
fi

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

    echo "Path: $path"
    echo "  submission_id: $submission_id"
    echo "  workflow_name: $workflow_name"
    echo "  workflow_id:   $workflow_id"
    echo "  task_name:     $task_name"
    echo "  attempt:       $attempt"
    echo

    logFilename="data/logs/${task_name}.${workflow_id}.txt"

    if [ ! -f "$logFilename" ]; then
        gsutil cat "$path" > "$logFilename"
    fi

    echo "${submission_id}\t{$workflow_name}\t{$workflow_id}\t{$task_name}\t{$attempt}" >> "data/logSummary.tsv"
done
