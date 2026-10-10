#!/usr/bin/env python3
"""Prospective NHL MC / Ensemble tracker; independent model comparison, no betting.

Locks only already-PUBLISHED and observed research outputs while the game is
upcoming. Later jobs grade immutable locks against official NHL final game IDs.
Neither a past forecast nor a result can be backfilled into a pre-game lock.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from modeles.simulations.nhl_independant import Game
from outils.clairvoyance_nhl_moneypuck_shadow import as_utc
from outils.nhl_settlement_officiel import download_results

VERSION = "revue_nhl_frontend_prospective_v1"
REPORT_VERSION = "revue_nhl_frontend_observed_v1"
LOCK_LEAD = timedelta(minutes=20)
FORECAST_MAX_AGE = timedelta(hours=12)
SEASON_BUFFER = timedelta(hours=3)
MIN_EVIDENCE = 100
MODELS = ("monte_carlo_home", "ensemble_home")


def probability(v: object) -> bool:
    return type(v) in (int, float) and math.isfinite(v) and 0 < v < 1


def valid_report(doc: dict, now: datetime) -> bool:
    if not isinstance(doc, dict) or now.tzinfo is None:
        return False
    if (doc.get("version") != REPORT_VERSION
        or doc.get("status") != "prospective_research_partial_input_frontend_not_parity"
        or doc.get("exact_original_frontend_predictions_verified") is not False
        or doc.get("odds_and_value_bets_enabled") is not False
        or doc.get("real_bets_enabled") is not False
        or doc.get("paper_bets_auto_created") is not False
        or doc.get("updated_frozen_ledgers") is not False
        or doc.get("no_fictitious_injuries_or_confirmed_goalies") is not True
        or not isinstance(doc.get("games"), list)
        or doc.get("games_emitted") != len(doc["games"])):
        return False
    try:
        stamp = as_utc(doc["generated_at_utc"])
        if not stamp <= now <= stamp + FORECAST_MAX_AGE:
            return False
        times = doc["source_snapshot_utc"]
        if not isinstance(times, dict) or not times:
            return False
        if any(not as_utc(v) <= stamp for v in times.values()):
            return False
    except (KeyError, ValueError, TypeError):
        return False
    return True


def lockable(row: dict, doc: dict, now: datetime) -> dict | None:
    try:
        game = str(row["event_id"])
        if not game.isdecimal() or len(game) < 9 or len(game) > 13:
            return None
        start = as_utc(row["start_utc"])
        created = as_utc(doc["generated_at_utc"])
        if start <= now + LOCK_LEAD or start <= created + LOCK_LEAD:
            return None
        if (row.get("retroactive_prediction") is not False
            or row.get("source_equivalent_predictions") is not False
            or row.get("feature_status") != "partial_neutral_inputs_not_original_frontend_parity"
            or row.get("injuries_verified") is not False
            or row.get("starting_goalies_verified") is not False
            or row.get("bookmaker_quotes_available") is not False):
            return None
        h, a = row["home"], row["away"]
        if (not isinstance(h,str) or not isinstance(a,str) or h==a
            or not 2<=len(h)<=4 or not 2<=len(a)<=4
            or not h.isalpha() or not a.isalpha()
            or h!=h.upper() or a!=a.upper()):
            return None
        research = row.get("research") or {}
        if (not all(probability(research.get(k)) for k in MODELS)
            or research.get("simulation_draws") != 25000
            or research.get("calibrated") is not False
            or research.get("actionable") is not False
            or research.get("market_blended") is not False):
            return None
    except (KeyError,ValueError,TypeError):
        return None
    return {
        "event_id": game,"home":h,"away":a,"kickoff_utc":start.isoformat(),
        "locked_at_utc":now.isoformat(),
        "source_prediction_at_utc":created.isoformat(),
        "source_snapshot_utc":deepcopy(doc["source_snapshot_utc"]),
        "model_monte_carlo":float(research["monte_carlo_home"]),
        "model_ensemble":float(research["ensemble_home"]),
        "simulation_draws":25000,
        "calibrated":False,
        "original_prediction_parity_verified":False,
        "goalies_and_injuries_verified":False,
        "status":"pending",
        "resolved_at_utc":None,"actual_home_win":None,
        "home_goals":None,"away_goals":None,
        "score_source":None,
        "brier_monte_carlo":None,"brier_ensemble":None,
    }


def update_ledger(previous: dict | None, forecast: dict, finals: list[Game],
                  now: datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("UTC-aware clock mandatory")
    now = now.astimezone(timezone.utc)
    if previous is not None and (previous.get("version")!=VERSION or
                                 not isinstance(previous.get("events"),list)):
        raise ValueError("Unknown immutable NHL frontend ledger")
    events={}
    for r in (previous or {}).get("events",[]):
        if not isinstance(r,dict) or not r.get("event_id"):
            raise ValueError("Malformed existing lock")
        ident=str(r["event_id"])
        if ident in events:
            raise ValueError("Duplicate existing game locks")
        events[ident]=deepcopy(r)
    if valid_report(forecast,now):
        seen=set()
        candidates=[]
        for r in forecast["games"]:
            ident=str(r.get("event_id"))
            if ident in seen:
                raise ValueError("Duplicate fixture in research report")
            seen.add(ident)
            if ident not in events:
                prospective=lockable(r,forecast,now)
                if prospective:
                    candidates.append(prospective)
        for c in candidates:
            events[c["event_id"]]=c
    completed={}
    for game in finals:
        if not game.final or game.start_utc>=now:
            continue
        if game.id in completed and completed[game.id]!=game:
            raise ValueError("Conflicting official NHL final ID")
        completed[game.id]=game
    for ident, r in events.items():
        if r.get("status")!="pending":
            continue
        g=completed.get(ident)
        if g is None:
            continue
        # Exact game identity/time controls cannot be weakened by an update.
        if (g.home!=r["home"] or g.away!=r["away"]
            or g.start_utc!=as_utc(r["kickoff_utc"])
            or g.start_utc<as_utc(r["locked_at_utc"])+LOCK_LEAD
            or g.home_goals is None or g.away_goals is None
            or g.home_goals==g.away_goals):
            continue
        outcome=int(g.home_goals>g.away_goals)
        r.update({
            "status":"settled","resolved_at_utc":now.isoformat(),
            "actual_home_win":outcome,
            "home_goals":g.home_goals,"away_goals":g.away_goals,
            "score_source":"NHL official final",
            "brier_monte_carlo":round((r["model_monte_carlo"]-outcome)**2,6),
            "brier_ensemble":round((r["model_ensemble"]-outcome)**2,6),
        })
    for orig in (previous or {}).get("events",[]):
        actual=events[str(orig["event_id"])]
        immutable_keys=("event_id","home","away","kickoff_utc","locked_at_utc",
            "source_prediction_at_utc","source_snapshot_utc","model_monte_carlo",
            "model_ensemble","simulation_draws","calibrated",
            "original_prediction_parity_verified","goalies_and_injuries_verified")
        if any(actual.get(k)!=orig.get(k) for k in immutable_keys):
            raise AssertionError("Historical prospective NHL prediction modified")
        if orig["status"]=="settled" and actual!=orig:
            raise AssertionError("Already graded NHL fixture modified")
        if orig["status"]=="pending" and actual["status"] not in ("pending","settled"):
            raise AssertionError("Unexpected NHL state transition")
    return {
        "version":VERSION,"updated_at_utc":now.isoformat(),
        "source":"prospective Revue MC+Ensemble partial-input research; no bets",
        "prediction_model_calibrated":False,
        "original_clairvoyance_picks_identical":False,
        "real_bets_enabled":False,"odds_available":False,
        "events":sorted(events.values(),key=lambda r:(r["kickoff_utc"],r["event_id"])),
    }


def summarize(ledger:dict,now:datetime)->dict:
    if ledger.get("version")!=VERSION:
        raise ValueError("Unknown NHL frontend ledger")
    rows=ledger["events"]
    settled=[r for r in rows if r.get("status")=="settled"]
    pending=sum(r.get("status")=="pending" for r in rows)
    # Evaluate paired forecasts on EXACTLY the same settled fixtures.
    for r in settled:
        y=r.get("actual_home_win")
        if (type(y)!=int or y not in (0,1)
            or any(not probability(r.get(p)) for p in
                   ("model_monte_carlo","model_ensemble"))):
            raise ValueError("Invalid settled NHL probability or outcome")
    models={}
    for label,pfield,bfield in (
        ("monte_carlo","model_monte_carlo","brier_monte_carlo"),
        ("ensemble","model_ensemble","brier_ensemble"),
    ):
        count=len(settled)
        mean_b=sum((r[pfield]-r["actual_home_win"])**2 for r in settled)/count if count else None
        mean_log=sum(-(r["actual_home_win"]*math.log(r[pfield])+
                        (1-r["actual_home_win"])*math.log(1-r[pfield]))
                     for r in settled)/count if count else None
        models[label]={
            "settled_sample":count,
            "brier":round(mean_b,6) if count else None,
            "log_loss":round(mean_log,6) if count else None,
            "mean_home_win_probability":round(sum(r[pfield] for r in settled)/count,6) if count else None,
            "status":"insufficient_sample" if count<MIN_EVIDENCE else "evaluation_research_only",
        }
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"prospective_partial_input_nhl_comparison_no_bets",
        "model_names":["nhlMC","nhlEns"],
        "locked_games":len(rows),"pending_games":pending,"settled_games":len(settled),
        "min_settled_for_initial_assessment":MIN_EVIDENCE,
        "statistically_valid_profitability_proven":False,
        "real_bets_enabled":False,"roi":None,
        "same_game_comparison":True,
        "models":models,
        "note":"Locked only while upcoming and with pregame source timestamps. Score NHL official, 2-way final incl OT/SO; lower Brier and Log Loss is better. No betting EV or cash ROI; incomplete data and models uncalibrated.",
    }


def due_scoreboard_days(ledger: dict, now: datetime) -> list[str]:
    from zoneinfo import ZoneInfo
    eastern=ZoneInfo("America/New_York")
    dates={as_utc(x["kickoff_utc"]).astimezone(eastern).date().isoformat()
        for x in ledger.get("events",[])
        if x.get("status")=="pending" and as_utc(x["kickoff_utc"])<now-timedelta(hours=1)}
    return sorted(dates,reverse=True)[:14]


def process(previous:dict|None,forecast:dict,now:datetime,fetcher=None)->tuple[dict,dict]:
    from outils.nhl_settlement_officiel import _get_json
    if now.tzinfo is None:
        raise ValueError("Aware clock mandatory")
    # A valid report can create new pregame locks before looking up scores.
    candidate=update_ledger(previous,forecast,[],now)
    dates=due_scoreboard_days(candidate,now)
    finals=download_results(dates,fetcher or _get_json) if dates else []
    ledger=update_ledger(previous,forecast,finals,now)
    return ledger,summarize(ledger,now)


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--docs",default="docs")
    args=cli.parse_args()
    root=Path(args.docs)
    report=json.loads((root/"nhl-frontend-observed-latest.json").read_text(encoding="utf8"))
    ledger_path=root/"nhl-frontend-prospective-ledger.json"
    old=json.loads(ledger_path.read_text(encoding="utf8")) if ledger_path.exists() else None
    now=datetime.now(timezone.utc)
    updated,perf=process(old,report,now)
    # Don't create a missing lock file unless genuine pregame locks exist.
    # Once created it remains an audit trail of exact observed prices/probabilities.
    if old is None and not updated["events"]:
        print("NHL MC+Ensemble: no eligible pregame locks; no retrospective backfill.")
        return
    for path,doc in (
        (ledger_path,updated),
        (root/"nhl-frontend-prospective-performance.json",perf),
    ):
        path.write_text(json.dumps(doc,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print("NHL frontend 25k-sample: prospective locks",perf["locked_games"],
          "settled",perf["settled_games"],"pending",perf["pending_games"],
          "research-only, no odds, no bets.")


if __name__=="__main__":
    main()
