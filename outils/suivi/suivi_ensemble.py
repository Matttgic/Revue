#!/usr/bin/env python3
"""Prospective paired model audit: real scores vs frozen 1X2 at pregame time.

Supports only 2-outcome games in NBA, WNBA, NCAA basketball, NFL and MLB.
Locks baseline / Monte Carlo-Bayes-Elo snapshots before kickoff and settles
them from ESPN final scores. No odds, no stakes, no unconfirmed picks.
A failed/stale input may NOT create new locks but can settle past locks.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timedelta,timezone
import json,math
from pathlib import Path

from modeles.simulations.football_avance_independant import utc

SUPPORTED=frozenset({"NBA","WNBA","NCAAB","NFL","MLB"})
PREGAME_BUFFER=timedelta(minutes=20)
MAX_PREDICTION_AGE=timedelta(hours=8)


def normalize_two_way(p:object)->tuple[float,float]|None:
    if not isinstance(p,dict):return None
    try:
        h,a=float(p["home_win"]),float(p["away_win"])
    except (TypeError,ValueError,KeyError):return None
    if (not math.isfinite(h) or not math.isfinite(a) or
        h<=0 or a<=0 or h>=1 or a>=1 or abs(h+a-1)>.003):
        return None
    return (h/(h+a),a/(h+a))


def score_pair(p:tuple[float,float],is_home:int)->dict:
    h=p[0]
    actual=float(is_home)
    return {"brier":round((h-actual)**2,6),
            "logloss":round(-math.log(max(1e-12,h if is_home else 1-h)),6)}


def step(ledger:dict,baseline:dict,experiment:dict,history:dict,
         now:datetime)->tuple[dict,dict]:
    if now.tzinfo is None:raise ValueError("Offset-aware clock required")
    events=ledger.setdefault("events",{})
    if not isinstance(events,dict):raise ValueError("Ledger must contain an event map")
    b_at=utc(baseline.get("generated_at_utc"))
    e_at=utc(experiment.get("generated_at_utc"))
    can_lock=(b_at and e_at and b_at<=now and e_at<=now
              and now-b_at<=MAX_PREDICTION_AGE
              and now-e_at<=MAX_PREDICTION_AGE)
    recorded=0
    if can_lock:
        for lg,row in (experiment.get("leagues") or {}).items():
            if lg not in SUPPORTED:continue
            old_games=(baseline.get("competitions") or {}).get(lg,{}).get("games") or []
            old={str(x.get("event_id")):x for x in old_games}
            for g in row.get("games") or []:
                event_id=str(g.get("event_id") or "")
                if not event_id:continue
                key=f"{lg}:{event_id}"
                if key in events:continue
                ref=old.get(event_id)
                if not ref:continue
                start=utc(g.get("start_utc"))
                if (start is None or utc(ref.get("start_utc"))!=start
                    or now>=start-PREGAME_BUFFER
                    or not (b_at<start and e_at<start)
                    or (g.get("home")!=ref.get("home"))
                    or (g.get("away")!=ref.get("away"))):
                    continue
                p_baseline=normalize_two_way(ref.get("probabilities"))
                p_ensemble=normalize_two_way(g.get("probabilities"))
                if not p_baseline or not p_ensemble:continue
                if g.get("status")!="shadow_non_calibre":continue
                events[key]={
                    "league":lg,"event_id":event_id,
                    "home":g["home"],"away":g["away"],
                    "start_utc":start.isoformat(),
                    "locked_at_utc":now.isoformat(),
                    "baseline_published_at":b_at.isoformat(),
                    "ensemble_published_at":e_at.isoformat(),
                    "baseline":list(p_baseline),"ensemble":list(p_ensemble),
                    "ensemble_method":"MC(768)+Beta-Binomial+Elo",
                    "status":"pending",
                }
                recorded+=1
    valid={}
    for lg,row in (history.get("leagues") or {}).items():
        if lg not in SUPPORTED:continue
        for e in (row.get("events") or []):
            if (e.get("complete") is True and
                e.get("home_score") is not None and
                e.get("away_score") is not None):
                valid[(lg,str(e.get("id")))]=e
    graded=ties=0
    for record in events.values():
        if record.get("status")!="pending":continue
        start=utc(record.get("start_utc"))
        lock=utc(record.get("locked_at_utc"))
        a=utc(record.get("baseline_published_at"))
        b=utc(record.get("ensemble_published_at"))
        if not start or not lock or not a or not b or (
            lock>=start-PREGAME_BUFFER or a>lock or b>lock):
            record["status"]="invalid_chronology"
            continue
        if now<=start:continue
        outcome=valid.get((record["league"],record["event_id"]))
        if (outcome is None or utc(outcome.get("start"))!=start or
            outcome.get("home")!=record.get("home") or
            outcome.get("away")!=record.get("away")):
            continue
        hs,as_=outcome.get("home_score"),outcome.get("away_score")
        try:h,away=float(hs),float(as_)
        except (ValueError,TypeError):continue
        # A drawn NFL game is incompatible with a 2-way moneyline forecast.
        # Do not grade it as an away win.
        if h==away:
            record["status"]="draw_unsettled_2way"
            ties+=1
            continue
        y=int(h>away)
        record["outcome"]="home" if y else "away"
        record["score"]={"home":h,"away":away}
        record["baseline_metrics"]=score_pair(tuple(record["baseline"]),y)
        record["ensemble_metrics"]=score_pair(tuple(record["ensemble"]),y)
        record["settled_at_utc"]=now.isoformat()
        record["status"]="graded"
        graded+=1
    return ledger,{"added":recorded,"graded":graded,"draws_skipped":ties}


def summarize(ledger:dict,now:datetime)->dict:
    src=list((ledger.get("events") or {}).values())
    output={}
    for lg in ["ALL",*sorted(SUPPORTED)]:
        items=src if lg=="ALL" else [e for e in src if e.get("league")==lg]
        done=[e for e in items if e.get("status")=="graded"]
        n=len(done)
        row={"recorded":len(items),"settled":n,
             "pending":sum(e.get("status")=="pending" for e in items),
             "invalid":sum(e.get("status")=="invalid_chronology" for e in items),
             "draws_skipped":sum(e.get("status")=="draw_unsettled_2way" for e in items)}
        if n:
            def average(which,field):
                return round(sum(e[which][field] for e in done)/n,6)
            row["baseline"]={"brier":average("baseline_metrics","brier"),
                             "logloss":average("baseline_metrics","logloss")}
            row["ensemble"]={"brier":average("ensemble_metrics","brier"),
                             "logloss":average("ensemble_metrics","logloss")}
            row["delta_brier_candidate_vs_baseline"]=round(
                row["ensemble"]["brier"]-row["baseline"]["brier"],6)
        output[lg]=row
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"prospective_experiment_only",
        "summary":output,
        "promotion_allowed":False,
        "thresholds_before_independent_research_review":{
            "minimum_prospective_settled":150,
            "requires_independent_holdout":True,
        },
        "note":"Locked before the match, score-only. No ROI and no proven bookmaker advantage."
    }


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--baseline",default="docs/multisports-latest.json")
    a.add_argument("--model",default="docs/ensemble-mc-bayes-latest.json")
    a.add_argument("--history",default="docs/multisports-history.json")
    a.add_argument("--ledger",default="docs/ensemble-mc-bayes-ledger.json")
    a.add_argument("--output",default="docs/ensemble-mc-bayes-performance.json")
    args=a.parse_args()
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    now=datetime.now(timezone.utc)
    target=Path(args.ledger)
    ledger=load(target) if target.exists() else {"version":1,"events":{}}
    ledger,change=step(ledger,load(args.baseline),load(args.model),
                       load(args.history),now)
    report=summarize(ledger,now)
    for p,d in ((target,ledger),(Path(args.output),report)):
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Ensemble pre-match lock:",change,"settled total:",report["summary"]["ALL"]["settled"])

if __name__=="__main__":
    main()
