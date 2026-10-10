"""MLB Elo fallback scenario respects actual source behavior and chronology."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.mlb_source_elo_gap import analyze
from modeles.reproduction.clairvoyance_predictor import Game,mlb
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
def when(hours):return (NOW+timedelta(hours=hours)).isoformat()

def data():
    fixtures={"status":"prototype_non_calibre","generated_at_utc":when(-1),
              "competitions":{"MLB":{"games":[
                {"event_id":"401900111","home":"AAA","away":"BBB","start_utc":when(4)},
                {"event_id":"401900112","home":"BBB","away":"AAA","start_utc":when(7)}]}}}
    history={"version":1,"leagues":{"MLB":{"events":[
        {"id":str(401800001+i),"league":"MLB","start":when(-300+i*4),
         "home":"AAA","away":"BBB","complete":True,
         "home_score":4.0 if i%2==0 else 1.0,
         "away_score":1.0 if i%2==0 else 5.0}
        for i in range(28)]}}}
    return fixtures,history

class MLBScenarios(unittest.TestCase):
    def test_sensitivity_replay_vs_original_missing_elo_default(self):
        doc=analyze(*data(),NOW)
        self.assertEqual(doc["games_comparable"],2)
        self.assertGreater(doc["diagnostic_revue_completed_espn_games"],20)
        self.assertTrue(doc["original_sql_missing_team_status_known"] is False)
        self.assertTrue(doc["historical_statuses_are_not_point_in_time_observations"])
        self.assertFalse(doc["real_bets_enabled"])
        for r in doc["games"]:
            expected=mlb(Game(r["event_id"],r["home"],r["away"]),1500.,1500.)
            self.assertEqual(r["original_default_both_missing_home_probability"],
                             expected["model_home_win_prob"])
            self.assertIsNone(r["betting_recommendation"])
            self.assertAlmostEqual(
                r["replay_vs_both_default_pp"],
                round(100*(r["replayed_revue_home_probability"]-
                           r["original_default_both_missing_home_probability"]),2))
        self.assertNotEqual(doc["games"][0]["replayed_revue_home_probability"],
                            doc["games"][0]["original_default_both_missing_home_probability"])

    def test_past_fixtures_never_become_new_recommendations(self):
        f,h=data()
        f["competitions"]["MLB"]["games"][0]["start_utc"]=when(-5)
        report=analyze(f,h,NOW)
        self.assertEqual(report["games_comparable"],1)
        self.assertEqual(report["skipped"]["not_upcoming_20_minutes"],1)

    def test_unknown_teams_not_given_a_fake_revue_elo(self):
        f,h=data()
        f["competitions"]["MLB"]["games"][0]["home"]="UNKNOWN"
        report=analyze(f,h,NOW)
        self.assertEqual(report["games_comparable"],1)
        self.assertEqual(report["skipped"]["missing_revue_elo_coverage"],1)

    def test_stale_future_snapshot_rejected(self):
        f,h=data()
        f["generated_at_utc"]=when(-13)
        with self.assertRaises(ValueError):analyze(f,h,NOW)
        f,h=data()
        f["generated_at_utc"]=when(1)
        with self.assertRaises(ValueError):analyze(f,h,NOW)

    def test_duplicate_events_and_corrupt_history_fail(self):
        f,h=data()
        f["competitions"]["MLB"]["games"][1]["event_id"]="401900111"
        with self.assertRaises(ValueError):analyze(f,h,NOW)
        f,h=data();h["version"]=999
        with self.assertRaises(Exception):analyze(f,h,NOW)

if __name__=="__main__":unittest.main()
