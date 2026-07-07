#!/usr/bin/env bash
set -Eeuo pipefail

redoData=true

# cmd line options
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      echo "Usage: generateReport.sh [--redo]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

if [ ! -d "../data" ]; then
  mkdir "../data"
fi

python gatherWorkflows.py

# Report generation
Rscript -e "rmarkdown::run('../notebooks/CostReport.Rmd', shiny_args = list(launch.browser=TRUE))"