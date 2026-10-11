#!/usr/bin/env python3
"""CI parity check against 4 real source-side NBA preprocessing functions.

Reference is an ephemeral public repository checkout, AST extraction (pure
functions only). Does not fetch paid basketball-reference pages, redistribute
unlicensed code or claim live data parity.
"""
from __future__ import annotations
import argparse,ast,copy
from datetime import date,datetime,timezone
import json,os,random
from pathlib import Path
import subprocess
from modeles.reproduction.clairvoyance_nba_source import (
    prior_nba_end_year,select_team_stats,build_team_ratings,annotate_player_tiers
)

NAMES={"nba_season_end_year","_bb_float","_nba_mov_prior",
       "select_nba_team_stats","build_nba_team_ratings","apply_nba_player_tiers"}
CONSTANTS={
    "NBA_MIN_GAMES_FOR_CURRENT":15,
    "NBA_MIN_TEAMS_FOR_CURRENT":24,
    "NBA_ELO_MEAN":1550,
    "NBA_ELO_PER_POINT":28,
    "NBA_PRIOR_CARRY":.75,
    "NBA_PRIOR_GAMES":20,
    "NBA_TIER_MIN_GP":15,
    "NBA_TIER_PPG":((24.,"PREMIUM"),(18.,"OPTIMAL"),(12.,"GOOD")),
}

def original_functions(root:Path):
    ref=root/"scripts/clairvoyance_update.py"
    content=ref.read_text(encoding="utf-8")
    tree=ast.parse(content)
    methods=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name in NAMES]
    if len(methods)!=len(NAMES):
        raise AssertionError("Source changed; expected 6 reference functions, found "+str([x.name for x in methods]))
    code=ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[]))
    env={"os":os,"datetime":datetime,"NOW_MT":datetime(2026,10,10),"TODAY_ISO":"2026-10-10",
         "log":lambda *args,**kwargs:None, **CONSTANTS}
    exec(compile(code,str(ref),"exec"),env)
    return env

def verify(root:Path):
    env=original_functions(root)
    checked=0
    counts={"backend_nba_season":0,"backend_nba_stats_selection":0,
            "backend_nba_team_ratings":0,"backend_nba_player_tiers":0}
    def match(label,key,reference,actual):
        nonlocal checked
        checked+=1
        if reference!=actual:
            raise AssertionError(f"Mismatch {label}: SOURCE {reference!r} REPLICA {actual!r}")
        counts[key]+=1
    for month in range(1,13):
        for value in [None,"",2028,"2027","2101","1999","garbage"," 2026 "]:
            x=date(2026,month,15)
            reference=env["nba_season_end_year"](today=x,override=value)
            actual=prior_nba_end_year(x,value)
            match("season "+str(month)+"/"+str(value),"backend_nba_season",reference,actual)
    rng=random.Random(2048)
    for i in range(90):
        last={}
        cur={}
        for j in range(30):
            abbr=f"T{j:02d}"
            if rng.random()<.83:
                last[abbr]={"name":abbr,"gp":82,"ortg":rng.uniform(105,126),
                            "drtg":rng.uniform(105,126),"pace":rng.uniform(94,105)}
            if rng.random()<.9:
                gp=rng.randint(0,82)
                cur[abbr]={"name":abbr,"gp":gp,
                           "ortg":rng.uniform(105,126) if rng.random()>.2 else None,
                           "drtg":rng.uniform(105,126) if rng.random()>.2 else None}
        min_teams=rng.choice([0,10,20,24,29,30,35])
        min_games=rng.choice([0,2,5,15,30])
        result=env["select_nba_team_stats"](cur,last,2027,2026,min_games,min_teams)
        own=select_team_stats(cur,last,2027,2026,min_games,min_teams)
        match("stats select "+str(i),"backend_nba_stats_selection",result,own)

    team_names=[f"T{i:02d}" for i in range(14)]
    for i in range(100):
        prev={}
        current={}
        espn_before={}
        espn_now={}
        for abbr in team_names:
            if rng.random()<.73:
                prev[abbr]={"name":abbr,"w":rng.randint(0,82),"l":rng.randint(0,82),
                    "srs":rng.uniform(-12,13) if rng.random()<.6 else None,
                    "mov":rng.uniform(-12,13) if rng.random()<.6 else None,
                    "net_rtg":rng.uniform(-12,13) if rng.random()<.6 else None,
                    "ortg":rng.uniform(103,127),"drtg":rng.uniform(103,127),
                    "pace":rng.uniform(90,106)}
            if rng.random()<.6:
                current[abbr]={"name":abbr,"w":rng.randint(0,32),"l":rng.randint(0,32),
                    "mov":rng.uniform(-15,15) if rng.random()<.7 else None,
                    "net_rtg":rng.uniform(-14,14)}
            if rng.random()<.83:
                espn_before[abbr]={"w":str(rng.randint(20,65)),
                                   "l":str(rng.randint(20,65)),
                                   "diff":str(round(rng.uniform(-12,12),3))}
            if rng.random()<.63:
                espn_now[abbr]={"w":str(rng.randint(0,25)),
                                "l":str(rng.randint(0,25)),
                                "diff":str(round(rng.uniform(-12,12),3))}
        selection={"seasonUsed":rng.choice([2026,2027,"2027/2026",None]),
                   "mode":rng.choice(["prior","current","mixed","none"])}
        ref=env["build_nba_team_ratings"](prev,current,espn_before,espn_now,
                                          2027,2026,selection)
        got=build_team_ratings(prev,current,espn_before,espn_now,
                               2027,2026,selection,"2026-10-10")
        match("team ratings "+str(i),"backend_nba_team_ratings",ref,got)
    for i in range(80):
        roster={f"player{j}":{"team":"BOS",
                  **({"rating":"GOOD"} if rng.random()<.32 else {})}
                for j in range(12)}
        players=[{"name":f"Player{j}","gp":rng.randint(0,35),
                  "ppg":round(rng.uniform(0,33),2)}
                 for j in range(12)]
        flag=bool(i%2)
        a=copy.deepcopy(roster)
        b=copy.deepcopy(roster)
        count_a=env["apply_nba_player_tiers"](a,players,only_missing=flag)
        count_b=annotate_player_tiers(b,players,only_missing=flag)
        match("tier count "+str(i),"backend_nba_player_tiers",count_a,count_b)
        match("tier roster "+str(i),"backend_nba_player_tiers",a,b)
    sha=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                       capture_output=True,text=True,check=True).stdout.strip()
    return {"generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "reference":"Purple-Wraith/clairvoyance-backend",
            "reference_commit":sha,
            "source_file":"scripts/clairvoyance_update.py",
            "status":"nba_preprocessing_exact_parity_verified",
            "verified_modules":list(counts),
            "exact_equality_tests_passed":checked,
            "checked_examples":counts,
            "note":"Only source-function behavior on same synthetic inputs. No live NBA dataset equivalence verified."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",required=True)
    ap.add_argument("--output",default="docs/parite-clairvoyance-nba-source.json")
    a=ap.parse_args()
    result=verify(Path(a.reference))
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("Source NBA exact parity:",result["exact_equality_tests_passed"],
          "comparisons over",len(result["verified_modules"]),"target functions.")

if __name__=="__main__":main()
