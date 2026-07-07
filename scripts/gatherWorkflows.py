#!/usr/bin/env python3

import yaml
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import sys
import google.auth
from google.auth.transport.requests import Request
from pathlib import Path

# current solution for authenticating for google cloud access
# requires setup of refresh token on whatever system is running this tool
def get_access_token():
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

# convert submission response json to table of workflow data
def json_to_table(sub_json):
    subTable = pd.DataFrame(sub_json['workflows'])
    subTable['workflowVersion'] = sub_json['methodConfigurationName']
    subTable['sample'] = [entity['entityName'] for entity in subTable['workflowEntity']]
    subTable['entityType'] = [entity['entityType'] for entity in subTable['workflowEntity']] # needed to split single vs multi-sample workflows
    subTable['workflow'] = [inputRes[0]['inputName'].split('.')[0] for inputRes in subTable['inputResolutions']]
    return(subTable)

def main():
    # set up retry mechanism
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # set up general workspace variable from config file + api path
    with open("../config/config.yml", "r") as config_file: # potential here for cmd line option spec
        config = yaml.safe_load(config_file)
    workspaceName = config['workspace']['name']
    workspaceNamespace = config['workspace']['namespace']
    base_url = "https://api.firecloud.org/api/"


    # set up refresh token authorization, headers that will be used throughout script
    TOKEN = get_access_token()
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    # Get a list of all workspace submissions + metadata
    url = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/submissions"
    response = requests.get(url, headers=headers, params={})
    if response.ok:
        subIds = [sub['submissionId'] for sub in response.json()]
    else:
        print(response.status_code, response.text)
        sys.exit(1)

    # check if processed submissions list exists
    hasSubRecord = Path("../data/submission_list.txt").is_file()
    if hasSubRecord:
        # get already processed ids and remove from current list
        with open("../data/submission_list.txt", 'r') as f:
            procSubIds = [line.rstrip() for line in f]
        subIds = [subId for subId in subIds if subId not in procSubIds]

    # Get a list of all workspace method configs
    # Used to filter workflow table to only contain current workflows
    attr_url = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/methodconfigs"
    response = requests.get(attr_url, headers=headers, params={'allRepos' : 'true'})
    if not response.ok:
        print(response.status_code, response.text)
    currentMethods = [method['name'] for method in response.json()]

    # Get list of workflow entities
    entity_url = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/entities/sample_set"
    response = requests.get(entity_url, headers=headers, params={})
    if not response.ok:
        print(response.status_code, response.text)
    pd.DataFrame(pd.json_normalize(response.json())).to_csv("../data/workspace_entities.tsv")

    # Process each submission individually and add data to workspace table
    wfData = pd.DataFrame()
    for id in subIds:
        print(f"processing submission {id}") # TODO: verbosity options?
        suburl = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/submissions/{id}"
        response = requests.get(suburl, headers=headers, params={})
        if response.ok:
            respJson = response.json()
            if any([method in respJson['methodConfigurationName'] for method in currentMethods]):
                wfData = pd.concat([wfData, json_to_table(respJson)])
            else:
                print(f"submission using config {respJson['methodConfigurationName']} does not match a current workflow method")
        else:
            print(response.status_code, response.text)
    wfData.to_csv("../data/workflowData.tsv", sep = '\t')

    # If submissions are processed without error, write/append to record
    with open("../data/submission_list.txt", 'a' if hasSubRecord else 'w') as f:
        f.write("\n".join(subIds))

    # storage cost estimates
    storage_url = f"{base_url}/workspaces/v2/{workspaceNamespace}/{workspaceName}/storageCostEstimate"
    response = requests.get(storage_url, headers=headers, params={})
    if response.ok:
        pd.DataFrame(pd.json_normalize(response.json())).to_csv("../data/StorageEstimate.tsv", sep = '\t')
    else:
        print(response.status_code, response.text)

if __name__ == "__main__":
    main()
