#!/usr/bin/env python3
"""Independent real ESPN football TEAM match-stat aggregates (not Opta / not xG).

No raw ESPN response copied or published. Only minimal match-level *derived*
numeric aggregates needed for original independent model research are cached,
limited to recent completed events. Never backdate observation times.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timedelta,timezone
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

from modeles.simulations.multisports_independant import LEAGUES
from modeles.simulations.football_avance_independant import utc

LEAGUES_ESPN={x.key:x.provider for x in LEAGUES if x.style=="soccer"}
STATS=("totalShots","shotsOnTarget","possessionPct","accuratePasses",
       "totalPasses","interceptions","totalTackles")
MAX_CALLS=28
MAX_DAYS=70
MIN_AGE_HOURS=12
SOURCE="ESPN soccer summary / original derived team-level indicators"


def numeric(v,minimum=0,max_value=2000):
    if isinstance(v,bool):return None
    try:
        s=str(v).strip().replace("%","").replace(",","")
        n=float(s)
    except (ValueError,TypeError):return None
    if not math.isfinite(n) or n<minimum or n>max_value:return None
    return n


def extract_boxscore(raw:dict,home_id:str,away_id:str) -> dict|None:
    """Only accept both exact ESPN ids and enough comparable shot data."""
    teams={}
    for t in ((raw.get("boxscore") or {}).get("teams") or []):
        team=str((t.get("team") or {}).get("id") or "")
        if not team or team in teams:continue
        values={}
        for r in t.get("statistics") or []:
            key=r.get("name")
            if key not in STATS:continue
            val=numeric(r.get("displayValue",r.get("value")),
                        max_value=100 if key=="possessionPct" else 2000)
            if val is not None:values[key]=val
        if {"totalShots","shotsOnTarget"}.issubset(values):
            if values["shotsOnTarget"]>values["totalShots"]:continue
            teams[team]=values
    if home_id==away_id or home_id not in teams or away_id not in teams:
        return None
    return {"home":teams[home_id],"away":teams[away_id]}


def fetch_stat(league:str,event_id:str) -> dict:
    if league not in LEAGUES_ESPN or not str(event_id).isdigit():
        raise ValueError("Unsupported league or event")
    url=("https://site.api.espn.com/apis/site/v2/sports/"+
         LEAGUES_ESPN[league]+"/summary?"+urlencode({"event":event_id}))
    with urlopen(Request(url,headers={"Accept":"application/json"}),timeout=14) as r:
        data=json.loads(r.read().decode("utf-8"))
    if not isinstance(data,dict):raise ValueError("Malformed ESPN reply")
    return data


def update_cache(history:dict,existing:dict,now:datetime,
                 fetch=fetch_stat,max_calls:int=MAX_CALLS)->tuple[dict,dict]:
    if not 0<=max_calls<=MAX_CALLS:raise ValueError("budget must be 0..28")
    rows=existing.get("events") if isinstance(existing,dict) else None
    saved=dict(rows) if isinstance(rows,dict) else {}
    recent=now-timedelta(days=MAX_DAYS)
    for k,x in list(saved.items()):
        dt=utc(x.get("start_utc"))
        if dt is None or dt<recent or dt>now or x.get("league") not in LEAGUES_ESPN:
            del saved[k]
    candidates=[]
    for league,d in (history.get("leagues") or {}).items():
        if league not in LEAGUES_ESPN:continue
        for g in d.get("events") or []:
            start=utc(g.get("start"))
            if (not g.get("complete") or start is None or start<recent or
                start>now-timedelta(hours=MIN_AGE_HOURS) or
                g.get("home_score") is None or g.get("away_score") is None):
                continue
            eid=str(g.get("id") or "")
            cache_key=f"{league}:{eid}"
            if cache_key not in saved:
                candidates.append((start,league,eid,g))
    # Prioritize historical stats for teams with the earliest FUTURE
    # matches. Avoid 1 sample for 24 unrelated clubs (not enough for any
    # reliable feature); obtain at least 3 prior games for both sides of
    # an upcoming match before spreading out to new teams/leagues.
    all_candidates=sorted(candidates,key=lambda e:e[0],reverse=True)
    by_team=defaultdict(list)
    for item in all_candidates:
        _,league,_,g=item
        for tid in (str(g.get("home_id") or ""),str(g.get("away_id") or "")):
            if tid:by_team[(league,tid)].append(item)
    observed_games=defaultdict(int)
    for item in saved.values():
        lg=item.get("league")
        for tid in (item.get("home_id"),item.get("away_id")):
            if lg in LEAGUES_ESPN and tid:
                observed_games[(lg,str(tid))]+=1
    upcoming=[]
    for league,d in (history.get("leagues") or {}).items():
        if league not in LEAGUES_ESPN:continue
        for g in d.get("events") or []:
            kickoff=utc(g.get("start"))
            if (not g.get("complete") and kickoff and
                now<kickoff<now+timedelta(days=3)):
                upcoming.append((kickoff,league,g))
    upcoming.sort(key=lambda x:(x[0],x[1]))
    selected=[]
    selected_ids=set()
    def select(item):
        _,lg,eid,g=item
        key=f"{lg}:{eid}"
        if key in selected_ids or key in saved or len(selected)>=max_calls:
            return False
        selected.append(item);selected_ids.add(key)
        for tid in (g.get("home_id"),g.get("away_id")):
            if tid:observed_games[(lg,str(tid))]+=1
        return True
    for _,league,g in upcoming:
        for tid in (str(g.get("home_id") or ""),str(g.get("away_id") or "")):
            for item in by_team.get((league,tid),[]):
                if len(selected)>=max_calls or observed_games[(league,tid)]>=3:break
                select(item)
    # Fill unused budget from newest completed matches, balanced by league.
    league_lists=defaultdict(list)
    for item in all_candidates:
        if f"{item[1]}:{item[2]}" not in selected_ids:
            league_lists[item[1]].append(item)
    while len(selected)<max_calls and any(league_lists.values()):
        for league in LEAGUES_ESPN:
            if league_lists[league] and len(selected)<max_calls:
                select(league_lists[league].pop(0))
    errors=defaultdict(int)
    successes=0
    for start,league,eid,g in selected:
        try:
            data=fetch(league,eid)
            parsed=extract_boxscore(data,str(g["home_id"]),str(g["away_id"]))
            if parsed is None:
                errors["incomplete_shot_stats"]+=1
                continue
            saved[f"{league}:{eid}"]={
                "league":league,"start_utc":start.isoformat(),
                "observed_at_utc":now.isoformat(),
                "home_id":str(g["home_id"]),"away_id":str(g["away_id"]),
                "derived":parsed,
            }
            successes+=1
        except Exception:
            errors["unavailable"]+=1
    out={"generated_at_utc":now.isoformat(),"source":SOURCE,
         "warning":"Match stats are NOT Opta xG and never substituted as true xG.",
         "events":saved}
    status={"calls_attempted":len(selected),"responses_parsed":successes,
            "cached_games":len(saved),"errors":dict(errors),
            "source":"ESPN public soccer summaries"}
    return out,status


def _team_sample(rows:list[dict])->dict:
    n=len(rows)
    if not n:return {}
    def avg(attr):
        values=[r[attr] for r in rows if attr in r]
        return round(sum(values)/len(values),3) if values else None
    return {"games":n,"shots_per_game":avg("totalShots"),
            "sot_per_game":avg("shotsOnTarget"),
            "shots_allowed_per_game":avg("shotsAllowed"),
            "sot_allowed_per_game":avg("sotAllowed"),
            "possession_pct":avg("possessionPct"),
            "passes_per_game":avg("totalPasses"),
            "accurate_passes_per_game":avg("accuratePasses"),
            "interceptions_per_game":avg("interceptions"),
            "tackles_per_game":avg("totalTackles")}


def calculate_team_features(cache:dict,as_of:datetime,min_games:int=3)->dict:
    """Point-in-time observations ONLY, never infer a historical publish date."""
    pool=defaultdict(list)
    for event in (cache.get("events") or {}).values():
        start=utc(event.get("start_utc"))
        observed=utc(event.get("observed_at_utc"))
        if not start or not observed or start>as_of or observed>as_of:continue
        league=event.get("league")
        if league not in LEAGUES_ESPN:continue
        for side in ("home","away"):
            tid=str(event.get(f"{side}_id") or "")
            both=(event.get("derived") or {})
            stats=both.get(side)
            opponent=both.get("away" if side=="home" else "home")
            if tid and isinstance(stats,dict):
                row=dict(stats)
                if isinstance(opponent,dict):
                    if "totalShots" in opponent:
                        row["shotsAllowed"]=opponent["totalShots"]
                    if "shotsOnTarget" in opponent:
                        row["sotAllowed"]=opponent["shotsOnTarget"]
                pool[(league,tid)].append((start,observed,row))
    result={}
    for (league,team),values in pool.items():
        games=sorted(values,key=lambda t:t[0],reverse=True)[:12]
        if len(games)<min_games:continue
        sample=_team_sample([x[2] for x in games])
        # Aggregate snapshot cannot predate the newest source observation.
        published=max(t[1] for t in games)
        result[f"{league}:{team}"]={
            "league":league,"team_id":team,"published_at":published.isoformat(),
            "source":SOURCE,"type":"observed_shots_not_xg",
            **sample,
        }
    return result


def build(history:dict,cache:dict,now:datetime,max_calls=MAX_CALLS,fetch=fetch_stat):
    fresh,status=update_cache(history,cache,now,max_calls=max_calls,fetch=fetch)
    features=calculate_team_features(fresh,now)
    report={
        "generated_at_utc":now.isoformat(),
        "status":"real_boxscore_derived_not_opta",
        "source":SOURCE,
        "xg_available":False,"opta_available":False,
        "statistics":status,"teams":features,
        "disclaimer":"Observed shots/SOT/possession etc. No Opta xG, no predictions or betting claims.",
    }
    return fresh,report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--history",default="docs/multisports-history.json")
    ap.add_argument("--cache",default="docs/football-espn-stat-cache.json")
    ap.add_argument("--output",default="docs/football-espn-team-features.json")
    ap.add_argument("--max-calls",type=int,default=MAX_CALLS)
    args=ap.parse_args()
    history=json.loads(Path(args.history).read_text(encoding="utf-8"))
    path=Path(args.cache)
    existing=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"events":{}}
    cache,report=build(history,existing,datetime.now(timezone.utc),
                       max_calls=args.max_calls)
    for dest,obj in ((path,cache),(Path(args.output),report)):
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ESPN football advanced stats:",report["statistics"],
          "teams eligible:",len(report["teams"]), "no actual Opta xG")


if __name__=="__main__":
    main()
