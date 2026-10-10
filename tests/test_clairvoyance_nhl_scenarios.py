"""Sensitivity of independently reconstructed NHL backend formula on real proxy inputs."""
import copy,unittest
from outils.clairvoyance_nhl_scenarios import investigate,model_prob
from modeles.reproduction.clairvoyance_predictor import Game,nhl
from datetime import datetime,timezone,timedelta
T=datetime(2026,10,10,15,tzinfo=timezone.utc)
def iso(hours=0):return (T+timedelta(hours=hours)).isoformat()
def samples():
    g={"event_id":"2026020077","home":"PIT","away":"DAL","start_utc":iso(8),
       "home_elo_proxy":1430,"away_elo_proxy":1530,
       "historical_goalie_proxy":{"home":{"save_pct":.91},"away":{"save_pct":.92}}}
    p=model_prob(g,1430,1530,51,53,.91,.92)
    g["home_win"]=p
    f={"version":"nhl_input_gap_forensics_v1",
       "status":"nhl_forensics_verified_observation_alignment",
       "exact_prediction_replication_verified":False,"generated_at_utc":iso(),
       "match_diagnostics":[{
          "event_id":g["event_id"],"home":"PIT","away":"DAL",
          "kickoff_utc":iso(8),"market":"moneyline_including_overtime",
          "side":"home","reference_probability":.52,
          "xg_identity":"same_xg_both_teams",
          "reference_5v5_xg_pct":{"home":51,"away":53}}]}
    s={"status":"experimental_not_calibrated","bookmaker_odds_available":False,
       "generated_at_utc":iso(),"games":[g]}
    return f,s

class SensitivityTests(unittest.TestCase):
    def test_reproduces_logged_model_on_same_observed_elo_goalie_xg(self):
        f,s=samples()
        r=investigate(f,s)
        self.assertEqual(r["matched_scenarios"],1)
        self.assertEqual(r["games"][0]["recomputed_revue_probability"],s["games"][0]["home_win"])
        self.assertFalse(r["actual_original_hidden_elo_or_starters_verified"])
        self.assertFalse(r["original_published_model_family_verified"])
        self.assertFalse(r["real_bets_enabled"])
        self.assertEqual(len(r["games"][0]["counterfactuals"]),5)

    def test_equal_elo_is_hypothesis_not_an_observed_original_rating(self):
        f,s=samples()
        x=investigate(f,s)["games"][0]
        self.assertNotEqual(x["counterfactuals"]["equal_elo_1500"]["model_probability"],
                            x["counterfactuals"]["observed_revue_inputs"]["model_probability"])
        self.assertTrue(x["not_identified_as_causal_explanation"])

    def test_away_side_probabilities_complement_home(self):
        f,s=samples()
        f["match_diagnostics"][0]["side"]="away"
        f["match_diagnostics"][0]["reference_probability"]=.48
        r=investigate(f,s)
        p=s["games"][0]["home_win"]
        self.assertAlmostEqual(r["games"][0]["recomputed_revue_probability"],round(1-p,3))

    def test_mismatched_expected_revue_snapshot_skipped(self):
        f,s=samples();s["games"][0]["home_win"]=.9
        self.assertEqual(investigate(f,s)["matched_scenarios"],0)

    def test_forensics_source_not_verified_rejected(self):
        f,s=samples();f["status"]="nhl_forensics_waiting_same_observation"
        with self.assertRaises(ValueError):investigate(f,s)

    def test_actual_source_xg_mismatch_must_not_be_used_in_equal_xg_analysis(self):
        f,s=samples();f["match_diagnostics"][0]["xg_identity"]="different_xg_input"
        self.assertEqual(investigate(f,s)["matched_scenarios"],0)

    def test_model_formula_declares_no_recommendations_in_scenario(self):
        f,s=samples();r=investigate(f,s)
        self.assertIs(r["calibration_or_betting_recommendations"],False)
        self.assertIsNone(r["mean_abs_gap_published_vs_observed_revue_pp"] if r["matched_scenarios"]==0 else None)
if __name__=="__main__":unittest.main()
