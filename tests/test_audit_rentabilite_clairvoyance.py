"""Audit de rentabilité Clairvoyance : chronologie + provenance des cotes."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outils.clairvoyance.audit_rentabilite_clairvoyance import (  # noqa: E402
    audit, backfilled, decimal_odds, family, price_provenance, start_index, summary,
)

NOW = datetime(2026, 10, 11, tzinfo=timezone.utc)
START = 1790000000000  # epoch ms
HOUR = 3600000


def pick(i, outcome="win", lead_h=2.0, **kw):
    base = {"id": f"p{i}", "sport": "NHL", "betType": "ML", "hA": "BOS", "awA": "NYR",
            "date": "2026-09-21", "ml": "+120", "decOdds": 2.2, "winProb": 0.55,
            "outcome": outcome, "startMs": START, "lockedAt": START - lead_h * HOUR,
            "priceSource": "market"}
    base.update(kw)
    return base


class PriceTests(unittest.TestCase):
    def test_decimal_from_american_when_dec_missing(self):
        self.assertAlmostEqual(decimal_odds({"ml": "-110"}), 1 + 100 / 110)
        self.assertAlmostEqual(decimal_odds({"ml": "+150"}), 2.5)
        self.assertIsNone(decimal_odds({"ml": "-50"}))
        self.assertIsNone(decimal_odds({"ml": None}))

    def test_provenance_flags_unobserved_prices(self):
        self.assertEqual(price_provenance({"priceSource": "market"}, 2.0), "market")
        self.assertEqual(price_provenance({"winProb": 0.6}, 1 / 0.6), "model_fair_1_over_p")
        self.assertEqual(price_provenance({"winProb": 60, "ml": "-110"}, 1 / 0.6), "model_fair_1_over_p")
        self.assertEqual(price_provenance({"ml": "-110", "winProb": 0.7}, 1.909), "default_minus_110")
        self.assertEqual(price_provenance({"ml": "-150", "winProb": 0.7}, 1.667), "unlabelled")

    def test_families(self):
        self.assertEqual(family({"sport": "PL", "betType": "ML"}), "soccer_1x2")
        self.assertEqual(family({"sport": "LIIGA", "betType": "SPREAD"}), "hockey_handicap")
        self.assertEqual(family({"sport": "FOOTBALL", "league": "CFB", "betType": "OU"}),
                         "us_football_spread_total")


class AuditTests(unittest.TestCase):
    def test_late_locks_are_separated_from_forecasts(self):
        picks = [pick(1, lead_h=1), pick(2, "loss", lead_h=1), pick(3, lead_h=-1), pick(4, lead_h=-5)]
        rep = audit(picks, {}, "abc", NOW)
        self.assertEqual(rep["by_lock_timing"]["pre"]["n"], 2)
        self.assertEqual(rep["by_lock_timing"]["during"]["n"], 1)
        self.assertEqual(rep["by_lock_timing"]["after"]["n"], 1)
        self.assertEqual(rep["as_published_all_settled"]["n"], 4)
        self.assertAlmostEqual(rep["by_lock_timing"]["pre"]["units"], 0.2)

    def test_default_prices_never_prove_profit(self):
        picks = [pick(i, lead_h=3, priceSource=None, ml="-110", decOdds=1.909, winProb=0.7)
                 for i in range(200)]
        rep = audit(picks, {}, None, NOW)
        self.assertGreater(rep["pre_start_by_price_provenance"]["default_minus_110"]["roi"], 0.5)
        self.assertNotIn("market", rep["pre_start_by_price_provenance"])
        self.assertFalse(rep["verdict"]["profitability_demonstrated"])

    def test_profit_requires_ci_above_zero_on_market_prices(self):
        winners = [pick(i, lead_h=3) for i in range(300)]
        losers = [pick(1000 + i, "loss", lead_h=3) for i in range(150)]
        rep = audit(winners + losers, {}, None, NOW)
        self.assertTrue(rep["verdict"]["profitability_demonstrated"])
        coin = [pick(i, "win" if i % 2 else "loss", lead_h=3, decOdds=2.0, ml="+100") for i in range(100)]
        self.assertFalse(audit(coin, {}, None, NOW)["verdict"]["profitability_demonstrated"])

    def test_pending_parlays_and_unpriced_rows_ignored(self):
        picks = [pick(1, "pending"), pick(2, betType="PARLAY"), pick(3, decOdds=None, ml=None), pick(4)]
        self.assertEqual(audit(picks, {}, None, NOW)["as_published_all_settled"]["n"], 1)

    def test_unknown_start_is_not_pre_start(self):
        rep = audit([pick(1, startMs=None)], {}, None, NOW)
        self.assertEqual(list(rep["by_lock_timing"]), ["unknown"])
        self.assertIsNone(rep["pre_start_market_priced_period"])

    def test_backfilled_stamps_are_counted(self):
        old = pick(1, startMs=None, lockedAt=1747872000000, date="2026-05-22")  # verrou daté 2025
        self.assertTrue(backfilled(old))
        self.assertFalse(backfilled(pick(2)))
        self.assertFalse(backfilled({"lockedAt": "x", "date": "2026-01-01"}))
        rep = audit([old, pick(2)], {}, None, NOW)
        self.assertEqual(rep["lock_stamp_over_300_days_before_game"]["n"], 1)
        self.assertIsNone(audit([pick(3)], {}, None, NOW)["lock_stamp_over_300_days_before_game"])

    def test_summary_ci(self):
        rows = [{"odds": 2.0, "won": i % 2 == 0, "p": 0.5} for i in range(100)]
        s = summary(rows)
        self.assertEqual(s["roi"], 0.0)
        self.assertFalse(s["roi_ci_excludes_zero"])
        self.assertIsNone(summary([]))


class IndexTests(unittest.TestCase):
    def test_schedule_and_history_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            (docs / "nhl_schedule.json").write_text(json.dumps(
                {"games": [{"date": "2026-09-22T01:00Z", "home": "BOS", "away": "NYR"}, {"date": "bad"}]}))
            (docs / "nfl_schedule.json").write_text(json.dumps(
                {"weeks": {"1": [{"date": "2026-09-13T17:00Z", "home": "KC", "away": "BUF"}]}}))
            (docs / "game_start_history.json").write_text(json.dumps(
                {"games": {"2026-08-01|A|B": 1785000000000}}))
            idx = start_index(docs)
        # 01:00 UTC on 22/09 is still 21/09 in America/Denver
        self.assertIn("2026-09-21|BOS|NYR", idx)
        self.assertIn("2026-09-13|BUF|KC", idx)
        self.assertEqual(idx["2026-08-01|A|B"], 1785000000000.0)
        rep = audit([pick(1, startMs=None, lockedAt=idx["2026-09-21|BOS|NYR"] - HOUR)], idx, None, NOW)
        self.assertEqual(rep["by_lock_timing"]["pre"]["n"], 1)


if __name__ == "__main__":
    unittest.main()
