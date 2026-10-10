"""Offline regression tests for fail-closed official MoneyPuck publication audit."""
import copy
import unittest
from outils.verifier_integrite_moneypuck import validate

YEAR="2026-2027"

def fixtures():
    teams={
        "source":"MoneyPuck.com","is_live":False,"current_season":YEAR,
        "status":{YEAR:{"status":"available","rows":1}},
        "seasons":{YEAR:[{
            "team":"BOS","situation":"5on5","season":YEAR,
            "xg_share":.52,"save_pct":.91,
            "xg_for_60":2.7,"xg_against_60":2.4,
            "shots_for_60":28.0,"shots_against_60":27.0
        }]}
    }
    goalies={
        "source":"MoneyPuck.com","is_live":False,
        "confirmed_starters":False,"current_season":YEAR,
        "statuses":{YEAR:{"status":"available","goalies":1}},
        "seasons":{YEAR:[{
            "name":"Goalie","team":"BOS","season":YEAR,"starter_status":"unknown",
            "save_pct":.92,"xg_against":9.4,"goals_against":7.0,"gsax":2.4
        }]}
    }
    return teams, goalies

class AuditMoneyPuckTests(unittest.TestCase):
    def test_valid_observations(self):
        self.assertEqual(validate(*fixtures()),[])

    def test_missing_season_rejected(self):
        teams,goalies=fixtures()
        teams["seasons"]={}
        teams["status"]={}
        self.assertTrue(validate(teams,goalies))

    def test_malformed_rate_rejected(self):
        teams,goalies=fixtures()
        teams["seasons"][YEAR][0]["xg_for_60"]=float("nan")
        self.assertTrue(any("xg_for_60" in issue for issue in validate(teams,goalies)))

    def test_ghost_starter_rejected(self):
        teams,goalies=fixtures()
        goalies["seasons"][YEAR][0]["starter_status"]="confirmed"
        self.assertTrue(any("starter status" in issue for issue in validate(teams,goalies)))

    def test_invalid_xg_goalie_arithmetic_rejected(self):
        teams,goalies=fixtures()
        goalies["seasons"][YEAR][0]["gsax"]=45.
        self.assertTrue(any("GSAx" in issue for issue in validate(teams,goalies)))

    def test_duplicate_records_rejected(self):
        teams,goalies=fixtures()
        original=copy.deepcopy(teams["seasons"][YEAR][0])
        teams["seasons"][YEAR].append(original)
        teams["status"][YEAR]["rows"]=2
        self.assertTrue(any("duplicate" in issue for issue in validate(teams,goalies)))

    def test_wrong_count_and_status_rejected(self):
        teams,goalies=fixtures()
        teams["status"][YEAR]["rows"]=999
        goalies["statuses"][YEAR]["status"]="unavailable"
        self.assertGreaterEqual(len(validate(teams,goalies)),2)

if __name__=="__main__":
    unittest.main()
