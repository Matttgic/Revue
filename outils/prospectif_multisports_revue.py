#!/usr/bin/env python3
"""Immutable multisport prospective predictions and strict official-result evaluation.

Distinct from the original NHL Clairvoyance ledger. Tracks Revue's *independent*
two-outcome score models (NHL, basketball, NFL, MLB). Soccer 1X2 settlement is
NOT enabled: extra time/penalties vs 90-minute rules need independent checks.
Never generates bookmaker bets or retrospectively backfills alternative models.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import argparse,json,math
from pathlib import Path

from outils.match_center_revue import instant,probability,game_key,compatible

VERSION="revue_multisport_pre_match_v1"
MIN_BEFORE=timedelta(minutes=20)
SUPPORTED=frozenset({"NHL","NBA","WNBA","NFL","MLB","NCAAB"})
MODEL_IDS=frozenset({"revue_multisports_score_model","revue_ensemble_mc_bayes_elo",
                     "clairvoyance_nhl_formula_revue_inputs","revue_nhl_low_sample_shrink_v1"})


def empty_ledger():
    return {"version":VERSION,"events":[]}


def lock(ledger:dict | None,center:dict,as_of:datetime) -> dict:
    if as_of.tzinfo is None:
        raise ValueError("Timestamp must be aware")
    if not ledger:
        ledger=empty_ledger()
    if ledger.get("version") != VERSION or not isinstance(ledger.get("events"),list):
        raise ValueError("Unsupported prospective ledger schema")
    old={r["key"]:r for r in ledger["events"]}
    if len(old)!=len(ledger["events"]):
        raise ValueError("Duplicate frozen game key")
    if center.get("status") != "experimental_revue_match_center":
        return ledger
    if center.get("real_bets_enabled") is not False or center.get("bookmaker_prices_are_live") is not False:
        raise ValueError("Research mode required")
    for event in center.get("events") or []:
        league=event.get("league")
        if league not in SUPPORTED:
            continue
        key=game_key(league,event.get("event_id"))
        if key in old:
            continue
        try:
            kickoff=instant(event["start_utc"])
            if not as_of <= kickoff-MIN_BEFORE:
                continue
            models={}
            for m in event.get("research") or []:
                mid=m.get("id")
                p=m.get("probabilities") or {}
                if mid not in MODEL_IDS or "draw_90" in p:
                    continue
                if (not probability(p.get("home_win")) or not probability(p.get("away_win")) or
                    abs(p["home_win"]+p["away_win"]-1)>.02):
                    continue
                trained=instant(m["source_generated_utc"])
                if not trained <= as_of or trained >= kickoff:
                    continue
                models[mid]={"p_home":float(p["home_win"]),"source_generated_utc":trained.isoformat()}
            if not models:
                continue
            old[key]={
                "key":key,"league":league,"event_id":str(event["event_id"]),
                "home":event["home"],"away":event["away"],"kickoff_utc":kickoff.isoformat(),
                "locked_at_utc":as_of.isoformat(),"status":"pending",
                "models":models,"result":None,"score":None,"resolved_at_utc":None,
                "brier_by_model":None,"logloss_by_model":None,
                "real_bet":False,"staked_units":0,
            }
        except (ValueError,TypeError,KeyError):
            continue
    return {"version":VERSION,"events":sorted(old.values(),key=lambda r:(r["kickoff_utc"],r["key"]))}


def settle(ledger:dict,scores:dict,as_of:datetime) -> dict:
    if ledger.get("version")!=VERSION:
        raise ValueError("Unknown schema")
    result=json.loads(json.dumps(ledger))
    valid={}
    try:
        generated=instant(scores["generated_at_utc"])
        eligible=(scores.get("status")=="observed_scoreboard_not_streaming" and
                  as_of-timedelta(hours=2)<=generated<=as_of and
                  scores.get("scores_are_live_stream") is False)
    except (KeyError,ValueError,TypeError):
        eligible=False
    if eligible:
        for row in scores.get("events") or []:
            if row.get("state")!="final" or row.get("league") not in SUPPORTED:
                continue
            try:
                key=game_key(row["league"],row["event_id"])
                if instant(row["observed_at_utc"]) != generated:
                    continue
                h,a=row.get("home_score"),row.get("away_score")
                if (type(h) is not int or type(a) is not int or
                    not 0<=h<=500 or not 0<=a<=500 or h==a):
                    continue
                valid[key]=row
            except (KeyError,ValueError,TypeError):
                continue
    for row in result["events"]:
        if row["status"]!="pending":
            continue
        official=valid.get(row["key"])
        if official is None or not compatible(row,official):
            continue
        kickoff=instant(row["kickoff_utc"])
        if not (kickoff < generated <= as_of):
            continue
        outcome=int(official["home_score"]>official["away_score"])
        by_model={}
        loss={}
        for name,p in row["models"].items():
            x=p["p_home"]
            if not probability(x) or not 0<x<1:
                raise ValueError("Corrupted frozen prediction")
            by_model[name]=round((x-outcome)**2,6)
            loss[name]=round(-math.log(x if outcome else (1-x)),6)
        row.update({
            "status":"settled",
            "result":outcome,
            "score":{"home":official["home_score"],"away":official["away_score"]},
            "resolved_at_utc":generated.isoformat(),
            "brier_by_model":by_model,"logloss_by_model":loss,
        })
    return result


def performance(ledger:dict,as_of:datetime) -> dict:
    results=ledger.get("events") or []
    by_model={}
    for event in results:
        if event["status"]!="settled":
            continue
        for name in event["models"]:
            item=by_model.setdefault(name,{"settled":0,"brier_sum":0.0,"logloss_sum":0.0})
            if name in (event.get("brier_by_model") or {}):
                item["settled"]+=1
                item["brier_sum"]+=event["brier_by_model"][name]
                item["logloss_sum"]+=event["logloss_by_model"][name]
    for item in by_model.values():
        n=item.pop("settled")
        item["settled"]=n
        item["mean_brier"]=round(item.pop("brier_sum")/n,6) if n else None
        item["mean_logloss"]=round(item.pop("logloss_sum")/n,6) if n else None
    return {
        "generated_at_utc":as_of.isoformat(),
        "status":"experimental_not_calibrated","version":VERSION,
        "total_locked":len(results),
        "pending":sum(e["status"]=="pending" for e in results),
        "settled":sum(e["status"]=="settled" for e in results),
        "by_league":{lg:{
            "locked":sum(e["league"]==lg for e in results),
            "settled":sum(e["league"]==lg and e["status"]=="settled" for e in results),
        } for lg in sorted({e["league"] for e in results})},
        "models":by_model,
        "real_bets":0,"roi":None,
        "note":"Brier/Log Loss from genuinely pre-game predictions only. Never infer profitability or compare models over different game samples.",
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--center",default="docs/match-center-latest.json")
    cli.add_argument("--scores",default="docs/scoreboard-revue-latest.json")
    cli.add_argument("--ledger",default="docs/multisport-prospective-ledger.json")
    cli.add_argument("--report",default="docs/multisport-prospective-performance.json")
    a=cli.parse_args()
    now=datetime.now(timezone.utc)
    stored=Path(a.ledger)
    base=json.loads(stored.read_text(encoding="utf-8")) if stored.exists() else None
    center=json.loads(Path(a.center).read_text(encoding="utf-8"))
    scores=json.loads(Path(a.scores).read_text(encoding="utf-8")) if Path(a.scores).exists() else {}
    # Freeze new picks only when the matching source report is reasonably fresh.
    source_at=instant(center["generated_at_utc"])
    if not now-timedelta(hours=3) <= source_at <= now:
        raise ValueError("Refusing new forecast locks based on stale/future match-center report")
    frozen=lock(base,center,now)
    result=settle(frozen,scores,now)
    summary=performance(result,now)
    for path,data in ((stored,result),(Path(a.report),summary)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Prospective multisport",summary["total_locked"],"locked,",summary["settled"],"settled,",summary["pending"],"pending")


if __name__=="__main__":main()
