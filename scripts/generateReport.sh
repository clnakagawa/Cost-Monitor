#!/usr/bin/env bash
set -Eeuo pipefail

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

configPath="../config/config.yml"

# cmd line options
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      echo "Usage: generateReport.sh [--redo]"
      exit 0
      ;;
    -c|--config)
      shift 
      configPath=$1
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

python gatherWorkflows.py "$configPath"

# Report generation
Rscript -e "rmarkdown::run('../notebooks/CostReport.Rmd', shiny_args = list(launch.browser=TRUE))"