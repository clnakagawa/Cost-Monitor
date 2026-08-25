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
    if not response.ok:
        print(response.text)
        return

    # get list of fails for the specified submission
    subTbl = json_to_table(response.json())  
    fails = subTbl[subTbl['status'] == "Failed"]['sample']
    entType = subTbl['entityType'][1]

    entDict = set_table_dict(f"../data/{ws.name}/{entType}_set_attributes.tsv", entType)
    fails = [f for f in fails if entDict[f] != args.fail_set]

    if len(fails) < 1:
        print("No fails to move")
        return

    print(f"Adding {len(fails)} samples to set {args.fail_set}")    
    response = update_set(ws, s, args.fail_set, fails, [], entType)

    if not response.ok:
        print(response.text)
        return

    if args.keep:
        print("Keeping entities in original sets")
        return

    # make dict to figure out sample sets to edit
    # probably most robust way of doing this
    entDict = set_table_dict(f"../data/{ws.name}/{entType}_set_attributes.tsv", entType)

    

    

    
    

if __name__ == "__main__":
    main()