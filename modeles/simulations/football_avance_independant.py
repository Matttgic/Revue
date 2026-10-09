#!/usr/bin/env python3
"""Independent football research model: rolling Elo + goals, optional licensed xG.

NOT Clairvoyance source code and NOT an exact copy of its parameters.
No unlicensed Opta scraping or redistribution. Scores: ESPN point-in-time.
Optional xG/power snapshots: supplied with verifiable licence AND timestamp.

Model is SHADOW ONLY: it does not feed betting suggestions or paper locks.
Compare with existing baseline on past score results first.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from modeles.simulations.multisports_independant import (
    LEAGUES, Event, _read_cached_event, _logistic, _poisson, calculate
)

PARIS=ZoneInfo("Europe/Paris")
SOCCER={l.key:l for l in LEAGUES if l.style=="soccer"}
LAG=timedelta(hours=8)
MIN_TEAM_GAMES=5
DC_RHO=-0.06
PRIOR_TEAM_MATCHES=8.
MAX_FEATURE_AGE=timedelta(days=12)
MIN_XG_GAMES=5


def utc(s:str|None) -> datetime|None:
    if not isinstance(s,str):return None
    try:
        x=datetime.fromisoformat(s.replace("Z","+00:00"))
        return x.astimezone(timezone.utc) if x.tzinfo else None
    except (ValueError,OverflowError):
        return None


def _finite(value:object,low:float,high:float)->float|None:
    if isinstance(value,bool):return None
    try:
        x=float(value)
    except (ValueError,TypeError):
        return None
    return x if math.isfinite(x) and low<=x<=high else None


def validate_licensed_snapshots(raw:dict)->tuple[dict,dict]:
    """Strict provenance. A public URL by itself is NOT a licence."""
    if not isinstance(raw,dict) or raw.get("authorized") is not True or not raw.get("permission_reference"):
        return {},{"status":"no_authorized_source","records":0}
    found:dict[tuple[str,str],list[dict]]=defaultdict(list)
    errors=0
    for r in raw.get("snapshots") or []:
        if not isinstance(r,dict) or r.get("league") not in SOCCER:
            errors+=1;continue
        league,team=str(r["league"]),str(r.get("team_id") or "")
        date=utc(r.get("published_at"))
        n=_finite(r.get("games"),0,200)
        attack=_finite(r.get("xg_for_per90"),.05,6.5)
        defence=_finite(r.get("xg_against_per90"),.05,6.5)
        rating=_finite(r.get("power_rating"),0,100)
        if (not team or not date or n is None or attack is None
            or defence is None or rating is None or not r.get("source")):
            errors+=1;continue
        found[(league,team)].append({
            "published_at":date,"games":n,
            "xg_for_per90":attack,"xg_against_per90":defence,
            "power_rating":rating,"source":str(r["source"]),
        })
    for value in found.values():
        value.sort(key=lambda x:x["published_at"])
    return dict(found),{
        "status":"licensed_input_valid" if found else "no_valid_snapshots",
        "records":sum(len(v) for v in found.values()),"rejected":errors,
    }


def feature_at(index:dict,league:str,team_id:str,cutoff:datetime)->dict|None:
    # Data published exactly at kickoff is not demonstrably pre-match.
    relevant=[r for r in index.get((league,team_id),[]) if
        r["published_at"]<cutoff and
        timedelta(0)<=cutoff-r["published_at"]<=MAX_FEATURE_AGE and
        r["games"]>=MIN_XG_GAMES]
    return relevant[-1] if relevant else None


def _dixon_coles(lh:float,la:float,rho:float=DC_RHO)->tuple[float,float,float,float]:
    """Normalized truncated grid; four low-goal cells receive DC adjustment."""
    ph,pa=_poisson(lh,18),_poisson(la,18)
    w=d=l=over=0.0
    mass=0.0
    for h, hp in enumerate(ph):
        for a, ap in enumerate(pa):
            tau=1.0
            if h==a==0:tau=1-rho*lh*la
            elif h==0 and a==1:tau=1+rho*lh
            elif h==1 and a==0:tau=1+rho*la
            elif h==a==1:tau=1-rho
            val=max(0.,tau)*hp*ap
            mass+=val
            if h>a:w+=val
            elif h==a:d+=val
            else:l+=val
            if h+a>=3:over+=val
    if mass<=0:raise ValueError("Poisson mass zero")
    return w/mass,d/mass,l/mass,over/mass


def predict(league:str,events:list[Event],candidate:Event,
            cutoff:datetime,features:dict|None=None,
            min_team_games:int=MIN_TEAM_GAMES,
            espn_features:dict|None=None)->dict:
    """Only matches that started >=8h before forecast cutoff enter training."""
    if league not in SOCCER or cutoff.tzinfo is None:
        raise ValueError("League or timestamp not supported")
    older=sorted((e for e in events
        if e.league==league and e.scored and
        e.id!=candidate.id and e.start<=cutoff-LAG),
        key=lambda e:(e.start,e.id))
    by:dict[str,list[tuple[float,float]]]=defaultdict(list)
    ratings=defaultdict(lambda:1500.0)
    for e in older:
        a,b=ratings[e.home_id],ratings[e.away_id]
        ex=_logistic(a,b,30)
        outcome=1 if e.home_score>e.away_score else 0 if e.home_score<e.away_score else .5
        d=20*(outcome-ex)
        ratings[e.home_id]+=d;ratings[e.away_id]-=d
        by[e.home_id].append((e.home_score,e.away_score))
        by[e.away_id].append((e.away_score,e.home_score))
    home,away=by[candidate.home_id],by[candidate.away_id]
    base={
        "event_id":candidate.id,"home":candidate.home,"away":candidate.away,
        "start_utc":candidate.start.isoformat(),
        "league":league,"model":"advanced_shadow_v1",
        "training_games":{"home":len(home),"away":len(away)},
        "probabilities":None,"expected_score":None,
        "xg_used":False,"espn_stats_used":False,
        "status":"historique_insuffisant",
        "odds":None,
    }
    if len(home)<min_team_games or len(away)<min_team_games:
        return base
    avg=(sum(e.home_score+e.away_score for e in older)/(2*len(older))
         if older else 1.45)
    avg=max(0.8,min(2.5,.55*1.45+.45*avg))
    def rate(team:list[tuple[float,float]])->tuple[float,float,float]:
        n=len(team)
        gf=(sum(t[0] for t in team)+PRIOR_TEAM_MATCHES*avg)/(n+PRIOR_TEAM_MATCHES)
        ga=(sum(t[1] for t in team)+PRIOR_TEAM_MATCHES*avg)/(n+PRIOR_TEAM_MATCHES)
        rec=team[-5:]
        rec_gf=sum(t[0] for t in rec)/len(rec)
        # Form uses recent scores only, very small influence/maximum 8%.
        form=max(-.08,min(.08,.045*(rec_gf-gf)))
        return gf,ga,form
    hgf,hga,hform=rate(home);agf,aga,aform=rate(away)
    h_feat=feature_at(features or {},league,candidate.home_id,cutoff)
    a_feat=feature_at(features or {},league,candidate.away_id,cutoff)
    if h_feat and a_feat:
        # Shrink toward goal rates. This is NOT an Opta proprietary formula.
        hgf=.60*hgf+.40*h_feat["xg_for_per90"]
        hga=.60*hga+.40*h_feat["xg_against_per90"]
        agf=.60*agf+.40*a_feat["xg_for_per90"]
        aga=.60*aga+.40*a_feat["xg_against_per90"]
        base["xg_used"]=True
        base["features_published_at"]={
            "home":h_feat["published_at"].isoformat(),
            "away":a_feat["published_at"].isoformat(),
        }
        power=max(-.11,min(.11,(h_feat["power_rating"]-a_feat["power_rating"])*.006))
    else:
        power=0.
    # Do not raise probabilities blindly for ratings gap; use as
    # small multiplier to expected goals, bounded for sports realism.
    lh=max(.3,min(3.8,hgf*aga/avg*1.07*(1+hform)*math.exp(power)))
    la=max(.3,min(3.8,agf*hga/avg*.93*(1+aform)*math.exp(-power)))
    # ESPN football box scores have real shots/SOT, NOT real expected goals.
    # Apply a small independent shooting-pressure modifier only if BOTH
    # teams have recent pre-forecast observed features.
    def _espn_team(tid):
        record=(espn_features or {}).get(f"{league}:{tid}")
        if not isinstance(record,dict):return None
        published=utc(record.get("published_at"))
        if (record.get("type")!="observed_shots_not_xg" or
            published is None or published>=cutoff or
            cutoff-published>MAX_FEATURE_AGE or
            int(record.get("games") or 0)<3):
            return None
        needed=("shots_per_game","sot_per_game","sot_allowed_per_game")
        if any(_finite(record.get(k),0,100) is None for k in needed):return None
        return record
    eh,ea=_espn_team(candidate.home_id),_espn_team(candidate.away_id)
    if eh and ea:
        # Bounded multiplicative effect; deliberately no proprietary
        # power rating nor xG inference from shot counts.
        def shot_term(attack,opp):
            atk=.55*(attack["sot_per_game"]/4.4-1)
            volume=.15*(attack["shots_per_game"]/13-1)
            opp_concede=.30*(opp["sot_allowed_per_game"]/4.4-1)
            return max(-.09,min(.09,.11*(atk+volume+opp_concede)))
        hshot=shot_term(eh,ea)
        ashot=shot_term(ea,eh)
        lh=max(.3,min(3.8,lh*math.exp(hshot)))
        la=max(.3,min(3.8,la*math.exp(ashot)))
        base["espn_stats_used"]=True
        base["espn_stats_source"]="ESPN observed boxscore stats; not xG/Opta"
        base["espn_features_published_at"]={
            "home":eh["published_at"],"away":ea["published_at"],
        }
    ph,pd,pa,over=_dixon_coles(lh,la)
    elo=_logistic(ratings[candidate.home_id],ratings[candidate.away_id],35)
    # Blend 15% Elo into the decisive-outcome mass, preserving DC draw.
    home_win=.85*ph+.15*(1-pd)*elo
    away_win=1-pd-home_win
    base.update({
        "status":"shadow_non_calibre",
        "probabilities":{
            "home_win_90":round(home_win,5),
            "draw_90":round(pd,5),
            "away_win_90":round(away_win,5),
            "over_2_5":round(over,5),
        },
        "expected_score":{"home":round(lh,3),"away":round(la,3)},
    })
    return base


def _brier(probs:list[float],idx:int)->float:
    return sum((p-(1 if j==idx else 0))**2 for j,p in enumerate(probs))


def _loss(probs:list[float],idx:int)->float:
    return -math.log(max(1e-7,probs[idx]))


def evaluate(league:str,events:list[Event],features:dict|None=None,
             espn_features:dict|None=None)->dict:
    """Walk-forward. Cannot evaluate later-published licensed data in prior games."""
    cfg=SOCCER[league]
    settled=sorted([e for e in events if e.scored],
                   key=lambda e:(e.start,e.id))
    scores={"shadow":[],"baseline":[]}
    n=0;late=0
    for game in settled:
        cutoff=game.start-timedelta(minutes=1)
        older=[e for e in settled if e.start<=cutoff-LAG and e.id!=game.id]
        target=replace(game,complete=False,home_score=None,away_score=None)
        pred=predict(league,older,target,cutoff,features,
                     espn_features=espn_features)
        if not pred["probabilities"]:
            continue
        if pred["xg_used"]:late+=1
        # The original Revue baseline has a different minimum, but its
        # inputs are restricted to the SAME known-before-cutoff games.
        base=calculate(cfg,older+[target],cutoff,days=1)
        prev=next((x for x in base if x["event_id"]==game.id),None)
        if not prev or not prev["probabilities"]:continue
        idx=0 if game.home_score>game.away_score else 2 if game.away_score>game.home_score else 1
        for name,p in (("shadow",pred["probabilities"]),("baseline",prev["probabilities"])):
            vec=[p["home_win_90"],p["draw_90"],p["away_win_90"]]
            scores[name].append((_brier(vec,idx),_loss(vec,idx)))
        n+=1
    if n==0:
        return {"status":"insufficient_history","n":0}
    result={"status":"small_historical_score_backtest","n":n,
            "licensed_features_used_in_backtest":late}
    for key,values in scores.items():
        result[key]={
            "brier":round(sum(v[0] for v in values)/n,5),
            "logloss":round(sum(v[1] for v in values)/n,5),
        }
    result["shadow_brier_delta_vs_baseline"]=round(
        result["shadow"]["brier"]-result["baseline"]["brier"],5)
    result["interpretation"]="Negative delta favors shadow, but this is NOT proof of value against bookmakers."
    return result


def build(cache:dict,features_raw:dict|None,now:datetime,days:int=3,
          espn_raw:dict|None=None)->dict:
    if not 1<=days<=7:raise ValueError("1-7 days")
    feat,diag=validate_licensed_snapshots(features_raw or {})
    leagues=cache.get("leagues") or {}
    observed=(espn_raw or {}).get("teams") or {}
    if not isinstance(observed,dict):observed={}
    output={}
    for league in SOCCER:
        entries=leagues.get(league,{}).get("events") or []
        events=[e for raw in entries if (e:=_read_cached_event(raw)) is not None]
        future=sorted((e for e in events if not e.complete and
              e.start>now and now.astimezone(PARIS).date()
              <=e.start.astimezone(PARIS).date()
              <now.astimezone(PARIS).date()+timedelta(days=days)),
              key=lambda e:e.start)
        output[league]={
            "name":SOCCER[league].label,
            "games":[predict(league,events,e,now,feat,
                             espn_features=observed) for e in future],
            "evaluation":evaluate(league,events,feat,observed),
        }
    return {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"shadow_experimental_never_auto_bet",
        "licensed_advanced_features":diag,
        "espn_observed_features":{
            "status":"available" if observed else "not_available",
            "teams":len(observed),"genuine_xg":False,
        },
        "competitions":output,
        "disclaimer":"Independent candidate model, no proprietary weights copied. No bookmaker edge confirmed; not sent to Engine V2 paper locks.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cache",default="docs/multisports-history.json")
    p.add_argument("--features",default="data/football_features_authorized.json")
    p.add_argument("--output",default="docs/football-advanced-shadow.json")
    p.add_argument("--espn-team-stats",default="docs/football-espn-team-features.json")
    p.add_argument("--days",type=int,default=3)
    args=p.parse_args()
    cache=json.loads(Path(args.cache).read_text(encoding="utf-8"))
    feature_path=Path(args.features)
    raw={}
    if feature_path.exists():
        raw=json.loads(feature_path.read_text(encoding="utf-8"))
    espn_path=Path(args.espn_team_stats)
    espn_data=(json.loads(espn_path.read_text(encoding="utf-8"))
               if espn_path.exists() else {})
    report=build(cache,raw,datetime.now(timezone.utc),args.days,
                 espn_raw=espn_data)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for lg,row in report["competitions"].items():
        print(f"{lg}: future {len(row['games'])}, "
              f"forecast {sum(bool(g['probabilities']) for g in row['games'])}, "
              f"backtest {row['evaluation'].get('n',0)}")
    print("Licensed features:",report["licensed_advanced_features"]["status"])


if __name__=="__main__":
    main()
