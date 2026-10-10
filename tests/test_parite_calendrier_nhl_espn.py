"""Cross-provider NHL/ESPN fixture identity cannot be inferred from fixture order."""
from datetime import datetime,timedelta,timezone
from copy import deepcopy
import unittest

from outils.parite_calendrier_nhl_espn import resolve_reference_ids,build

NOW=datetime(2026,10,10,11,tzinfo=timezone.utc)
KICK=(NOW+timedelta(hours=6)).isoformat()

def source():
    return {"games":[{"id":"401892469","home":"BOS","away":"PHI","date":KICK,
                      "homeML":-135,"awayML":115,
                      "goalies":{"home":{"name":"Tester","status":"projected"}}}]}

def own():
    return {"generated_at_utc":NOW.isoformat(),"games":[{
        "event_id":"2026020070","home":"BOS","away":"PHI","start_utc":KICK,
        "home_win":.65,"away_win":.35,
    }]}

class FixtureIdentityTests(unittest.TestCase):
    def test_exact_match_exposes_only_factual_identifier_concordance(self):
        report=build(source(),own(),"pinned-commit",NOW)
        self.assertEqual(report["matched"],1)
        self.assertEqual(report["unmatched"],0)
        self.assertEqual(report["mappings"][0]["original_espn_id"],"401892469")
        self.assertEqual(report["mappings"][0]["nhl_game_id"],"2026020070")
        self.assertNotIn("homeML",str(report))
        self.assertNotIn("Tester",str(report))
        self.assertNotIn("home_win",str(report))
        self.assertEqual(report["actual_prediction_parity"],"NOT_VERIFIED")

    def test_club_time_and_duplicate_source_entries_must_agree(self):
        for field,value in [
            ("away","ANA"),("date",(NOW+timedelta(hours=7)).isoformat()),
            ("home","NJD"),
        ]:
            original=source()
            original["games"][0][field]=value
            self.assertEqual(resolve_reference_ids(original,own())[0],[])
            with self.assertRaises(ValueError):
                build(original,own(),"pinned",NOW)
        original=source()
        original["games"].append(deepcopy(original["games"][0]))
        self.assertEqual(resolve_reference_ids(original,own())[0],[])
        with self.assertRaises(ValueError):
            build(original,own(),"pinned",NOW)

    def test_duplicate_revue_ids_cannot_be_mapped(self):
        fixtures=own()
        fixtures["games"].append(deepcopy(fixtures["games"][0]))
        with self.assertRaises(ValueError):
            resolve_reference_ids(source(),fixtures)

    def test_future_source_or_missing_commit_rejected(self):
        fixtures=own()
        fixtures["generated_at_utc"]=(NOW+timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError):
            build(source(),fixtures,"source",NOW)
        with self.assertRaises(ValueError):
            build(source(),own(),"",NOW)

if __name__=="__main__":unittest.main()
