#!/usr/bin/env python3
"""Read-only ESPN NHL probable-starting-goalie observations joined to NHL game IDs.

ESPN's game identifiers are different from the official NHL IDs. Revue joins
only exact team pairs and <=10min starts, and labels CONFIRMED vs PROJECTED.
Missing/ambiguous ESPN reports remain missing; no injury/lineup is invented.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime,timedelta,timezone
import argparse
import json
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo

from modeles.reproduction.clairvoyance_nhl_goalies_source import espn_probables
from outils.suivi.clairvoyance_nhl_moneypuck_shadow import as_utc

ESPN="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
EASTERN=ZoneInfo("America/New_York")
CODES={
    "TB":"TBL","SJ":"SJS","NJ":"NJD","LA":"LAK","MON":"MTL",
    "MTL":"MTL","VEG":"VGK","VGK":"VGK",
    "UTH":"UTA","UTAH":"UTA","ARI":"UTA",  # legacy team abbreviations are not proof of identity
}
# A former franchise abbreviation is deliberately NOT accepted as current.
CODES.pop("ARI")
MAX_PAGES=4
LEAD=timedelta(minutes=20)
KICKOFF_TOLERANCE=timedelta(minutes=10)


def team_code(comp):
    raw=(comp.get("team") or {}).get("abbreviation")
    if not isinstance(raw,str):
        return None
    code=CODES.get(raw.strip().upper(),raw.strip().upper())
    return code if len(code) in (2,3) and code.isascii() and code.isalpha() else None


def espn_candidate(raw):
    try:
        when=as_utc(raw["date"])
        competitors=raw["competitions"][0]["competitors"]
        if not isinstance(competitors,list) or len(competitors)!=2:
            return None
        teams={}
        for comp in competitors:
            side=comp.get("homeAway")
            if side not in ("home","away") or side in teams:
                return None
            teams[side]=team_code(comp)
        if not teams.get("home") or not teams.get("away") or teams["home"]==teams["away"]:
            return None
        unknown=set()
        statuses=espn_probables(competitors,unknown)
        sides={}
        for side in ("home","away"):
            g=statuses.get(side)
            sides[side]={
                "name":g["name"],"status":g["status"],"source":"ESPN probableStartingGoalie",
            } if g and g.get("status") in ("confirmed","projected") else None
        return {
            "home":teams["home"],"away":teams["away"],"start_utc":when.isoformat(),
            "espn_event_id":str(raw.get("id") or ""),
            "goalies":sides,"unknown_statuses":sorted(unknown),
        }
    except (TypeError,KeyError,IndexError,ValueError):
        return None


def combine(forecast,scoreboards,now):
    if now.tzinfo is None:
        raise ValueError("Aware observation timestamp required")
    now=now.astimezone(timezone.utc)
    if (forecast.get("version")!="revue_nhl_frontend_observed_v1" or
        forecast.get("status")!="prospective_research_partial_input_frontend_not_parity" or
        forecast.get("real_bets_enabled") is not False or
        forecast.get("exact_original_frontend_predictions_verified") is not False or
        not isinstance(forecast.get("games"),list)):
        raise ValueError("Only established experimental NHL pregame fixtures supported")
    candidates=[]
    checked=Counter()
    for data in scoreboards:
        if not isinstance(data,dict) or not isinstance(data.get("events"),list):
            checked["invalid_espn_feed"]+=1
            continue
        checked["provider_responses"]+=1
        for raw in data["events"]:
            parsed=espn_candidate(raw)
            if parsed:
                candidates.append(parsed)
            else:
                checked["unmatched_or_invalid_espn_events"]+=1
    rows=[]
    seen=set()
    for g in forecast["games"]:
        ident=str(g.get("event_id") or "")
        if ident in seen:
            raise ValueError("Duplicate official NHL fixture")
        seen.add(ident)
        start=as_utc(g["start_utc"])
        if start<=now+LEAD:
            continue
        matched=[e for e in candidates if
            e["home"]==g["home"] and e["away"]==g["away"] and
            abs(as_utc(e["start_utc"])-start)<=KICKOFF_TOLERANCE]
        # IMPORTANT: never arbitrarily choose between two ESPN records.
        if len(matched)!=1:
            checked["no_unique_espn_match"]+=1
            continue
        e=matched[0]
        if not e["goalies"]["home"] and not e["goalies"]["away"]:
            checked["matched_without_reported_starters"]+=1
        checked["matched_fixtures"]+=1
        rows.append({
            "event_id":ident,"home":g["home"],"away":g["away"],
            "start_utc":start.isoformat(),"espn_event_id":e["espn_event_id"],
            "observed_at_utc":now.isoformat(),
            "home_goalie":e["goalies"]["home"],
            "away_goalie":e["goalies"]["away"],
            "starter_status_provenance":"ESPN probableStartingGoalie: confirmed vs projected",
            "matched_by":"both team codes and <=10min verified kickoff",
            "used_in_model_probabilities":False,
            "injuries_verified":False,
            "sportsbook_prices_verified":False,
        })
    return {
        "generated_at_utc":now.isoformat(),
        "status":"espn_probable_goalies_observed_not_part_of_model",
        "source":"ESPN NHL scoreboard, separate from official NHL IDs",
        "requests_count":len(scoreboards),
        "verified_current_starters":sum(bool(g.get(key) and g[key]["status"]=="confirmed")
            for g in rows for key in ("home_goalie","away_goalie")),
        "projected_starters":sum(bool(g.get(key) and g[key]["status"]=="projected")
            for g in rows for key in ("home_goalie","away_goalie")),
        "provider_rows_matched":len(rows),
        "diagnostics":dict(checked),
        "confirmed_is_not_a_guarantee_of_start":True,
        "used_in_prediction_model":False,
        "real_bets_enabled":False,
        "injuries_verified":False,
        "rows":rows,
        "note":"ESPN explicitly confirms or projects only when those statuses are present. Blank ≠ confirmed. No starter assumptions affect model outputs; do not reinterpret research probabilities as validated.",
    }


def download(day):
    url=ESPN+"?dates="+day.replace("-","")
    req=Request(url,headers={"Accept":"application/json","User-Agent":"RevueNHLResearch/1.0"})
    with urlopen(req,timeout=20) as r:
        body=r.read(4_000_001)
    if len(body)>4_000_000:
        raise ValueError("Oversized ESPN scoreboard")
    return json.loads(body.decode("utf8"))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args=parser.parse_args()
    root=Path(args.docs)
    report=json.loads((root/"nhl-frontend-observed-latest.json").read_text("utf8"))
    now=datetime.now(timezone.utc)
    dates=sorted({as_utc(g["start_utc"]).astimezone(EASTERN).date().isoformat()
      for g in report.get("games",[]) if as_utc(g["start_utc"])>now+LEAD})[:MAX_PAGES]
    boards=[]
    failures=[]
    for day in dates:
        try:
            boards.append(download(day))
        except Exception as e:
            # No exception text/URLs with potentially sensitive metadata.
            failures.append({"day":day,"reason":type(e).__name__})
    out=combine(report,boards,now)
    out["scoreboard_dates_attempted"]=dates
    out["errors"]=failures
    out["complete_coverage_verified"]=not failures and out["provider_rows_matched"]==len(
       [g for g in report.get("games",[]) if as_utc(g["start_utc"])>now+LEAD])
    (root/"nhl-espn-goalies-latest.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    print("ESPN goalie observations",out["verified_current_starters"],"confirmed,",
          out["projected_starters"],"projected across",
          out["provider_rows_matched"],"fixtures; request failures",len(failures))


if __name__=="__main__":
    main()
