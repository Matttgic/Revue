#!/usr/bin/env python3
"""Clairvoyance NHL predictor on independently acquired, timestamped inputs.

FORMULA: modeles.reproduction.clairvoyance_predictor.nhl (source-parity tested).
INPUTS: official MoneyPuck current-season derived team/goalie summaries and
independently recomputed NHL-API historical Elo (NOT Clairvoyance's own database).
The source parity of the formula DOES NOT prove full-pipeline prediction parity.
All outputs are uncalibrated SHADOW forecasts, without odds or betting advice.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

from modeles.reproduction.clairvoyance_predictor import Game as PredictorGame, nhl
from outils.nhl_moneypuck_prudent import prudent_forecast
from modeles.simulations.nhl_independant import (
    Game, PARIS, _update_elo, download_season, is_final_before,
    prev_season, season_code,
)


def as_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp absent")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Naive timestamp")
    return parsed.astimezone(timezone.utc)


def _snapshot_ready(report: dict, season_label: str, state: str) -> bool:
    key = "status" if state == "teams" else "statuses"
    return (report.get("source") == "MoneyPuck.com" and
            report.get("current_season") == season_label and
            report.get(key, {}).get(season_label, {}).get("status") == "available")


def _data_asof(report: dict, season_label: str, state: str) -> datetime:
    key = "status" if state == "teams" else "statuses"
    return as_utc(report[key][season_label]["source_updated_utc"])


def _elo_from_scores(prior: list[Game], current: list[Game], as_of: datetime) -> dict[str, float]:
    """Independently estimated Elo proxy, not original Clairvoyance DB ratings."""
    historical = {g.id:g for g in prior if is_final_before(g,as_of)}
    current_scores = {g.id:g for g in current if is_final_before(g,as_of)}
    # Do not double update one fixture appearing in both downloaded season files.
    for key in current_scores:
        historical.pop(key,None)
    ratings: dict[str,float] = defaultdict(lambda:1500.0)
    for g in sorted(historical.values(), key=lambda x:(x.start_utc,x.id)):
        _update_elo(ratings,g)
    # Same previous-season shrink used by the independent NHL model.
    for team in list(ratings):
        ratings[team] = 1500 + 0.70 * (ratings[team] - 1500)
    for g in sorted(current_scores.values(), key=lambda x:(x.start_utc,x.id)):
        _update_elo(ratings,g)
    return ratings


def _most_used_goalie(goalies:list[dict], team:str) -> dict | None:
    """Match backend proxy: most games played; NOT a starter confirmation."""
    group=[g for g in goalies if g.get("team")==team and
           isinstance(g.get("games_played"),int) and g["games_played"]>0 and
           isinstance(g.get("save_pct"),(int,float)) and 0<g["save_pct"]<=1]
    return max(group,key=lambda g:(g["games_played"],g.get("ice_hours") or 0,g["name"])) if group else None


def predict_shadow(prior:list[Game],current:list[Game],teams:dict,goalies:dict,
                   as_of:datetime,for_date:date,days:int=2) -> dict:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    as_of=as_of.astimezone(timezone.utc)
    if not 1<=days<=7:
        raise ValueError("days must be between 1 and 7")
    key=f"{int(season_code(for_date)[:4])}-{int(season_code(for_date)[:4])+1}"
    if not _snapshot_ready(teams,key,"teams") or not _snapshot_ready(goalies,key,"goalies"):
        raise ValueError("Official MoneyPuck current-season feeds unavailable: fail closed")
    source_times=(_data_asof(teams,key,"teams"),_data_asof(goalies,key,"goalies"),
                  as_utc(teams["generated_at_utc"]),as_utc(goalies["generated_at_utc"]))
    if any(dt>as_of for dt in source_times):
        raise ValueError("MoneyPuck report timestamp is in the future")
    team_stats={r["team"]:r for r in teams["seasons"][key]
                if r.get("situation")=="5on5" and r.get("xg_share") is not None}
    goalies_current=goalies["seasons"][key]
    preceding=f"{int(key[:4])-1}-{int(key[:4])}"
    prior_meta=teams.get("status",{}).get(preceding,{})
    prior_rows=[]
    if prior_meta.get("status")=="available" and preceding in teams.get("seasons",{}):
        prior_updated=prior_meta.get("source_updated_utc")
        if prior_updated is None or as_utc(prior_updated)<=as_of:
            prior_rows=teams["seasons"][preceding]
    prior_stats={r["team"]:r for r in prior_rows if r.get("situation")=="5on5"}
    elo=_elo_from_scores(prior,current,as_of)
    rows=[]
    seen=set()
    for event in sorted(current,key=lambda g:(g.start_utc,g.id)):
        if event.id in seen:
            continue
        seen.add(event.id)
        if event.final or event.start_utc<=as_of or (
            event.start_utc<=max(source_times)
        ):
            continue
        local_date=event.start_utc.astimezone(PARIS).date()
        if not (for_date<=local_date<for_date+timedelta(days=days)):
            continue
        home_stats,away_stats=team_stats.get(event.home),team_stats.get(event.away)
        # Both teams must have observed, same-season official xG.
        if home_stats is None or away_stats is None:
            continue
        home_goalie=_most_used_goalie(goalies_current,event.home)
        away_goalie=_most_used_goalie(goalies_current,event.away)
        hxg=float(home_stats["xg_share"])*100
        axg=float(away_stats["xg_share"])*100
        hg=float(home_goalie["save_pct"]) if home_goalie else None
        ag=float(away_goalie["save_pct"]) if away_goalie else None
        model=nhl(
            PredictorGame(espn_id=event.id,home_team=event.home,
                          away_team=event.away,game_time_utc=event.start_utc.isoformat()),
            home_elo=elo[event.home],
            away_elo=elo[event.away],
            home_xgoals_pct=hxg,away_xgoals_pct=axg,
            home_goalie_sv_pct=hg,away_goalie_sv_pct=ag,
        )
        # Independent research variant; original source formula remains untouched.
        prudent=prudent_forecast(event.id,event.home,event.away,
                elo[event.home],elo[event.away],home_stats,away_stats,
                prior_stats.get(event.home),prior_stats.get(event.away),
                home_goalie,away_goalie)
        # MoneyPuck current season may have very few games: record sample sizes.
        rows.append({
            "event_id":event.id,"home":event.home,"away":event.away,
            "start_utc":event.start_utc.isoformat(),
            "start_paris":event.start_utc.astimezone(PARIS).isoformat(),
            "home_win":model["model_home_win_prob"],
            "away_win":model["model_away_win_prob"],
            "model_id":"clairvoyance_nhl_backend_formula_with_revue_elo_proxy",
            "calibrated":False,
            "source_reproduction_complete":False,
            "home_elo_proxy":round(elo[event.home],2),
            "away_elo_proxy":round(elo[event.away],2),
            "xg_5v5_share_pct":{"home":hxg,"away":axg},
            "xg_games_observed":{"home":home_stats.get("games_played"),
                                 "away":away_stats.get("games_played")},
            "historical_goalie_proxy":{
                "home":({"name":home_goalie["name"],"games":home_goalie["games_played"],
                          "save_pct":hg} if home_goalie else None),
                "away":({"name":away_goalie["name"],"games":away_goalie["games_played"],
                          "save_pct":ag} if away_goalie else None),
                "selection_rule":"Most games played, not projected/confirmed starters",
            },
            "research_low_sample_shrink":prudent,
            "market_odds":None,"betting_recommendation":None,
            "shadow_only":True,
        })
    return {
        "generated_at_utc":as_of.isoformat(),
        "date_paris":for_date.isoformat(),"days":days,
        "season":season_code(for_date),
        "model":"Clairvoyance backend NHL formula / Revue observed data (SHADOW)",
        "parity_scope":"Formula only; NHL Elo history and MoneyPuck inputs differ from original database",
        "research_model":"revue_nhl_low_sample_shrink_v1 (separate experimental candidate)",
        "status":"experimental_not_calibrated",
        "confirmed_starters":False,
        "bookmaker_odds_available":False,
        "sources":{
            "fixtures_elo":"NHL Web API / Revue independent Elo ratings",
            "xg_goalies":"MoneyPuck.com official season summary",
            "money_puck_data_page":teams["source_page"],
            "source_updated_utc":{
                "teams":source_times[0].isoformat(),"goalies":source_times[1].isoformat()},
            "source_snapshot_utc":{
                "teams":source_times[2].isoformat(),"goalies":source_times[3].isoformat()},
            "source_usage":"personal non-commercial with attribution",
        },
        "games":rows,
        "warning":"Real observed stats, but team/goalie source samples can be tiny. Research shrink model is NOT original Clairvoyance and neither model is calibrated. No confirmed starter, calibrated probabilities, or live betting edges."
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teams",default="docs/moneypuck-nhl-latest.json")
    parser.add_argument("--goalies",default="docs/moneypuck-goalies-latest.json")
    parser.add_argument("--output",default="docs/nhl-clairvoyance-shadow-latest.json")
    parser.add_argument("--ledger",default="docs/nhl-shadow-ledger.json")
    parser.add_argument("--performance",default="docs/nhl-shadow-performance.json")
    parser.add_argument("--days",type=int,default=3)
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    target=now.astimezone(PARIS).date()
    season=season_code(target)
    t=json.loads(Path(args.teams).read_text(encoding="utf-8"))
    g=json.loads(Path(args.goalies).read_text(encoding="utf-8"))
    previous=download_season(prev_season(season))
    current=download_season(season)
    report=predict_shadow(previous,current,t,g,now,target,args.days)
    outfile=Path(args.output)
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                       encoding="utf-8")
    from outils.nhl_shadow_tracker import summarize,update_ledger
    ledger_path=Path(args.ledger)
    existing=json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else None
    ledger=update_ledger(existing,report,current,now)
    ledger_path.parent.mkdir(parents=True,exist_ok=True)
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                           encoding="utf-8")
    perf=summarize(ledger,now)
    perf_path=Path(args.performance)
    perf_path.parent.mkdir(parents=True,exist_ok=True)
    perf_path.write_text(json.dumps(perf,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                         encoding="utf-8")
    print("Clairvoyance NHL SHADOW with official MoneyPuck:",len(report["games"]),"future games")
    print("Prospective locks:",perf["locked_events"],"resolved:",perf["settled"],
          "mean Brier:",perf["mean_brier"])


if __name__=="__main__":
    main()
