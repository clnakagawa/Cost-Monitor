#!/usr/bin/env bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

pip install -r "../requirements.txt"

Rscript -e "
    install.packages(c('shiny', 'ggplot2', 'data.table', 
        'DT', 'stringr', 'flexdashboard',
        'circlize', 'patchwork'), repos='https://cloud.r-project.org')
    if (!require('BiocManager', quietly = TRUE)) {
        install.packages('BiocManager')
    }
    BiocManager::install('ComplexHeatmap')
"