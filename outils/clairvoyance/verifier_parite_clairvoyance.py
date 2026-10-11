#!/usr/bin/env python3
"""Compare reconstructed predictors against the checked-out PUBLIC reference.

Only the original reference's handful of Python functions are loaded from
an ephemeral READ-ONLY checkout to evaluate their behaviour. The original
source is NOT copied into Revue, bundled, published, or used in production.
Reference imports and databases are NOT executed: dependencies are deterministic
test doubles. This verifies predictor ARITHMETIC + recommendation semantics,
not the proprietary source data, DB retrieval, or docs/app.html frontend models.
"""
from __future__ import annotations
import argparse,ast,asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from modeles.reproduction.clairvoyance_predictor import (
    Game, american_probability,american_quote,advantage_points,
    elo_home_probability,mlb,nhl,
)
PURE={"american_to_implied","implied_to_american","edge_pct","elo_win_prob"}
PREDICTORS={"predict_mlb_game","predict_nhl_game"}


def reference_functions(source:Path):
    p=source/"app/services/predictor.py"
    if not p.is_file():raise FileNotFoundError(f"Reference source absent: {p}")
    parsed=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    funcs=[n for n in parsed.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
           and n.name in PURE|PREDICTORS]
    missing=(PURE|PREDICTORS)-{x.name for x in funcs}
    if missing:raise RuntimeError(f"Reference model missing functions: {missing}")
    import math
    env={"math":math,
         "MLBGame":object,"NHLGame":object,"AsyncSession":object,
         "_DEFAULT_ELO":1500.,"_MIN_EDGE":3.}
    ast_module=ast.Module(body=funcs,type_ignores=[])
    ast.fix_missing_locations(ast_module)
    exec(compile(ast_module,str(p),"exec"),env)
    async def get_elo(db,team,sport):
        return db.elos.get((sport,team),1500.)
    async def get_moneypuck(db,team):
        value=db.xg.get(team)
        return SimpleNamespace(x_goals_pct=value) if value is not None else None
    async def get_goalie(db,team):
        return db.goalies.get(team)
    env["_get_elo"]=get_elo
    env["_get_moneypuck"]=get_moneypuck
    env["_get_starting_goalie_save_pct"]=get_goalie
    return env


def test_cases()->list[dict]:
    cases=[]
    for i,(he,ae,home_ml,away_ml,ph,pa) in enumerate([
        (1500.,1500.,-120,110,"Starter A","Starter B"),
        (1641.,1383.,-240,205,None,None),
        (1380.,1660.,270,-300,"Pitcher Alpha","Pitcher Beta"),
        (1500.,1500.,None,None,"Left","Right"),
        (1553.7,1533.2,110,-102,None,"Pitcher B"),
        (1900.,950.,-1500,900,"Home P","Away P"),
        (1050.,1890.,800,-1450,None,None),
        (1470.,1560.,-100,-100,None,None),
    ]):
        cases.append({
            "label":f"mlb_{i:02d}",
            "sport":"mlb",
            "game":Game(str(2000+i),"HOM","AWY",
                 "2026-10-10","2026-10-10T18:00:00Z",
                 home_ml,away_ml,8.5,ph,pa),
            "home_elo":he,"away_elo":ae,
        })
    for i,(he,ae,xgh,xga,gh,ga,home_ml,away_ml) in enumerate([
        (1500.,1500.,None,None,None,None,-120,110),
        (1500.,1500.,53.5,48.2,.915,.905,-105,125),
        (1700.,1400.,65.,38.,.925,.880,-210,190),
        (1400.,1700.,38.,65.,.870,.930,280,-340),
        (1521.,1498.,0.,52.,.917,.908,None,-105),
        (1480.,1560.,50.,49.,None,.900,250,-270),
        (1500.,1500.,100.,1.,.995,.800,-110,100),
        (1500.,1500.,1.,100.,.800,.995,150,-160),
        (1500.,1500.,50.,50.,.900,.900,-110,-110),
        (1450.,1650.,50.5,52.9,.900,.912,200,-250),
    ]):
        cases.append({
            "label":f"nhl_{i:02d}",
            "sport":"nhl",
            "game":Game(str(4000+i),"HOM","AWY",
                "2026-10-10","2026-10-10T19:00:00Z",
                home_ml,away_ml,5.5),
            "home_elo":he,"away_elo":ae,
            "home_xg":xgh,"away_xg":xga,
            "home_goalie":gh,"away_goalie":ga,
        })
    return cases


def verify(source:Path)->dict:
    ref=reference_functions(source)
    checks=0
    def agree(label,a,b):
        nonlocal checks
        checks+=1
        if a!=b:
            raise AssertionError(f"{label}: expected {b!r} reference, got {a!r}")
    for prob in [.01,.05,.18,.499,.5,.6,.87,.95,.99]:
        agree(f"prob->american {prob}",american_quote(prob),
              ref["implied_to_american"](prob))
    for line in [-500,-240,-110,-101,100,135,280,900]:
        agree(f"american implied {line}",american_probability(line),
              ref["american_to_implied"](line))
    for h,a,boost in [(1500.,1500.,25.),(1400.,1700.,35.),
                      (1650.,1525.,20.),(1750.,1450.,35.)]:
        agree("elo",elo_home_probability(h,a,boost),
              ref["elo_win_prob"](h,a,boost))
    for line in [-220,-100,105,240]:
        agree("market edge",advantage_points(.54,line),
              ref["edge_pct"](.54,line))
    count_by_sport={"mlb":0,"nhl":0}
    for case in test_cases():
        game=case["game"]
        sport=case["sport"]
        db=SimpleNamespace(
            elos={(sport,"HOM"):case["home_elo"],
                  (sport,"AWY"):case["away_elo"]},
            xg={"HOM":case.get("home_xg"),"AWY":case.get("away_xg")},
            goalies={"HOM":case.get("home_goalie"),
                     "AWY":case.get("away_goalie")},
        )
        if sport=="mlb":
            actual=mlb(game,case["home_elo"],case["away_elo"])
            expected=asyncio.run(ref["predict_mlb_game"](game,db))
        else:
            actual=nhl(game,case["home_elo"],case["away_elo"],
                       case.get("home_xg"),case.get("away_xg"),
                       case.get("home_goalie"),case.get("away_goalie"))
            expected=asyncio.run(ref["predict_nhl_game"](game,db))
        agree(case["label"],actual,expected)
        count_by_sport[sport]+=1
    commit=subprocess.run(["git","-C",str(source),"rev-parse","HEAD"],
              capture_output=True,text=True,check=True).stdout.strip()
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "reference":"Purple-Wraith/clairvoyance-backend",
        "reference_commit":commit,
        "reference_function_file":"app/services/predictor.py",
        "implementation_file":"modeles/reproduction/clairvoyance_predictor.py",
        "status":"predictor_formula_parity_verified",
        "exact_equality_tests_passed":checks,
        "checked_examples":count_by_sport,
        "reference_functions_verified":sorted(PURE|PREDICTORS),
        "verified_modules":["backend_mlb_elo","backend_nhl_elo_moneypuck_goalie"],
        "input_data_coverage":"mocked_observed_inputs_not_live_moneypuck_or_goalies",
        "remaining":["data_providers","database_behavior","frontend_app_models",
                     "historical_backtest","price_markets","seasons"],
        "strict_limits":"Formula parity under supplied inputs ONLY. Not complete Clairvoyance replication. No source code redistributed, no financial claims.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",required=True)
    p.add_argument("--output",default="docs/parite-clairvoyance-predictor.json")
    args=p.parse_args()
    result=verify(Path(args.reference))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PARITÉ SOURCE :",result["exact_equality_tests_passed"],
          "test comparisons matched; modules:",result["verified_modules"],
          "source:",result["reference_commit"])


if __name__=="__main__":
    main()
