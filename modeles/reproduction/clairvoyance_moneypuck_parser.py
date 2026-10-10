#!/usr/bin/env python3
"""Independent semantic replica of Clairvoyance's MoneyPuck CSV row normalizer.

Reference: Purple-Wraith/clairvoyance-backend/app/scrapers/moneypuck.py.
No data fetched here. MoneyPuck allows non-commercial use with attribution;
commercial rights require permission: https://www.moneypuck.com/data.htm.
This parser is a DATA input stage, not a new predictive model.
"""
from __future__ import annotations

import csv
import io
from typing import Optional


def numeric(value:object)->Optional[float]:
    if value is None or str(value).strip() in {"","-","N/A","nan"}:
        return None
    try:
        return float(str(value).replace("%","").strip())
    except (ValueError,TypeError):
        return None


def integer(value:object)->Optional[int]:
    out=numeric(value)
    return int(out) if out is not None else None


def rate_per_hour(value:object,minutes:Optional[float])->Optional[float]:
    if not minutes:
        return None
    n=numeric(value)
    return round(60*n/minutes,4) if n is not None else None


def normalize_team_record(row:dict)->dict|None:
    raw_team=row.get("team") or row.get("Team")
    if not raw_team or str(raw_team).strip() in ("","team"):
        return None
    minutes=numeric(row.get("iceTime"))
    gf=integer(row.get("goalsFor") or row.get("GF"))
    ga=integer(row.get("goalsAgainst") or row.get("GA"))
    sf=numeric(row.get("shotsOnGoalFor"))
    sa=numeric(row.get("shotsOnGoalAgainst"))
    shoot=gf/sf if gf is not None and sf else None
    saves=1-ga/sa if ga is not None and sa else None
    pdo=(shoot+saves) if shoot is not None and saves is not None else None
    return {
        "team":str(raw_team).strip().upper(),
        "situation":str(row.get("situation") or "all").strip(),
        "games_played":integer(row.get("games_played") or row.get("gamesPlayed")),
        "shots_for_60":rate_per_hour(row.get("shotsOnGoalFor"),minutes),
        "shots_against_60":rate_per_hour(row.get("shotsOnGoalAgainst"),minutes),
        "goals_for_60":rate_per_hour(row.get("goalsFor"),minutes),
        "goals_against_60":rate_per_hour(row.get("goalsAgainst"),minutes),
        "x_goals_for_60":rate_per_hour(row.get("xGoalsFor"),minutes),
        "x_goals_against_60":rate_per_hour(row.get("xGoalsAgainst"),minutes),
        "x_goals_pct":numeric(row.get("xGoalsPercentage") or row.get("xGF%")),
        "corsi_for_pct":numeric(row.get("corsiPercentage") or row.get("CF%")),
        "fenwick_for_pct":numeric(row.get("fenwickPercentage") or row.get("FF%")),
        "shooting_pct":round(shoot,4) if shoot is not None else None,
        "save_pct":round(saves,4) if saves is not None else None,
        "pdo":round(pdo,4) if pdo is not None else None,
        "goals_for":gf,
        "goals_against":ga,
        "x_goals_for":numeric(row.get("xGoalsFor")),
        "x_goals_against":numeric(row.get("xGoalsAgainst")),
        "high_danger_goals_for":integer(row.get("highDangerGoalsFor")),
        "high_danger_goals_against":integer(row.get("highDangerGoalsAgainst")),
        "medium_danger_goals_for":integer(row.get("mediumDangerGoalsFor")),
        "medium_danger_goals_against":integer(row.get("mediumDangerGoalsAgainst")),
        "low_danger_goals_for":integer(row.get("lowDangerGoalsFor")),
        "low_danger_goals_against":integer(row.get("lowDangerGoalsAgainst")),
    }


def read_team_csv(csv_text:str)->list[dict]:
    return [d for raw in csv.DictReader(io.StringIO(csv_text))
            if (d:=normalize_team_record(raw)) is not None]
