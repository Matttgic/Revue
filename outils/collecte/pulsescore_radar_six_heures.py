#!/usr/bin/env python3
"""Revue six-hour PulseScore radar: strictly incremental, no paper bets.

The existing four daily full-scan Engine V2 jobs remain unchanged.
This small scan uses <=8 HTTP requests, and publishes only its own
timestamped market observations; it never overwrites a full scan,
locks a paper selection, fabricates odds, or executes a wager.

At four mini-runs/day plus four full scans/day (max 32 requests each),
the nominal 31-day upper bound is 4,960 requests. Manual re-runs,
retries and any other quota-consuming jobs are outside that bound.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path

from outils.collecte.pulsescore_v2 import scan
from outils.suivi.revue_engine_v2 import timestamp
from outils.collecte.tableau_cotes import build_board

MAX_CALLS=100
HORIZON_HOURS=6
MAX_MODEL_AGE=timedelta(hours=6)
VERSION="revue_pulsescore_six_hour_radar_v1"


def compute(models:dict,now:datetime,key:str="",scanner=scan,max_calls:int=MAX_CALLS)->dict:
    if now.tzinfo is None:
        raise ValueError("Timezone aware clock required")
    now=now.astimezone(timezone.utc)
    if not 1<=max_calls<=MAX_CALLS:
        raise ValueError(f"Radar hard cap: at most {MAX_CALLS} requests")
    stamp=timestamp(models.get("generated_at_utc"))
    valid=bool(stamp and stamp<=now and now-stamp<=MAX_MODEL_AGE and
              models.get("status")=="prototype_non_calibre" and
              isinstance(models.get("competitions"),dict))
    status="no_api_key" if not key else "model_stale_or_invalid" if not valid else "observed"
    empty={"events":[],"events_count":0,"bookmaker_market_rows":0,
           "status":"no_matching_valid_prices"}
    stats={"requests":0,"matched_events":0,"matched_leagues":{},
           "sports":[],"errors":{},"truncated":False}
    board=empty
    if key and valid:
        odds,stats=scanner(key,models,now,max_calls=max_calls,
                           days_horizon=HORIZON_HOURS,balanced=True)
        if type(stats.get("requests")) is not int or not 0<=stats["requests"]<=max_calls:
            raise ValueError("Provider exceeded mini scan budget")
        board=build_board(models,odds,now)
        if not isinstance(board.get("events"),list):
            raise ValueError("Observed bookmaker rows missing")
    return {
        "version":VERSION,
        "generated_at_utc":now.isoformat(),
        "source_model_generated_at_utc":stamp.isoformat() if stamp else None,
        "status":status,
        "horizon_hours":HORIZON_HOURS,
        "request_cap":max_calls,
        "requests_used":stats["requests"],
        "provider":"PulseScore",
        "scope":"FR observed snapshots, no currently bookable odds guaranteed",
        "bookmakers_supported":["betclic_fr","winamax_fr","unibet_fr","pmu_fr"],
        "market_prices_are_live":False,
        "positive_ev_verified":False,
        "model_is_calibrated":False,
        "real_bets_enabled":False,
        "new_paper_bets_created":False,
        "existing_paper_ledger_modified":False,
        "matches_observed":board["events_count"],
        "market_rows_observed":board["bookmaker_market_rows"],
        "observations":board["events"],
        "diagnostics":{
            "sport_groups_attempted":stats.get("sports",[]),
            "calls_by_sport":stats.get("calls_by_sport",{}),
            "allocation_mode":stats.get("allocation_mode","sport_balanced"),
            "matched_events":stats.get("matched_events",0),
            "matched_leagues":stats.get("matched_leagues",{}),
            "truncated":stats.get("truncated",False),
            "errors":stats.get("errors",{}),
        },
        "note":"Only existing pregame forecasted events <=6 h are queried; <=8 authenticated calls. Differences across French books are not a calibrated fair price, proven positive EV, or a current offer."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models",default="docs/multisports-latest.json")
    p.add_argument("--out",default="docs/pulsescore-radar-latest.json")
    p.add_argument("--max-calls",type=int,default=MAX_CALLS)
    args=p.parse_args()
    models=json.loads(Path(args.models).read_text(encoding="utf8"))
    now=datetime.now(timezone.utc)
    payload=compute(models,now,os.environ.get("PULSESCORE_API_KEY",""),
                    max_calls=args.max_calls)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    print("Six-hour PulseScore radar:",
          payload["status"],payload["requests_used"],"/",payload["request_cap"],
          "calls,",payload["matches_observed"],"matches;",
          "0 simulated or real bets")


if __name__=="__main__":
    main()
