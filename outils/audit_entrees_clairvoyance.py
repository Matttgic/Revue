#!/usr/bin/env python3
"""Read-only coverage audit for REPRODUCING Clairvoyance input datasets.

A source-formula parity result is NOT a real-input parity result.
Never infer availability from schema presence, static fallback tables,
generated odds, generic team scores, or a previous-season season label.
No external requests and no user betting actions.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path


def json_read(root:Path,name:str)->dict:
    path=root/"docs"/name
    if not path.is_file():return {}
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        return {}
    return value if isinstance(value,dict) else {}


def check(root:Path,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Use timezone aware clock")
    advanced=json_read(root,"clairvoyance-nba-advanced-ratings.json")
    parser=json_read(root,"parite-clairvoyance-espn-nba.json")
    sport=json_read(root,"football-espn-team-features.json")
    scanner=json_read(root,"engine-v2-latest.json")
    rates=advanced.get("teamRatings") or {}
    teams=rates.get("teams") or {}
    teams=teams if isinstance(teams,dict) else {}
    prior=sum(bool((x.get("prior") or {}).get("ortg") is not None and
                   (x.get("prior") or {}).get("drtg") is not None)
              for x in teams.values() if isinstance(x,dict))
    current=sum(bool((x.get("current") or {}).get("netRtg") is not None)
                for x in teams.values() if isinstance(x,dict))
    verified_parser=(parser.get("status")=="nba_espn_byteam_strict_parity"
                     and parser.get("tests_passed",0)>=400)
    source_tally=(advanced.get("teams_with_previous_advanced"),
                  advanced.get("teams_with_current_advanced"))
    nba_prior_pass=bool(verified_parser and prior>=28 and
                        source_tally[0]==prior)
    # Deliberately require observed CURRENT-SEASON advanced data,
    # not stale 2025-26/standings/preseason projections.
    nba_current_pass=bool(verified_parser and current>=28 and
                          source_tally[1]==current)
    sources={
        "nba_previous_advanced":{
            "status":"available_verified_input_parser" if nba_prior_pass else "incomplete",
            "observed_teams":prior,"needed_teams":30,
            "source":"ESPN 2025-26 real prior regular-season efficiencies",
            "warning":"Prior season, not current roster"},
        "nba_current_advanced":{
            "status":"available_verified_input_parser" if nba_current_pass else "missing_or_partial",
            "observed_teams":current,"needed_teams":30,
            "source":"ESPN current regular-season efficiencies",
            "warning":"Do not substitute preseason standings or prior ratings for current advanced stats"},
        "nhl_moneypuck":{
            "status":"unverified_live_inputs",
            "source":"Original references MoneyPuck 5on5; Revue has no independently verified matching game-time feed",
            "warning":"A NHL simulation or skater table is not a matched MoneyPuck dataset"},
        "nhl_goalies":{
            "status":"unverified_live_inputs",
            "source":"Original has goalies and expected goalie starts, but matching pregame snapshots not validated",
            "warning":"Most-played goalie is not a confirmed starter"},
        "football_authorized_xg":{
            "status":"missing" if not sport.get("opta_available") else "unverified_live_inputs",
            "source":"Real ESPN boxscore shots may exist; these are NOT Opta xG/xGA",
            "warning":"No redistribution or invention of Opta proprietary fields"},
        "bookmaker_original_price_match":{
            "status":"unverified_live_inputs",
            "quote_snapshots":(scanner.get("odds_board") or {}).get("events_count",0),
            "source":"Revue PulseScore snapshots; source-specific market, odds timestamp and normalization not yet matched to Clairvoyance",
            "warning":"Live odds from different providers/instants need not agree"},
    }
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"source_data_parity_not_yet_verified",
        "formula_parity_not_sufficient":True,
        "cfb_excluded":True,
        "sources":sources,
        "completed_data_checks":sum(
            x["status"]=="available_verified_input_parser" for x in sources.values()),
        "total_data_checks":len(sources),
        "full_model_output_parity_on_real_games":False,
        "note":"No percentage of whole repository claimed; counts refer to 6 explicit data-source checks."
    }


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",default=".")
    a.add_argument("--output",default="docs/parite-donnees-clairvoyance.json")
    args=a.parse_args()
    report=check(Path(args.root),datetime.now(timezone.utc))
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOURCE-DATA COVERAGE:",report["completed_data_checks"],"/",
          report["total_data_checks"],"matched data checks; real prediction parity UNVERIFIED")

if __name__=="__main__":
    main()
