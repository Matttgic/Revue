#!/usr/bin/env python3
"""Check EVERY historical Revue MLB Elo update against current original source.

Only reads and interprets source functions from an ephemeral GitHub checkout;
no third-party code is checked in. Same Elo arithmetic on Revue observations
does NOT establish equality of original SQL ratings or training history.
"""
from __future__ import annotations

import argparse
import asyncio
import ast
from datetime import datetime,timezone
import json
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace

from modeles.reproduction.clairvoyance_predictor import Game,mlb
from outils.verifier_parite_clairvoyance import reference_functions
from api_revue.mlb_elo import replay_mlb_elo,expected_score,update_winner_loser


def reference_elo(path:Path):
    source=path/"app/services/elo.py"
    parsed=ast.parse(source.read_text(encoding="utf-8"),filename=str(source))
    nodes=[]
    for node in parsed.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id in {"DEFAULT_RATING","K_FACTOR"}
            for t in node.targets):
            nodes.append(node)
        if isinstance(node,ast.FunctionDef) and node.name in {
            "expected_score","update_ratings",
        }:
            nodes.append(node)
    tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    env={}
    exec(compile(tree,str(source),"exec"),env)
    if not all(k in env for k in ("K_FACTOR","DEFAULT_RATING","expected_score","update_ratings")):
        raise ValueError("Original Elo computation is incomplete")
    if env["K_FACTOR"]!=32.0 or env["DEFAULT_RATING"]!=1500.0:
        raise AssertionError("Original Elo constants changed, reproduction must be revisited")
    return env


def compare_original(reference:Path,history:dict,as_of:datetime)->dict:
    original=reference_elo(reference)
    predictor=reference_functions(reference)
    replay=replay_mlb_elo(history,as_of)
    lookup={str(e["id"]):e for e in history["leagues"]["MLB"]["events"]}
    checked=0
    matched_prediction_outputs=0
    for trace in replay["trace"]:
        game=lookup[trace["espn_id"]]
        hr,ar=trace["before_home_elo"],trace["before_away_elo"]
        for a,b in ((hr,ar),(ar,hr)):
            if expected_score(a,b)!=original["expected_score"](a,b):
                raise AssertionError(f"Expected-score parity failure: {trace['espn_id']}")
        if game["home_score"]>game["away_score"]:
            want=original["update_ratings"](hr,ar)
            got=update_winner_loser(hr,ar)
            after=(trace["after_home_elo"],trace["after_away_elo"])
        else:
            want=original["update_ratings"](ar,hr)
            got=update_winner_loser(ar,hr)
            after=(trace["after_away_elo"],trace["after_home_elo"])
        if not (want==got==after):
            raise AssertionError(f"Original/Revue full Elo update mismatch: {trace['espn_id']}")
        # Compare the entire response to the original predictor functions
        # on real fixtures but independently generated pregame Elo priors.
        g=Game(str(trace["espn_id"]),trace["home"],trace["away"],
               game_date=trace["kickoff_utc"][:10],
               game_time_utc=trace["kickoff_utc"])
        db=SimpleNamespace(
            elos={("mlb",trace["home"]):hr,("mlb",trace["away"]):ar},
            xg={},goalies={},
        )
        expected=asyncio.run(predictor["predict_mlb_game"](g,db))
        actual=mlb(g,hr,ar)
        if expected!=actual:
            raise AssertionError(f"Full original/Revue MLB predictor parity mismatch {trace['espn_id']}")
        matched_prediction_outputs+=1
        checked+=1
    commit=subprocess.check_output(["git","-C",str(reference),"rev-parse","HEAD"],text=True).strip()
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"verified_elo_rule_on_revue_espn_history",
        "reference_commit":commit,
        "reference_elo_source_sha256":hashlib.sha256((reference/"app/services/elo.py").read_bytes()).hexdigest(),
        "historical_mlb_final_games_checked":checked,
        "elo_expected_probability_checks":checked*2,
        "exact_update_equal_to_original":checked,
        "mlb_original_predictor_sha256":hashlib.sha256((reference/"app/services/predictor.py").read_bytes()).hexdigest(),
        "same_input_full_prediction_objects_equal":matched_prediction_outputs,
        "predictions_are_historical_equality_tests_not_pregame_bets":True,
        "teams":replay["teams_count"],
        "default_elo":original["DEFAULT_RATING"],
        "k_factor":original["K_FACTOR"],
        "original_clairvoyance_sql_rating_parity":"NOT_VERIFIED",
        "original_clairvoyance_full_history_identical":False,
        "original_source_code_redistributed":False,
        "note":"Every Revue ESPN final replayed using source's exact Elo formula; original DB's starting ratings, data completeness and ingest time are unavailable. No betting profit claim.",
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--reference",required=True)
    cli.add_argument("--history",default="docs/multisports-history.json")
    cli.add_argument("--output",default="docs/parite-elo-mlb-source.json")
    args=cli.parse_args()
    history=json.loads(Path(args.history).read_text(encoding="utf-8"))
    report=compare_original(Path(args.reference),history,datetime.now(timezone.utc))
    destination=Path(args.output)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ELO source equality:",report["exact_update_equal_to_original"],
          "of",report["historical_mlb_final_games_checked"],"Revue ESPN finals")


if __name__=="__main__":
    main()
