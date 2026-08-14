#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys

def load_flagstat(sid,flgPath):
    flgTbl = pd.read_csv(flgPath, header=None, sep=' ', usecols=[0,2], names = ["pass", "fail"])
    flgTbl['metric'] = ["total", "primary", "secondary", "supplementary",
                        "duplicates", "primary_duplicates", "mapped", "primary_mapped",
                        "paired", "read1", "read2", "proper_pair", "mate_mapped",
                        "singleton", "discordant", "discordant_mapq5"]
    flgTbl = pd.melt(flgTbl, id_vars = ["metric"], value_vars = ["pass", "fail"],
                     var_name = "QC", value_name = "count")
    outTbl = flgTbl[['count']].T 
    outTbl.columns = flgTbl['metric'] + "_" + flgTbl['QC']
    outTbl['sample_ID'] = sid
    return(outTbl)


def main():
    entityTbl = sys.argv[1]
    data = pd.read_table(entityTbl)

    summTbl = pd.concat([load_flagstat(sid,path) for sid,path in zip(data['Sample_ID'], data['flagstat']) if isinstance(path, str) and "flagstat" in path])

    summTbl.to_csv(sys.argv[1].replace("_attributes.tsv", "_flagstat.tsv"), sep='\t',
                   index = False)
    # denom = summTbl["total_pass"] + summTbl["total_fail"]
    # cols = list(summTbl.columns.difference(["total_pass", "total_fail"]))
    # summTbl[cols] = summTbl[cols].div(denom, axis=0)

    # summTblPass = summTbl.iloc[:,0:16]
    # summTblFail = summTbl.iloc[:,16:32]
    # print(summTbl.columns)

    # print(summTblPass)
    # print(summTblFail)


    # # QC passed reads
    # summTblPass = pd.melt(summTblPass, var_name="variable", value_name="value")
    # gpass = sns.FacetGrid(summTblPass, row = "variable",
    #                   height=1.2, aspect=5, sharex=False)
    # gpass.map(sns.boxplot, "value")
    # plt.savefig("../plots/flagstat_pass_boxplot.png")
    # plt.clf()

    # # QC Failed reads
    # summTblFail = pd.melt(summTblFail, var_name="variable", value_name="value")
    # gfail = sns.FacetGrid(summTblFail, row = "variable",
    #                       height=1.2, aspect=5, sharex=False)
    # gfail.map(sns.boxplot, "value")
    # plt.savefig("../plots/flagstat_fail_boxplot.png")

    # #TODO Filter and create lists to remove
    # # Integrate with API to edit sets? Not sure


if __name__ == "__main__":
    main()