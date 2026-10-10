#!/usr/bin/env python3
"""Experimental small-sample NHL forecast, compared prospectively with Clairvoyance.

Not part of the source-reproduction claim. Apply pre-declared shrinkage to
official MoneyPuck seasonal aggregates before calling the unchanged, parity-
verified Clairvoyance NHL formula. No betting odds or starter confirmations.
"""
from __future__ import annotations

import math
from modeles.reproduction.clairvoyance_predictor import Game as PredictorGame, nhl

XG_PRIOR_GAMES = 12.0
GOALIE_PRIOR_GAMES = 8.0
NEUTRAL_XG_SHARE = 0.50
NEUTRAL_GOALIE_SAVE = 0.905
MODEL_ID = "revue_nhl_low_sample_shrink_v1"


def _finite(value: object, low: float, high: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and (
        math.isfinite(value) and low <= value <= high
    )


def xg_shrunk(current: dict, previous: dict | None) -> tuple[float, str]:
    """Effective xG share, retaining last-season data only as a declared prior."""
    share, n = current.get("xg_share"), current.get("games_played")
    if not _finite(share, 0, 1) or not _finite(n, 1, 100):
        raise ValueError("Current-season xG and number of games required")
    prev_share = (previous or {}).get("xg_share")
    prev_games = (previous or {}).get("games_played")
    if _finite(prev_share, 0, 1) and _finite(prev_games, 20, 100):
        baseline, label = float(prev_share), "previous_regular_season_5v5"
    else:
        baseline, label = NEUTRAL_XG_SHARE, "neutral_50pct"
    return ((float(share) * float(n) + baseline * XG_PRIOR_GAMES) /
            (float(n) + XG_PRIOR_GAMES), label)


def goalie_shrunk(goalie: dict | None) -> float | None:
    """Historical MOST-USED goalie only; the starter remains unknown."""
    if goalie is None:
        return None
    p, n = goalie.get("save_pct"), goalie.get("games_played")
    if not _finite(p, 0, 1) or not _finite(n, 1, 100):
        return None
    return ((float(p) * float(n) + NEUTRAL_GOALIE_SAVE * GOALIE_PRIOR_GAMES) /
            (float(n) + GOALIE_PRIOR_GAMES))


def prudent_forecast(event_id: str, home: str, away: str, home_elo: float,
                     away_elo: float, home_stats: dict, away_stats: dict,
                     prev_home: dict | None, prev_away: dict | None,
                     home_goalie: dict | None, away_goalie: dict | None) -> dict:
    hx, hp = xg_shrunk(home_stats, prev_home)
    ax, ap = xg_shrunk(away_stats, prev_away)
    hg, ag = goalie_shrunk(home_goalie), goalie_shrunk(away_goalie)
    base = nhl(PredictorGame(espn_id=str(event_id),
                            home_team=home, away_team=away),
               home_elo, away_elo, hx * 100, ax * 100, hg, ag)
    return {
        "model_id": MODEL_ID,
        "home_win": base["model_home_win_prob"],
        "away_win": base["model_away_win_prob"],
        "calibrated": False,
        "shadow_only": True,
        "previous_season_xg_prior": {"home": hp, "away": ap},
        "xg_prior_games": XG_PRIOR_GAMES,
        "goalie_prior_games": GOALIE_PRIOR_GAMES,
        "goalie_neutral_prior": NEUTRAL_GOALIE_SAVE,
        "xg_shrunk_pct": {"home": round(hx * 100, 2),
                          "away": round(ax * 100, 2)},
        "goalie_sv_shrunk": {"home": round(hg, 4) if hg is not None else None,
                             "away": round(ag, 4) if ag is not None else None},
        "note": "Separate research model; former-season 5v5 xG or neutral prior; historical goalie proxy is not a confirmed starter.",
    }
