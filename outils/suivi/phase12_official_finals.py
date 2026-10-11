"""Phase 12: recover ONLY ESPN finals for prospectively locked model fixtures.

A missed scoreboard polling window must not permanently strand existing locks.
No historical forecasts, bookmaker quotes, paper bets or paid API calls.
ESPN final results are joined later using exact ID, team names and kickoff.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from modeles.simulations.multisports_independant import (
    LEAGUES, _fetch, query_url, parse_event,
)
from outils.publication.match_center_revue import compatible, instant, game_key

VERSION="revue_phase12_espn_pending_finals_v1"
LEDGER_VERSION="revue_phase10_forward_ledger_v1"
SOCCER={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"}
SUPPORTED=SOCCER|{"NBA","MLB"}
CATALOG={league.key:league for league in LEAGUES if league.key in SUPPORTED}
PARIS=ZoneInfo("Europe/Paris")
EAST=ZoneInfo("America/New_York")
AGE_LIMIT=timedelta(days=21)
GRACE=timedelta(minutes=95)
MAX_FETCH=12


def eligible_targets(ledger:dict,now:datetime) -> dict:
    if now.tzinfo is None:raise ValueError("UTC timezone required")
    if ledger.get("version")!=LEDGER_VERSION or not isinstance(ledger.get("records"),dict):
        raise ValueError("Cannot scan without valid frozen prospective ledger")
    targets={}
    for k,r in ledger["records"].items():
        if not isinstance(r,dict) or r.get("status")!="pending":
            continue
        if r.get("league") not in SUPPORTED:
            continue
        try:
            kickoff=instant(r["kickoff_utc"])
            frozen=instant(r["locked_at_utc"])
            if not now-AGE_LIMIT<=kickoff<=now-GRACE or frozen>kickoff-timedelta(minutes=20):
                continue
            if (r.get("real_bet") is not False or r.get("stake_units")!=0 or
                r.get("outcome_price") is not None or
                not isinstance(r.get("home"),str) or not isinstance(r.get("away"),str) or
                str(r.get("event_id"))=="" or r.get("home")==r.get("away")):
                continue
            key=game_key(r["league"],r["event_id"])
            ident=(r["home"],r["away"],kickoff.isoformat())
            if key in targets and targets[key]!=ident:
                raise ValueError("Frozen model fixtures disagree about ESPN identity: "+key)
            targets[key]=ident
        except (KeyError,TypeError,ValueError) as error:
            if str(error).startswith("Frozen model fixtures disagree"):
                raise
    return targets


def schedule_dates(targets:dict,now:datetime,max_fetch:int=MAX_FETCH) -> list:
    dates={}
    for key,ident in targets.items():
        league=key.split(":",1)[0]
        kickoff=instant(ident[2])
        # ESPN daily labels may follow US/Eastern or European dates.
        region=PARIS if league in SOCCER else EAST
        candidates={kickoff.astimezone(region).date(),kickoff.date()}
        for day in candidates:
            tup=(league,day)
            dates[tup]=max(kickoff,dates.get(tup,kickoff))
    # Prioritize recent due games; the rest remain locked and are retried.
    ordered=sorted(dates,key=lambda tup:(-dates[tup].timestamp(),tup[0],tup[1]))
    if max_fetch<1:raise ValueError("Need a positive public API request cap")
    return ordered[:max_fetch]


def parse_final(raw:dict,league:str,now:datetime) -> dict|None:
    parsed=parse_event(raw,league)
    if not parsed or not parsed.complete or not parsed.scored:
        return None
    h,a=parsed.home_score,parsed.away_score
    if (type(h) not in (int,float) or type(a) not in (int,float) or
        not 0<=h<=300 or not 0<=a<=300 or
        h!=int(h) or a!=int(a) or
        (league in {"NBA","MLB"} and h==a) or
        parsed.start+GRACE>now):
        return None
    return {"league":league,"event_id":parsed.id,"home":parsed.home,"away":parsed.away,
       "kickoff_utc":parsed.start.isoformat(),"state":"final",
       "home_score":int(h),"away_score":int(a),
       "observed_at_utc":now.isoformat(),
       "source":"ESPN scoreboard","prospective_bet_result":False}


def recover(ledger:dict,now:datetime,fetcher=_fetch,max_fetch:int=MAX_FETCH) -> dict:
    if now.tzinfo is None:raise ValueError("Timezone aware settlement required")
    now=now.astimezone(timezone.utc)
    targets=eligible_targets(ledger,now)
    queries=schedule_dates(targets,now,max_fetch)
    candidates={}
    conflicts=set()
    warnings=Counter()
    ok=0
    for league,day in queries:
        try:
            response=fetcher(query_url(CATALOG[league],day,day))
            if not isinstance(response,dict) or not isinstance(response.get("events"),list):
                raise ValueError("Malformed ESPN day response")
            ok+=1
            for raw in response["events"]:
                final=parse_final(raw,league,now)
                if final is None:continue
                key=game_key(final["league"],final["event_id"])
                expected=targets.get(key)
                if expected is None:continue
                if not compatible(
                     {"home":expected[0],"away":expected[1],"start_utc":expected[2]},
                     {"home":final["home"],"away":final["away"],"start_utc":final["kickoff_utc"]}):
                    warnings["team_or_kickoff_mismatch"]+=1
                    continue
                signature=(final["home"],final["away"],final["kickoff_utc"],
                           final["home_score"],final["away_score"])
                if key in candidates and candidates[key][0]!=signature:
                    conflicts.add(key);warnings["conflicting_ESPN_finals"]+=1
                else:
                    candidates[key]=(signature,final)
        except (OSError,TimeoutError,ValueError,RuntimeError,KeyError,TypeError):
            warnings["ESPN_day_unavailable"]+=1
            continue
    events=[entry[1] for key,entry in candidates.items() if key not in conflicts]
    events.sort(key=lambda e:(e["kickoff_utc"],e["league"],e["event_id"]))
    return {"version":VERSION,"generated_at_utc":now.isoformat(),
       "status":"observed_scoreboard_not_streaming",
       "scores_are_live_stream":False,"pricing_used":False,
       "requests":{"attempted":len(queries),"successful":ok,
                   "capped_to":max_fetch,"failures":len(queries)-ok},
       "pending_events_eligible":len(targets),"verified_finals":len(events),
       "unresolved_eligible":len(targets)-len(events),
       "conflicting_final_ids":sorted(conflicts),
       "diagnostics":dict(warnings),"events":events,
       "no_forecasts_created":True,"no_historical_predictions_backfilled":True,
       "no_real_bets":True,"paid_api_calls":0,
       "source_note":"Current ESPN final queried by calendar date only for previously frozen model IDs. Final time is observation time, not claimed historical publication time. Conflicts and missing games remain pending."}


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--ledger",default="docs/phase10-modeles-prospectif-ledger.json")
    cli.add_argument("--output",default="docs/phase12-official-finals-latest.json")
    args=cli.parse_args()
    ledger=json.loads(Path(args.ledger).read_text(encoding="utf8"))
    result=recover(ledger,datetime.now(timezone.utc))
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print("Phase12 ESPN finals:",result["verified_finals"],"of",
       result["pending_events_eligible"],"eligible pending fixtures",
       result["requests"]["successful"],"/",result["requests"]["attempted"],"scoreboard dates")
if __name__=="__main__":main()
