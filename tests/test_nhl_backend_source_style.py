"""Point-in-time tests for the source-style NHL research adapter."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import unittest

from modeles.reproduction.clairvoyance_predictor import Game, nhl
from outils.nhl_backend_source_style import build

NOW = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
LABEL = "2026-2027"
SEASON = "20262027"
EARLY = (NOW - timedelta(hours=2)).isoformat()
MID = (NOW - timedelta(hours=1)).isoformat()
KICK = (NOW + timedelta(hours=3)).isoformat()


def fixture():
    team = {
        "source": "MoneyPuck.com", "is_live": False,
        "current_season": LABEL, "generated_at_utc": EARLY,
        "status": {LABEL: {"status": "available", "source_updated_utc": EARLY}},
        "seasons": {LABEL: [
            {"team": h, "situation": sit, "season": LABEL, "xg_share": share}
            for h, sit, share in (
                ("BOS", "5on5", .51), ("PHI", "5on5", .32),
                ("BOS", "all", .60), ("PHI", "all", .44))
        ]},
    }
    official = {
        "source": "api.nhle.com/stats/rest/en",
        "status": "verified_nhl_official_stats_snapshot",
        "season": SEASON, "game_type_id": 2,
        "generated_at_utc": MID,
        "reports": {"goalie_summary": {"status": "available"}},
        "goalies": [
            {"season": SEASON, "game_type_id": 2,
             "team_abbrev": "BOS", "games_played": 4,
             "overall_save_pct": .88, "player_name": "Home one"},
            {"season": SEASON, "game_type_id": 2,
             "team_abbrev": "PHI", "games_played": 4,
             "overall_save_pct": .91, "player_name": "Away one"},
        ],
    }
    source = nhl(Game("2026020070", "BOS", "PHI"),
                 1530, 1480, 51., 32., .92, .90)
    shadow = {
        "status": "experimental_not_calibrated",
        "season": SEASON,
        "bookmaker_odds_available": False,
        "confirmed_starters": False,
        "generated_at_utc": EARLY,
        "games": [{
            "event_id": "2026020070",
            "home": "BOS", "away": "PHI",
            "start_utc": KICK,
            "home_elo_proxy": 1530, "away_elo_proxy": 1480,
            "xg_5v5_share_pct": {"home": 51, "away": 32},
            "historical_goalie_proxy": {
                "home": {"save_pct": .92}, "away": {"save_pct": .90}
            },
            "home_win": source["model_home_win_prob"],
            "away_win": source["model_away_win_prob"],
        }],
    }
    return team, official, shadow


class NHLSourceStyleTests(unittest.TestCase):
    def test_aligned_official_goaltenders_and_all_situation_xg(self):
        teams, official, shadow = fixture()
        before = copy.deepcopy((teams, official, shadow))
        report = build(teams, official, shadow, NOW)
        self.assertEqual(report["future_matched_games"], 1)
        self.assertEqual(report["complete_goalie_comparisons"], 1)
        row = report["games"][0]
        expected_raw = nhl(Game("2026020070", "BOS", "PHI"), 1530, 1480,
                           .60, .44, .88, .91)["model_home_win_prob"]
        expected_pct = nhl(Game("2026020070", "BOS", "PHI"), 1530, 1480,
                           60., 44., .88, .91)["model_home_win_prob"]
        self.assertEqual(row["raw_fraction_home_probability"], expected_raw)
        self.assertEqual(row["percentage_point_home_probability"], expected_pct)
        self.assertNotEqual(expected_raw, expected_pct)
        self.assertFalse(row["source_observed_by_frozen_model_time"])
        self.assertFalse(row["actual_original_best_bet_reproduced"])
        self.assertEqual((teams, official, shadow), before)
        self.assertFalse(report["frozen_ledger_unchanged"] is False)
        self.assertFalse(report["public_default_config_matches_scenario"])
        self.assertFalse(report["has_verified_original_predictions"])

    def test_ambiguous_goalies_are_not_guessed(self):
        t, g, s = fixture()
        g["goalies"].append({
            "season": SEASON, "game_type_id": 2, "team_abbrev": "BOS",
            "games_played": 4, "overall_save_pct": .99, "player_name": "Tie"
        })
        report = build(t, g, s, NOW)
        self.assertEqual(report["future_matched_games"], 1)
        self.assertEqual(report["complete_goalie_comparisons"], 0)
        self.assertEqual(report["skipped"]["ambiguous_or_missing_official_goalie"], 1)
        self.assertIsNone(report["games"][0]["raw_fraction_home_probability"])

    def test_old_or_finished_games_not_recomputed_as_forecasts(self):
        t, g, s = fixture()
        s["games"][0]["start_utc"] = (NOW + timedelta(minutes=5)).isoformat()
        report = build(t, g, s, NOW)
        self.assertEqual(report["future_matched_games"], 0)
        self.assertEqual(report["skipped"]["not_upcoming_20min"], 1)

    def test_provider_after_kickoff_cutoff_rejected(self):
        t, g, s = fixture()
        g["generated_at_utc"] = (NOW + timedelta(hours=2, minutes=50)).isoformat()
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)
        # Observed now, match 21 minutes away: model must not use a just-arrived
        # update at less than 20m before its scheduled start.
        t, g, s = fixture()
        s["games"][0]["start_utc"] = (NOW + timedelta(minutes=21)).isoformat()
        g["generated_at_utc"] = (NOW + timedelta(minutes=2)).isoformat()
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)

    def test_invalid_provenance_and_season_are_rejected(self):
        t, g, s = fixture()
        g["season"] = "20252026"
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)
        t, g, s = fixture()
        t["is_live"] = True
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)
        t, g, s = fixture()
        s["bookmaker_odds_available"] = True
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)

    def test_corrupt_money_puck_or_stale_frozen_inputs_fail_closed(self):
        t, g, s = fixture()
        t["seasons"][LABEL][0]["xg_share"] = .55
        d = build(t, g, s, NOW)
        self.assertEqual(d["future_matched_games"], 0)
        self.assertEqual(d["skipped"]["changed_five_on_five_snapshot"], 1)
        t, g, s = fixture()
        s["games"][0]["home_win"] = .01
        d = build(t, g, s, NOW)
        self.assertEqual(d["future_matched_games"], 0)
        self.assertEqual(d["skipped"]["frozen_probability_inconsistent"], 1)

    def test_duplicate_event_is_rejected_and_nans_never_accepted(self):
        t, g, s = fixture()
        s["games"].append(copy.deepcopy(s["games"][0]))
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)
        t, g, s = fixture()
        g["goalies"][0]["overall_save_pct"] = float("nan")
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)

    def test_timezones_and_future_data(self):
        t, g, s = fixture()
        t["generated_at_utc"] = "2026-10-10T12:00:00"
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)
        t, g, s = fixture()
        t["generated_at_utc"] = (NOW + timedelta(minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            build(t, g, s, NOW)


if __name__ == "__main__":
    unittest.main()
