"""Tests sans connexion réseau pour le prototype NHL indépendant de Revue."""
import unittest
from datetime import datetime, timedelta, timezone
from math import isclose

from modeles.simulations.nhl_independant import (
    Game, PARIS, _distribution, _elo_probability, _over, _poisson,
    _score_for_goals, _update_elo, parse_game, parse_timestamp,
    predict, prev_season, season_code,
)
from datetime import date


def raw_game(id, when, h="BOS", a="NYR", state="OFF", hs=None, aus=None, shootout=False):
    return {
        "id": id,
        "gameType": 2,
        "startTimeUTC": when.isoformat().replace("+00:00", "Z"),
        "homeTeam": {"abbrev": h, **({"score": hs} if hs is not None else {})},
        "awayTeam": {"abbrev": a, **({"score": aus} if aus is not None else {})},
        "gameState": state,
        "gameOutcome": {"lastPeriodType": "SO" if shootout else "REG"},
    }


class NHLIndependentTests(unittest.TestCase):
    def test_regular_season_and_preseason(self):
        dt = datetime(2026, 10, 9, 1, tzinfo=timezone.utc)
        r = raw_game(11, dt, hs=3, aus=2)
        self.assertTrue(parse_game(r).final)
        r["gameType"] = 1
        self.assertIsNone(parse_game(r))

    def test_future_not_final(self):
        dt = datetime(2026, 10, 9, 1, tzinfo=timezone.utc)
        g = parse_game(raw_game(20, dt, state="FUT"))
        self.assertFalse(g.final)
        self.assertIsNone(g.home_goals)

    def test_date_with_timezone(self):
        self.assertEqual(parse_timestamp("2026-10-09T01:00:00Z").utcoffset().total_seconds(), 0)
        with self.assertRaises(ValueError):
            parse_timestamp("2026-10-09T01:00:00")

    def test_poisson_sums_to_one(self):
        for lam in (0.7, 1.5, 3.0, 6.0):
            self.assertAlmostEqual(sum(_poisson(lam)), 1, places=12)

    def test_equal_goal_rate_is_balanced(self):
        p, draw = _distribution(3.0, 3.0)
        self.assertAlmostEqual(p * 2 + draw, 1.0, places=9)
        self.assertGreater(draw, 0)
        self.assertLess(draw, 0.3)

    def test_over_probabilities_monotone(self):
        for lam in (2.5, 5.0, 7.5):
            self.assertGreater(_over(lam, 4.5), _over(lam, 5.5))
            self.assertGreater(_over(lam, 5.5), _over(lam, 6.5))
        with self.assertRaises(ValueError):
            _over(5.5, 5.0)

    def test_elo_rating_zero_sum(self):
        dt = datetime(2026, 10, 9, 1, tzinfo=timezone.utc)
        g = parse_game(raw_game(11, dt, hs=3, aus=2))
        ratings = {"BOS": 1500., "NYR": 1500.}
        _update_elo(ratings, g)
        self.assertAlmostEqual(ratings["BOS"] + ratings["NYR"], 3000.)
        self.assertGreater(ratings["BOS"], ratings["NYR"])

    def test_shootout_extra_goal_removed_for_totals(self):
        dt = datetime(2026, 10, 9, 1, tzinfo=timezone.utc)
        so = parse_game(raw_game(1, dt, hs=4, aus=3, shootout=True))
        reg = parse_game(raw_game(2, dt, hs=4, aus=3, shootout=False))
        self.assertEqual(_score_for_goals(so), (3, 3))
        self.assertEqual(_score_for_goals(reg), (4, 3))

    def test_previous_season_code(self):
        self.assertEqual(season_code(date(2026, 10, 9)), "20262027")
        self.assertEqual(season_code(date(2027, 2, 9)), "20262027")
        self.assertEqual(prev_season("20262027"), "20252026")

    def test_prediction_is_future_and_deduplicated(self):
        now = datetime.now(timezone.utc)
        before = now - timedelta(days=5)
        tomorrow = now + timedelta(days=1)
        two_days = now + timedelta(days=2)
        prior = [parse_game(raw_game(i, before - timedelta(days=i),
                                     hs=3 + i % 3, aus=1 + i % 2))
                 for i in range(1, 9)]
        curr = [
            parse_game(raw_game(100, before, hs=5, aus=2)),
            parse_game(raw_game(101, tomorrow, state="FUT")),
            parse_game(raw_game(101, tomorrow, state="FUT")),
            parse_game(raw_game(102, two_days, state="FUT")),
            parse_game(raw_game(103, now - timedelta(days=2), hs=2, aus=4)),
        ]
        target = tomorrow.astimezone(PARIS).date()
        results = predict(prior, curr, now, target, days=1)
        self.assertEqual(len(results), 1)
        prediction = results[0]
        self.assertEqual(prediction["event_id"], "101")
        p = prediction["probabilities"]
        self.assertAlmostEqual(p["home_win"] + p["away_win"], 1.0)
        self.assertTrue(0.0 < p["over_5_5"] < 1.0)
        self.assertNotIn("bet_recommendation", prediction)

    def test_already_started_game_excluded(self):
        now = datetime.now(timezone.utc)
        started = now - timedelta(minutes=20)
        unfinished = parse_game(raw_game(100, started, state="LIVE"))
        self.assertEqual(predict([], [unfinished], now, now.astimezone(PARIS).date()), [])

    def test_empty_training_is_not_a_profitable_backtest(self):
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=28)
        g = parse_game(raw_game(800, future, state="FUT"))
        result = predict([], [g], now, future.astimezone(PARIS).date())
        self.assertEqual(len(result), 1)
        self.assertIn("non calibrées", result[0]["note"])

    def test_home_advantage_elo(self):
        self.assertGreater(_elo_probability(1500, 1500), 0.5)


if __name__ == "__main__":
    unittest.main()
