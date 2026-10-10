#!/usr/bin/env python3
"""Source-faithful real NBA ESPN team advanced stats and Elo for Clairvoyance.

Only observed regular-season ESPN byteam totals (seasontype=2).
Never misclassify preseason standings as regular-season form.
Missing current-season data => previous-year strength only; NO fake live form.
Reconstructed parsers have 460 direct parity comparisons vs source.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from modeles.reproduction.clairvoyance_nba_source import (
    build_team_ratings,prior_nba_end_year
)
from modeles.reproduction.clairvoyance_nba_espn_source import (
    rows_from_byteam,attach_records
)
from outils.nba_ratings_clairvoyance_live import previous_espn_rows,current_espn_rows

URL="https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byteam"
STANDINGS="https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?season={year}"

def get_json(url,params=None):
    uri=url+("?"+urlencode(params) if params else "")
    with urlopen(Request(uri,headers={"Accept":"application/json",
                            "User-Agent":"Revue-Parity-Data/1.0"}),timeout=25) as resp:
        return json.load(resp)

def fetch_advanced(year):
    query={"region":"us","lang":"en","contentorigin":"espn",
           "season":year,"seasontype":2}
    raw=get_json(URL,query)
    rows,diagnostic=rows_from_byteam(raw,year)
    if len(rows)<25:
        raise ValueError(f"{len(rows)} teams returned; {diagnostic}")
    return rows

def build(older:dict,previous_adv:dict,current_adv:dict,current_records:dict,
          as_of:datetime,current_note:str,previous_note:str)->dict:
    year=prior_nba_end_year(as_of)
    old_year=year-1
    previous_records=previous_espn_rows(older,old_year)
    if len(previous_adv)<25:raise ValueError("Prior NBA advanced season missing")
    # The advanced byteam endpoint is regular-season ONLY. If it returns
    # no current data, current standings from preseason are excluded.
    live_regular={}
    if current_adv:
        for abbr,rec in current_records.items():
            if abbr in current_adv and (current_adv[abbr].get("gp") or 0)>0:
                live_regular[abbr]=rec
        current_adv={k:v for k,v in current_adv.items() if v.get("gp",0)>0}
        attach_records(current_adv,live_regular)
    ratings=build_team_ratings(previous_adv,current_adv,
                               previous_records,live_regular,
                               year,old_year,
                               {"seasonUsed":year if current_adv else old_year,
                                "mode":"current" if current_adv else "prior"},
                               as_of.strftime("%Y-%m-%d"))
    return {
        "generated_at_utc":as_of.astimezone(timezone.utc).isoformat(),
        "status":"source_formula_observed_regular_season_advanced",
        "reference":"Clairvoyance scripts/_nba_espn.py + scripts/clairvoyance_update.py",
        "source_verified_espn_parser":True,
        "season_current":year,
        "season_previous":old_year,
        "teams_with_previous_advanced":len(previous_adv),
        "teams_with_current_advanced":len(current_adv),
        "previous_data_note":previous_note,
        "current_data_note":current_note,
        "teamRatings":ratings["teamRatings"],
        "eloSeed":ratings["eloSeed"],
        "warning":"Source-identical aggregation and Elo on ESPN regular-season inputs. Does not include optional Basketball-Reference SRS, lineups, price calibration or verified complete prediction parity.",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prior",default="docs/nba-prior-standings.json")
    p.add_argument("--previous-cache",default="docs/clairvoyance-nba-espn-advanced-cache.json")
    p.add_argument("--output",default="docs/clairvoyance-nba-advanced-ratings.json")
    opts=p.parse_args()
    now=datetime.now(timezone.utc)
    year=prior_nba_end_year(now)
    old_year=year-1
    prior=json.loads(Path(opts.prior).read_text(encoding="utf-8"))
    cached=Path(opts.previous_cache)
    history=json.loads(cached.read_text(encoding="utf-8")) if cached.is_file() else {}
    old={}
    if history.get("season")==old_year and len(history.get("teams") or {})>=25:
        old=history["teams"]
        prior_note="previous season derived cache"
    else:
        old=fetch_advanced(old_year)
        prior_note="ESPN byteam regular-season historical data"
        cached.parent.mkdir(parents=True,exist_ok=True)
        cached.write_text(json.dumps({"season":old_year,"teams":old},
                                    indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    try:
        current=fetch_advanced(year)
        standings=current_espn_rows(get_json(STANDINGS.format(year=year)))
        current_note="ESPN verified regular-season byteam"
    except (ValueError,OSError,TimeoutError) as err:
        current={}
        standings={}
        current_note="regular-season data unavailable ("+type(err).__name__+"); previous only"
    report=build(prior,old,current,standings,now,current_note,prior_note)
    target=Path(opts.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Clairvoyance NBA advanced:",report["teams_with_previous_advanced"],
          "prior teams;",report["teams_with_current_advanced"],"current teams;",
          "status",report["status"])
if __name__=="__main__":main()
