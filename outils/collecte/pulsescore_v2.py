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
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from outils.suivi.revue_engine_v2 import match_fixture, timestamp, ODDS_SPORTS, KICKOFF_BUFFER

SOURCE="https://api.pulsescore.net/api"
BOOKMAKERS={
    "betclic_fr":"betclic",
    "winamax_fr":"winamax",
    "unibet_fr":"unibet-fr",
    "pmu_fr":"pmu",
}
# Le « netbet » de PulseScore est netbet.co.uk (UK), pas NetBet France : exclu.
# PS3838 sert uniquement de référence sharp (jamais parié, jamais appelé Pinnacle).
# Orbit Exchange (bourse adossée à la liquidité Betfair) : référence pour la NHL,
# absente de PS3838. Prix « back » de la bourse ; jamais parié.
REFERENCE_BOOKS={"ps3838":"ps3838","orbit_exchange":"orbitxch"}
SCAN_BOOKS={**BOOKMAKERS,**REFERENCE_BOOKS}
# Une référence n'est interrogée que pour les sports où elle sert (appels économisés).
REFERENCE_SPORTS={"orbit_exchange":{"ice-hockey"}}
# Bourse : un prix sans au moins 20 £ disponibles n'est pas une référence fiable.
MIN_EXCHANGE_LIQUIDITY=20.0


def books_for(sport:str)->list[str]:
    return [b for b in SCAN_BOOKS if sport in REFERENCE_SPORTS.get(b,{sport})]
# Offre Pro : 1 requête par seconde et par bookmaker.
MIN_INTERVAL_PER_BOOK=1.1
SPORT_GROUPS={
    "NBA":"basketball","WNBA":"basketball","NCAAB":"basketball",
    "NFL":"american-football",
    "MLB":"baseball","NHL":"ice-hockey",
    "PL":"soccer","LALIGA":"soccer","SERIEA":"soccer",
    "BUNDESLIGA":"soccer","LIGUE1":"soccer","MLS":"soccer",
}
# Accès PulseScore Pro illimité : 5 sports x 5 sources x 4 pages couvre
# tout le catalogue ; le plafond reste un garde-fou contre une boucle folle.
MAX_PAGES=4
MAX_CALLS=100
HORIZON_HOURS=36
MAX_LEAGUE_LISTING_PAGES=5
RETRIES_429=3

# Collecte par ligue : la pagination globale (30 prochains matchs toutes ligues
# confondues) rate la NHL ou la Premier League derrière la KHL ou la D2
# algérienne. Noms observés dans les catalogues PulseScore (diagnostic du
# 2026-10-12), comparés sans le pays ni la saison.
LEAGUE_NAMES={
    "NFL":{"nfl"},"MLB":{"mlb","major league"},"NHL":{"nhl"},
    "PL":{"premier league"},
    "LALIGA":{"laliga","la liga","laliga ea sports","primera division"},
    "SERIEA":{"serie a"},
    "BUNDESLIGA":{"bundesliga","bundesliga 1","1. bundesliga"},
    "LIGUE1":{"ligue 1","ligue 1 mcdonalds","ligue 1 mcdonald's"},
    "MLS":{"mls","major league soccer"},
}
# Pays exigé quand le bookmaker l'indique (« Egypt - Premier League » refusé).
LEAGUE_COUNTRIES={
    "PL":{"england","angleterre","gb","eng","royaume-uni","united kingdom"},
    "LALIGA":{"spain","espagne","es"},
    "SERIEA":{"italy","italie","it"},
    "BUNDESLIGA":{"germany","allemagne","de"},
    "LIGUE1":{"france","fr"},
    "MLS":{"usa","us","états-unis","etats-unis","united states"},
}


def league_matches(name,country,revue_league:str)->bool:
    """Vrai si une ligue du catalogue bookmaker est la ligue Revue demandée."""
    if revue_league not in LEAGUE_NAMES or not isinstance(name,str):return False
    core=" ".join(name.lower().split())
    core=re.sub(r"\s*\d{4}/\d{2,4}$","",core)
    country=" ".join(str(country or "").lower().split()) or None
    if " - " in core:
        prefix,core=core.split(" - ",1)
        country=country or prefix.strip()
    allowed=LEAGUE_COUNTRIES.get(revue_league)
    if allowed and country is None:
        for alias in sorted(allowed,key=len,reverse=True):
            if core.startswith(alias+" "):
                core,country=core[len(alias)+1:],alias
                break
    if core.strip() not in LEAGUE_NAMES[revue_league]:return False
    return allowed is None or country is None or country in allowed


def _get_json(book:str,sport:str,suffix:str,key:str,params:dict) -> dict:
    """GET {SOURCE}/{book}/{sport}/{suffix}; erreurs nettoyées (ni URL ni clé)."""
    if book not in SCAN_BOOKS.values() or sport not in set(SPORT_GROUPS.values()):
        raise ValueError("Unrecognized PulseScore sports/bookmaker")
    url=f"{SOURCE}/{book}/{sport}/{suffix}?{urlencode(params)}"
    for attempt in range(RETRIES_429+1):
        try:
            with urlopen(Request(url,headers={"X-Secret":key,"Accept":"application/json"}),
                         timeout=22) as response:
                data=json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as err:
            if err.code==429 and attempt<RETRIES_429:
                # Limite de fréquence du bookmaker : on attend puis on réessaie.
                try:
                    delay=min(float(err.headers.get("Retry-After")),30.0)
                except (AttributeError,TypeError,ValueError):
                    delay=2.0*(attempt+1)
                time.sleep(max(delay,1.0))
                continue
            raise RuntimeError(f"HTTP {err.code} from PulseScore {book}/{sport}") from None
        except (URLError,TimeoutError,ValueError) as err:
            raise RuntimeError(f"{type(err).__name__} from PulseScore {book}/{sport}") from None
    if not isinstance(data,dict):
        raise RuntimeError(f"Malformed PulseScore payload from {book}/{sport}")
    return data


def _request(book:str,sport:str,key:str,page:int) -> tuple[list[dict],bool]:
    data=_get_json(book,sport,"events",key,{"page":page,"limit":30})
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
    if m.get("isActive") is False or m.get("suspended") is True:return None
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
        back=selection.get("back")
        if isinstance(back,list) and back:
            try:
                liquidity=float(back[0].get("liquidity"))
            except (AttributeError,TypeError,ValueError):
                liquidity=None
            if liquidity is None or liquidity<MIN_EXCHANGE_LIQUIDITY:continue
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
            "raw_market_name":str(m.get("rawName") or ""),
            "period":str(m.get("period") or ""),
            "outcomes":outcomes}


def translate_event(raw:dict,book_key:str,observed:datetime)->dict|None:
    """Return The Odds API-compatible event with one observed FR book."""
    if raw.get("live") is True or raw.get("isLive") is True or raw.get("suspended") is True:
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
         fetch=None, balanced:bool=False, sleep=time.sleep, get=None) -> tuple[dict,dict]:
    """Collecte les cotes des matchs Revue à venir, bornée en appels.

    Mode « ligue » (appels réels, ou `get` fourni) : catalogue des ligues de
    chaque bookmaker, puis matchs des seules ligues suivies. Si le catalogue
    échoue ou ne contient pas la ligue, retour à la pagination globale
    (`fetch`, mode historique, aussi utilisé seul quand seul `fetch` est fourni).
    """
    if not 1<=max_calls<=MAX_CALLS:raise ValueError("Invalid max_calls")
    if not 1<=days_horizon<=72:raise ValueError("Invalid horizon")
    pace=fetch is None and get is None
    league_mode=get is not None or fetch is None
    fetch=fetch or _request
    get=get or _get_json
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
    # Prioritize the sport whose matching fixture starts earliest.
    earliest={sport:min(timestamp(g["start_utc"]) for league,games in interested.items()
            if SPORT_GROUPS[league]==sport for g in games) for sport in sports}
    sport_order=sorted(sports,key=lambda sport:earliest[sport])
    first="listing" if league_mode else "events"
    # Task = (sport, book, kind, league name or None, page).
    tasks=(deque((sport,b,first,None,1) for b in SCAN_BOOKS for sport in sport_order
                 if b in books_for(sport))
           if balanced else
           deque((sport,b,first,None,1) for sport in sport_order for b in books_for(sport)))
    results=defaultdict(dict)
    added=set()
    found=defaultdict(set)
    stats={"status":"active","requests":0,"errors":{},"matched_events":0,
           "sports":sport_order,"bookmakers":list(BOOKMAKERS),
           "reference_books":list(REFERENCE_BOOKS),"matched_by_book":{},
           "truncated":False,"max_calls":max_calls,
           "allocation_mode":"sport_balanced" if balanced else "sport_priority",
           "collection_mode":"league" if league_mode else "paging",
           "league_names":{},"fallback_paging":[],
           "calls_by_sport":{},
           "horizon_hours":days_horizon,
           "observation_provenance":"provider updatedAt when present; else time fetched",
           }

    def consume(records,book_key,sport):
        for record in records:
            translated=translate_event(record,book_key,now)
            if not translated:continue
            for league,games in interested.items():
                if SPORT_GROUPS[league]!=sport:continue
                matched=match_fixture(translated,games,league)
                if matched is None:continue
                # Match against Revue's stable event rather than aggregating
                # vendor event ids across different bookmakers.
                key_id=str(matched["event_id"])
                if (league,key_id,book_key) in added:continue  # même match vu deux fois
                added.add((league,key_id,book_key))
                stored=results[league].setdefault(key_id,{
                    "id":f"review:{league}:{key_id}",
                    "home_team":matched["home"],"away_team":matched["away"],
                    "commence_time":matched["start_utc"],
                    "bookmakers":[],
                })
                stored["bookmakers"].extend(translated["bookmakers"])
                stats["matched_events"]+=1
                stats["matched_by_book"][book_key]=stats["matched_by_book"].get(book_key,0)+1

    def within_horizon(records):
        last_start=timestamp(records[-1].get("startTime")) if records else None
        return last_start is None or last_start<=horizon

    last_call={}
    while tasks and stats["requests"]<max_calls:
        sport,book_key,kind,name,page=tasks.popleft()
        prefix=SCAN_BOOKS[book_key]
        stats["calls_by_sport"][sport]=stats["calls_by_sport"].get(sport,0)+1
        if pace:
            wait=last_call.get(prefix,0.0)+MIN_INTERVAL_PER_BOOK-time.monotonic()
            if wait>0:sleep(wait)
            last_call[prefix]=time.monotonic()
        stats["requests"]+=1
        label=f"{book_key}:{sport}:{kind}{':'+name if name else ''}:p{page}"
        try:
            if kind=="events":
                records,has_next=fetch(prefix,sport,key,page)
            else:
                suffix=("leagues" if kind=="listing" else
                        f"leagues/{quote(name,safe='')}/events")
                data=get(prefix,sport,suffix,key,{"page":page,"limit":100 if kind=="listing" else 50})
                has_next=data.get("hasNextPage") is True
                records=data.get("leagues" if kind=="listing" else "events")
                if not isinstance(records,list):
                    raise RuntimeError("Malformed PulseScore list")
        except Exception as err:
            # Do not include exception URL or secret in reports
            stats["errors"][label]=f"{type(err).__name__}: no valid feed"
            if kind=="listing":
                stats["fallback_paging"].append(f"{book_key}:{sport}")
                tasks.append((sport,book_key,"events",None,1))
            continue
        if kind=="listing":
            needed=[lg for lg in interested if SPORT_GROUPS[lg]==sport]
            for item in records:
                if not isinstance(item,dict):continue
                for lg in needed:
                    if league_matches(item.get("name"),item.get("country"),lg):
                        found[(sport,book_key)].add(str(item["name"]))
                        stats["league_names"].setdefault(book_key,{}).setdefault(lg,[]).append(str(item["name"]))
            if has_next and page<MAX_LEAGUE_LISTING_PAGES:
                tasks.appendleft((sport,book_key,"listing",None,page+1))
            elif found[(sport,book_key)]:
                for league_name in sorted(found[(sport,book_key)]):
                    tasks.append((sport,book_key,"league",league_name,1))
            else:
                stats["fallback_paging"].append(f"{book_key}:{sport}")
                tasks.append((sport,book_key,"events",None,1))
            continue
        consume(records,book_key,sport)
        if has_next and page<MAX_PAGES and stats["requests"]<max_calls and within_horizon(records):
            tasks.append((sport,book_key,kind,name,page+1))
    stats["truncated"]=len(tasks)>0
    output={league:list(events.values()) for league,events in results.items()}
    stats["matched_leagues"]={league:len(rows) for league,rows in output.items()}
    return output,stats
