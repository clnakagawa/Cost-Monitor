# Terra Workflow Cost Monitoring

Workflow cost monitoring tool for Terra projects. Incorporates data from the Terra FISS API and monitoring logs from GCP buckets. 

## Installation

The requirements.txt file handles all necessary Python packages. R packages for the markdown file are also installed if not found on report generation. Pandoc must be installed separately for now.

## Running the Tool

Currently the only inputs are workspace name and namespace. These are specified in the config.yml file. 

## TODO

- Fix GCP token handling (either check and regen token or find permanent solution)
- Add GCP log download or summary stat generation
- Add flexible markdown options (optional list of samples, processed samples, gcp report addition)