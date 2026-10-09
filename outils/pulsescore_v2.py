#!/usr/bin/env python3
"""PulseScore Pro prematch adapter for Revue V2. Original integration code.

Converts PulseScore canonical market schema into the exact shared quote
representation consumed by Revue Engine V2. Prefers real provider update
times, otherwise timestamps OUR own authenticated observation at fetch time.

All API calls are bounded. Never print credentials, store X-Secret in JSON,
or pretend PS3838 is identical to Pinnacle.
"""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from outils.revue_engine_v2 import match_fixture, timestamp, ODDS_SPORTS, KICKOFF_BUFFER

SOURCE="https://api.pulsescore.net/api"
BOOKMAKERS={
    "betclic_fr":"betclic",
    "winamax_fr":"winamax",
    "unibet_fr":"unibet-fr",
    "netbet_fr":"netbet",
    "pmu_fr":"pmu",
}
SPORT_GROUPS={
    "NBA":"basketball","WNBA":"basketball","NCAAB":"basketball",
    "NFL":"american-football","CFB":"american-football",
    "MLB":"baseball","NHL":"ice-hockey",
    "PL":"soccer","LALIGA":"soccer","SERIEA":"soccer",
    "BUNDESLIGA":"soccer","LIGUE1":"soccer","MLS":"soccer",
}
MAX_PAGES=2
MAX_CALLS=32
HORIZON_HOURS=36


def _request(book:str,sport:str,key:str,page:int) -> tuple[list[dict],bool]:
    if book not in BOOKMAKERS.values() or sport not in set(SPORT_GROUPS.values()):
        raise ValueError("Unrecognized PulseScore sports/bookmaker")
    query=urlencode({"page":page,"limit":30})
    url=f"{SOURCE}/{book}/{sport}/events?{query}"
    try:
        with urlopen(Request(url,headers={"X-Secret":key,"Accept":"application/json"}),
                     timeout=22) as response:
            data=json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        raise RuntimeError(f"HTTP {err.code} from PulseScore {book}/{sport}") from None
    except (URLError,TimeoutError,ValueError) as err:
        raise RuntimeError(f"{type(err).__name__} from PulseScore {book}/{sport}") from None
    records=data.get("events")
    if not isinstance(records,list):
        raise RuntimeError(f"Malformed PulseScore events from {book}/{sport}")
    next_page=data.get("hasNextPage") is True
    return records,next_page


def _side(outcome:str,home:str,away:str) -> str|None:
    lookup={
        "HOME":home,"1":home,
        "AWAY":away,"2":away,
        "DRAW":"Draw","X":"Draw",
        "OVER":"Over","UNDER":"Under",
    }
    val=lookup.get(str(outcome).strip().upper())
    return val


def translate_market(m:dict,event:dict,observed:datetime) -> dict|None:
    """Normalize only verified full-game head-to-head/total market structures."""
    if m.get("isActive") is False:return None
    period=str(m.get("period") or "").upper()
    if period not in ("FULL_TIME","MATCH","GAME","GAME_INCLUDING_OVERTIME",""):
        return None
    canonical=str(m.get("canonicalMarket") or "").upper()
    raw=str(m.get("rawName") or "").lower()
    # Avoid first-half, team totals or player props silently treated as FT.
    if any(x in raw for x in ("player","1st period","1st half","first half","team total",
                              "quarter","period goals")):
        return None
    if canonical in ("MATCH_RESULT","MATCH_WINNER","MONEYLINE","HEAD_TO_HEAD","WINNER"):
        market="h2h"
    elif canonical in ("OVER_UNDER","TOTAL_GOALS","TOTAL_POINTS","MATCH_TOTAL"):
        if any(x in raw for x in ("corner","card","booking","yellow","red","penalt")):
            return None
        market="totals"
    else:
        return None
    outcomes=[]
    for selection in m.get("selections") or []:
        if selection.get("isActive") is False:continue
        name=_side(selection.get("canonicalOutcome"),event["home"],event["away"])
        if name is None:
            name=_side(selection.get("rawName"),event["home"],event["away"])
        if name is None:
            # Source may use participant team name directly.
            rawname=str(selection.get("rawName") or "")
            if rawname in (event["home"],event["away"]):name=rawname
            else:continue
        try:
            price=float(selection["odds"])
            if not 1.0<price<=100:continue
        except (KeyError,ValueError,TypeError):
            continue
        record={"name":name,"price":price}
        if market=="totals":
            try:
                record["point"]=float(selection["line"])
            except (TypeError,ValueError,KeyError):
                continue
        outcomes.append(record)
    if market=="h2h":
        if len(outcomes) not in (2,3):return None
        if len({x["name"] for x in outcomes})!=len(outcomes):return None
        if "Over" in [x["name"] for x in outcomes]:return None
    if market=="totals":
        lines=defaultdict(set)
        for o in outcomes:lines[o["point"]].add(o["name"])
        # A market object can contain alternative lines. Filter to complete pairs.
        good={point for point,names in lines.items() if names=={"Over","Under"}}
        outcomes=[x for x in outcomes if x["point"] in good]
        if not outcomes:return None
    raw_stamp=m.get("updatedAt") or m.get("lastUpdate") or event.get("updatedAt")
    update=timestamp(raw_stamp) or observed
    return {"key":market,"last_update":update.isoformat(),
            "observed_origin":"provider" if timestamp(raw_stamp) else "fetch_observation",
            "outcomes":outcomes}


def translate_event(raw:dict,book_key:str,observed:datetime)->dict|None:
    """Return The Odds API-compatible event with one observed FR book."""
    if raw.get("live") is True or raw.get("isLive") is True:
        return None
    home,away=raw.get("home"),raw.get("away")
    start=timestamp(raw.get("startTime") or raw.get("startDate"))
    if not isinstance(home,str) or not isinstance(away,str) or not start or home==away:
        return None
    if start <= observed+KICKOFF_BUFFER:
        return None
    if not raw.get("eventId"):
        return None
    markets=[x for x in (translate_market(m,raw,observed)
                        for m in (raw.get("markets") or [])) if x]
    if not markets:
        return None
    return {
        "id":str(raw["eventId"]),"home_team":home,"away_team":away,
        "commence_time":start.isoformat(),
        "bookmakers":[{
            "key":book_key,"last_update":observed.isoformat(),
            "markets":markets,
        }],
    }


def scan(key:str,models:dict,now:datetime,
         max_calls:int=MAX_CALLS,days_horizon:int=HORIZON_HOURS,
         fetch=None) -> tuple[dict,dict]:
    """Radar: scan each sport/book ONCE, then optionally a second page.

    Limits calls globally rather than per sport to prevent monthly blowups.
    """
    if not 1<=max_calls<=MAX_CALLS:raise ValueError("Invalid max_calls")
    if not 1<=days_horizon<=72:raise ValueError("Invalid horizon")
    fetch=fetch or _request
    horizon=now+timedelta(hours=days_horizon)
    interested={}
    for league,entry in models.get("competitions",{}).items():
        if league not in SPORT_GROUPS or league not in ODDS_SPORTS:
            continue
        upcoming=[]
        for g in entry.get("games") or []:
            start=timestamp(g.get("start_utc"))
            if (start and now+KICKOFF_BUFFER<start<=horizon
                  and g.get("status")=="prototype_non_calibre" and
                  isinstance(g.get("probabilities"),dict)):
                upcoming.append({**g,"_league":league})
        if upcoming:
            interested[league]=upcoming

    sports={SPORT_GROUPS[lg] for lg in interested}
    # All five bookmakers for all selected sports before second-page scans.
    # Prioritize the sport whose matching fixture starts earliest.
    earliest={sport:min(timestamp(g["start_utc"]) for league,games in interested.items()
            if SPORT_GROUPS[league]==sport for g in games) for sport in sports}
    sport_order=sorted(sports,key=lambda sport:earliest[sport])
    tasks=deque((sport,b,1) for sport in sport_order for b in BOOKMAKERS)
    results=defaultdict(dict)
    stats={"status":"active","requests":0,"errors":{},"matched_events":0,
           "sports":sport_order,"bookmakers":list(BOOKMAKERS),
           "truncated":False,"max_calls":max_calls,
           "horizon_hours":days_horizon,
           "observation_provenance":"provider updatedAt when present; else time fetched",
           }
    while tasks and stats["requests"]<max_calls:
        sport,book_key,page=tasks.popleft()
        prefix=BOOKMAKERS[book_key]
        try:
            records,has_next=fetch(prefix,sport,key,page)
            stats["requests"]+=1
        except Exception as err:
            stats["requests"]+=1
            # Do not include exception URL or secret in reports
            stats["errors"][f"{book_key}:{sport}:p{page}"]=(f"{type(err).__name__}: no valid feed")
            continue
        seen_at=now
        for record in records:
            translated=translate_event(record,book_key,seen_at)
            if not translated:continue
            for league,games in interested.items():
                if SPORT_GROUPS[league]!=sport:continue
                matched=match_fixture(translated,games,league)
                if matched is None:continue
                # Match against Revue's stable event rather than aggregating
                # vendor event ids across different bookmakers.
                key_id=str(matched["event_id"])
                stored=results[league].setdefault(key_id,{
                    "id":f"review:{league}:{key_id}",
                    "home_team":matched["home"],"away_team":matched["away"],
                    "commence_time":matched["start_utc"],
                    "bookmakers":[],
                })
                stored["bookmakers"].extend(translated["bookmakers"])
                stats["matched_events"]+=1
        if has_next and page<MAX_PAGES and stats["requests"]<max_calls:
            # Only proceed when earliest event could still be within horizon.
            last_start=timestamp(records[-1].get("startTime")) if records else None
            if last_start is None or last_start<=horizon:
                tasks.append((sport,book_key,page+1))
    stats["truncated"]=len(tasks)>0
    output={league:list(events.values()) for league,events in results.items()}
    stats["matched_leagues"]={league:len(rows) for league,rows in output.items()}
    return output,stats
