#!/usr/bin/env python3
"""Point-in-time cross-source guard for MoneyPuck NHL shadow predictions.

A season-aggregate snapshot cannot be used for historical walk-forward replay:
it is only valid from its actual publication time onward. Verify its reported
game sample against independent completed NHL fixtures at source timestamp.
Fail closed if a team/goalie claims observations not present in the official
schedule. Never use this to retroactively populate old forecast locks.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import math

from modeles.simulations.nhl_independant import Game, season_code
from outils.clairvoyance_nhl_moneypuck_shadow import as_utc

ALLOWED_SNAPSHOT_AGE = timedelta(days=7)
MAX_CURRENT_GAMES = 100


def _whole_nonnegative(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_CURRENT_GAMES


def verify_point_in_time(
    teams: dict, goalies: dict, current: list[Game],
    as_of: datetime, expected_season: str,
) -> dict:
    """Verify no season sample implies games after its declared source cutoff.

    Checks both team situations, goalie/team membership, non-future publishing,
    no duplicate NHL fixtures, and official completed-game upper bounds.
    Official NHL data can be newer than MoneyPuck; *undercounts* are valid.
    """
    if as_of.tzinfo is None:
        raise ValueError("Prediction timestamp must have a timezone")
    now = as_of.astimezone(timezone.utc)
    first = int(expected_season[:4])
    source_label = f"{first}-{first + 1}"
    if (season_code(now.date()) != expected_season or
        teams.get("current_season") != source_label or
        goalies.get("current_season") != source_label):
        raise ValueError("MoneyPuck and NHL season identity mismatch")
    info = teams.get("status", {}).get(source_label, {})
    goalie_info = goalies.get("statuses", {}).get(source_label, {})
    if info.get("status") != "available" or goalie_info.get("status") != "available":
        raise ValueError("Current-season MoneyPuck files unavailable")
    source_dates = []
    for doc, state in ((teams, info), (goalies, goalie_info)):
        if doc.get("source") != "MoneyPuck.com" or doc.get("is_live") is not False:
            raise ValueError("Missing attribution or wrongly advertised live stats")
        source_time = as_utc(state["source_updated_utc"])
        generated = as_utc(doc["generated_at_utc"])
        if source_time > generated or generated > now:
            raise ValueError("Future or inconsistent source/snapshot timestamps")
        if now - source_time > ALLOWED_SNAPSHOT_AGE:
            raise ValueError("MoneyPuck snapshot too old to validate current projections")
        source_dates.append(source_time)

    current_rows = teams.get("seasons", {}).get(source_label, [])
    goalie_rows = goalies.get("seasons", {}).get(source_label, [])
    if not current_rows or not goalie_rows:
        raise ValueError("Empty MoneyPuck current season")
    unique = set()
    for game in current:
        if game.id in unique:
            raise ValueError("Duplicate NHL game ID in schedule")
        unique.add(game.id)

    observations_by_date = {}
    for dt in set(source_dates):
        official: Counter[str] = Counter()
        for g in current:
            if not g.final or g.start_utc >= dt:
                continue
            if g.start_utc.tzinfo is None or g.start_utc > now:
                raise ValueError("Invalid NHL game timestamp")
            official[g.home] += 1
            official[g.away] += 1
        observations_by_date[dt] = official

    observed_teams: dict[str, dict] = {}
    checked_team_rows = 0
    for row in current_rows:
        if row.get("situation") != "5on5":
            continue
        code = row.get("team")
        games = row.get("games_played")
        if not isinstance(code, str) or not _whole_nonnegative(games):
            raise ValueError("Invalid team identity or observation count")
        if code in observed_teams:
            raise ValueError(f"Duplicate 5on5 MoneyPuck team: {code}")
        observed_teams[code] = row
        limit = observations_by_date[source_dates[0]][code]
        if games > limit:
            raise ValueError(
                f"Look-ahead/data mismatch: {code} MoneyPuck has {games} "
                f"games, NHL official history before source timestamp has {limit}"
            )
        xg = row.get("xg_share")
        if (not isinstance(xg, (float, int)) or isinstance(xg, bool) or
            not math.isfinite(xg) or not 0 <= xg <= 1):
            raise ValueError(f"Invalid xG share for {code}")
        checked_team_rows += 1

    if not observed_teams:
        raise ValueError("No 5on5 team observations")
    checked_goalies = 0
    for row in goalie_rows:
        code = row.get("team")
        games = row.get("games_played")
        if code not in observed_teams or not _whole_nonnegative(games):
            raise ValueError("Goalie has no corresponding valid team/count")
        if games > observations_by_date[source_dates[1]][code]:
            raise ValueError(f"Look-ahead/data mismatch: goalie at {code} ({games} games)")
        if row.get("starter_status") != "unknown":
            raise ValueError("MoneyPuck goalie is falsely reported as confirmed starter")
        checked_goalies += 1

    # This is evidence of temporal consistency, not proof that an external
    # publisher's historical CSV itself never contained contaminated figures.
    return {
        "status": "verified_temporal_bounds",
        "as_of_utc": now.isoformat(),
        "source_updated_utc": {
            "teams": source_dates[0].isoformat(),
            "goalies": source_dates[1].isoformat(),
        },
        "max_source_age_days": ALLOWED_SNAPSHOT_AGE.days,
        "team_5v5_rows_checked": checked_team_rows,
        "goalie_rows_checked": checked_goalies,
        "official_games_before_team_source": sum(observations_by_date[source_dates[0]].values()) // 2,
        "money_puck_team_games_observed": sum(r["games_played"] for r in observed_teams.values()) // 2,
        "note": "Source as-of consistency only; no historical replay or calibrated claim.",
    }
