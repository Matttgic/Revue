#!/usr/bin/env python3
"""Read-only official NHL Stats REST source snapshot for Clairvoyance field contracts.

No use of original Clairvoyance private SQL data or copy of their source code.
NHL Stats API publicly observed season regular-season summaries. Stores
selected factual stats with explicit source timestamp; no lineup confirmations.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse
import json
import math
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen

API="https://api.nhle.com/stats/rest/en"
REPORTS={
    "team_directory":"team",
    "team_summary":"team/summary",
    "team_powerplay":"team/powerplay",
    "team_penaltykill":"team/penaltykill",
    "goalie_summary":"goalie/summary",
    "goalie_strength":"goalie/savesByStrength",
    "skater_summary":"skater/summary",
    "skater_shots":"skater/shottype",
}


def fetch_report(kind:str,season:str) -> list[dict]:
    if kind not in REPORTS or not season.isdecimal() or len(season)!=8:
        raise ValueError("Unknown official report or NHL season")
    query={"limit":"-1"}
    if kind!="team_directory":
        query["cayenneExp"]=f"seasonId={season} and gameTypeId=2"
        query["isAggregate"]="false"
        query["isGame"]="false"
    url=f"{API}/{REPORTS[kind]}?{urlencode(query)}"
    req=Request(url,headers={"User-Agent":"Revue-NHL-research/1.0","Accept":"application/json"})
    with urlopen(req,timeout=22) as response:
        if response.status!=200:
            raise ValueError(f"NHL statistics HTTP {response.status}")
        obj=json.load(response)
    if not isinstance(obj,dict) or not isinstance(obj.get("data"),list):
        raise ValueError("NHL API response lacks data array")
    records=obj["data"]
    if len(records)>2500 or any(not isinstance(x,dict) for x in records):
        raise ValueError("Unexpected NHL Stats report size/schema")
    return records


def positive_number(x,*,fraction=False):
    if type(x) not in (float,int) or not math.isfinite(x) or x<0:
        return None
    if fraction and x>1: return None
    return x


def source_id(x):
    if type(x) is int and x>0:return x
    if isinstance(x,str) and x.isdecimal() and int(x)>0:return int(x)
    return None


def _name(x):
    return x.strip() if isinstance(x,str) and x.strip() else None


def clean(loaded:dict[str,list[dict]], season:str,generated:datetime) -> dict:
    if generated.tzinfo is None:raise ValueError("Time must be aware")
    directory={}
    for r in loaded.get("team_directory",[]):
        tid=source_id(r.get("id"))
        tricode=_name(r.get("triCode") or r.get("rawTricode"))
        if tid and tricode and len(tricode)==3 and tricode.isascii():
            directory[tid]=tricode.upper()
    rows:dict[str,list[dict]]={}
    status={}
    for name in REPORTS:
        source=loaded.get(name)
        status[name]={"status":"available" if source is not None else "unavailable",
                      "rows":len(source) if source is not None else 0}
        rows[name]=source if isinstance(source,list) else []
    cleaned={"teams":[],"goalies":[],"skaters":[]}
    seen=set()
    for r in rows["team_summary"]:
        tid=source_id(r.get("teamId"))
        team=directory.get(tid)
        if not team or team in seen:
            continue
        gp=positive_number(r.get("gamesPlayed"))
        if gp is None:continue
        cleaned["teams"].append({
            "team_id":tid,"team_abbrev":team,
            "team_name":_name(r.get("teamFullName")),
            "season":season,"game_type_id":2,
            "games_played":gp,
            "wins":positive_number(r.get("wins")),
            "losses":positive_number(r.get("losses")),
            "ot_losses":positive_number(r.get("otLosses")),
            "goals_for":positive_number(r.get("goalsFor")),
            "goals_against":positive_number(r.get("goalsAgainst")),
            "goals_for_per_game":positive_number(r.get("goalsForPerGame")),
            "goals_against_per_game":positive_number(r.get("goalsAgainstPerGame")),
            "shots_for_per_game":positive_number(r.get("shotsForPerGame")),
            "shots_against_per_game":positive_number(r.get("shotsAgainstPerGame")),
            "pp_pct":None,"pk_pct":None,
            "offensive_zone_time_pct":None,"defensive_zone_time_pct":None,
            "neutral_zone_time_pct":None,
            "id":tid,  # Revue's own NHL team id, NOT Clairvoyance SQL pk
        })
        seen.add(team)
    # All team-specific supplemental reports use NHL team IDs.
    for kind,col,aliases in (
        ("team_powerplay","pp_pct",("powerPlayPct","ppPct","powerPlayPercentage")),
        ("team_penaltykill","pk_pct",("penaltyKillPct","pkPct","penaltyKillPercentage")),
    ):
        lookup={}
        for r in rows[kind]:
            tid=source_id(r.get("teamId"))
            if tid and tid not in lookup:
                lookup[tid]=r
        for row in cleaned["teams"]:
            info=lookup.get(row["team_id"],{})
            for alias in aliases:
                v=positive_number(info.get(alias))
                if v is not None:
                    row[col]=v
                    break
    for key,original,namekey in (
        ("goalies","goalie_summary","goalieFullName"),
        ("skaters","skater_summary","skaterFullName"),
    ):
        ids=set()
        for r in rows[original]:
            player=source_id(r.get("playerId"))
            name=_name(r.get(namekey))
            if player is None or player in ids or not name:continue
            team=_name(r.get("teamAbbrevs"))
            if team is None or len(team)!=3:
                # Multi-team player 'NYR,PHI' can't be attached to one team.
                continue
            ids.add(player)
            common={"id":player,"player_id":player,"player_name":name,
                    "team_abbrev":team.upper(),
                    "season":season,"game_type_id":2}
            if key=="goalies":
                common.update({
                    "games_played":positive_number(r.get("gamesPlayed")),
                    "overall_save_pct":positive_number(r.get("savePct"),fraction=True),
                    "goals_against_avg":positive_number(r.get("goalsAgainstAverage")),
                    "saves_even_strength":None,"save_pct_even_strength":None,
                    "saves_power_play":None,"save_pct_power_play":None,
                    "saves_short_handed":None,"save_pct_short_handed":None,
                })
            else:
                common.update({
                    "shots_wrist":None,"shots_snap":None,"shots_slap":None,
                    "shots_backhand":None,"shots_tip":None,
                    "shots_deflected":None,"shots_wrap_around":None,
                    "avg_speed":None,"top_speed":None,
                })
            cleaned[key].append(common)
    goalie_strength={r.get("playerId"):r for r in rows["goalie_strength"]}
    for row in cleaned["goalies"]:
        r=goalie_strength.get(row["player_id"],{})
        # NHL strength report column naming varies; set only sourced fields.
        for field,alias in (
            ("saves_even_strength","evSaves"),
            ("save_pct_even_strength","evSavePct"),
            ("saves_power_play","ppSaves"),
            ("save_pct_power_play","ppSavePct"),
            ("saves_short_handed","shSaves"),
            ("save_pct_short_handed","shSavePct"),
        ):
            row[field]=positive_number(r.get(alias),fraction="pct" in field)
    shot_types={r.get("playerId"):r for r in rows["skater_shots"]}
    for row in cleaned["skaters"]:
        r=shot_types.get(row["player_id"],{})
        for field,aliases in (
            ("shots_wrist",("shotsOnNetWrist","wristShots","shotsWrist")),
            ("shots_snap",("shotsOnNetSnap","snapShots","shotsSnap")),
            ("shots_slap",("shotsOnNetSlap","slapShots","shotsSlap")),
            ("shots_backhand",("shotsOnNetBackhand","backhandShots","shotsBackhand")),
            ("shots_tip",("shotsOnNetTipIn","tipShots","shotsTip")),
            ("shots_deflected",("shotsOnNetDeflected","deflectedShots","shotsDeflected")),
            ("shots_wrap_around",("shotsOnNetWrapAround","wrapAroundShots","shotsWrapAround")),
        ):
            for alias in aliases:
                v=positive_number(r.get(alias))
                if v is not None:
                    row[field]=v
                    break
    if len(cleaned["teams"])<25:
        raise ValueError("NHL Stats API did not return enough current-season team identities")
    return {
        "generated_at_utc":generated.astimezone(timezone.utc).isoformat(),
        "source":"api.nhle.com/stats/rest/en",
        "status":"verified_nhl_official_stats_snapshot",
        "season":season,"game_type_id":2,
        "reports":status,
        **{key:sorted(values,key=lambda r:(r["team_abbrev"],r.get("player_id",0)))
           for key,values in cleaned.items()},
        "disclaimer":"Official NHL season stats observed at timestamp. NHL IDs are not Clairvoyance SQL primary keys. Not a lineup or confirmed starting goalie feed.",
    }


def build(season:str)->dict:
    observed=datetime.now(timezone.utc)
    loaded={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(fetch_report,k,season):k for k in REPORTS}
        for f in as_completed(jobs):
            kind=jobs[f]
            try:
                loaded[kind]=f.result()
            except (OSError,HTTPError,URLError,TimeoutError,ValueError) as exc:
                print(f"{kind} unavailable: {type(exc).__name__}: {str(exc)[:80]}")
    # Public schema diagnostics (field names only; never log player records).
    if loaded.get("skater_shots"):
        print("NHL SHOTTYPE COLUMN NAMES:",sorted(loaded["skater_shots"][0].keys()))
    report=clean(loaded,season,observed)
    print("Official NHL observed:",len(report["teams"]),"teams,",
          len(report["goalies"]),"goalies,",len(report["skaters"]),"skaters;",
          {k:v["status"] for k,v in report["reports"].items()})
    return report


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--season",default="20262027")
    cli.add_argument("--output",default="docs/nhl-official-stats-latest.json")
    args=cli.parse_args()
    report=build(args.season)
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")


if __name__=="__main__":main()
