#!/usr/bin/env python3
"""Real NHL fixture input-output parity versus current original predictor.

Uses ONLY independently observed Revue xG, goalie and Elo proxy features
on genuine NHL fixtures. Source predictor AST is executed in read-only CI
test doubles. This never establishes that source provider/DB inputs matched
Clairvoyance's live system; that is a separate unverified question.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import subprocess
from types import SimpleNamespace

from modeles.reproduction.clairvoyance_predictor import Game,nhl
from outils.verifier_parite_clairvoyance import reference_functions
from outils.nhl_point_in_time_audit import as_utc


def _goalie(row:dict,side:str) -> float | None:
    item=(row.get("historical_goalie_proxy") or {}).get(side)
    if item is None:
        return None
    save=item.get("save_pct")
    if type(save) not in (int,float) or not math.isfinite(save) or not 0<save<=1:
        raise ValueError("Incorrect goalie proxy save percentage")
    return float(save)


def validate_rows(report:dict) -> list[dict]:
    if (report.get("status")!="experimental_not_calibrated" or
        (report.get("point_in_time_audit") or {}).get("status")!="verified_temporal_bounds" or
        report.get("bookmaker_odds_available") is not False):
        raise ValueError("Revue NHL source lacks provenance / safe status")
    source_time=as_utc(report["generated_at_utc"])
    if source_time != as_utc(report["point_in_time_audit"]["as_of_utc"]):
        raise ValueError("Mismatch in NHL audit timestamp")
    rows=report.get("games")
    if not isinstance(rows,list) or not rows:
        raise ValueError("No genuine NHL events available to compare")
    ids=set()
    for game in rows:
        key=game["event_id"]
        if key in ids:
            raise ValueError("Duplicated NHL event ID")
        ids.add(key)
        if not (as_utc(game["start_utc"])>source_time):
            raise ValueError("Non-prospective fixture in the audit")
        for field in ("home_elo_proxy","away_elo_proxy"):
            x=game[field]
            if type(x) not in (int,float) or not math.isfinite(x):
                raise ValueError("Non-finite Elo input")
        xg=game.get("xg_5v5_share_pct") or {}
        for side in ("home","away"):
            val=xg.get(side)
            if type(val) not in (float,int) or not math.isfinite(val) or not 0<=val<=100:
                raise ValueError("Invalid MoneyPuck xG input")
            _goalie(game,side)
        if game.get("market_odds") is not None or game.get("betting_recommendation") is not None:
            raise ValueError("Only no-market research forecasts can be audited")
    return rows


def compare(source:Path,report:dict) -> dict:
    rows=validate_rows(report)
    functions=reference_functions(source)
    commit=subprocess.run(["git","-C",str(source),"rev-parse","HEAD"],
        capture_output=True,text=True,check=True).stdout.strip()
    checked=[]
    for row in rows:
        home,away=row["home"],row["away"]
        h_elo,a_elo=float(row["home_elo_proxy"]),float(row["away_elo_proxy"])
        xg=row["xg_5v5_share_pct"]
        hg,ag=_goalie(row,"home"),_goalie(row,"away")
        game=Game(str(row["event_id"]),home,away,game_time_utc=row["start_utc"])
        db=SimpleNamespace(
            elos={("nhl",home):h_elo,("nhl",away):a_elo},
            xg={home:xg["home"],away:xg["away"]},
            goalies={home:hg,away:ag},
        )
        reference=asyncio.run(functions["predict_nhl_game"](game,db))
        own=nhl(game,h_elo,a_elo,xg["home"],xg["away"],hg,ag)
        # Entire result dict (including metadata and recommendation) must match.
        if reference != own:
            raise AssertionError("Original/Revue outputs differ on an observed NHL event")
        checked.append({
            "event_id":str(row["event_id"]),
            "matched_all_output_fields":True,
            "matches_published_shadow_probability":
                own["model_home_win_prob"]==row["home_win"] and
                own["model_away_win_prob"]==row["away_win"],
        })
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "reference":"Purple-Wraith/clairvoyance-backend",
        "reference_commit":commit,
        "report_input_generated_at_utc":report["generated_at_utc"],
        "status":"exact_model_output_parity_on_same_revue_observed_inputs",
        "input_origin":"Revue observed NHL Web API Elo proxy and MoneyPuck seasonal aggregates",
        "original_data_sources_identical":False,
        "identical_original_clairvoyance_predictions_proven":False,
        "real_nhl_fixtures_compared":len(checked),
        "reference_vs_revue_entire_output_dict_equal":len(checked),
        "same_published_shadow_probability_count":sum(
            x["matches_published_shadow_probability"] for x in checked
        ),
        "published_forecasts_with_rounded_elo_proxy_mismatch":sum(
            not x["matches_published_shadow_probability"] for x in checked
        ),
        "games":checked,
        "note":"All original and Revue outputs are compared on common real Revue inputs. It does NOT prove the original's own Elo database, pregame goalie selections or model datasets matched. Published Elo proxy rounds to 2 decimals; tiny published probability deviations may follow.",
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--reference",required=True)
    cli.add_argument("--input",default="docs/nhl-clairvoyance-shadow-latest.json")
    cli.add_argument("--output",default="docs/parite-clairvoyance-nhl-observe.json")
    args=cli.parse_args()
    report=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result=compare(Path(args.reference),report)
    p=Path(args.output)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("NHL reference vs Revue on real observed inputs:",result["reference_vs_revue_entire_output_dict_equal"],"/",result["real_nhl_fixtures_compared"],"matched, original-data parity unverified")


if __name__=="__main__":
    main()
