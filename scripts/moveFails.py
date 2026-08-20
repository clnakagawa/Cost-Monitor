#!/usr/bin/env python3

from costutils import *
import argparse

def main():
    parser = argparse.ArgumentParser(description="Script to move failed samples from a workflow to a specified sample set")
    parser.add_argument('workspace', help="Name of the workspace to edit formatted as <namespace>/<name>")
    # parser.add_argument('entity_type', help="Name of the entity type in the sample set") # maybe could derive this from something else
    parser.add_argument('submission_id', help="Submission id of workflow submission to organize fails")
    parser.add_argument('fail_set', help="Name of sample set to move failed workflows to")
    parser.add_argument('--keep', action='store_true', help="If set, samples are moved to failure set but not removed from original set")

    args = parser.parse_args()

    s = get_session()
    ws = Workspace(args.workspace.split('/')[0], args.workspace.split('/')[1])

    response = get_submission_info(ws, args.submission_id, s)
    if response.status_code != 200:
        print(response.text)
        return

    # get list of fails for the specified submission
    subTbl = json_to_table(response.json())  
    fails = subTbl[subTbl['status'] == "Failed"]['sample']
    entType = subTbl['entityType'][1]
    

if __name__ == "__main__":
    main()