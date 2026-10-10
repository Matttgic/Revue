"""Offline, reproducible controls for future-only NHL calibration research."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
import unittest

from outils.nhl_calibration_prospective import build_report, TRAIN_MIN, HOLDOUT_MIN
from outils.nhl_shadow_tracker import VERSION

UTC = timezone.utc
START = datetime(2026, 10, 10, 12, tzinfo=UTC)


def sample(n=140, include_variant=True):
    rows = []
    for i in range(n):
        game_time = START + timedelta(days=i)
        final_time = game_time + timedelta(hours=4)
        # 50-50 distribution across two strength bins; designed to be
        # miscalibrated (p .8 or .2 vs true .7/.3) in synthetic TESTS ONLY.
        high = i % 2 == 0
        local = (i // 2) % 10
        y = int(local < (7 if high else 3))
        row = {
            "event_id":str(100000 + i),
            "home":"BOS","away":"NYR",
            "kickoff_utc":game_time.isoformat(),
            "locked_at_utc":(game_time-timedelta(hours=2)).isoformat(),
            "source_prediction_at_utc":(game_time-timedelta(hours=2)).isoformat(),
            "home_win_probability":0.8 if high else 0.2,
            "research_home_win_probability":(0.78 if high else 0.22) if include_variant else None,
            "status":"settled","resolved_at_utc":final_time.isoformat(),
            "result":y,"home_goals":3 if y else 1,"away_goals":1 if y else 3,
            "brier":0.0,
        }
        rows.append(row)
    return {"version":VERSION, "events":rows}


class NHLProspectiveCalibrationTests(unittest.TestCase):
    def report(self,n):
        return build_report(sample(n),START+timedelta(days=n+2))

    def test_no_data_never_claims_calibration(self):
        report = self.report(0)
        self.assertEqual(report["status"],"prospective_research_only")
        self.assertFalse(report["auto_promotion"])
        self.assertFalse(report["real_bets_enabled"])
        self.assertIsNone(report["sportsbook_roi"])
        for m in report["models"].values():
            self.assertEqual(m["settled_samples"],0)
            self.assertEqual(m["training_remaining"],100)
            self.assertEqual(m["calibration_status"],"insufficient_training")
            self.assertIsNone(m["parameters"])
            self.assertEqual(len(m["reliability_bins"]),5)
            self.assertTrue(all(b["count"] == 0 for b in m["reliability_bins"]))

    def test_99_outcomes_still_insufficient(self):
        study = self.report(99)["models"]["clairvoyance_formula"]
        self.assertEqual(study["training_remaining"],1)
        self.assertIsNone(study["parameters"])

    def test_first_100_are_train_only_and_never_claim_validation(self):
        study = self.report(100)["models"]["clairvoyance_formula"]
        self.assertEqual(study["training_samples"],100)
        self.assertEqual(study["holdout_samples"],0)
        self.assertEqual(study["holdout_required"],40)
        self.assertIsNone(study["holdout_metrics"])
        self.assertEqual(study["calibration_status"],"awaiting_future_holdout")
        self.assertFalse(study["approved_for_betting"])
        self.assertTrue(math.isfinite(study["parameters"]["slope"]))

    def test_139_outcomes_waits_for_holdout(self):
        study=self.report(139)["models"]["clairvoyance_formula"]
        self.assertEqual(study["holdout_samples"],39)
        self.assertEqual(study["holdout_remaining"],1)
        self.assertIsNone(study["holdout_metrics"])

    def test_140_have_real_chronological_holdout_metrics(self):
        doc=self.report(140)
        study=doc["models"]["clairvoyance_formula"]
        self.assertEqual(study["holdout_samples"],40)
        self.assertEqual(study["training_samples"],100)
        self.assertEqual(study["calibration_status"],"experimental_holdout_better")
        metrics=study["holdout_metrics"]
        self.assertLess(metrics["calibrated_brier"],metrics["raw_brier"])
        self.assertLess(metrics["calibrated_brier"],metrics["train_only_baseline_brier"])
        self.assertLess(metrics["calibrated_logloss"],metrics["raw_logloss"])
        self.assertFalse(study["approved_for_betting"])
        self.assertEqual(sum(b["count"] for b in study["reliability_bins"]),140)
        self.assertEqual(doc["models"]["revue_prudent"]["holdout_samples"],40)

    def test_more_future_results_never_change_first_100_parameters(self):
        first=self.report(140)["models"]["clairvoyance_formula"]
        later=self.report(180)["models"]["clairvoyance_formula"]
        self.assertEqual(first["parameters"],later["parameters"])
        self.assertEqual(first["training_cutoff_utc"],later["training_cutoff_utc"])
        self.assertEqual(later["holdout_samples"],80)

    def test_late_settled_early_game_cannot_enter_holdout(self):
        dataset=sample(140)
        late=deepcopy(dataset["events"][70])
        late["event_id"]="late"
        late["resolved_at_utc"]=(START+timedelta(days=150)).isoformat()
        dataset["events"].append(late)
        result=build_report(dataset,START+timedelta(days=155))
        study=result["models"]["clairvoyance_formula"]
        self.assertEqual(study["holdout_samples"],40)
        self.assertEqual(study["training_samples"],100)

    def test_incorrect_result_or_probability_rejected(self):
        for field, value in (("result",2),("home_win_probability",1.0),
                             ("home_win_probability",float("nan")),
                             ("resolved_at_utc",(START-timedelta(days=1)).isoformat()),
                             ("locked_at_utc",(START+timedelta(hours=1)).isoformat())):
            with self.subTest(field=field):
                dataset=sample(1)
                dataset["events"][0][field]=value
                with self.assertRaises(ValueError):
                    build_report(dataset,START+timedelta(days=2))

    def test_result_must_be_known_after_game_and_before_report(self):
        sample_set=sample(1)
        game=sample_set["events"][0]
        game["resolved_at_utc"]=(START-timedelta(minutes=5)).isoformat()
        with self.assertRaisesRegex(ValueError,"pre-kickoff"):
            build_report(sample_set,START+timedelta(days=3))
        sample_set=sample(1)
        with self.assertRaisesRegex(ValueError,"settled by now"):
            build_report(sample_set,START+timedelta(minutes=30))

    def test_official_final_goals_must_match_the_winner(self):
        sample_set=sample(1)
        sample_set["events"][0]["home_goals"]=0
        sample_set["events"][0]["away_goals"]=3
        with self.assertRaisesRegex(ValueError,"goals disagree"):
            build_report(sample_set,START+timedelta(days=3))

    def test_old_original_only_samples_do_not_backfill_candidate(self):
        doc=build_report(sample(140,include_variant=False),START+timedelta(days=145))
        self.assertEqual(doc["models"]["clairvoyance_formula"]["holdout_samples"],40)
        self.assertEqual(doc["models"]["revue_prudent"]["settled_samples"],0)
        self.assertIsNone(doc["models"]["revue_prudent"]["parameters"])

    def test_pending_predictions_do_not_count(self):
        dataset=sample(140)
        for e in dataset["events"][100:]:
            e["status"]="pending"
            e["result"]=None
            e["resolved_at_utc"]=None
        doc=build_report(dataset,START+timedelta(days=145))
        self.assertEqual(doc["models"]["clairvoyance_formula"]["settled_samples"],100)
        self.assertEqual(doc["models"]["clairvoyance_formula"]["holdout_samples"],0)

    def test_duplicate_and_unknown_schema_rejected(self):
        dataset=sample(2)
        dataset["events"].append(deepcopy(dataset["events"][0]))
        with self.assertRaises(ValueError):
            build_report(dataset,START)
        dataset=sample(2)
        dataset["version"]="other"
        with self.assertRaises(ValueError):
            build_report(dataset,START)

if __name__ == "__main__":
    unittest.main()
