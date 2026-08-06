#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import sys

def load_flagstat(flgPath):
    flgTbl = pd.read_csv(flgPath, header=None, sep=' ', usecols=[0,2], names = ["pass", "fail"])
    flgTbl['metric'] = ["total", "primary", "secondary", "supplementary",
                        "duplicates", "primary_duplicates", "mapped", "primary_mapped",
                        "paired", "read1", "read2", "proper_pair", "mate_mapped",
                        "singleton", "discordant", "discordant_mapq5"]
    flgTbl = pd.melt(flgTbl, id_vars = ["metric"], value_vars = ["pass", "fail"],
                     var_name = "QC", value_name = "count")
    outTbl = flgTbl[['count']].T 
    outTbl.columns = flgTbl['metric'] + "_" + flgTbl['QC']
    return(outTbl)


def main():
    entityTbl = sys.argv[1]
    data = pd.read_table(entityTbl)

    summTbl = pd.concat([load_flagstat(path) for path in data['flagstat'] if isinstance(path, str) and "flagstat" in path])
    print(summTbl)

    boxplt = sns.boxplot(x="variable", y="value", data=pd.melt(summTbl))
    boxplt.get_figure().savefig("../flagstat_boxplot.png")



if __name__ == "__main__":
    main()