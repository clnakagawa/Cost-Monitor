#!/usr/bin/env python3

import pandas as pd
import argparse
import seaborn as sns
from pathlib import Path
import matplotlib.pyplot as plt
import sys

def load_flagstat(sid,flagPath):
    flgTbl = pd.read_csv(flagPath, header=None, sep=' ', usecols=[0,2], names = ["pass", "fail"])
    flgTbl['metric'] = ["total", "primary", "secondary", "supplementary",
                        "duplicates", "primary_duplicates", "mapped", "primary_mapped",
                        "paired", "read1", "read2", "proper_pair", "mate_mapped",
                        "singleton", "discordant", "discordant_mapq5"]
    flgTbl = pd.melt(flgTbl, id_vars = ["metric"], value_vars = ["pass", "fail"],
                     var_name = "QC", value_name = "count")
    outTbl = flgTbl[['count']].T 
    outTbl.columns = flgTbl['metric'] + "_" + flgTbl['QC']
    outTbl.insert(0, 'sample', [sid])
    return(outTbl)

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
    parser.add_argument("-f", "--flagstat_field", default="flagstat", help="optional specification of flagstat output column in Terra data table")
    args = parser.parse_args()


    entityTbl = scriptDir / f"../data/{args.workspace}/{args.entType}_attributes.tsv"
    data = pd.read_table(entityTbl, sep='\t')
    charrPath = str(entityTbl).replace("_attributes.tsv", "_charr.tsv")
    demoPath = str(entityTbl).replace("_attributes.tsv", "_demo.tsv")
    flagPath = str(entityTbl).replace("_attributes.tsv", "_flag.tsv")
    charrTblSet = Path(charrPath).is_file() 
    demoTblSet = Path(demoPath).is_file()
    flagTblSet = Path(flagPath).is_file()

    charrField = f"attributes.{args.charr_field}"
    demoField = f"attributes.{args.demo_field}"
    flagField = f"attributes.{args.flagstat_field}"

    if charrField in data.columns:
        dataCharr = data[data[charrField].notna()]

        # if any charr data already stored, no need re-add data
        if charrTblSet:
            logCharr = pd.read_table(charrPath, sep='\t')
            dataCharr = dataCharr[~dataCharr['name'].isin(logCharr['#SAMPLE'])]

        print(f"Gathering charr stats for {len(dataCharr)} samples")
        summTblCharr = pd.concat([load_char(sid,path) 
                                for sid,path in 
                                zip(dataCharr['name'], dataCharr[charrField])]) if len(dataCharr) > 0 else pd.DataFrame()

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
                                zip(dataDemo['name'], dataDemo[demoField])]) if len(dataDemo) > 0 else pd.DataFrame()
        if demoTblSet:
            summTblDemo = pd.concat([logDemo, summTblDemo])
        summTblDemo.to_csv(demoPath, sep='\t',
                        index = False)
    else:
        print(f"Demographic output column {demoField} does not exist in specified table {entityTbl}")

    if flagField in data.columns:
        dataFlag = data[data[flagField].notna()]
        if flagTblSet:
            logFlag = pd.read_table(flagPath, sep='\t')
            dataFlag = dataFlag[~dataFlag['name'].isin(logFlag['sample'])]

        print(f"Gathering flagstat data for {len(dataFlag)} samples")
        summTblFlag = pd.concat([load_flagstat(sid,path) 
                                 for sid,path in zip(dataFlag['name'], dataFlag[flagField])]) if len(dataFlag) > 0 else pd.DataFrame()
        if flagTblSet:
            summTblFlag = pd.concat([logFlag, summTblFlag])
        summTblFlag.to_csv(flagPath, sep='\t', index=False)

    else:
        print("flagstat field not found in table columns")

if __name__ == "__main__":
    main()