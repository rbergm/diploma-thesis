#!/usr/bin/env python3

import argparse

import pandas as pd

from transform import mosp
from postgres import hint


def read_input(src: str, query_col: str) -> pd.DataFrame:
    df = pd.read_csv(src)
    df[query_col] = df[query_col].apply(mosp.MospQuery.parse)
    return df


def main():
    parser = argparse.ArgumentParser(description="Generates SQL query hints for various workloads.")
    parser.add_argument("input", action="store", help="CSV file containing the workload queries")
    parser.add_argument("--mode", "-m", action="store", default="ues-idxnlj", help="The kind of hints to produce. "
                        "Currently only 'ues-idxnlj' (the default) is supported, which enforces an "
                        "Index-NestedLoopJoin in UES subqueries queries.", choices=["ues-idxnlj"])
    parser.add_argument("--idx-target", action="store", default="fk", choices=["pk", "fk"], help="For "
                        "'ues-idxnlj'-mode: The subquery join-partner that should be implemented as IndexScan. Can be "
                        "either 'pk' or 'fk', denoting the Primary key table and Foreign key table, respectively.")
    parser.add_argument("--nlj-scope", action="store", default="first", choices=["first", "all"], help=" For "
                        "'ues-idxnlj'-mode: How many Index-Nested loop joins should be generated. Can be either "
                        "'first' denoting only the innermost join, or 'all', denoting all joins.")
    parser.add_argument("--out", "-o", action="store", default="out.csv", help="Name of the CSV file to store the "
                        "output")
    parser.add_argument("--query-col", action="store", default="query", help="Name of the CSV column containing the "
                        "workload")
    parser.add_argument("--hint-col", action="store", default="hint", help="Name of the CSV column to write the "
                        "generated hints to")

    args = parser.parse_args()
    df = read_input(args.input, args.query_col)
    df[args.hint_col] = (df[args.query_col]
                         .apply(hint.idxnlj_subqueries, nestloop=args.nlj_scope, idxscan=args.idx_target)
                         .apply(hint.HintedMospQuery.generate_sqlcomment, strip_empty=True))

    df.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
