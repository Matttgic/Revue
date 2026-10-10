#!/usr/bin/env python3
"""Strict prospective paper-ledger probability evaluation (not fitted models).

One-vs-rest binary Brier/log loss for each *verified* locked selection. Compare
the same realized selection with bookmaker break-even probability 1/price.
The raw bookmaker implied probability INCLUDES vig and is not calibrated fair
value. It is a descriptive benchmark, not a betting edge or model selection.
Never backfill, mutate, use future ungraded results, or call odds APIs.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from math import isfinite, log
from pathlib import Path

from outils.revue_engine_v2 import verified_pre_match, timestamp

MIN_EVIDENCE = 100
VERSION = "revue_prospective_paper_calibration_v1"
CLOSED = {"won", "lost", "push"}


def score(probability:float, outcome:int)->tuple[float,float]:
    p=min(max(probability,1e-12),1-1e-12)
    return (probability-outcome)**2, -(outcome*log(p)+(1-outcome)*log(1-p))


def valid_entry(b:dict)->bool:
    if not isinstance(b,dict) or b.get("status") not in {"won","lost"}:
        return False
    if not verified_pre_match(b) or b.get("market_rule_verified") is not True:
        return False
    if b.get("league")=="CFB" or b.get("market") not in ("h2h","totals"):
        return False
    p=b.get("p_model")
    odds=b.get("bookmaker_price")
    if type(p) not in (int,float) or not isfinite(p) or not 0<p<1:
        return False
    if type(odds) not in (int,float) or not isfinite(odds) or not 1<odds<=100:
        return False
    if not b.get("event_id") or not isinstance(b.get("selection_id"),str):
        return False
    start=timestamp(b.get("start_utc"))
    settled=timestamp(b.get("settled_at"))
    if not start or not settled or settled<=start:
        return False
    stake=b.get("paper_stake_units")
    returned=b.get("paper_units_returned")
    if type(stake) not in (int,float) or not isfinite(stake) or not 0<stake<=10000:
        return False
    if type(returned) not in (int,float) or not isfinite(returned):
        return False
    expected=stake*odds if b["status"]=="won" else 0
    if abs(returned-expected)>1e-5:
        return False
    return True


def summarize(entries:list[dict])->dict:
    n=len(entries)
    if not n:
        return {"count":0,"distinct_events":0,"wins":0,"observed_frequency":None,
                "mean_model_probability":None,"mean_bookmaker_implied_probability":None,
                "brier_model":None,"brier_bookmaker_raw":None,
                "log_loss_model":None,"log_loss_bookmaker_raw":None,
                "brier_delta_model_minus_bookmaker":None,
                "status":"insufficient_sample"}
    ys=[int(e["status"]=="won") for e in entries]
    model=[float(e["p_model"]) for e in entries]
    market=[1/float(e["bookmaker_price"]) for e in entries]
    brier_m=sum(score(p,y)[0] for p,y in zip(model,ys))/n
    brier_b=sum(score(p,y)[0] for p,y in zip(market,ys))/n
    log_m=sum(score(p,y)[1] for p,y in zip(model,ys))/n
    log_b=sum(score(p,y)[1] for p,y in zip(market,ys))/n
    return {
        "count":n,
        "distinct_events":len({(e["league"],str(e["event_id"])) for e in entries}),
        "wins":sum(ys),
        "observed_frequency":round(sum(ys)/n,6),
        "mean_model_probability":round(sum(model)/n,6),
        "mean_bookmaker_implied_probability":round(sum(market)/n,6),
        "brier_model":round(brier_m,6),
        "brier_bookmaker_raw":round(brier_b,6),
        "log_loss_model":round(log_m,6),
        "log_loss_bookmaker_raw":round(log_b,6),
        "brier_delta_model_minus_bookmaker":round(brier_m-brier_b,6),
        "status":"insufficient_sample" if n<MIN_EVIDENCE
                 or len({(e["league"],str(e["event_id"])) for e in entries})<MIN_EVIDENCE
                 else "research_only_preliminary_evidence",
    }


def evaluate(ledger:dict,now:datetime)->dict:
    if now.tzinfo is None:
        raise ValueError("Timezone aware evaluation required")
    now=now.astimezone(timezone.utc)
    if ledger.get("version")!=1 or not isinstance(ledger.get("bets"),list):
        raise ValueError("Unrecognized paper registry")
    unique=set()
    used=[]
    ignored=Counter()
    for row in ledger["bets"]:
        if row.get("status")=="pending":
            ignored["pending"]+=1;continue
        if row.get("status")=="push":
            ignored["push_not_binary_outcome"]+=1;continue
        if not valid_entry(row):
            ignored["unsafe_or_ambiguous"]+=1;continue
        if timestamp(row["settled_at"])>now:
            ignored["future_settlement"]+=1;continue
        ident=row["selection_id"]
        if ident in unique:
            # Duplicate locks are not independent samples.
            raise ValueError("Duplicate settled selection ID")
        unique.add(ident)
        used.append(row)
    groups=defaultdict(list)
    for item in used:
        groups[item["league"]].append(item)
    total=summarize(used)
    total["independent_fixture_count_warning"]=(
        "Multiple model picks on one match share the same outcome and are correlated."
        if total["distinct_events"]<total["count"] else None)
    return {
        "version":VERSION,"generated_at_utc":now.isoformat(),
        "status":"prospective_probabilities_descriptive_not_calibrated",
        "source":"immutable engine-v2-ledger.json only",
        "predictions_published_before_start_only":True,
        "real_bets_enabled":False,
        "odds_api_requests":0,
        "fitted_or_recalibrated_model":False,
        "claim_model_profitable":False,
        "verified_positive_ev":False,
        "bookmaker_baseline_includes_vig":True,
        "selection_outcome_semantics":"won=1, lost=0; push/unknown excluded; evaluate each selected event vs its complement",
        "min_independent_fixtures_for_preliminary_evaluation":MIN_EVIDENCE,
        "total":total,
        "by_sport":{lg:summarize(v) for lg,v in sorted(groups.items())},
        "excluded":dict(ignored),
        "note":"A descriptive evaluation on prospective, locked, graded simulations. Low Brier/LogLoss is better, but 1/price includes vig. Small, correlated samples cannot demonstrate betting advantage.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ledger",default="docs/engine-v2-ledger.json")
    parser.add_argument("--output",default="docs/revue-model-quality-latest.json")
    args=parser.parse_args()
    ledger=json.loads(Path(args.ledger).read_text(encoding="utf8"))
    report=evaluate(ledger,datetime.now(timezone.utc))
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    print("Revue model quality: eligible",report["total"]["count"],
          "distinct",report["total"]["distinct_events"],
          "ignored",report["excluded"],"status",report["total"]["status"])


if __name__=="__main__":main()
