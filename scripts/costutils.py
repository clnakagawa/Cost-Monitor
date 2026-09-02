#!/usr/bin/env python3

import yaml
import re
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

def get_session():
    TOKEN=get_access_token()
    s = requests.Session()
    s.headers.update({'Authorization': f"Bearer {TOKEN}"})
    return(s)

# get array of entity names
def get_entity_types(ws, s):
    response = s.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/entities")
    return(list(response.json().keys()))

def get_entity_table(ws, entType, s):
    response = s.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/entities/{entType}")
    return(pd.json_normalize(response.json()))

# get all submissions for a workspace
def get_submissions(ws, s):
    response = s.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/submissions")
    # return([sub['submissionId'] for sub in response.json()])
    return([sub['submissionId'] for sub in response.json() if sub['status'] in ["Done", "Aborted"]])

def get_methods(ws, s):
    response = s.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/methodconfigs",
                     params={'allRepos': True})
    return([method['name'] for method in response.json()])


def get_submission_info(ws, subId, s):
    response = s.get(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/submissions/{subId}")
    return(response)

# get submission data from list of IDs and create table
def get_submission_table(ws, subList, methodList, s):
    newSubTbl=pd.DataFrame()
    for id in subList:
        print(f"processing submission {id}") # TODO: verbosity options?
        response = get_submission_info(ws, id, s)
        if response.ok:
            respJson = response.json()
            if any([method in respJson['methodConfigurationName'] for method in methodList]):
                newSubTbl = pd.concat([newSubTbl, json_to_table(respJson)])
            else:
                print(f"submission using config {respJson['methodConfigurationName']} does not match a current workflow method")
        else:
            print(response.status_code, response.text)
    return(newSubTbl)

def get_storage_cost_table(ws, s):
    response = s.get(f"{BASE_URL}/workspaces/v2/{ws.namespace}/{ws.name}/storageCostEstimate")
    return(pd.DataFrame(pd.json_normalize(response.json())))


# format workflow table for dashboard processing
def json_to_table(sub_json):
    subTable = pd.DataFrame(sub_json['workflows'])
    subTable['workflowVersion'] = sub_json['methodConfigurationName']
    if not 'workflowEntity' in subTable.columns:
        return(pd.DataFrame())
    subTable['sample'] = [entity['entityName'] for entity in subTable['workflowEntity']]
    subTable['entityType'] = [entity['entityType'] for entity in subTable['workflowEntity']] # needed to split single vs multi-sample workflows
    subTable['workflow'] = [inputRes[0]['inputName'].split('.')[0] for inputRes in subTable['inputResolutions']]
    return(subTable)

# json list element to include in sample set patch request data to add element
def format_add_json(entName, entType):
    return({'op': 'AddListMember', 'attributeListName': f"{entType}s", 
            'newMember': {'entityType': entType, 'entityName': entName}})

# json list element to include in sample set patch request data to remove element
def format_rem_json(entName, entType):
    return({'op': 'RemoveListMember', 'attributeListName': f"{entType}s", 
            'removeMember': {'entityType': entType, 'entityName': entName}})

# update sample set with additions/removals 
def update_set(ws, s, set, add, remove, entType):
    url = f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/entities/{entType}_set/{set}"
    data = [format_add_json(ent, entType) for ent in add] + [format_rem_json(ent, entType) for ent in remove]
    return(s.patch(url, json = data))

# add sample sets to workspace
def add_sets(ws, s, sets, entType):
    setdf = pd.DataFrame(sets, columns = [f"entity:{entType}_set_id"])
    return(s.post(f"{BASE_URL}/workspaces/{ws.namespace}/{ws.name}/flexibleImportEntities",
                  files={"entities": setdf.to_csv(sep='\t', index=0)}))

# get all samples currently assigned to sets
def get_assigned_entities(setTblPath, entType):
    tbl = pd.read_csv(setTblPath, sep='\t')
    set_ents = []
    for set in tbl[f"attributes.{entType}s.items"]:
        set_ents = set_ents + re.findall("(?<=Name': ').*?(?='})", set)
    return(set_ents)

# make dictionary object from sample_set attribute table
def set_table_dict(setTblPath, entType):
    tbl = pd.read_csv(setTblPath, sep='\t')
    entDict = {}
    for index, row in tbl.iterrows():
        for ent in re.findall("(?<=Name': ').*?(?='})", row[f"attributes.{entType}s.items"]):
            entDict[ent] = row['name']
    return(entDict)