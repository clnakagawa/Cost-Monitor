#!/usr/bin/env python3

import yaml
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import sys
import google.auth
from google.auth.transport.requests import Request
from pathlib import Path

# constants
BASE_URL = "https://api.firecloud.org/api"

# workspace class to avoid too many args
# just storing info for now
class Workspace:
    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

# current solution for authenticating for google cloud access
# requires setup of refresh token on whatever system is running this tool
def get_access_token():
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

# get array of entity names
def get_entity_types(ws, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/entities", 
                            headers=headers, 
                            params={})
    # return(response.text)
    return(list(response.json().keys()))

# get table for a given entity
def get_entity_tables(ws, entTypes, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/entities_with_type",
                            headers=headers,
                            params={})

    # make dict with entry for each entity
    entTbls = {entType:[] for entType in entTypes}

    # iterate over list of entities and assign by entity type
    for ent in response.json():
        entTbls[ent['entityType']].append(ent['attributes'])
    
    return({ent:pd.json_normalize(entTbl) for ent, entTbl in entTbls.items()})

# get all submissions for a workspace
def get_submissions(ws, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/submissions",
                            headers=headers,
                            params={})
    return([sub['submissionId'] for sub in response.json() if sub['status'] in ["Done", "Aborted"]])

def get_methods(ws, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/methodconfigs",
                            headers=headers,
                            params={'allRepos' : 'true'})
    return([method['name'] for method in response.json()])


def get_submission_info(ws, subId, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/submissions/{subId}", headers=headers, params={})
    return(response.json())

def get_workflow_info(ws, wfId, headers):
    response = requests.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/workflows")

# get submission data from list of IDs and create table
def get_submission_table(ws, subList, methodList, headers):
    newSubTbl=pd.DataFrame()
    for id in subList:
        print(f"processing submission {id}") # TODO: verbosity options?
        suburl = f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/submissions/{id}"
        response = requests.get(suburl, headers=headers, params={})
        if response.ok:
            respJson = response.json()
            if any([method in respJson['methodConfigurationName'] for method in methodList]):
                newSubTbl = pd.concat([newSubTbl, json_to_table(respJson)])
            else:
                print(f"submission using config {respJson['methodConfigurationName']} does not match a current workflow method")
        else:
            print(response.status_code, response.text)
    return(newSubTbl)

def get_storage_cost_table(ws, headers):
    response = requests.get(f"{BASE_URL}/workspaces/v2/{ws.namespace}/{ws.name}/storageCostEstimate", headers=headers, params={})
    return(pd.DataFrame(pd.json_normalize(response.json())))


# format workflow table for dashboard processing
def json_to_table(sub_json):
    subTable = pd.DataFrame(sub_json['workflows'])
    subTable['workflowVersion'] = sub_json['methodConfigurationName']
    subTable['sample'] = [entity['entityName'] for entity in subTable['workflowEntity']]
    subTable['entityType'] = [entity['entityType'] for entity in subTable['workflowEntity']] # needed to split single vs multi-sample workflows
    subTable['workflow'] = [inputRes[0]['inputName'].split('.')[0] for inputRes in subTable['inputResolutions']]
    return(subTable)
