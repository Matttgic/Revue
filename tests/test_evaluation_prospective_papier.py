"""Prospective locked model scoring must never confuse paper ROI with calibration."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from math import log
from pathlib import Path
import json

from outils.suivi.evaluation_prospective_papier import evaluate,score,valid_entry,MIN_EVIDENCE

DOC=Path(__file__).resolve().parents[1]/"docs"
REAL=json.loads((DOC/"engine-v2-ledger.json").read_text(encoding="utf8"))
NOW=datetime(2026,10,11,tzinfo=timezone.utc)


def synthetic():
    start=NOW-timedelta(days=1)
    return {
        "selection_id":"PL|test|h2h|home|None|betclic_fr",
        "league":"PL","event_id":"fixture-test","market":"h2h",
        "market_rule_verified":True,"status":"won",
        "p_model":.6,"bookmaker_price":2.0,
        "paper_stake_units":1.0,"paper_units_returned":2.0,
        "chronology":"pre_valide",
        "start_utc":start.isoformat(),
        "locked_at":(start-timedelta(hours=3)).isoformat(),
        "quote_at":(start-timedelta(hours=3,minutes=1)).isoformat(),
        "model_at":(start-timedelta(hours=4)).isoformat(),
        "settled_at":(start+timedelta(hours=4)).isoformat(),
    }


class PaperQuality(unittest.TestCase):
    def test_existing_real_ledger_is_read_only_with_strict_small_sample_flags(self):
        original=deepcopy(REAL)
        report=evaluate(REAL,NOW)
        self.assertEqual(REAL,original)
        self.assertEqual(report["version"],"revue_prospective_paper_calibration_v1")
        self.assertEqual(report["status"],"prospective_probabilities_descriptive_not_calibrated")
        self.assertTrue(report["bookmaker_baseline_includes_vig"])
        self.assertFalse(report["real_bets_enabled"])
        self.assertFalse(report["fitted_or_recalibrated_model"])
        self.assertFalse(report["verified_positive_ev"])
        self.assertEqual(report["odds_api_requests"],0)
        self.assertTrue(report["total"]["count"]<MIN_EVIDENCE)
        self.assertEqual(report["total"]["status"],"insufficient_sample")
        self.assertGreater(report["total"]["count"],0)
        self.assertGreaterEqual(report["total"]["count"],report["total"]["distinct_events"])
        self.assertTrue(0<=report["total"]["brier_model"]<=1)
        self.assertIsNotNone(report["total"]["log_loss_bookmaker_raw"])
        self.assertIn("unsafe_or_ambiguous",report["excluded"])

    def test_binary_brier_and_log_loss(self):
        a,b=score(.6,1)
        self.assertAlmostEqual(a,.16)
        self.assertAlmostEqual(b,-log(.6))
        r=evaluate({"version":1,"bets":[synthetic()]},NOW)
        self.assertEqual(r["total"]["count"],1)
        self.assertEqual(r["total"]["wins"],1)
        self.assertEqual(r["total"]["distinct_events"],1)
        self.assertAlmostEqual(r["total"]["brier_model"],.16)
        self.assertAlmostEqual(r["total"]["brier_bookmaker_raw"],.25)
        self.assertAlmostEqual(r["total"]["log_loss_model"],-log(.6),places=5)
        self.assertAlmostEqual(r["total"]["brier_delta_model_minus_bookmaker"],-.09)
        self.assertFalse(r["claim_model_profitable"])

    def test_pending_push_and_invalid_markets_never_contribute(self):
        good=synthetic()
        variants=[]
        for status in ("pending","push","market_rule_unverified"):
            b=deepcopy(good);b["status"]=status;b["selection_id"]+=":"+status
            variants.append(b)
        unverified=deepcopy(good)
        unverified["market_rule_verified"]=False;unverified["selection_id"]+=":bad"
        variants.append(unverified)
        no_utc=deepcopy(good)
        no_utc["quote_at"]="";no_utc["selection_id"]+=":nodat"
        variants.append(no_utc)
        fake_price=deepcopy(good)
        fake_price["bookmaker_price"]=True;fake_price["selection_id"]+=":price"
        variants.append(fake_price)
        out=evaluate({"version":1,"bets":[good,*variants]},NOW)
        self.assertEqual(out["total"]["count"],1)
        self.assertEqual(out["excluded"]["pending"],1)
        self.assertEqual(out["excluded"]["push_not_binary_outcome"],1)
        self.assertGreaterEqual(out["excluded"]["unsafe_or_ambiguous"],4)

    def test_duplicate_settled_selection_is_not_extra_sample(self):
        good=synthetic()
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            evaluate({"version":1,"bets":[good,deepcopy(good)]},NOW)

    def test_forged_settlement_and_future_result_rejected(self):
        b=synthetic();b["paper_units_returned"]=200
        self.assertFalse(valid_entry(b))
        out=evaluate({"version":1,"bets":[b]},NOW)
        self.assertEqual(out["total"]["count"],0)
        self.assertIsNone(out["total"]["brier_model"])
        b=synthetic()
        b["settled_at"]=(NOW+timedelta(hours=1)).isoformat()
        out=evaluate({"version":1,"bets":[b]},NOW)
        self.assertEqual(out["total"]["count"],0)
        self.assertEqual(out["excluded"]["future_settlement"],1)

    def test_multiple_selections_on_same_fixture_are_not_independent_games(self):
        first=synthetic()
        second=deepcopy(first)
        second["selection_id"]="PL|test|h2h|away|None|pmu_fr"
        second["status"]="lost"
        second["paper_units_returned"]=0.0
        second["p_model"]=.4
        r=evaluate({"version":1,"bets":[first,second]},NOW)
        self.assertEqual(r["total"]["count"],2)
        self.assertEqual(r["total"]["distinct_events"],1)
        self.assertIn("correlated",r["total"]["independent_fixture_count_warning"])

    def test_unknown_ledger_and_naive_clock_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"version":2,"bets":[]},NOW)
        with self.assertRaises(ValueError):
            evaluate({"version":1,"bets":[]},datetime(2026,10,11))
        self.assertEqual(evaluate({"version":1,"bets":[]},NOW)["total"]["status"],
                         "insufficient_sample")


if __name__=="__main__":unittest.main()
