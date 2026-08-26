#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
from pathlib import Path
import matplotlib.pyplot as plt
import sys

def load_char(sid,charrPath):
    charrTbl = pd.read_csv(charrPath, sep='\t')
    charrTbl.at[0, '#SAMPLE'] = sid
    return(charrTbl)

def load_demo(sid,demoPath):
    demoTbl = pd.read_csv(demoPath, sep='\t')
    demoTbl.at[0, 'Sample'] = sid
    return(demoTbl)

def main():
    entityTbl = sys.argv[1]
    data = pd.read_table(entityTbl, sep='\t')
    charrPath = sys.argv[1].replace("_attributes.tsv", "_charr.tsv")
    demoPath = sys.argv[1].replace("_attributes.tsv", "_demo.tsv")
    hasCharr = Path(charrPath).is_file()
    hasDemo = Path(demoPath).is_file()

    dataCharr = data[data['attributes.charr_output'].str.contains('contamination')].copy()
    dataDemo = data[data['attributes.demographics_file'].str.contains('demo.txt')].copy()

    if hasCharr:
        logCharr = pd.read_table(charrPath, sep='\t')
        dataCharr = dataCharr[~dataCharr['name'].isin(logCharr['#SAMPLE'])]

    print(f"Gathering charr stats for {len(dataCharr)} samples")
    summTblCharr = pd.concat([load_char(sid,path) 
                              for sid,path in 
                              zip(dataCharr['name'], dataCharr['attributes.charr_output'])]) if len(dataCharr) > 0 else pd.DataFrame()
    
    if hasCharr:
        summTblCharr = pd.concat([logCharr, summTblCharr])
    summTblCharr.to_csv(charrPath, sep='\t',
                   index = False)

    if hasDemo:
        logDemo = pd.read_table(demoPath, sep='\t')
        dataDemo = dataDemo[~dataDemo['name'].isin(logDemo['Sample'])]

    print(f"Gathering demographic info for {len(dataDemo)} samples")
    summTblDemo = pd.concat([load_demo(sid,path) 
                             for sid,path in 
                             zip(dataDemo['name'], dataDemo['attributes.demographics_file'])]) if len(dataDemo) > 0 else pd.DataFrame()
    if hasDemo:
        summTblDemo = pd.concat([logDemo, summTblDemo])
    summTblDemo.to_csv(demoPath, sep='\t',
                       index = False)

if __name__ == "__main__":
    main()