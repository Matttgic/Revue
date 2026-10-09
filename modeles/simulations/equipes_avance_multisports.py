#!/usr/bin/env python3
"""Independent, uncalibrated team model. No copied Clairvoyance code or data.

NBA/WNBA/NCAAB/NFL/CFB/MLB: Elo + Bayesian score-margin and last-5 form,
then a chronological scores-only benchmark. SHADOW ONLY, not betting.
"""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from modeles.simulations.multisports_independant import (
    Event,LEAGUES,_read_cached_event,calculate,_logistic)
LAG=timedelta(hours=8)
# required games/team; expected one-game margin standard deviation; Elo home bonus
SPORTS={"NBA":(7,12.,52.),"WNBA":(7,11.,50.),"NCAAB":(5,11.,45.),
        "NFL":(3,13.,35.),"CFB":(4,18.,35.),"MLB":(7,3.1,24.)}
BASE={l.key:l for l in LEAGUES if l.key in SPORTS}

def history_before(events:list[Event],league:str,when:datetime)->list[Event]:
    if when.tzinfo is None:raise ValueError("UTC offset needed")
    return sorted((e for e in events if e.league==league and e.scored
                   and e.start<=when-LAG),key=lambda x:(x.start,x.id))

def predict(league:str,events:list[Event],game:Event,when:datetime)->dict:
    if league not in SPORTS:raise ValueError("Unsupported league")
    minimum,sigma,hfa=SPORTS[league]
    past=history_before(events,league,when)
    scores=defaultdict(list)
    elo=defaultdict(lambda:1500.)
    for e in past:
        p=_logistic(elo[e.home_id],elo[e.away_id],hfa)
        win=.5 if e.home_score==e.away_score else (1. if e.home_score>e.away_score else 0.)
        delta=22*(win-p)
        elo[e.home_id]+=delta;elo[e.away_id]-=delta
        scores[e.home_id].append(e.home_score-e.away_score)
        scores[e.away_id].append(e.away_score-e.home_score)
    h,a=scores[game.home_id],scores[game.away_id]
    result={"event_id":game.id,"league":league,"home":game.home,"away":game.away,
            "start_utc":game.start.isoformat(),"status":"insufficient_history",
            "model":"elo_recent_margin_shadow_v1",
            "training_games":{"home":len(h),"away":len(a)},
            "probabilities":None,"odds":None}
    if min(len(h),len(a))<minimum:return result
    def strength(rows):
        n=len(rows);mean=sum(rows)/n
        prior=mean*n/(n+10)
        last=rows[-5:]
        form=max(-sigma*.5,min(sigma*.5,sum(last)/len(last)-mean))
        return .75*prior+.25*form
    margin=max(-2*sigma,min(2*sigma,
               (strength(h)-strength(a))/2+.07*sigma))
    p_margin=.5*(1+math.erf(margin/(math.sqrt(2)*sigma)))
    p_elo=_logistic(elo[game.home_id],elo[game.away_id],hfa)
    p=max(.01,min(.99,.63*p_elo+.37*p_margin))
    result.update({
        "status":"shadow_non_calibre",
        "probabilities":{"home_win":round(p,5),"away_win":round(1-p,5)},
        "expected_margin_home":round(margin,3),
        "components":{"elo_probability":round(p_elo,4),
                      "margin_probability":round(p_margin,4),
                      "last_games_form":5},
    })
    return result

def score_metrics(items:list[tuple[float,int]])->dict:
    n=len(items)
    if not n:return {}
    b=sum((p-y)**2 for p,y in items)/n
    ll=-sum(y*math.log(max(1e-10,p))+(1-y)*math.log(max(1e-10,1-p))
         for p,y in items)/n
    return {"brier_binary":round(b,5),"logloss_binary":round(ll,5)}

def evaluate(league:str,events:list[Event])->dict:
    finals=sorted((e for e in events if e.league==league and e.scored),
                  key=lambda e:(e.start,e.id))
    current=[];old=[]
    for game in finals:
        if game.home_score==game.away_score:continue # 2-way ML ties not graded
        when=game.start-timedelta(minutes=1)
        train=history_before(finals,league,when)
        target=Event(game.id,game.league,game.start,game.home_id,game.away_id,
                     game.home,game.away,False,None,None)
        candidate=predict(league,train,target,when)
        if not candidate["probabilities"]:continue
        baseline=calculate(BASE[league],train+[target],when,2)
        match=next((x for x in baseline if x["event_id"]==game.id),None)
        if not match or not match["probabilities"]:continue
        outcome=int(game.home_score>game.away_score)
        current.append((candidate["probabilities"]["home_win"],outcome))
        old.append((match["probabilities"]["home_win"],outcome))
    n=len(current)
    if not n:return {"n":0,"status":"insufficient_history"}
    c,b=score_metrics(current),score_metrics(old)
    return {"n":n,"status":"small_walk_forward_scores_only",
            "candidate":c,"baseline":b,
            "brier_delta_candidate_minus_baseline":round(
                c["brier_binary"]-b["brier_binary"],5),
            "note":"No historical sportsbook odds; not a profit claim."}

def build(cache:dict,now:datetime,days:int=3)->dict:
    if now.tzinfo is None or not 1<=days<=7:raise ValueError("invalid clock/days")
    out={}
    for league in SPORTS:
        data=(cache.get("leagues") or {}).get(league,{}).get("events") or []
        events=[e for x in data if (e:=_read_cached_event(x)) is not None]
        future=sorted((e for e in events if not e.complete
            and now<e.start<now+timedelta(days=days)),key=lambda x:(x.start,x.id))
        out[league]={"games":[predict(league,events,e,now) for e in future],
                     "evaluation":evaluate(league,events)}
    return {"generated_at_utc":now.astimezone(timezone.utc).isoformat(),
            "mode":"SHADOW_NO_BET","source":"ESPN archived scores",
            "leagues":out,
            "warning":"Not calibrated; no injuries, starting pitcher, QB or lineups. Never auto-selected."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",default="docs/multisports-history.json")
    parser.add_argument("--output",default="docs/equipes-avance-shadow.json")
    parser.add_argument("--days",default=3,type=int)
    a=parser.parse_args()
    raw=json.loads(Path(a.history).read_text(encoding="utf-8"))
    report=build(raw,datetime.now(timezone.utc),a.days)
    f=Path(a.output);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for key,d in report["leagues"].items():
        print(key,"forecast",sum(bool(g["probabilities"]) for g in d["games"]),
              "backtest",d["evaluation"]["n"])

if __name__=="__main__":main()
