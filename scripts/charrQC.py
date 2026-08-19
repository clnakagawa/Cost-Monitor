#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys

def load_char(sid,charrPath):
    charrTbl = pd.read_csv(charrPath, sep='\t')
    return(charrTbl)


def main():
    entityTbl = sys.argv[1]
    data = pd.read_table(entityTbl, sep='\t')

    summTbl = pd.concat([load_char(sid,path) for sid,path in zip(data['Sample_ID'], data['charr_output']) if isinstance(path, str) and "contamination" in path])

    summTbl.to_csv(sys.argv[1].replace("_attributes.tsv", "_charr.tsv"), sep='\t',
                   index = False)

if __name__ == "__main__":
    main()