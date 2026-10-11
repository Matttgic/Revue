#!/usr/bin/env python3
"""Observed sport scores from official NHL and ESPN scoreboard APIs.

Unlike prospective probability research, this is a read-only scoreboard.
'Live' means ESPN explicitly reports play in progress at observation time,
NOT a live subscription; snapshots can become stale. No outcome is fabricated
for an unscored game or a league with a failed/unavailable public API.
"""
from __future__ import annotations
from datetime import date,datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from modeles.simulations.multisports_independant import LEAGUES, _fetch, query_url, parse_event
from modeles.simulations.nhl_independant import _get_json as nhl_get_json, parse_game

PARIS=ZoneInfo("Europe/Paris")
EASTERN=ZoneInfo("America/New_York")
LEAGUE_MAP={x.key:x for x in LEAGUES}
MAX_WORKERS=5
WINDOW=timedelta(hours=40)


def _parse_score_event(raw:dict,league:str,at:datetime) -> dict | None:
    parsed=parse_event(raw,league)
    if not parsed:
        return None
    try:
        kickoff=parsed.start
        if not at-WINDOW <= kickoff <= at+timedelta(hours=8):
            return None
        comp=raw["competitions"][0]
        sides=comp["competitors"]
        home=next(x for x in sides if x.get("homeAway")=="home")
        away=next(x for x in sides if x.get("homeAway")=="away")
        state=((raw.get("status") or {}).get("type") or
               (comp.get("status") or {}).get("type") or {}).get("state")
        state="final" if parsed.complete else "in_progress" if state=="in" else "scheduled"
        def score(rawside):
            val=rawside.get("score")
            if val is None or isinstance(val,bool):
                return None
            n=float(val)
            return int(n) if n>=0 and n==int(n) else None
        hs,aws=score(home),score(away)
        if state=="scheduled":
            hs,aws=None,None
        if state=="final" and (hs is None or aws is None):
            return None
        return {
            "league":league,"event_id":parsed.id,
            "home":parsed.home,"away":parsed.away,
            "kickoff_utc":kickoff.isoformat(),
            "state":state,"home_score":hs,"away_score":aws,
            "observed_at_utc":at.isoformat(),
            "source":"ESPN scoreboard",
            "prospective_bet_result":False,
        }
    except (ValueError,TypeError,KeyError,StopIteration,IndexError):
        return None


def download_espn(league:str, day:date,at:datetime, fetcher=_fetch) -> list[dict]:
    if league not in LEAGUE_MAP:
        raise ValueError("Unsupported ESPN league")
    payload=fetcher(query_url(LEAGUE_MAP[league],day,day))
    if not isinstance(payload,dict) or not isinstance(payload.get("events"),list):
        raise ValueError("Malformed ESPN scoreboard")
    rows=[]
    for raw in payload["events"]:
        item=_parse_score_event(raw,league,at)
        if item:
            rows.append(item)
    return rows


def download_nhl(day:date,at:datetime,fetcher=nhl_get_json) -> list[dict]:
    payload=fetcher("https://api-web.nhle.com/v1/score/"+day.isoformat())
    if not isinstance(payload,dict) or payload.get("currentDate") != day.isoformat():
        raise ValueError("Official NHL scoreboard date mismatch")
    games=payload.get("games")
    if not isinstance(games,list):
        raise ValueError("Missing official NHL games")
    rows=[]
    for raw in games:
        g=parse_game(raw)
        if not g or not at-WINDOW<=g.start_utc<=at+timedelta(hours=8):
            continue
        state="final" if g.final else "in_progress" if raw.get("gameState") in ("LIVE","CRIT") else "scheduled"
        home=raw.get("homeTeam") or {}
        away=raw.get("awayTeam") or {}
        hs=home.get("score")
        aws=away.get("score")
        def valid_score(s):
            return s if type(s) is int and 0 <= s <= 99 else None
        hs=valid_score(hs) if state!="scheduled" else None
        aws=valid_score(aws) if state!="scheduled" else None
        if state=="final" and (hs is None or aws is None):
            continue
        rows.append({
            "league":"NHL","event_id":g.id,"home":g.home,"away":g.away,
            "kickoff_utc":g.start_utc.isoformat(),"state":state,
            "home_score":hs,"away_score":aws,
            "observed_at_utc":at.isoformat(),
            "source":"NHL official scoreboard",
            "prospective_bet_result":False,
        })
    return rows


def collect(now:datetime,espn_fetcher=_fetch,nhl_fetcher=nhl_get_json) -> dict:
    if now.tzinfo is None:
        raise ValueError("An aware observation time is mandatory")
    now=now.astimezone(timezone.utc)
    local=now.astimezone(PARIS).date()
    east=now.astimezone(EASTERN).date()
    tasks=[(league,day) for league in LEAGUE_MAP
           for day in (local-timedelta(days=1),local)]
    tasks += [("NHL",d) for d in (east-timedelta(days=1),east)]
    matches:dict[str,dict]={}
    status={"ok":0,"failed":0,"errors":[]}
    def fetch(task):
        league,day=task
        return (download_nhl(day,now,nhl_fetcher) if league=="NHL"
                else download_espn(league,day,now,espn_fetcher))
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures={pool.submit(fetch,task):task for task in tasks}
        for future in as_completed(futures):
            league,day=futures[future]
            try:
                rows=future.result()
                status["ok"]+=1
                for event in rows:
                    key=event["league"]+":"+event["event_id"]
                    old=matches.get(key)
                    if old and ((old["kickoff_utc"],old["home"],old["away"]) !=
                                (event["kickoff_utc"],event["home"],event["away"])):
                        raise ValueError("Conflicting scoreboard fixture")
                    # Favor final over in-progress, in-progress over scheduled.
                    importance={"scheduled":0,"in_progress":1,"final":2}
                    if old is None or importance[event["state"]]>importance[old["state"]]:
                        matches[key]=event
            except Exception as err:
                status["failed"]+=1
                status["errors"].append(f"{league} {day}: {type(err).__name__} ({str(err)[:64]})")
    rows=sorted(matches.values(),key=lambda x:(x["kickoff_utc"],x["league"],x["event_id"]),reverse=True)
    return {
        "generated_at_utc":now.isoformat(),"status":"observed_scoreboard_not_streaming",
        "scores_are_live_stream":False,"pricing_used":False,
        "requests":{**status,"total":len(tasks)},
        "final":sum(x["state"]=="final" for x in rows),
        "in_progress":sum(x["state"]=="in_progress" for x in rows),
        "events":rows,
        "note":"Public scoreboard snapshots; NOT continuous live tracking. Data availability per league varies. These scores are not used to retroactively backfill any prospective model predictions.",
    }


def main() -> None:
    cli=argparse.ArgumentParser()
    cli.add_argument("--output",default="docs/scoreboard-revue-latest.json")
    args=cli.parse_args()
    report=collect(datetime.now(timezone.utc))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Observed scoreboards:",report["final"],"final,",report["in_progress"],"in progress;",report["requests"]["ok"],"/",report["requests"]["total"],"requests ok")


if __name__=="__main__":main()
