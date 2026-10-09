#!/usr/bin/env python3
"""Faithful behavioural reconstruction of Clairvoyance's Python predictor layer.

Reference: Purple-Wraith/clairvoyance-backend at app/services/predictor.py.
Independent implementation without copying that repository's source. All
constants/transformations here follow the observed public predictor rules.
The original source has no express redistribution license: reference source
is NEVER vendored, imported in production or copied into our repository.

MLB Python backend: Elo only. Starting pitcher strings do not affect win odds.
NHL Python backend: Elo + both MoneyPuck xGoals% + both goalie save proportions.
"Goalie starter" in the original backend is simply the most-played goalie,
not a confirmed starter. Market edge is p_model - implied(moneyline), in
PERCENTAGE POINTS (not EV based on decimal odds). Home pick takes priority.
No real-betting action. Inputs must supply observed, time-valid data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REFERENCE="Purple-Wraith/clairvoyance-backend:app/services/predictor.py"
ELO_DEFAULT=1500.0
EDGE_THRESHOLD=3.0


@dataclass(frozen=True)
class Game:
    espn_id: str
    home_team: str
    away_team: str
    game_date: Any = None
    game_time_utc: Any = None
    home_moneyline: int | None = None
    away_moneyline: int | None = None
    over_under: float | None = None
    home_pitcher: str | None = None
    away_pitcher: str | None = None


def american_probability(line: int) -> float:
    return 100 / (line + 100) if line >= 0 else -line / (-line + 100)


def american_quote(probability: float) -> int:
    p=max(.01,min(.99,probability))
    if p>=.5:
        return -round(p/(1-p)*100)
    return round((1-p)/p*100)


def advantage_points(probability: float, line: int) -> float:
    return 100*(probability-american_probability(line))


def elo_home_probability(home: float,away: float,home_bonus:float=35.)->float:
    return 1/(1+10**((away-(home+home_bonus))/400))


def _result_shell(game:Game,sport:str,p:float,home_elo:float,
                  away_elo:float)->dict:
    """Match the original public observable result schema and rounding."""
    result={
        "espn_id":game.espn_id,
        "sport":sport,
        "home_team":game.home_team,
        "away_team":game.away_team,
        "game_date":game.game_date,
        "game_time_utc":game.game_time_utc,
        "home_elo":round(home_elo),
        "away_elo":round(away_elo),
        "model_home_win_prob":round(p,3),
        "model_away_win_prob":round(1-p,3),
        "model_home_ml":american_quote(p),
        "model_away_ml":american_quote(1-p),
        "market_home_ml":game.home_moneyline,
        "market_away_ml":game.away_moneyline,
        "over_under":game.over_under,
        "recommendation":None,
        "edge_pct":None,
    }
    if game.home_moneyline and game.away_moneyline:
        edge_home=advantage_points(p,game.home_moneyline)
        edge_away=advantage_points(1-p,game.away_moneyline)
        if edge_home>=EDGE_THRESHOLD:
            result["recommendation"]=f"{game.home_team} ML"
            result["edge_pct"]=round(edge_home,1)
        elif edge_away>=EDGE_THRESHOLD:
            result["recommendation"]=f"{game.away_team} ML"
            result["edge_pct"]=round(edge_away,1)
    return result


def mlb(game:Game,home_elo:float=ELO_DEFAULT,away_elo:float=ELO_DEFAULT)->dict:
    p=elo_home_probability(home_elo,away_elo)
    result=_result_shell(game,"mlb",p,home_elo,away_elo)
    # Original model carries pitcher metadata but DOES NOT apply it to p.
    return {
        "espn_id":result["espn_id"],
        "sport":result["sport"],
        "home_team":result["home_team"],
        "away_team":result["away_team"],
        "game_date":result["game_date"],
        "game_time_utc":result["game_time_utc"],
        "home_pitcher":game.home_pitcher,
        "away_pitcher":game.away_pitcher,
        **{k:v for k,v in result.items()
           if k not in {"espn_id","sport","home_team","away_team",
                        "game_date","game_time_utc"}},
    }


def nhl(game:Game,home_elo:float=ELO_DEFAULT,away_elo:float=ELO_DEFAULT,
        home_xgoals_pct:float|None=None,away_xgoals_pct:float|None=None,
        home_goalie_sv_pct:float|None=None,away_goalie_sv_pct:float|None=None)->dict:
    p=elo_home_probability(home_elo,away_elo,25.)
    if home_xgoals_pct and away_xgoals_pct:
        p+=((home_xgoals_pct-away_xgoals_pct)/100)*.3
    if home_goalie_sv_pct and away_goalie_sv_pct:
        p+=(home_goalie_sv_pct-away_goalie_sv_pct)*10*.2
    p=max(.05,min(.95,p))
    result=_result_shell(game,"nhl",p,home_elo,away_elo)
    before="model_home_win_prob"
    output={}
    for k,v in result.items():
        if k==before:
            output["home_xgoals_pct"]=home_xgoals_pct
            output["away_xgoals_pct"]=away_xgoals_pct
            output["home_goalie_sv_pct"]=home_goalie_sv_pct
            output["away_goalie_sv_pct"]=away_goalie_sv_pct
        output[k]=v
    return output
