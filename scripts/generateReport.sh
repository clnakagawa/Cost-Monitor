#!/usr/bin/env bash
set -Eeuo pipefail

# Terra workflow info
python scripts/gatherWorkflows.py

# TODO: GCP monitoring logs

# Report generation
Rscript -e "rmarkdown::render('notebooks/CostReport.Rmd', output_dir = 'reports/')"