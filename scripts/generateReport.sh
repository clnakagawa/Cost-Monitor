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
    -r|--redo)
      redoData=false
      shift 1
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Terra workflow info
if $redoData; then
    python scripts/gatherWorkflows.py
fi

# TODO: GCP monitoring logs

# Report generation
Rscript -e "rmarkdown::render('notebooks/CostReport.Rmd', output_dir = 'reports/')"