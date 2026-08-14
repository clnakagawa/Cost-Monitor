#!/usr/bin/env python3

import yaml
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import sys
import google.auth
from google.auth.transport.requests import Request
from pathlib import Path

from costutils import *

def main():
    # get config
    config_path = sys.argv[1]

    # set up retry mechanism
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # set up general workspace variable from config file + api path
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    # workspaceName = config['workspace']['name']
    # workspaceNamespace = config['workspace']['namespace']
    base_url = "https://api.firecloud.org/api/"

    wsList = [Workspace(ws['namespace'], ws['name']) for ws in config['workspaces']]

    for ws in wsList:
        # make data directory for workspace if doesn't exist
        Path(f"../data/{ws.name}").mkdir(parents=True, exist_ok=True)

        # set up refresh token authorization, headers that will be used throughout script
        TOKEN = get_access_token()
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        # get tables for all entity types in workspace
        entTypes = get_entity_types(ws, headers)
        for entType, entTbl in get_entity_tables(ws, entTypes, headers).items():
            entTbl.to_csv(f"../data/{ws.name}/{entType}_attributes.tsv", sep='\t', index=False)

        # Get a list of all workspace submissions + metadata
        subIds = get_submissions(ws, headers)

        # check if processed submissions list exists
        hasSubRecord = Path(f"../data/{ws.name}/submission_list.txt").is_file()
        if hasSubRecord:
            # get already processed ids and remove from current list
            with open(f"../data/{ws.name}/submission_list.txt", 'r') as f:
                procSubIds = [line.rstrip() for line in f]
            subIds = [subId for subId in subIds if subId not in procSubIds]

        # Get a list of all workspace method configs
        # Used to filter workflow table to only contain current workflows
        currentMethods = get_methods(ws, headers)

        # Process each submission individually and add data to workspace table
        wfData = pd.read_table(f"../data/{ws.name}/workflowData.tsv") if hasSubRecord else pd.DataFrame()
        wfData = pd.concat([wfData, get_submission_table(ws, subIds, currentMethods, headers)])
        wfData.to_csv(f"../data/{ws.name}/workflowData.tsv", sep = '\t')

        # If submissions are processed without error, write/append to record
        with open(f"../data/{ws.name}/submission_list.txt", 'a' if hasSubRecord else 'w') as f:
            f.write("\n".join(subIds))

        # storage cost estimates
        get_storage_cost_table(ws, headers).to_csv(f"../data/{ws.name}/StorageEstimate.tsv", sep = '\t')

if __name__ == "__main__":
    main()
