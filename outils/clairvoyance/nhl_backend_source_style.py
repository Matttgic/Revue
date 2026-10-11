"""Research-only NHL calculation with publicly observable backend-style inputs.

Clairvoyance backend predictor requests MoneyPuck situation=all and chooses
the NHL Stats goalie with the greatest number of games; its deployed SQL Elo,
season configuration, raw units, exact inputs and public frontend selections
cannot be recovered here. This tool DOES NOT emulate the published bestBets.

This is a separate prospective diagnostic. It never mutates frozen predictions,
settled picks, bankrolls, odds, or the original algorithm implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from modeles.reproduction.clairvoyance_predictor import Game, nhl

MIN_LEAD = timedelta(minutes=20)
VERSION = "revue_nhl_backend_source_style_v1"
# Defaults in the original public app/config.py, not an assertion about deployment:
PUBLIC_ORIGINAL_DEFAULTS = {"NHL_SEASON": "20252026", "NHL_GAME_TYPE": 3}
SCENARIO_SEASON_TYPE = 2


def utc(raw):
    if not isinstance(raw, str):
        raise ValueError("Missing timestamp")
    instant = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("Naive timestamp")
    return instant.astimezone(timezone.utc)


def scalar(value, lower, upper):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Non-finite input")
    if not lower <= value <= upper:
        raise ValueError("Input outside supported bounds")
    return float(value)


def seasons(teams, official):
    label = teams.get("current_season")
    if (not isinstance(label, str) or len(label) != 9 or label[4] != "-"
            or not label[:4].isdigit() or not label[5:].isdigit()
            or int(label[5:]) != int(label[:4]) + 1):
        raise ValueError("Invalid MoneyPuck season")
    if (teams.get("source") != "MoneyPuck.com"
            or teams.get("is_live") is not False
            or teams.get("status", {}).get(label, {}).get("status") != "available"
            or not isinstance(teams.get("seasons", {}).get(label), list)):
        raise ValueError("MoneyPuck season is not supported or available")
    if (official.get("source") != "api.nhle.com/stats/rest/en"
            or official.get("status") != "verified_nhl_official_stats_snapshot"
            or official.get("season") != label.replace("-", "")
            or official.get("game_type_id") != SCENARIO_SEASON_TYPE
            or official.get("reports", {}).get("goalie_summary", {}).get("status") != "available"
            or not isinstance(official.get("goalies"), list)):
        raise ValueError("Official goalie season, type or report mismatch")
    return label


def team_index(teams, label):
    five, all_situations = {}, {}
    for row in teams["seasons"][label]:
        if row.get("situation") not in ("5on5", "all"):
            continue
        team = row.get("team")
        if not isinstance(team, str) or not team.isalpha() or not 2 <= len(team) <= 4:
            raise ValueError("Invalid team code")
        target = five if row["situation"] == "5on5" else all_situations
        if team in target:
            raise ValueError("Duplicate MoneyPuck team-situation")
        if row.get("season") != label:
            raise ValueError("MoneyPuck mixed seasons")
        target[team] = scalar(row["xg_share"], 0, 1)
    return five, all_situations


def goalie_index(official, label):
    grouped = {}
    for row in official["goalies"]:
        if row.get("season") != label.replace("-", "") or row.get("game_type_id") != 2:
            raise ValueError("Goalie row not from same season/game type")
        team = row.get("team_abbrev")
        if not isinstance(team, str) or not team.isalpha() or not 2 <= len(team) <= 4:
            raise ValueError("Invalid goalie team")
        gp = row.get("games_played")
        if type(gp) is not int or gp < 0:
            raise ValueError("Invalid goalie games played")
        grouped.setdefault(team, []).append(row)
    result = {}
    for team, goalies in grouped.items():
        top = max(g["games_played"] for g in goalies)
        tied = [g for g in goalies if g["games_played"] == top]
        if top == 0 or len(tied) != 1:
            result[team] = {"status": "tie_or_zero", "games": top, "save_pct": None}
            continue
        g = tied[0]
        if g.get("overall_save_pct") is None:
            result[team] = {"status": "no_save_rate", "games": top, "save_pct": None}
            continue
        pct = scalar(g["overall_save_pct"], 0, 1)
        result[team] = {
            "status": "unique_most_games", "games": top, "save_pct": pct,
            "name": g.get("player_name"),
            "confirmed_tonight": False,
        }
    return result


def build(teams, official, shadow, now):
    if now.tzinfo is None:
        raise ValueError("Naive run clock")
    now = now.astimezone(timezone.utc)
    label = seasons(teams, official)
    if (shadow.get("status") != "experimental_not_calibrated"
            or shadow.get("season") != label.replace("-", "")
            or shadow.get("bookmaker_odds_available") is not False
            or shadow.get("confirmed_starters") is not False
            or not isinstance(shadow.get("games"), list)):
        raise ValueError("Shadow provenance or season mismatch")
    stamps = {
        "money_puck_observed": utc(teams["generated_at_utc"]),
        "money_puck_source_updated": utc(teams["status"][label]["source_updated_utc"]),
        "nhl_goalies_observed": utc(official["generated_at_utc"]),
        "shadow_generated": utc(shadow["generated_at_utc"]),
    }
    if any(stamp > now for stamp in stamps.values()):
        raise ValueError("Future source observation")
    if stamps["money_puck_source_updated"] > stamps["money_puck_observed"]:
        raise ValueError("MoneyPuck source updated after observation")
    five, all_situations = team_index(teams, label)
    goalie = goalie_index(official, label)
    records, skipped, seen = [], Counter(), set()
    for row in shadow["games"]:
        eid = str(row.get("event_id", ""))
        if not eid.isdecimal() or eid in seen:
            raise ValueError("Invalid or duplicate NHL fixture")
        seen.add(eid)
        start = utc(row["start_utc"])
        if start < now + MIN_LEAD:
            skipped["not_upcoming_20min"] += 1
            continue
        # Any of the feeds observed after the betting cutoff disqualifies comparison.
        if any(t > start - MIN_LEAD for t in stamps.values()):
            skipped["not_point_in_time"] += 1
            continue
        h, a = row.get("home"), row.get("away")
        if h == a or h not in five or a not in five or h not in all_situations or a not in all_situations:
            skipped["missing_team_xg"] += 1
            continue
        locked_xg = row.get("xg_5v5_share_pct") or {}
        if any(abs(100 * five[t] - scalar(locked_xg.get(side), 0, 100)) > .001
               for t, side in ((h, "home"), (a, "away"))):
            skipped["changed_five_on_five_snapshot"] += 1
            continue
        eh = scalar(row.get("home_elo_proxy"), 500, 2500)
        ea = scalar(row.get("away_elo_proxy"), 500, 2500)
        frozen = row.get("historical_goalie_proxy") or {}
        def frozen_pct(side):
            record = frozen.get(side)
            return None if not record or record.get("save_pct") is None else scalar(record["save_pct"], 0, 1)
        gh, ga = frozen_pct("home"), frozen_pct("away")
        # Refuse silently comparing to a mutated/mismatching stored baseline.
        game = Game(eid, h, a, game_time_utc=start.isoformat())
        original_frozen = nhl(game, eh, ea, 100 * five[h], 100 * five[a], gh, ga)
        if (original_frozen["model_home_win_prob"] != row.get("home_win")
                or original_frozen["model_away_win_prob"] != row.get("away_win")):
            skipped["frozen_probability_inconsistent"] += 1
            continue
        home_g = goalie.get(h, {"status": "missing", "save_pct": None})
        away_g = goalie.get(a, {"status": "missing", "save_pct": None})
        complete = home_g["status"] == away_g["status"] == "unique_most_games"
        if not complete:
            skipped["ambiguous_or_missing_official_goalie"] += 1
        # The Python backend divides its numeric stored xG share by 100.
        # The original database stores the scraped CSV number *without*
        # normalization in the published source code. SQL contents are unknown.
        raw_model = nhl(game, eh, ea, all_situations[h], all_situations[a],
                        home_g["save_pct"], away_g["save_pct"]) if complete else None
        pct_model = nhl(game, eh, ea, 100 * all_situations[h], 100 * all_situations[a],
                        home_g["save_pct"], away_g["save_pct"]) if complete else None
        record = {
            "event_id": eid, "home": h, "away": a,
            "kickoff_utc": start.isoformat(),
            "source_observed_by_frozen_model_time": all(
                stamp <= stamps["shadow_generated"] for name, stamp in stamps.items()
                if name != "shadow_generated"),
            "home_elo_revue_proxy": eh, "away_elo_revue_proxy": ea,
            "frozen_revue_home_probability": row["home_win"],
            "moneypuck_situation_5on5_share": {"home": five[h], "away": five[a]},
            "moneypuck_situation_all_raw_share": {
                "home": all_situations[h], "away": all_situations[a]
            },
            "official_goalies": {"home": home_g, "away": away_g},
            "raw_fraction_home_probability": raw_model["model_home_win_prob"] if raw_model else None,
            "percentage_point_home_probability": pct_model["model_home_win_prob"] if pct_model else None,
            "raw_fraction_vs_frozen_pp": round(100 * (raw_model["model_home_win_prob"] - row["home_win"]), 2) if raw_model else None,
            "percentage_point_vs_frozen_pp": round(100 * (pct_model["model_home_win_prob"] - row["home_win"]), 2) if pct_model else None,
            "frozen_prediction_overwritten": False,
            "original_sql_elo_and_raw_xg_verified": False,
            "actual_original_best_bet_reproduced": False,
        }
        records.append(record)
    shifts = [abs(r["raw_fraction_vs_frozen_pp"]) for r in records
              if r["raw_fraction_vs_frozen_pp"] is not None]
    return {
        "version": VERSION,
        "generated_at_utc": now.isoformat(),
        "status": "backend_style_input_scenario_not_original_model_parity",
        "source_code_predictor_formula_reused_in_revue": True,
        "source_public_config_defaults": PUBLIC_ORIGINAL_DEFAULTS,
        "scenario_actual_season": label.replace("-", ""),
        "scenario_game_type": SCENARIO_SEASON_TYPE,
        "public_default_config_matches_scenario": (
            PUBLIC_ORIGINAL_DEFAULTS["NHL_SEASON"] == label.replace("-", "")
            and PUBLIC_ORIGINAL_DEFAULTS["NHL_GAME_TYPE"] == SCENARIO_SEASON_TYPE
        ),
        "public_deployment_configuration_verified": False,
        "original_sql_ratings_available": False,
        "reference_uses_same_frontend_best_bets_model_verified": False,
        "has_verified_original_predictions": False,
        "real_bets_enabled": False,
        "odds_collected": False,
        "frozen_ledger_unchanged": True,
        "input_observed_utc": {k: v.isoformat() for k, v in stamps.items()},
        "shadow_games": len(shadow["games"]),
        "future_matched_games": len(records),
        "complete_goalie_comparisons": len(shifts),
        "mean_abs_raw_fraction_vs_frozen_pp": round(sum(shifts) / len(shifts), 2) if shifts else None,
        "skipped": dict(sorted(skipped.items())),
        "games": records,
        "warning": (
            "Source-style NHL research calculation only: Revue Elo proxy, different "
            "season/gameType than public defaults, no verified original SQL or "
            "published best-bet model inputs. Official most-played goalie is NOT "
            "a confirmed game starter. Distinguish raw MoneyPuck fraction (0..1) "
            "from percentage points (0..100). Never backfill prior locks."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--out", default="docs/nhl-backend-source-style-latest.json")
    args = ap.parse_args()
    root = Path(args.docs)
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    doc = build(read("moneypuck-nhl-latest.json"),
                read("nhl-official-stats-latest.json"),
                read("nhl-clairvoyance-shadow-latest.json"),
                datetime.now(timezone.utc))
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(VERSION, doc["future_matched_games"], "source-style candidates;",
          doc["complete_goalie_comparisons"], "fully observed goalies; NO original SQL parity")


if __name__ == "__main__":
    main()
