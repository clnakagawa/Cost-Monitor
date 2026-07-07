# Terra Workflow Cost Monitoring

Workflow cost monitoring tool for Terra projects. Incorporates data from the Terra FISS API and monitoring logs from GCP buckets. 

# Installation

Run the following to install all required Python/R packages and set up necessary directories

```bash
scripts/install.sh
```

# Running the Tool

The following will grab submission data from a Terra workspace and generate an interactive R dashboard. 

```bash
scripts/generateReport.sh -c <config_path>
```

The config argument is optional, by default the script checks for the config under config/config.yml. The config must adhere to the following format:

```yml
workspace:
  name: <workspace name>
  namespace: <workspace namespace>
creds_path: <gcloud_credentials_json>
```

The credentials json can be generated following the instructions on [this](https://docs.cloud.google.com/docs/authentication/application-default-credentials) page.
