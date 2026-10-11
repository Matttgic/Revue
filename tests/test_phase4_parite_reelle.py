"""Phase 4 chronology and source provenance regression suite."""
import unittest
from copy import deepcopy
from datetime import datetime,timezone
from outils.clairvoyance.phase4_parite_reelle import build,stamp,prob
NOW=datetime(2026,10,10,21,0,tzinfo=timezone.utc)
def sample():
    g={"status":"public_original_source_fixture_and_nhl_output_diagnostic",
       "reference_repository":"Purple-Wraith/clairvoyance-backend",
       "real_bets_enabled":False,"live_french_odds_verified":False,
       "exact_prediction_parity_verified":False,"point_in_time_feature_parity_verified":False,
       "original_history_profit_report_excluded":True,
       "generated_at_utc":"2026-10-10T20:40:00+00:00","strict_event_matches":3,
       "nhl_source_vs_revue":[{
          "key":"NHL:2026020090","league":"NHL","home":"BOS","away":"PHI",
          "kickoff_utc":"2026-10-11T02:00:00+00:00",
          "market":"moneyline_including_overtime","side":"away","line":None,
          "original_observed_at_utc":"2026-10-10T19:00:00Z",
          "revue_observed_at_utc":"2026-10-10T20:00:00Z",
          "original_probability":.4,"revue_probability":.55,
          "difference_revue_minus_original_pp":15.0,
          "same_scheduled_fixture_and_market":True,"status":"compared"}]}
    s={"version":"revue_nhl_backend_source_style_v1",
       "status":"backend_style_input_scenario_not_original_model_parity",
       "has_verified_original_predictions":False,
       "original_sql_ratings_available":False,
       "public_deployment_configuration_verified":False,
       "reference_uses_same_frontend_best_bets_model_verified":False,
       "real_bets_enabled":False,"frozen_ledger_unchanged":True,
       "generated_at_utc":"2026-10-10T20:30:00Z",
       "games":[{"event_id":"2026020090","home":"BOS","away":"PHI",
          "kickoff_utc":"2026-10-11T02:00:00+00:00",
          "source_observed_by_frozen_model_time":True,
          "frozen_prediction_overwritten":False,
          "actual_original_best_bet_reproduced":False,
          "original_sql_elo_and_raw_xg_verified":False,
          "raw_fraction_home_probability":.6,
          "percentage_point_home_probability":.52}]}
    return g,s

class TestPhase4(unittest.TestCase):
    def test_comparison_not_source_prediction_parity(self):
        g,s=sample();r=build(g,s,NOW)
        self.assertEqual(r["observed_probability_comparisons"],1)
        self.assertEqual(r["matched_input_hypotheses"],1)
        self.assertEqual(r["mean_abs_delta_pp"],15)
        self.assertEqual(r["rows"][0]["hypotheses"]["xg_fraction_probability"],.4)
        self.assertEqual(r["rows"][0]["hypotheses"]["xg_percentage_points_probability"],.48)
        for k in ("original_sql_inputs_verified","actual_original_prediction_parity_verified",
                  "original_forecast_lock_time_verified","market_settlement_rules_verified",
                  "real_bets_enabled","roi_claimed"):
            self.assertFalse(r[k],k)
    def test_late_source_or_revue_excluded(self):
        for field in ("original_observed_at_utc","revue_observed_at_utc"):
            g,s=sample();g["nhl_source_vs_revue"][0][field]="2026-10-11T01:50:00Z"
            x=build(g,s,NOW)
            self.assertEqual(x["observed_probability_comparisons"],0)
            self.assertIsNone(x["rows"][0]["hypotheses"])
    def test_forged_source_claims_rejected(self):
        for k,v in (("real_bets_enabled",True),("exact_prediction_parity_verified",True),
                    ("original_history_profit_report_excluded",False)):
            g,s=sample();g[k]=v
            with self.assertRaises(ValueError):build(g,s,NOW)
        g,s=sample();s["original_sql_ratings_available"]=True
        with self.assertRaises(ValueError):build(g,s,NOW)
    def test_scenario_join_needs_exact_match(self):
        for k,v in (("home","FAKE"),("kickoff_utc","2026-10-11T03:00:00Z"),
                    ("frozen_prediction_overwritten",True)):
            g,s=sample();s["games"][0][k]=v
            self.assertEqual(build(g,s,NOW)["matched_input_hypotheses"],0)
    def test_totals_not_assigned_moneyline_scenarios(self):
        g,s=sample();g["nhl_source_vs_revue"][0].update(market="full_game_total",side="under",line=6.5)
        self.assertEqual(build(g,s,NOW)["matched_input_hypotheses"],0)
    def test_duplicate_fixtures_cannot_inflate(self):
        g,s=sample();s["games"].append(deepcopy(s["games"][0]))
        self.assertEqual(build(g,s,NOW)["matched_input_hypotheses"],0)
        g,s=sample();g["nhl_source_vs_revue"].append(deepcopy(g["nhl_source_vs_revue"][0]))
        r=build(g,s,NOW)
        self.assertEqual(r["observed_probability_comparisons"],1)
        self.assertEqual(r["exclusion_reasons"]["duplicate_selection"],1)
    def test_forged_differences_rejected(self):
        g,s=sample();g["nhl_source_vs_revue"][0]["difference_revue_minus_original_pp"]=0
        self.assertEqual(build(g,s,NOW)["observed_probability_comparisons"],0)
    def test_input_validation(self):
        for value in (float("nan"),True,-1,0,1,None):
            with self.assertRaises(ValueError):prob(value)
        with self.assertRaises(ValueError):stamp("2026-10-10T00:00:00")
    def test_real_stored_sources_if_present(self):
        from pathlib import Path
        import json
        root=Path(__file__).resolve().parents[1]/"docs"
        g=root/"clairvoyance-real-output-gap.json"
        s=root/"nhl-backend-source-style-latest.json"
        if not(g.exists() and s.exists()):self.skipTest("Data missing")
        r=build(json.loads(g.read_text()),json.loads(s.read_text()),datetime.now(timezone.utc))
        self.assertFalse(r["actual_original_prediction_parity_verified"])
        self.assertEqual(r["paid_api_calls"],0)
        self.assertLessEqual(r["matched_input_hypotheses"],r["observed_probability_comparisons"])
if __name__=="__main__":unittest.main()
