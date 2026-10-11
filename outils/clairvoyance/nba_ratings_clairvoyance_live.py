#!/usr/bin/env python3
"""Publish REAL ESPN inputs through the verified Clairvoyance NBA rating formula.

No custom model or substituted parameters. Calculations solely delegate to
modeles/reproduction/clairvoyance_nba_source.py (source parity verified).
Does not require restricted Opta/BBRef scraping or user bookmaker credentials.
"""
from __future__ import annotations
import argparse,json,math
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from modeles.reproduction.clairvoyance_nba_source import (
    build_team_ratings,prior_nba_end_year
)

API="https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?season={year}"

def good_number(v):
    if isinstance(v,bool):return None
    try:n=float(v)
    except (ValueError,TypeError):return None
    if not math.isfinite(n):return None
    return n

def current_espn_rows(payload:dict)->dict:
    """ESPN 2026-27 standings keyed by ESPN abbreviation, no invented values."""
    out={}
    def walk(container):
        for ent in ((container.get("standings") or {}).get("entries") or []):
            team=ent.get("team") or {}
            abbr=str(team.get("abbreviation") or "").strip().upper()
            if not abbr or len(abbr)>5:continue
            stats={s.get("name"):s.get("value") for s in ent.get("stats") or []
                   if isinstance(s,dict)}
            wins=good_number(stats.get("wins"))
            losses=good_number(stats.get("losses"))
            scored=good_number(stats.get("avgPointsFor"))
            allowed=good_number(stats.get("avgPointsAgainst"))
            if wins is None or losses is None or wins<0 or losses<0:
                continue
            diff=round(scored-allowed,4) if (
                wins+losses>0 and scored is not None and allowed is not None) else None
            out[abbr]={"w":int(wins),"l":int(losses),"diff":diff}
        for child in container.get("children") or []:
            if isinstance(child,dict):walk(child)
    if isinstance(payload,dict):walk(payload)
    return out

def previous_espn_rows(report:dict,year:int)->dict:
    if report.get("season_end_year")!=year or report.get("status")!="real_previous_season_aggregate":
        raise ValueError("Previous season has not been verified")
    out={}
    for t in (report.get("teams") or {}).values():
        abbr=str(t.get("abbr") or "").upper().strip()
        margin=good_number(t.get("margin"))
        if not abbr or margin is None:continue
        w,l=good_number(t.get("wins")),good_number(t.get("losses"))
        if w is None or l is None or w+l<50:continue
        out[abbr]={"w":int(w),"l":int(l),"diff":margin}
    if len(out)<25:raise ValueError("Less than 25 verified prior NBA teams")
    return out

def build_report(prior:dict,current:dict,as_of:datetime,source_note:str)->dict:
    if as_of.tzinfo is None:raise ValueError("Timezone required")
    cur_year=prior_nba_end_year(as_of)
    old_year=cur_year-1
    older=previous_espn_rows(prior,old_year)
    # No BBRef source in this adapter: original function uses the ESPN
    # differential fallback, and these are the EXACT inputs it expects.
    source=build_team_ratings({},{},older,current,cur_year,old_year,None,
                             as_of.astimezone(timezone.utc).date().isoformat())
    teams=source["teamRatings"]["teams"]
    return {
        "generated_at_utc":as_of.astimezone(timezone.utc).isoformat(),
        "reference":"Clairvoyance build_nba_team_ratings",
        "algorithm_source":"scripts/clairvoyance_update.py",
        "mode":"verified_formula_with_real_espn_fallback_inputs",
        "current_season_end_year":cur_year,
        "previous_season_end_year":old_year,
        "number_of_teams":len(teams),
        "current_teams_with_standings":len(current),
        "source_current":source_note,
        "source_previous":"ESPN 2025-26 standings verified from prior cache",
        "teamRatings":source["teamRatings"],
        "eloSeed":source["eloSeed"],
        "warning":"Same source formula on real ESPN standings, but no Basketball-Reference SRS/advanced metrics, no real lineup parity and no guaranteed identical forecasts.",
    }

def fetch_espn(year:int)->dict:
    with urlopen(Request(API.format(year=year),
                         headers={"Accept":"application/json"}),timeout=22) as resp:
        return json.load(resp)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--previous",default="docs/nba-prior-standings.json")
    p.add_argument("--output",default="docs/clairvoyance-nba-ratings.json")
    p.add_argument("--current-snapshot",default=None)
    a=p.parse_args()
    now=datetime.now(timezone.utc)
    prior=json.loads(Path(a.previous).read_text(encoding="utf-8"))
    if a.current_snapshot:
        data=json.loads(Path(a.current_snapshot).read_text(encoding="utf-8"))
        note="Provided ESPN standings snapshot"
    else:
        try:
            data=fetch_espn(prior_nba_end_year(now))
            note="ESPN public current season standings"
        except (OSError,TimeoutError,ValueError) as err:
            data={}
            note="Current season unavailable: "+type(err).__name__
    current=current_espn_rows(data)
    report=build_report(prior,current,now,note)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Clairvoyance NBA source formula / real ESPN:",
          report["number_of_teams"],"teams,",len(current),"current rows")
if __name__=="__main__":
    main()
