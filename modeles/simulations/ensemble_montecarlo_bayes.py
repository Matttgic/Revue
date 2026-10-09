#!/usr/bin/env python3
"""Independent shadow model: Elo + Beta-Binomial + seeded Monte Carlo.

Inspired by generic model ensembles, not copied from any unlicensed repository.
Scores from the existing timestamped ESPN cache only, with a strict pre-match
lag. Predictions contain NO odds, stakes or automatic bet recommendations.
College football is deliberately EXCLUDED at the user's request.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import pstdev

from modeles.simulations.multisports_independant import (
    Event, LEAGUES, _read_cached_event, _logistic, calculate,
)
from modeles.simulations.equipes_avance_multisports import (
    SPORTS, history_before, predict as old_shadow, score_metrics,
)

MODEL="mc_bayes_elo_shadow_v1"
SIMULATIONS=768
K_PRIOR=12.
BETA_PRIOR=8.
MIN_TRAIN=SPORTS
CONFIG={x.key:x for x in LEAGUES if x.key in SPORTS}
WEIGHTS={"monte_carlo":.52,"bayes":.23,"elo":.25}
assert abs(sum(WEIGHTS.values())-1)<1e-10


def clamp(x:float,lo:float=.01,hi:float=.99)->float:
    return min(hi,max(lo,x))


def expected_score_rows(past:list[Event])->dict[str,list[tuple[float,float]]]:
    rows=defaultdict(list)
    for event in past:
        rows[event.home_id].append((float(event.home_score),float(event.away_score)))
        rows[event.away_id].append((float(event.away_score),float(event.home_score)))
    return rows


def _rate(vals:list[tuple[float,float]],side:int,league_avg:float)->float:
    return (sum(row[side] for row in vals)+K_PRIOR*league_avg)/(len(vals)+K_PRIOR)


def _montecarlo(league:str,game:Event,rows:dict,league_avg:float,
                home_boost:float,samples:int=SIMULATIONS)->tuple[float,float,float]:
    if samples<100:raise ValueError("Monte Carlo needs >=100 draws")
    h=rows[game.home_id];a=rows[game.away_id]
    hgf=_rate(h,0,league_avg)
    hga=_rate(h,1,league_avg)
    agf=_rate(a,0,league_avg)
    aga=_rate(a,1,league_avg)
    # Opponent-adjusted, heavily shrunk points-per-game forecast.
    home_expect=max(.25,min(190.,(hgf+aga)/2+home_boost))
    away_expect=max(.25,min(190.,(agf+hga)/2))
    seed=int.from_bytes(hashlib.sha256(
        f"{MODEL}|{league}|{game.id}|{game.start.isoformat()}".encode()).digest()[:8],
        "big")
    rng=random.Random(seed)
    _,prior_std,_=SPORTS[league]
    # Shrink dispersion; short sequences of lopsided wins must not imply
    # unrealistically certain outcomes.
    h_stdev=pstdev([row[0] for row in h[-20:]]) if len(h)>=2 else 0.
    a_stdev=pstdev([row[0] for row in a[-20:]]) if len(a)>=2 else 0.
    team_sd=math.sqrt(max(.2,prior_std**2/2)*.7+
                      .3*(h_stdev**2+a_stdev**2)/2)
    team_sd=max(prior_std*.36,min(prior_std*1.2,team_sd))
    home=away=0
    for _ in range(samples):
        score_h=max(0.,rng.gauss(home_expect,team_sd))
        score_a=max(0.,rng.gauss(away_expect,team_sd))
        # With continuous-score Monte Carlo, draws have probability 0.
        if score_h>score_a:home+=1
        else:away+=1
    return (home/samples,home_expect,away_expect)


def predict(league:str,events:list[Event],game:Event,as_of:datetime,
            simulations:int=SIMULATIONS)->dict:
    if league not in SPORTS:raise ValueError("Sport not supported (CFB excluded)")
    if as_of.tzinfo is None or game.start<=as_of:
        raise ValueError("Forecast must precede kickoff")
    minimum,prior_sigma,elo_home=SPORTS[league]
    past=history_before(events,league,as_of)
    rows=expected_score_rows(past)
    hr=rows[game.home_id];ar=rows[game.away_id]
    base={"event_id":game.id,"league":league,"home":game.home,"away":game.away,
          "start_utc":game.start.isoformat(),"model":MODEL,"status":"insufficient_history",
          "training_games":{"home":len(hr),"away":len(ar)},
          "probabilities":None,"components":None}
    if min(len(hr),len(ar))<minimum:return base
    elo=defaultdict(lambda:1500.)
    result=defaultdict(lambda:[0,0])
    for x in past:
        h,a=elo[x.home_id],elo[x.away_id]
        expected=_logistic(h,a,elo_home)
        outcome=.5 if x.home_score==x.away_score else float(x.home_score>x.away_score)
        change=22*(outcome-expected)
        elo[x.home_id]+=change
        elo[x.away_id]-=change
        # Intentionally excludes ties from binary win records.
        if x.home_score!=x.away_score:
            result[x.home_id][0]+=int(x.home_score>x.away_score)
            result[x.home_id][1]+=1
            result[x.away_id][0]+=int(x.away_score>x.home_score)
            result[x.away_id][1]+=1
    p_elo=_logistic(elo[game.home_id],elo[game.away_id],elo_home)
    hw,hn=result[game.home_id]
    aw,an=result[game.away_id]
    b_h=(hw+BETA_PRIOR)/(hn+2*BETA_PRIOR)
    b_a=(aw+BETA_PRIOR)/(an+2*BETA_PRIOR)
    # A two-team win-percent proxy is NOT opponent-adjusted or calibrated.
    p_bayes=clamp(.5+(b_h-b_a)*.65+.026)
    mean_pts=(sum(e.home_score+e.away_score for e in past)/
              (2*len(past))) if past else 1.
    prior_mean={"NBA":108.,"WNBA":83.,"NCAAB":70.,"NFL":22.,"MLB":4.5}
    avg=max(.25,min(160.,(mean_pts*len(past)+prior_mean[league]*20)/
                     (len(past)+20)))
    home_boost=max(.1,min(4.,.07*prior_sigma))
    p_mc,home_pts,away_pts=_montecarlo(
        league,game,rows,avg,home_boost,simulations)
    ensemble=clamp(
        WEIGHTS["monte_carlo"]*p_mc+
        WEIGHTS["bayes"]*p_bayes+
        WEIGHTS["elo"]*p_elo)
    base.update({
        "status":"shadow_non_calibre",
        "probabilities":{"home_win":round(ensemble,5),
                         "away_win":round(1-ensemble,5)},
        "components":{"monte_carlo":round(p_mc,5),
                      "bayes":round(p_bayes,5),"elo":round(p_elo,5),
                      "weights":WEIGHTS,
                      "iterations":simulations,
                      "method":"deterministic_independent_gaussian_points"},
        "expected_score":{"home":round(home_pts,2),"away":round(away_pts,2)},
        "notes":"Independent research: score-only Monte Carlo, Beta(8,8), Elo. No confirmed injury/pitcher/quarterback data."
    })
    return base


def evaluate(league:str,events:list[Event])->dict:
    finals=sorted((e for e in events if e.scored and e.league==league),
                  key=lambda e:(e.start,e.id))
    observations={"baseline":[],"previous_shadow":[],"ensemble":[]}
    for e in finals:
        # Only binary final result; do not grade a tied score as ML loss.
        if e.home_score==e.away_score:continue
        cutoff=e.start-timedelta(minutes=1)
        past=history_before(finals,league,cutoff)
        target=Event(e.id,e.league,e.start,e.home_id,e.away_id,
                     e.home,e.away,False,None,None)
        pred=predict(league,past,target,cutoff)
        if pred["probabilities"] is None:continue
        prev=old_shadow(league,past,target,cutoff)
        old=calculate(CONFIG[league],past+[target],cutoff,days=2)
        original=next((x for x in old if x["event_id"]==e.id),None)
        if not prev["probabilities"] or not original or not original["probabilities"]:
            continue
        truth=int(e.home_score>e.away_score)
        observations["baseline"].append((original["probabilities"]["home_win"],truth))
        observations["previous_shadow"].append((prev["probabilities"]["home_win"],truth))
        observations["ensemble"].append((pred["probabilities"]["home_win"],truth))
    n=len(observations["ensemble"])
    if not n:return {"status":"history_insufficient","n":0}
    report={key:score_metrics(value) for key,value in observations.items()}
    return {"status":"chronological_score_backtest_no_odds",
            "n":n,"scores":report,
            "delta_brier_vs_baseline":round(
                report["ensemble"]["brier_binary"]-report["baseline"]["brier_binary"],5),
            "delta_brier_vs_previous_shadow":round(
                report["ensemble"]["brier_binary"]-report["previous_shadow"]["brier_binary"],5),
            "warning":"Small sample, same hyperparameters across sports. No ROI/CLV, no automatic promotion."}


def build(cache:dict,now:datetime,days:int=3)->dict:
    if now.tzinfo is None or not 1<=days<=7:raise ValueError("Invalid now/days")
    output={}
    for lg in SPORTS:
        raw=(cache.get("leagues") or {}).get(lg,{}).get("events") or []
        ev=[e for r in raw if (e:=_read_cached_event(r)) is not None]
        fut=sorted((e for e in ev if not e.complete and
                    now<e.start<now+timedelta(days=days)),
                   key=lambda g:(g.start,g.id))
        output[lg]={"games":[predict(lg,ev,e,now) for e in fut],
                    "evaluation":evaluate(lg,ev)}
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"experimental_no_bets",
        "source":"ESPN cached results; generated Revue model coefficients",
        "parameters":{"iterations":SIMULATIONS,"weights":WEIGHTS,
                      "prior_strength_games":K_PRIOR,
                      "bayes_beta_prior":BETA_PRIOR},
        "leagues":output,
        "exclusions":["CFB"],
        "disclaimer":"Uncalibrated independent model; no player injury or lineup signal, no exact Clairvoyance code reproduction."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",default="docs/multisports-history.json")
    parser.add_argument("--output",default="docs/ensemble-mc-bayes-latest.json")
    parser.add_argument("--days",type=int,default=3)
    a=parser.parse_args()
    history=json.loads(Path(a.history).read_text(encoding="utf-8"))
    data=build(history,datetime.now(timezone.utc),a.days)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for key,v in data["leagues"].items():
        print(key,":",len(v["games"]),"future,",
              sum(g["probabilities"] is not None for g in v["games"]),"predicted;",
              v["evaluation"]["n"],"backtest.")
if __name__=="__main__":
    main()
