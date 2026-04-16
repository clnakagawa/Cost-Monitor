#!/usr/bin/env python3

import yaml
import requests
import pandas as pd
import sys

def main():
    with open("misc/gcp_token", "r") as token_file:
        TOKEN = token_file.read().strip()
    with open("config/config.yml", "r") as config_file: # potential here for cmd line option spec
        config = yaml.safe_load(config_file)

    workspaceName = config['workspace']['name']
    workspaceNamespace = config['workspace']['namespace']
    base_url = "https://api.firecloud.org/api/"
    url = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/submissions"


    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    response = requests.get(url, headers=headers, params={})

    if response.ok:
        subIds = [sub['submissionId'] for sub in response.json()]
    else:
        print(response.status_code, response.text)
        sys.exit(1)

    workflows = []

    for id in subIds:
        print(f"processing submission {id}") # TODO: verbosity options?
        suburl = f"{base_url}/workspaces/{workspaceNamespace}/{workspaceName}/submissions/{id}"
        response = requests.get(suburl, headers=headers, params={})
        if response.ok:
            workflows += response.json()['workflows']
        else:
            print(response.status_code, response.text)

    wfData = pd.DataFrame(workflows)
    wfData['sample'] = [entity['entityName'] for entity in wfData['workflowEntity']]
    wfData['entityType'] = [entity['entityType'] for entity in wfData['workflowEntity']] # needed to split single vs multi-sample workflows
    wfData['workflow'] = [inputRes[0]['inputName'].split('.')[0] for inputRes in wfData['inputResolutions']]
    wfData.to_csv("data/workflowData.tsv", sep = '\t')

if __name__ == "__main__":
    main()
