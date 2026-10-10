#!/usr/bin/env python3
"""Exact row-parsing comparison against ORIGINAL Clairvoyance MoneyPuck parser.

Reads original source from temporary checkout via AST; stores ONLY a checksum
and equality counts. Never downloads MoneyPuck data and never republishes
Clairvoyance source. Synthetic fixtures intentionally include missing values.
"""
from __future__ import annotations
import argparse,ast,csv,io,json,random,subprocess
from datetime import datetime,timezone
from pathlib import Path
from typing import Optional
from modeles.reproduction.clairvoyance_moneypuck_parser import (
    numeric,integer,rate_per_hour,normalize_team_record,read_team_csv)

FUNCTIONS=("_f","_i","_per60","_parse_raw_row","_parse_csv")

def original(source:Path)->dict:
    path=source/"app/scrapers/moneypuck.py"
    if not path.is_file():raise FileNotFoundError(path)
    root=ast.parse(path.read_text(encoding="utf-8"))
    selected=[node for node in root.body if isinstance(node,
              (ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in FUNCTIONS]
    if {node.name for node in selected}!=set(FUNCTIONS):
        raise ValueError("MoneyPuck original function set changed")
    module=ast.Module(body=selected,type_ignores=[])
    ast.fix_missing_locations(module)
    context={"Optional":Optional,"csv":csv,"io":io}
    exec(compile(module,str(path),"exec"),context)
    return context


def samples()->list[dict]:
    source=random.Random(160987)
    rows=[{},{"team":"team"},{"team":""},{"Team":"SEA"},
          {"team":" BOS ","situation":"5on5",
           "gamesPlayed":"10","iceTime":"600","goalsFor":"19",
           "goalsAgainst":"15","shotsOnGoalFor":"222",
           "shotsOnGoalAgainst":"200",
           "xGoalsFor":"25.5","xGoalsAgainst":"21.1",
           "xGoalsPercentage":"0.547",
           "corsiPercentage":"0.51","fenwickPercentage":"0.52",
           "highDangerGoalsFor":"5"}]
    fields=("goalsFor","GF","goalsAgainst","GA","shotsOnGoalFor",
            "shotsOnGoalAgainst","xGoalsFor","xGoalsAgainst",
            "xGoalsPercentage","iceTime","gamesPlayed",
            "corsiPercentage","fenwickPercentage",
            "highDangerGoalsFor","mediumDangerGoalsAgainst",
            "lowDangerGoalsAgainst")
    vals=(None,0,1,"0","12","12.4","52.1%","","-", "N/A","nan",
          "1.25","500","98.5")
    for n in range(170):
        obj={"team":("BOS","NYR","BUF","MTL"," VAN ")[n%5],
             "situation":("5on5","all","powerPlay")[n%3]}
        for field in fields:
            if source.random()<.52:
                obj[field]=source.choice(vals)
        rows.append(obj)
    return rows


def check(source:Path)->dict:
    orig=original(source)
    checks=0
    failures=[]
    def compare(desc,received,expected):
        nonlocal checks
        checks+=1
        if received!=expected:
            failures.append({"case":desc,"ours":repr(received)[:220],
                             "original":repr(expected)[:220]})
    for value in (None,0,3,"12.6","-","N/A","nan","1.7%","not number"):
        compare("numeric "+repr(value),numeric(value),orig["_f"](value))
        compare("int "+repr(value),integer(value),orig["_i"](value))
        compare("per60 "+repr(value),rate_per_hour(value,31.5),
                orig["_per60"](value,31.5))
    for idx,row in enumerate(samples()):
        compare("row-"+str(idx),normalize_team_record(row),
                orig["_parse_raw_row"](row))
    simple={"team":"TOR","situation":"5on5","iceTime":"350",
            "goalsFor":"13","goalsAgainst":"9","shotsOnGoalFor":"104",
            "xGoalsPercentage":"0.51"}
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(simple))
    writer.writeheader();writer.writerow(simple)
    compare("CSV roundtrip",read_team_csv(output.getvalue()),
            orig["_parse_csv"](output.getvalue()))
    if failures:
        raise AssertionError("Source-vs-Revue MoneyPuck normalization differed: "+
                             json.dumps(failures[:8],ensure_ascii=False))
    commit=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],
                                    text=True).strip()
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"moneypuck_csv_parser_exact_parity_verified",
        "reference":"Purple-Wraith/clairvoyance-backend",
        "reference_file":"app/scrapers/moneypuck.py",
        "reference_commit":commit,
        "functions_verified":list(FUNCTIONS),
        "exact_equality_tests_passed":checks,
        "monetary_use_rights_checked":False,
        "actual_money_puck_data_collected":False,
        "source_data_parity_verified":False,
        "warning":"Only normalizer parity with synthetic fixtures. MoneyPuck data has non-commercial/attribution terms. Not fetched or redistributed."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",required=True)
    ap.add_argument("--output",default="docs/parite-clairvoyance-moneypuck-parser.json")
    a=ap.parse_args()
    report=check(Path(a.reference))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("MONEYPUCK ORIGINAL NORMALIZER PARITY:",
          report["exact_equality_tests_passed"],"tests PASS; zero external data fetched")
if __name__=="__main__":
    main()
