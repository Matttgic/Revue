#!/usr/bin/env python3
"""Immutable prematch lock + settlement ledger for MoneyPuck-backed NHL SHADOW.

Zero cash stakes; this measures prospective Brier accuracy, NOT profitability.
An event is locked only once and only >=20 minutes before kickoff, using
snapshots actually fetched before kickoff. Later runs may settle, never overwrite
a locked pick, probability, source timestamps or result.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from modeles.simulations.nhl_independant import Game
from outils.clairvoyance_nhl_moneypuck_shadow import as_utc

LOCK_MINUTES=20
VERSION="nhl_clairvoyance_moneypuck_shadow_v1"


def grade_brier(prob:float, result:int) -> float:
    if not 0<=prob<=1 or result not in (0,1):
        raise ValueError("Probability or result invalid")
    return round((prob-result)**2,6)


def grade_logloss(prob:float, result:int) -> float:
    """Binary logarithmic loss on frozen pre-match probability, not market ROI."""
    if (not isinstance(prob,(int,float)) or not math.isfinite(prob) or
        not 0<prob<1 or result not in (0,1)):
        raise ValueError("Probability or result invalid")
    return -math.log(prob if result else (1-prob))


def _audited_prediction(report: dict, as_of: datetime) -> bool:
    """Only audited, genuinely before-kickoff reports can create NEW locks.

    Existing locked forecasts remain authoritative and may always be settled.
    A missing or forged audit field is NOT grounds for retrospective backfill.
    """
    proof=report.get("point_in_time_audit") or {}
    if proof.get("status")!="verified_temporal_bounds":
        return False
    try:
        observed=as_utc(proof["as_of_utc"])
        generated=as_utc(report["generated_at_utc"])
        if observed!=generated or observed>as_of:
            return False
        published=report["sources"]["source_updated_utc"]
        if proof.get("source_updated_utc")!=published:
            return False
        if not isinstance(proof.get("team_5v5_rows_checked"),int) or proof["team_5v5_rows_checked"]<2:
            return False
    except (KeyError,TypeError,ValueError):
        return False
    return True


def _new_lock(row:dict, report:dict, as_of:datetime) -> dict | None:
    kickoff=as_utc(row["start_utc"])
    if kickoff-as_of<timedelta(minutes=LOCK_MINUTES):
        return None
    # Each source snapshot and the individual prediction must exist before
    # the bet cutoff, not merely ahead of the game. No backfilled locks.
    src=report.get("sources") or {}
    times=src.get("source_updated_utc") or {}
    snapshots=src.get("source_snapshot_utc") or {}
    original=as_utc(report["generated_at_utc"])
    if original>as_of or any(as_utc(t)>as_of for t in [*times.values(),*snapshots.values()]):
        return None
    probability=row.get("home_win")
    if (not isinstance(probability,(int,float)) or
        not math.isfinite(probability) or not 0<probability<1 or
        row.get("shadow_only") is not True or row.get("calibrated") is not False):
        return None
    candidate=row.get("research_low_sample_shrink") or {}
    research_p=candidate.get("home_win")
    if (candidate.get("model_id")!="revue_nhl_low_sample_shrink_v1" or
        candidate.get("shadow_only") is not True or
        candidate.get("calibrated") is not False or
        not isinstance(research_p,(int,float)) or
        not math.isfinite(research_p) or not 0<research_p<1):
        research_p=None
    return {
        "event_id":str(row["event_id"]),
        "home":row["home"],"away":row["away"],
        "kickoff_utc":kickoff.isoformat(),
        "locked_at_utc":as_of.isoformat(),
        "source_prediction_at_utc":original.isoformat(),
        "home_win_probability":round(float(probability),6),
        "away_win_probability":round(1-float(probability),6),
        "research_home_win_probability":round(float(research_p),6) if research_p is not None else None,
        "research_model_id":"revue_nhl_low_sample_shrink_v1" if research_p is not None else None,
        "source_updated_utc":dict(times),"source_snapshot_utc":dict(snapshots),
        "xg_games_observed":row.get("xg_games_observed"),
        "historical_goalie_proxy":row.get("historical_goalie_proxy"),
        "model_id":row["model_id"],
        "status":"pending","resolved_at_utc":None,
        "result":None,"home_goals":None,"away_goals":None,"brier":None,
        "research_brier":None,
    }


def update_ledger(previous:dict|None,prediction:dict,
                  schedule:list[Game],as_of:datetime) -> dict:
    if as_of.tzinfo is None:
        raise ValueError("now timezone mandatory")
    as_of=as_of.astimezone(timezone.utc)
    past=(previous or {}).get("events") or []
    if not isinstance(past,list):
        raise ValueError("Invalid ledger")
    ledger={}
    for row in past:
        key=str(row.get("event_id"))
        if key in ledger:
            raise ValueError("Duplicate historical event locks")
        # Records from disk are authoritative, no probability edits.
        ledger[key]=row.copy()
    if (prediction.get("status")=="experimental_not_calibrated" and
        _audited_prediction(prediction,as_of)):
        for row in prediction.get("games") or []:
            key=str(row["event_id"])
            if key not in ledger:
                lock=_new_lock(row,prediction,as_of)
                if lock:
                    ledger[key]=lock
    current={g.id:g for g in schedule if g.final and g.start_utc<as_of}
    for key,row in ledger.items():
        if row.get("status")!="pending":
            continue
        event=current.get(key)
        if event is None:
            continue
        if (event.home!=row["home"] or event.away!=row["away"] or
            event.start_utc!=as_utc(row["kickoff_utc"])):
            continue  # Refuse inaccurate game mapping.
        if event.home_goals==event.away_goals:
            continue  # NHL regulation draw without OT winner is not a graded ML.
        actual=int(event.home_goals>event.away_goals)
        row.update({"status":"settled","resolved_at_utc":as_of.isoformat(),
                    "result":actual,"home_goals":event.home_goals,
                    "away_goals":event.away_goals,
                    "brier":grade_brier(row["home_win_probability"],actual),
                    "research_brier":grade_brier(row["research_home_win_probability"],actual)
                    if isinstance(row.get("research_home_win_probability"),(int,float))
                    else None})
    return {
        "version":VERSION,"updated_at_utc":as_of.isoformat(),
        "rule":"Immutable predictions only if created >=20 minutes before kickoff",
        "evaluation":"2-way NHL final including OT/SO; Brier mean; no wagers/ROI",
        "events":sorted(ledger.values(),key=lambda x:(x["kickoff_utc"],x["event_id"])),
    }


def summarize(ledger:dict,now:datetime) -> dict:
    rows=ledger["events"]
    settled=[r for r in rows if r.get("status")=="settled" and
             isinstance(r.get("brier"),(int,float))]
    pending=[r for r in rows if r.get("status")=="pending"]
    n=len(settled)
    reference_brier=sum(r["brier"] for r in settled)/n if n else None
    reference_logloss=(sum(grade_logloss(r["home_win_probability"],r["result"])
                           for r in settled)/n) if n else None
    paired_locked=sum(1 for r in rows if isinstance(r.get("research_home_win_probability"),(int,float)))
    paired=[r for r in settled if isinstance(r.get("research_brier"),(int,float))]
    paired_count=len(paired)
    ref_paired=(sum(r["brier"] for r in paired)/paired_count) if paired_count else None
    alt_paired=(sum(r["research_brier"] for r in paired)/paired_count) if paired_count else None
    reference_logloss_paired=(sum(grade_logloss(r["home_win_probability"],r["result"])
                                  for r in paired)/paired_count) if paired_count else None
    research_logloss_paired=(sum(grade_logloss(r["research_home_win_probability"],r["result"])
                                 for r in paired)/paired_count) if paired_count else None
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "model":VERSION,
        "locked_events":len(rows),"pending":len(pending),"settled":n,
        "min_results_for_preliminary_assessment":100,
        "statistical_status":"preliminary_only" if n>=100 else "insufficient_sample",
        "mean_brier":round(reference_brier,6) if n else None,
        "mean_logloss":round(reference_logloss,6) if n else None,
        "coinflip_baseline_brier":0.25,
        "coinflip_baseline_logloss":round(math.log(2),6),
        "brier_skill_vs_coinflip":round(1-reference_brier/0.25,6) if n else None,
        "research_paired_locked":paired_locked,
        "research_paired_settled":paired_count,
        "mean_brier_reference_on_paired":round(ref_paired,6) if paired_count else None,
        "mean_brier_research":round(alt_paired,6) if paired_count else None,
        "mean_logloss_reference_on_paired":round(reference_logloss_paired,6) if paired_count else None,
        "mean_logloss_research":round(research_logloss_paired,6) if paired_count else None,
        "logloss_delta_research_minus_reference":round(research_logloss_paired-reference_logloss_paired,6) if paired_count else None,
        "research_brier_skill_vs_coinflip_paired":round(1-alt_paired/0.25,6) if paired_count else None,
        "brier_delta_research_minus_reference":round(alt_paired-ref_paired,6) if paired_count else None,
        "research_status":"experimental_not_promoted",
        "home_win_rate_observed":round(sum(r["result"] for r in settled)/n,4) if n else None,
        "home_win_probability_mean":round(sum(r["home_win_probability"] for r in settled)/n,4) if n else None,
        "roi":None,"staked_units":0,"cash_bets":0,
        "note":"Experimental evaluation without ROI. Lower Brier/Log Loss is better. A fixed p=0.5 baseline scores Brier 0.25 and Log Loss ln(2). Paired comparison uses only identical events with both predictions frozen before kickoff."
    }
