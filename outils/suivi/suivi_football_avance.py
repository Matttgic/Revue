#!/usr/bin/env python3
"""Prospective audit of the independent advanced-football SHADOW model.

Locks pairs of baseline/advanced 1X2 probabilities *before* kickoff with
provenance and settles domestic 90m league games using verified cached scores.
No betting, bookmaker account, stake or automatic model promotion.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import json
import math
from pathlib import Path

from modeles.simulations.football_avance_independant import utc

ALLOWED={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"}
SAFE_BUFFER=timedelta(minutes=20)
MAX_AGE=timedelta(hours=6)
SIGNAL_KEYS=("home_win_90","draw_90","away_win_90")


def probabilities(p:dict) -> list[float] | None:
    if not isinstance(p,dict):return None
    try:
        values=[float(p[k]) for k in SIGNAL_KEYS]
    except (TypeError,ValueError,KeyError):return None
    if not all(math.isfinite(v) and 0<=v<=1 for v in values):
        return None
    if abs(sum(values)-1)>.003:return None
    return [v/sum(values) for v in values]


def grade(p:list[float],target:int)->dict:
    return {"brier":round(sum((x-(1 if i==target else 0))**2
                     for i,x in enumerate(p)),6),
            "logloss":round(-math.log(max(1e-12,p[target])),6)}


def reconcile(ledger:dict,baseline:dict,shadow:dict,history:dict,now:datetime):
    if not now.tzinfo:raise ValueError("Clock without timezone")
    ledgers=ledger.setdefault("events",{})
    if not isinstance(ledgers,dict):raise ValueError("Invalid ledger")
    a_created=utc(baseline.get("generated_at_utc"))
    b_created=utc(shadow.get("generated_at_utc"))
    allowed_inputs=(a_created is not None and b_created is not None and
             a_created<=now and b_created<=now and
             now-a_created<=MAX_AGE and now-b_created<=MAX_AGE)
    added=0
    if allowed_inputs:
        for league,d in (shadow.get("competitions") or {}).items():
            if league not in ALLOWED:continue
            source_games=(baseline.get("competitions") or {}).get(league,{}).get("games") or []
            baseline_index={str(x.get("event_id")):x for x in source_games}
            for s in d.get("games") or []:
                gid=str(s.get("event_id") or "")
                key=f"{league}:{gid}"
                if not gid or key in ledgers:continue
                b=baseline_index.get(gid)
                if b is None:continue
                kickoff=utc(s.get("start_utc"))
                b_kickoff=utc(b.get("start_utc"))
                if (kickoff is None or b_kickoff!=kickoff or
                    now>=kickoff-SAFE_BUFFER or
                    s.get("home")!=b.get("home") or s.get("away")!=b.get("away") or
                    not (a_created<kickoff and b_created<kickoff)):
                    continue
                pa=probabilities(s.get("probabilities"))
                pb=probabilities(b.get("probabilities"))
                if pa is None or pb is None:continue
                ledgers[key]={
                    "id":gid,"league":league,
                    "home":str(s.get("home") or ""),
                    "away":str(s.get("away") or ""),
                    "start_utc":kickoff.isoformat(),
                    "locked_at_utc":now.isoformat(),
                    "baseline_generated_at_utc":a_created.isoformat(),
                    "shadow_generated_at_utc":b_created.isoformat(),
                    "baseline_1x2":pb,"shadow_1x2":pa,
                    "espn_stats_used":bool(s.get("espn_stats_used")),
                    "real_xg_used":bool(s.get("xg_used")),
                    "status":"pending",
                }
                added+=1

    verified={(lg,str(ev.get("id"))):ev for lg,sec in (history.get("leagues") or {}).items()
         for ev in (sec.get("events") or [])
         if ev.get("complete") is True and ev.get("home_score") is not None
            and ev.get("away_score") is not None}
    settled=0
    for item in ledgers.values():
        if item.get("status")!="pending":continue
        kickoff=utc(item.get("start_utc"))
        locked=utc(item.get("locked_at_utc"))
        ma=utc(item.get("baseline_generated_at_utc"))
        mb=utc(item.get("shadow_generated_at_utc"))
        if (kickoff is None or locked is None or ma is None or mb is None or
            locked>=kickoff-SAFE_BUFFER or ma>locked or mb>locked):
            item["status"]="invalid_chronology"
            continue
        if kickoff>=now:continue
        e=verified.get((item.get("league"),item.get("id")))
        # A numeric provider ID alone is not enough to prove fixture identity.
        # Reject schedule amendments or mis-mapped home/away participants.
        if (not e or utc(e.get("start"))!=kickoff or
            e.get("home")!=item.get("home") or
            e.get("away")!=item.get("away")):
            continue
        try:
            h,a=float(e["home_score"]),float(e["away_score"])
        except (ValueError,TypeError):
            continue
        ix=0 if h>a else 2 if a>h else 1
        item["outcome"]=("home","draw","away")[ix]
        item["score"]={"home":h,"away":a}
        item["baseline_metrics"]=grade(item["baseline_1x2"],ix)
        item["shadow_metrics"]=grade(item["shadow_1x2"],ix)
        item["settled_at_utc"]=now.isoformat()
        item["status"]="graded"
        settled+=1
    return ledger,{"new_prematch_snapshots":added,"newly_settled":settled}


def summarize(ledger:dict,now:datetime) -> dict:
    pools={"ALL":list((ledger.get("events") or {}).values())}
    for key in ALLOWED:
        pools[key]=[x for x in pools["ALL"] if x.get("league")==key]
    pools["WITH_ESPN_SHOTS"]=[x for x in pools["ALL"] if x.get("espn_stats_used")]
    pools["WITHOUT_ESPN_SHOTS"]=[x for x in pools["ALL"] if not x.get("espn_stats_used")]
    result={}
    for league,items in pools.items():
        done=[v for v in items if v.get("status")=="graded"
              and "baseline_metrics" in v and "shadow_metrics" in v]
        n=len(done)
        scores={}
        if n:
            for m in ("baseline_metrics","shadow_metrics"):
                scores[m]={"brier":round(sum(x[m]["brier"] for x in done)/n,6),
                           "logloss":round(sum(x[m]["logloss"] for x in done)/n,6)}
        result[league]={
            "n_recorded":len(items),"n_settled":n,
            "n_pending":sum(i.get("status")=="pending" for i in items),
            "n_invalid":sum(i.get("status")=="invalid_chronology" for i in items),
            "scores":scores,
            "brier_delta_candidate_minus_baseline":round(
                scores["shadow_metrics"]["brier"]-
                scores["baseline_metrics"]["brier"],6) if n else None,
        }
    return {
        "generated_at_utc":now.isoformat(),
        "status":"prospective_football_score_audit_only",
        "source":"ESPN final scores; only verified pre-match frozen predictions",
        "prediction_source":"Revue independent baseline and shadow model",
        "performance":result,
        "note":"No odds, ROI or value claims. Small n insufficient for automatic promotion."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",default="docs/multisports-latest.json")
    p.add_argument("--shadow",default="docs/football-advanced-shadow.json")
    p.add_argument("--history",default="docs/multisports-history.json")
    p.add_argument("--ledger",default="docs/football-shadow-ledger.json")
    p.add_argument("--report",default="docs/football-shadow-performance.json")
    args=p.parse_args()
    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    led_file=Path(args.ledger)
    ledger=load(led_file) if led_file.exists() else {"version":1,"events":{}}
    now=datetime.now(timezone.utc)
    ledger,changes=reconcile(ledger,load(args.baseline),load(args.shadow),
                             load(args.history),now)
    report=summarize(ledger,now)
    for dest,obj in ((led_file,ledger),(Path(args.report),report)):
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Shadow football audit:",changes,
          "all:",report["performance"]["ALL"])


if __name__=="__main__":
    main()
