"""Source input coverage must NOT be conflated with math formula equality."""
import json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from outils.audit_entrees_clairvoyance import check
NOW=datetime(2026,10,10,tzinfo=timezone.utc)

class DataAuditTests(unittest.TestCase):
    def test_no_files_never_claims_full_prediction_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=check(Path(tmp),NOW)
            self.assertFalse(r["full_model_output_parity_on_real_games"])
            self.assertTrue(r["formula_parity_not_sufficient"])
            self.assertEqual(r["completed_data_checks"],0)
            self.assertEqual(r["sources"]["football_authorized_xg"]["status"],"missing")
            self.assertEqual(r["sources"]["nhl_goalies"]["status"],"unverified_live_inputs")

    def test_valid_prior_not_conflated_with_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/"docs";d.mkdir()
            teams={str(i):{"prior":{"ortg":115,"drtg":111},
                           "current":{"netRtg":None}} for i in range(30)}
            (d/"clairvoyance-nba-advanced-ratings.json").write_text(json.dumps({
                "teamRatings":{"teams":teams},
                "teams_with_previous_advanced":30,
                "teams_with_current_advanced":0,
            }))
            (d/"parite-clairvoyance-espn-nba.json").write_text(json.dumps({
                "status":"nba_espn_byteam_strict_parity","tests_passed":460}))
            value=check(root,NOW)
            self.assertEqual(value["completed_data_checks"],1)
            self.assertEqual(value["sources"]["nba_previous_advanced"]["observed_teams"],30)
            self.assertEqual(value["sources"]["nba_current_advanced"]["observed_teams"],0)
            self.assertNotEqual(value["sources"]["nba_current_advanced"]["status"],
                                "available_verified_input_parser")

    def test_current_report_must_match_actual_teams(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"docs";d.mkdir()
            teams={str(i):{"prior":{"ortg":110,"drtg":113},
                           "current":{"netRtg":3}} for i in range(30)}
            (d/"clairvoyance-nba-advanced-ratings.json").write_text(json.dumps({
                "teamRatings":{"teams":teams},
                "teams_with_previous_advanced":30,
                "teams_with_current_advanced":0,
            }))
            (d/"parite-clairvoyance-espn-nba.json").write_text(json.dumps({
                "status":"nba_espn_byteam_strict_parity","tests_passed":460}))
            result=check(Path(tmp),NOW)
            self.assertEqual(result["completed_data_checks"],1)
            self.assertEqual(result["sources"]["nba_current_advanced"]["status"],
                             "missing_or_partial")

    def test_never_upgrade_to_opta_on_boolean_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/"docs";d.mkdir()
            (d/"football-espn-team-features.json").write_text(json.dumps({
                "opta_available":True
            }))
            a=check(Path(tmp),NOW)
            self.assertEqual(a["sources"]["football_authorized_xg"]["status"],
                             "unverified_live_inputs")
            self.assertFalse(a["full_model_output_parity_on_real_games"])

    def test_invalid_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            check(Path("."),datetime(2026,10,10))
if __name__=="__main__":unittest.main()
