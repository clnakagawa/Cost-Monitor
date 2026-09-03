#!/usr/bin/env python3

import yaml
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import sys
import google.auth
from google.auth.transport.requests import Request
from pathlib import Path
import argparse
from costutils import *

def main():
    scriptDir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Updates/Creates local tables for storing Terra workspace data (Workflow costs, sample attribute tables, etc.)")
    parser.add_argument('-c', '--config', default = scriptDir / "../config/config.yml", help="Optional argument specifying config file, defaults to config/config.yml")
    args = parser.parse_args()

    config_path = args.config

    # set up retry mechanism
    s = get_session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # set up general workspace variable from config file + api path
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    wsList = [Workspace(ws['namespace'], ws['name']) for ws in config['workspaces']]

    for ws in wsList:
        print(f"\nGathering data for workspace {ws.namespace}/{ws.name}")

        # make data directory for workspace if doesn't exist
        Path(scriptDir / f"../data/{ws.name}").mkdir(parents=True, exist_ok=True)

        # get tables for all entity types in workspace
        entTypes = get_entity_types(ws, s)
        for entType in entTypes:
            entTbl = get_entity_table(ws, entType, s)
            entTbl.to_csv(scriptDir / f"../data/{ws.name}/{entType}_attributes.tsv", sep='\t', index=False)

        # Get a list of all workspace submissions + metadata
        subIds = get_submissions(ws, s)

        # check if processed submissions list exists
        hasSubRecord = Path(scriptDir / f"../data/{ws.name}/submission_list.txt").is_file()
        if hasSubRecord:
            # get already processed ids and remove from current list
            with open(scriptDir / f"../data/{ws.name}/submission_list.txt", 'r') as f:
                procSubIds = [line.rstrip() for line in f]
            subIds = [subId for subId in subIds if subId not in procSubIds]

        # Get a list of all workspace method configs
        # Used to filter workflow table to only contain currently used workflows 
        currentMethods = get_methods(ws, s)

        # Process each submission individually + add data to workspace table
        wfData = pd.read_table(scriptDir / f"../data/{ws.name}/workflowData.tsv") if hasSubRecord else pd.DataFrame()
        wfData = pd.concat([wfData, get_submission_table(ws, subIds, currentMethods, s)])
        wfData.to_csv(scriptDir / f"../data/{ws.name}/workflowData.tsv", sep = '\t')

        # If submissions are processed without error, write/append to record
        with open(scriptDir / f"../data/{ws.name}/submission_list.txt", 'a' if hasSubRecord else 'w') as f:
            f.write("\n".join(subIds))

        # storage cost estimates
        get_storage_cost_table(ws, s).to_csv(scriptDir / f"../data/{ws.name}/StorageEstimate.tsv", sep = '\t')

if __name__ == "__main__":
    main()
