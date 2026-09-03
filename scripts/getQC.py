#!/usr/bin/env python3

import pandas as pd
import argparse
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
    scriptDir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Gathers output from charr and infer_sex_and_ancestry for optional display in workflow tracking page")
    parser.add_argument("workspace", help="Workspace to gather data from")
    parser.add_argument("entType", help="Workspace entity type to get QC metrics for")
    parser.add_argument("-c", "--charr_field", default="charr_output", help="optional specification of charr column name in Terra data table")
    parser.add_argument("-d", "--demo_field", default="demographics_file", help="optional specification of demographic column name in Terra data table")
    args = parser.parse_args()


    entityTbl = scriptDir / f"../data/{args.workspace}/{args.entType}_attributes.tsv"
    data = pd.read_table(entityTbl, sep='\t')
    charrPath = str(entityTbl).replace("_attributes.tsv", "_charr.tsv")
    demoPath = str(entityTbl).replace("_attributes.tsv", "_demo.tsv")
    charrTblSet = Path(charrPath).is_file()
    demoTblSet = Path(demoPath).is_file()

    charrField = f"attributes.{args.charr_field}"
    demoField = f"attributes.{args.demo_field}"

    if charrField in data.columns:
        dataCharr = data[data[charrField].notna()]

        # if any charr data already stored, no need re-add data
        if charrTblSet:
            logCharr = pd.read_table(charrPath, sep='\t')
            dataCharr = dataCharr[~dataCharr['name'].isin(logCharr['#SAMPLE'])]

        print(f"Gathering charr stats for {len(dataCharr)} samples")
        summTblCharr = pd.concat([load_char(sid,path) 
                                for sid,path in 
                                zip(dataCharr['name'], dataCharr['attributes.charr_output'])]) if len(dataCharr) > 0 else pd.DataFrame()

        # if charr tables exists append instead of write
        if charrTblSet:
            summTblCharr = pd.concat([logCharr, summTblCharr])
        summTblCharr.to_csv(charrPath, sep='\t',
                    index = False)
    else:
        print(f"CHARR output column {charrField} does not exist in specified table {entityTbl}")

    if demoField in data.columns:
        dataDemo = data[data[demoField].notna()]
        if demoTblSet:
            logDemo = pd.read_table(demoPath, sep='\t')
            dataDemo = dataDemo[~dataDemo['name'].isin(logDemo['Sample'])]

        print(f"Gathering demographic info for {len(dataDemo)} samples")
        summTblDemo = pd.concat([load_demo(sid,path) 
                                for sid,path in 
                                zip(dataDemo['name'], dataDemo['attributes.demographics_file'])]) if len(dataDemo) > 0 else pd.DataFrame()
        if demoTblSet:
            summTblDemo = pd.concat([logDemo, summTblDemo])
        summTblDemo.to_csv(demoPath, sep='\t',
                        index = False)
    else:
        print(f"Demographic output column {demoField} does not exist in specified table {entityTbl}")

if __name__ == "__main__":
    main()