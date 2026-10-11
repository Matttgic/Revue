#!/usr/bin/env python3
"""Phase 2: Revue-owned *prospective* multi-sport forecasting & Elo history.

No copied Clairvoyance SQL, fake training labels, sportsbook access or bets.
Start the history at the first real run, and NEVER backfill fixtures that began
before that run. Lock immutable pre-kickoff probabilities from the already
published Revue model snapshot. Grade locked games and build independent Elo
from subsequent observed official ESPN final results; no model retraining,
promotion or use of post-match outcomes as pre-match features.

Domestic soccer is 90-minute 1X2; NBA/WNBA/NCAAB, NFL, MLB are two-way
final-score markets (includes overtime). MLS, UCL and NHL remain under their
own market-specific trackers because 90-minute vs extra-time/OT rules require
additional provenance. ATP/WTA/UFC/LIIGA already have separate research feeds.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import math

VERSION="revue_phase2_owned_history_v1"
REPORT_VERSION="revue_phase2_owned_performance_v1"
START_BUFFER=timedelta(minutes=20)
MAX_SNAPSHOT_AGE=timedelta(hours=12)
SCORE_MIN_DELAY=timedelta(minutes=35)
SOCCER=frozenset(("PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"))
TWO_WAY=frozenset(("NBA","WNBA","NCAAB","NFL","MLB"))
SUPPORTED=SOCCER|TWO_WAY
MODEL_KEYS=("baseline","advanced_team","montecarlo_bayes","football_advanced","own_elo")
OWN_ELO_K=24.0
OWN_ELO_BASE=1500.0
HOLDOUT_MIN=100
OWN_ELO_MIN_GAMES=3

def utc(value):
    if not isinstance(value,str):raise ValueError("Missing timestamp")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Naive timestamp")
    return t.astimezone(timezone.utc)

def valid_probability(value):
    return type(value) in (int,float) and math.isfinite(value) and 0<=value<=1

def normalize(probs,league):
    if not isinstance(probs,dict):return None
    keys=("home_win_90","draw_90","away_win_90") if league in SOCCER else ("home_win","away_win")
    vals=[probs.get(k) for k in keys]
    if not all(valid_probability(v) for v in vals):return None
    total=sum(vals)
    if not 0.997<=total<=1.003:return None
    result=[round(v/total,9) for v in vals]
    if not all(0<p<1 for p in result):return None
    return result

def _valid_generated(doc,now):
    if not isinstance(doc,dict):return None
    try: t=utc(doc["generated_at_utc"])
    except (KeyError,TypeError,ValueError):return None
    if t>now or now-t>MAX_SNAPSHOT_AGE:return None
    return t

def _event_key(league,event_id):
    ident=str(event_id)
    if league not in SUPPORTED or not ident.isdecimal() or not ident:
        return None
    return f"{league}:{ident}"

def _forecast_index(doc,league,field):
    data=doc.get(field)
    if not isinstance(data,dict):return {}
    rows=data.get(league,{}).get("games",[])
    if not isinstance(rows,list):return {}
    counts=Counter(str(x.get("event_id")) for x in rows if isinstance(x,dict))
    return {str(x["event_id"]):x for x in rows
            if isinstance(x,dict) and counts[str(x.get("event_id"))]==1}

def _same_game(row,source):
    try:
        return (row["home"]==source["home"] and row["away"]==source["away"]
                and utc(row["start_utc"])==utc(source["start_utc"]))
    except (KeyError,TypeError,ValueError):
        return False

def _challenger(name,doc,source,league,now):
    created=_valid_generated(doc,now)
    if created is None:return None
    field="competitions" if name=="football_advanced" else "leagues"
    row=_forecast_index(doc,league,field).get(str(source["event_id"]))
    if row is None or not _same_game(row,source):return None
    if row.get("status")!="shadow_non_calibre" or row.get("odds") is not None:return None
    try:
        cutoff=utc(source["start_utc"])-START_BUFFER
    except (KeyError,ValueError,TypeError):return None
    if created>cutoff:return None
    if name=="football_advanced":
        times=(row.get("espn_features_published_at") or {})
        try:
            if any(utc(t)>min(now,cutoff) for t in times.values()):return None
        except (TypeError,ValueError):return None
    normalized=normalize(row.get("probabilities"),league)
    if normalized is None:return None
    return {"model_id":str(row.get("model") or name),
            "probabilities":normalized,"published_at_utc":created.isoformat(),
            "training_games":deepcopy(row.get("training_games"))}

def _own_elo_forecast(source,league,models,now):
    """Additional independent shadow probability, after >=3 OWN observed finals per team.

    Previous-run verified official results only. It is never substituted for a
    source Clairvoyance Elo and never backfilled into existing locked games.
    """
    if league not in TWO_WAY:return None
    ratings=models.get("owned_elo_ratings") or {}
    events=models.get("owned_elo_events") or {}
    pool=ratings.get(league,{})
    home,away=source["home"],source["away"]
    if (not isinstance(pool,dict) or home not in pool or away not in pool):
        return None
    counts=Counter()
    for e in events.values():
        if e.get("league")!=league:continue
        try: when=utc(e["observed_at_utc"])
        except (TypeError,KeyError,ValueError):return None
        if when>now:return None
        counts[e["home"]]+=1;counts[e["away"]]+=1
    if min(counts[home],counts[away])<OWN_ELO_MIN_GAMES:return None
    h,a=pool[home],pool[away]
    if any(type(x) not in (int,float) or not math.isfinite(x) or not 500<=x<=2500 for x in (h,a)):
        return None
    p=1/(1+10**((a-h)/400))
    if not 0<p<1:return None
    return {"model_id":"revue_own_future_only_elo_k24_v1",
            "probabilities":[round(p,9),round(1-p,9)],
            "published_at_utc":now.isoformat(),
            "training_games":{"home":counts[home],"away":counts[away]},
            "source":"only observed Revue-owned ESPN finals from prior runs",
            "home_advantage_added":False}

def _lock_game(source,league,models,now,since):
    try:
        kickoff=utc(source["start_utc"])
        event_id=str(source["event_id"])
        home,away=source["home"],source["away"]
    except (KeyError,ValueError,TypeError):return None
    if (_event_key(league,event_id) is None or kickoff<since
        or kickoff-now<START_BUFFER or
        not isinstance(home,str) or not isinstance(away,str)
        or not home or not away or home==away
        or source.get("status")!="prototype_non_calibre"
        or source.get("odds") is not None):
        return None
    base=normalize(source.get("probabilities"),league)
    if base is None:return None
    model_stamp=models["baseline_stamp"]
    if model_stamp>kickoff-START_BUFFER:return None
    frozen={"baseline":{
      "model_id":"revue_independent_score_elo_v1",
      "probabilities":base,"published_at_utc":model_stamp.isoformat(),
      "training_games":deepcopy(source.get("training_games")),
    }}
    own_elo=_own_elo_forecast(source,league,models,now)
    if own_elo:frozen["own_elo"]=own_elo
    for name in ("advanced_team","montecarlo_bayes","football_advanced"):
        doc=models.get(name)
        if not doc:continue
        item=_challenger(name,doc,source,league,now)
        if item:frozen[name]=item
    return {
      "event_id":event_id,"league":league,"home":home,"away":away,
      "start_utc":kickoff.isoformat(),"locked_at_utc":now.isoformat(),
      "market":"1X2_90min" if league in SOCCER else "full_game_two_way",
      "probabilities":frozen,
      "status":"pending","resolved_at_utc":None,
      "home_score":None,"away_score":None,"result":None,
      "score_source":None,
      "model_scores":None,"real_bet":False,"stake_units":0,
    }

def _valid_final(row,now,since):
    if not isinstance(row,dict):return None
    league=row.get("league")
    key=_event_key(league,row.get("event_id"))
    if key is None or row.get("state")!="final" or row.get("prospective_bet_result") is not False:
        return None
    if row.get("source")!="ESPN scoreboard":return None
    try:
        start=utc(row["kickoff_utc"])
        reported=utc(row["observed_at_utc"])
    except (KeyError,ValueError,TypeError):return None
    if start<since or reported<start+SCORE_MIN_DELAY or reported>now+timedelta(minutes=2):
        return None
    home,away=row.get("home"),row.get("away")
    if not isinstance(home,str) or not isinstance(away,str) or not home or not away or home==away:
        return None
    x,y=row.get("home_score"),row.get("away_score")
    if (type(x) is not int or type(y) is not int or not 0<=x<=250 or not 0<=y<=250):
        return None
    if league in TWO_WAY and x==y:return None
    return dict(key=key,league=league,event_id=str(row["event_id"]),
        home=home,away=away,start_utc=start.isoformat(),
        observed_at_utc=reported.isoformat(),home_score=x,away_score=y,
        score_source="ESPN scoreboard")

def _model_score(probabilities,league,home,away):
    truth=(0 if home>away else 2 if home<away else 1) if league in SOCCER else (0 if home>away else 1)
    p=probabilities[truth]
    return {"brier":round(sum((v-(1 if i==truth else 0))**2 for i,v in enumerate(probabilities)),8),
            "log_loss":round(-math.log(max(1e-12,p)),8)}

def _elo_advance(elo,home,away,home_points,away_points):
    eh,ea=float(elo.get(home,OWN_ELO_BASE)),float(elo.get(away,OWN_ELO_BASE))
    p=1/(1+10**((ea-eh)/400))
    outcome=1 if home_points>away_points else 0 if home_points<away_points else .5
    updated_home=round(eh+OWN_ELO_K*(outcome-p),2)
    updated_away=round(ea+OWN_ELO_K*((1-outcome)-(1-p)),2)
    elo[home],elo[away]=updated_home,updated_away
    return {"home_before":eh,"away_before":ea,"home_after":updated_home,
            "away_after":updated_away,"observed_home_outcome":outcome}

def step(previous,baseline,advanced,ensemble,football,scores,now):
    if now.tzinfo is None:raise ValueError("Run clock must be timezone aware")
    now=now.astimezone(timezone.utc)
    if previous is None:
        prev={"version":VERSION,"since_utc":now.isoformat(),
              "events":{},"elo_events":{},"elo_ratings":{}}
    else:
        prev=deepcopy(previous)
    if (prev.get("version")!=VERSION
        or not isinstance(prev.get("events"),dict)
        or not isinstance(prev.get("elo_events"),dict)
        or not isinstance(prev.get("elo_ratings"),dict)):
        raise ValueError("Unrecognized immutable Revue phase2 history")
    since=utc(prev["since_utc"])
    if since>now:raise ValueError("History cannot start in the future")
    ledger=prev["events"]
    models={"advanced_team":advanced,"montecarlo_bayes":ensemble,
            "football_advanced":football}
    base_at=_valid_generated(baseline,now)
    models["baseline_stamp"]=base_at
    models["owned_elo_ratings"]=prev["elo_ratings"]
    models["owned_elo_events"]=prev["elo_events"]
    added=0
    if (base_at is not None and baseline.get("status")=="prototype_non_calibre"
        and isinstance(baseline.get("competitions"),dict)):
        for league,block in baseline["competitions"].items():
            if league not in SUPPORTED or not isinstance(block,dict):continue
            entries=block.get("games")
            if not isinstance(entries,list):continue
            counts=Counter(str(x.get("event_id")) for x in entries if isinstance(x,dict))
            for source in entries:
                if not isinstance(source,dict):continue
                event_id=str(source.get("event_id"))
                key=_event_key(league,event_id)
                if not key or key in ledger or counts[event_id]!=1:continue
                new=_lock_game(source,league,models,now,since)
                if new is not None:
                    ledger[key]=new;added+=1
    # Fail closed on duplicated, conflicting scoreboard records. No old lock is
    # altered when a different score or identity appears later.
    finals={}
    invalid=set()
    if isinstance(scores,dict) and scores.get("status")=="observed_scoreboard_not_streaming" and scores.get("scores_are_live_stream") is False and scores.get("pricing_used") is False:
        for row in scores.get("events") or []:
            final=_valid_final(row,now,since)
            if not final:continue
            key=final["key"]
            if key in finals and finals[key]!=final:invalid.add(key)
            else:finals[key]=final
    for key in invalid:finals.pop(key,None)
    settled=0
    for key,item in ledger.items():
        if not isinstance(item,dict):
            raise ValueError("Malformed frozen prediction")
        if item.get("status")!="pending":continue
        official=finals.get(key)
        if not official or any(official[k]!=item[k] for k in ("league","event_id","home","away")) or official["start_utc"]!=item["start_utc"]:
            continue
        if utc(item["locked_at_utc"])>utc(item["start_utc"])-START_BUFFER:
            continue
        new_truth=0 if official["home_score"]>official["away_score"] else 2 if official["home_score"]<official["away_score"] else 1
        if item["league"] in TWO_WAY and new_truth==1:continue
        item.update({
          "status":"settled",
          "resolved_at_utc":official["observed_at_utc"],
          "home_score":official["home_score"],
          "away_score":official["away_score"],
          "result":"home" if new_truth==0 else "draw" if new_truth==1 else "away",
          "score_source":"ESPN scoreboard",
          "model_scores":{
              k:_model_score(v["probabilities"],item["league"],
                             official["home_score"],official["away_score"])
              for k,v in item["probabilities"].items()
          }
        })
        settled+=1
    # Elo is our OWN independent future-only history, from every observed final
    # AFTER the real ledger start. We may observe finals with no prediction:
    # those count for Elo history, never for prospective model calibration.
    ratings=prev["elo_ratings"]
    accepted=0
    for key,final in sorted(finals.items(),key=lambda kv:(kv[1]["start_utc"],kv[0])):
        if key in prev["elo_events"]:continue
        league=final["league"]
        if not (isinstance(ratings.get(league),dict) or league not in ratings):
            raise ValueError("Malformed Elo ratings")
        pool=ratings.setdefault(league,{})
        change=_elo_advance(pool,final["home"],final["away"],final["home_score"],final["away_score"])
        prev["elo_events"][key]={**final,**change}
        accepted+=1
    # Frozen fields must stay byte-for-byte the same after settlement.
    for key,old in (previous or {}).get("events",{}).items():
        newer=ledger.get(key)
        immutable=("event_id","league","home","away","start_utc",
                   "locked_at_utc","market","probabilities","real_bet","stake_units")
        if not newer or any(newer.get(k)!=old.get(k) for k in immutable):
            raise AssertionError("Attempt to rewrite prospectively frozen prediction")
        if old["status"]=="settled" and newer!=old:
            raise AssertionError("Previously settled forecast cannot change")
    prev["updated_at_utc"]=now.isoformat()
    return prev,{"new_prediction_locks":added,"new_graded_forecasts":settled,
                 "new_independent_elo_results":accepted,"scoreboard_conflicts_excluded":len(invalid)}

def summarize(ledger,now):
    if ledger.get("version")!=VERSION:raise ValueError("Unknown phase2 ledger")
    by=defaultdict(list)
    for event in ledger["events"].values():
        if event["status"]=="settled":by[event["league"]].append(event)
    stats={}
    for league in sorted(SUPPORTED):
        events=by.get(league,[])
        recorded=[v for v in ledger["events"].values() if v["league"]==league]
        models={}
        for name in MODEL_KEYS:
            valid=[v for v in events if name in v["model_scores"]]
            n=len(valid)
            models[name]={"settled":n,"brier":round(sum(v["model_scores"][name]["brier"] for v in valid)/n,6) if n else None,
                          "log_loss":round(sum(v["model_scores"][name]["log_loss"] for v in valid)/n,6) if n else None,
                          "status":"insufficient_prospective_sample" if n<HOLDOUT_MIN else "research_evidence_requires_holdout"}
        stats[league]={
          "locked":len(recorded),"settled":len(events),
          "pending":len(recorded)-len(events),"independent_elo_finals":sum(e["league"]==league for e in ledger["elo_events"].values()),
          "models":models,
        }
    return {
      "version":REPORT_VERSION,"generated_at_utc":now.isoformat(),
      "since_utc":ledger["since_utc"],
      "status":"new_revue_history_prospective_not_source_sql",
      "source":"Revue independently published model snapshots + ESPN observed finals",
      "total_unique_matches_locked":len(ledger["events"]),
      "total_unique_matches_settled":sum(v["status"]=="settled" for v in ledger["events"].values()),
      "total_independent_elo_finals":len(ledger["elo_events"]),
      "eligible_leagues":sorted(SUPPORTED),"excluded_unverified_90min_or_ot":["NHL","MLS","UCL"],
      "independent_elo_initial":OWN_ELO_BASE,"independent_elo_k":OWN_ELO_K,
      "identical_original_clairvoyance_sql_history":False,
      "replayed_old_results":False,
      "real_bets_enabled":False,"odds_queried":False,"roi_computed":False,
      "models_calibrated":False,"bet_recommendations_verified":False,
      "per_league":stats,
      "minimum_settled_per_model_before_independent_review":HOLDOUT_MIN,
      "note":"Starts at the first GitHub workflow run. Historical matches never become pregame locks. Own Elo updates from verified finals after that time, not Clairvoyance SQL; small Brier samples cannot prove edge."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--docs",default="docs")
    a=ap.parse_args()
    root=Path(a.docs)
    def read(p):
        f=root/p
        return json.loads(f.read_text("utf8")) if f.exists() else None
    now=datetime.now(timezone.utc)
    prev=read("phase2-owned-ledger.json")
    state,changes=step(prev,read("multisports-latest.json") or {},
        read("equipes-avance-shadow.json") or {},
        read("ensemble-mc-bayes-latest.json") or {},
        read("football-advanced-shadow.json") or {},
        read("scoreboard-revue-latest.json") or {},now)
    output=summarize(state,now)
    for p,data in (("phase2-owned-ledger.json",state),("phase2-owned-performance.json",output)):
        tmp=root/(p+".next")
        tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
        tmp.replace(root/p)
    print("Phase2:",changes,"locked",output["total_unique_matches_locked"],
          "settled",output["total_unique_matches_settled"],
          "own Elo finals",output["total_independent_elo_finals"])
if __name__=="__main__":main()
