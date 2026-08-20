#!/usr/bin/env python3

from costutils import *
import argparse

def main():
    parser = argparse.ArgumentParser(description="Script to add sample sets to a workspace")
    parser.add_argument('workspace', help="Name of the workspace to edit formatted as <namespace>/<name>")
    parser.add_argument('entity_type', help="Name of the entity type for sets to add")
    parser.add_argument('-s', '--setsize', type=int, help="Size of the sets to add (default 80)", default=80)
    parser.add_argument('-n', '--nsets', type=int, help="Number of sets to add (default as many as possible)", default=-1)
    parser.add_argument('-p', '--prefix', help="Prefix for set names (s.t. sets are <prefix>_set<set number>_<set size>)", default="")
    parser.add_argument('--setnames', nargs='+', help="space-separated list of new set names")

    args = parser.parse_args()
    ws = Workspace(args.workspace.split('/')[0], args.workspace.split('/')[1])

    setTblPath=f"../data/{ws.name}/{args.entity_type}_set_attributes.tsv"
    entTblPath=f"../data/{ws.name}/{args.entity_type}_attributes.tsv"
    prefix = args.prefix if args.prefix != "" else ws.name.split('-')[-1]

    # setup api session
    s = get_session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # number of existing sets
    setTbl = pd.read_csv(setTblPath, sep='\t')
    # doesn't count failure set (assumes failure set name !includes 'set')
    numOldSets=sum(1 for setname in setTbl['name'] if 'set' in setname) 

    # list of entity names already added to sets
    setEnts = get_assigned_entities(setTblPath, args.entity_type)

    # list of all entities
    allEnts = list(pd.read_csv(entTblPath, sep='\t')['name'])

    # list of entities to assign to sets
    newEnts = [ent for ent in allEnts if ent not in setEnts]

    # number of sets to make, default is max number possible
    nsets = args.nsets if args.nsets > 0 else -(len(newEnts) // -args.setsize)

    newSets = [newEnts[(setNum * args.setsize):(min(((setNum+1) * args.setsize, len(newEnts))))] for setNum in range(nsets)]

    if args.setnames is None:
        setNames = [f"{prefix}_set_{i+numOldSets+1}_{len(newSets[i])}" for i in range(nsets)]
    elif len(args.setnames) != nsets:
        print("Not enough set names provided, defaulting to standard naming scheme")
        setNames = [f"{prefix}_set_{i+numOldSets+1}_{len(newSets[i])}" for i in range(nsets)]
    else:
        setNames = args.setnames

    print(f"Total: {len(newEnts)}")
    print(f"Number of sets: {nsets}")

    response = add_sets(ws, s, setNames, args.entity_type)
    if (response.status_code != 200):
        print("There was an issue adding sample sets to workspace")
        print(response.text)

    for i in range(nsets):
        response = update_set(ws ,s, setNames[i], newSets[i], [], args.entity_type)
        if (response.status_code != 200):
            print(f"There was an issue adding set {setNames[i]} to workspace")
            print(response.text)


if __name__ == "__main__":
    main()

