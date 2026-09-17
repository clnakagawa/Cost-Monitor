#!/usr/bin/env bash

ws=$1
sampType=$2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
wsTblPath="${SCRIPT_DIR}/../data/${ws}/${sampType}_attributes.tsv"
gvcfTblPath="${SCRIPT_DIR}/../data/${ws}/${sampType}_gvcf_sizes.tsv"

IFS=$'\t' read -r -a colNames < $wsTblPath

tmpidx=0
nameidx=-1
gvcfidx=-1

for col in "${colNames[@]}"; do
    ((tmpidx++))
    if [ $col == "name" ]; then
        nameidx=$tmpidx
    elif [ $col == "attributes.gvcf" ]; then
        gvcfidx=$tmpidx
    fi
done

cutCols="${nameidx},${gvcfidx}"

if [ $gvcfidx -lt 0 ]; then
    echo "gvcf column not found"
    exit
fi

if [ $nameidx -lt 0 ]; then 
    echo "name column not found"
    exit
fi

hasTbl=false

if [[ -f $gvcfTblPath ]]; then
    hasTbl=true
fi

cut -d $'\t' -f"$cutCols" $wsTblPath | tail -n +2 | \
    while read -r -a line; do
        sampId=${line[0]}
        gvcfPath=${line[1]}

        # check for existing records
        if $hasTbl; then
            # check if sample already processed
            if [ $(grep "$sampId" $gvcfTblPath | wc -l) -gt 0 ]; then
                echo "Sample ${sampId} already processed, moving on"
            elif [[ "$gvcfPath" != "" ]]; then
                echo "getting size of file for sample ${sampId} at ${gvcfPath}"
                storData=$(gcloud storage du $gvcfPath)
                if [[ "$gvcfPath" != "" ]]; then
                    echo -e "${sampId}   ${storData}" >> $gvcfTblPath
                fi
            fi
        elif [[ "$gvcfPath" != "" ]]; then
            echo "getting size of file for sample ${sampId} at ${gvcfPath}"
            storData=$(gcloud storage du $gvcfPath)
            if [[ "$gvcfPath" != "" ]]; then
                echo -e "${sampId}   ${storData}" >> $gvcfTblPath
            fi
        fi
    done

