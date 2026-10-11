#!/usr/bin/env python3
"""Direct strict source parity for ESPN byteam parsing and advanced team ratings."""
from __future__ import annotations
import argparse,ast,copy,json,random,subprocess
from datetime import datetime,timezone
from pathlib import Path
from modeles.reproduction import clairvoyance_nba_espn_source as own

NAMES={"_f","parse_byteam","_poss","row_from_raw",
       "rows_from_byteam","attach_records"}
def orig(root:Path):
    file=root/"scripts/_nba_espn.py"
    tree=ast.parse(file.read_text(encoding="utf-8"))
    funcs=[node for node in tree.body if isinstance(node,ast.FunctionDef)
           and node.name in NAMES]
    if {f.name for f in funcs}!=NAMES:raise ValueError("Upstream NBA parser functions changed")
    env={"NBA_ESPN_TEAM_TOV_PER_GAME":.75,"NBA_ESPN_OT_PACE_FACTOR":.995}
    exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),
                 str(file),"exec"),env)
    return env

def fake(rng:random.Random,gp:int):
    def metrics(forward):
        return {"gamesPlayed":gp,
                "fieldGoalsAttempted":gp*rng.uniform(76,100),
                "fieldGoalsMade":gp*rng.uniform(34,42),
                "threePointFieldGoalsMade":gp*rng.uniform(11,18),
                "freeThrowsAttempted":gp*rng.uniform(12,30),
                "freeThrowsMade":gp*rng.uniform(10,22),
                "offensiveRebounds":gp*rng.uniform(6,15),
                "defensiveRebounds":gp*rng.uniform(23,35),
                "rebounds":gp*rng.uniform(40,45),
                "turnovers":gp*rng.uniform(9,17),
                "points":gp*rng.uniform(93,126)
                }
    a=metrics(True);b=metrics(False);b["gamesPlayed"]=gp
    return {"id":"123","name":"Test Team","own":a,"opp":b}

def verify(path:Path):
    ref=orig(path)
    rng=random.Random(82632)
    counts={"parse_byteam":0,"row_from_raw":0,
            "rows_from_byteam":0,"attach_records":0}
    def match(key,a,b):
        if a!=b:
            raise AssertionError(f"ESPNSOURCE PARITY {key}: reference={a!r} own={b!r}")
        counts[key]+=1
    for i in range(180):
        gp=rng.choice([0,1,2,5,15,82])
        raw=fake(rng,gp)
        if i%19==0:raw["own"].pop("points",None)
        if i%17==0:raw["opp"].pop("defensiveRebounds",None)
        if i%23==0:raw["own"]["fieldGoalsAttempted"]=0
        if i%31==0:raw["own"]["gamesPlayed"]="n/a"
        r1=ref["row_from_raw"](copy.deepcopy(raw))
        r2=own.row_from_raw(copy.deepcopy(raw))
        match("row_from_raw",r1,r2)
    for i in range(110):
        names=["general","offensive","defensive"]
        labels={category:list(fake(rng,10)["own"])[:8]
                for category in names}
        team=[]
        for t in range(i%7+1):
            a=fake(rng,10)
            team.append({"team":{"id":str(t),"abbreviation":f"T{t}","displayName":f"Team {t}"},
            "categories":[
                {"name":name,"splitId":part,
                 "values":[a["own" if part=="0" else "opp"].get(n)
                           for n in cols]}
                for name,cols in labels.items() for part in ("0","900")]})
        categories=[{"name":n,"names":v} for n,v in labels.items()]
        payload={"teams":team,"categories":categories,"requestedSeason":{"year":2026}}
        if i%13==0:payload["requestedSeason"]={"year":2025}
        if i%17==0:payload["categories"]=[]
        match("parse_byteam",ref["parse_byteam"](copy.deepcopy(payload),2026),
              own.parse_byteam(copy.deepcopy(payload),2026))
        match("rows_from_byteam",ref["rows_from_byteam"](copy.deepcopy(payload),2026),
              own.rows_from_byteam(copy.deepcopy(payload),2026))
    for i in range(60):
        test={f"T{k}":{"w":0,"l":0} for k in range(4)}
        standings={f"T{k}":{"w":str(i+k),"l":str(i//2+k)} for k in range(i%4)}
        a=copy.deepcopy(test);b=copy.deepcopy(test)
        match("attach_records",
              ref["attach_records"](a,standings),own.attach_records(b,standings))
    sha=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
                       text=True,capture_output=True,check=True).stdout.strip()
    return {"generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "reference_commit":sha,"status":"nba_espn_byteam_strict_parity",
            "checked_examples":counts,
            "tests_passed":sum(counts.values()),
            "note":"Direct equality to original ESPN source parser only. No claim of source data parity in all game states."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",required=True)
    ap.add_argument("--output",default="docs/parite-clairvoyance-espn-nba.json")
    args=ap.parse_args()
    report=verify(Path(args.reference))
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Strict ESPN NBA data parser parity:",report["tests_passed"])
if __name__=="__main__":main()
