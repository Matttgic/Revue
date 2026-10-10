"""Offline tests for MoneyPuck official goalie statistics (no starter inference)."""
from datetime import datetime, timezone
import unittest
from outils.moneypuck_goalies_feed import (
    Download, derived_goalies, create_snapshot, goalie_csv_url
)

def fixture(team="BOS",name="Sample Goalie",xga="8.4",goals="7"):
    return ("playerId,season,name,team,situation,games_played,icetime,xGoals,goals,ongoal\n"
            f"10001,2026,{name},{team},all,3,10800,{xga},{goals},86\n"
            f"10001,2026,{name},{team},5on5,3,9000,5,4,64\n")


class MoneyPuckGoalieTests(unittest.TestCase):
    def test_only_official_goalie_url(self):
        self.assertEqual(goalie_csv_url(2026),
            "https://moneypuck.com/moneypuck/playerData/seasonSummary/2026/regular/goalies.csv")
        with self.assertRaises(ValueError):
            goalie_csv_url(7)

    def test_gsax_goalie_not_starter(self):
        rows=derived_goalies(fixture(),2026)
        self.assertEqual(len(rows),1)
        r=rows[0]
        self.assertEqual(r["team"],"BOS")
        self.assertEqual(r["games_played"],3)
        self.assertEqual(r["ice_hours"],3)
        self.assertEqual(r["gsax"],1.4)
        self.assertEqual(r["gsax_per_60"],0.47)
        self.assertAlmostEqual(r["save_pct"],0.9186)
        self.assertEqual(r["starter_status"],"unknown")

    def test_reject_invalid_rows(self):
        self.assertFalse(derived_goalies(fixture(goals="90"),2026))
        self.assertFalse(derived_goalies(fixture(xga="-1"),2026))
        with self.assertRaises(ValueError):
            derived_goalies("team,situation\nBOS,all\n",2026)

    def test_distinguish_old_and_current_season(self):
        now=datetime(2026,10,10,tzinfo=timezone.utc)
        def fetch(y):
            if y==2026:raise TimeoutError("offline")
            return Download(fixture(team="NYR"))
        output=create_snapshot(now,fetch)
        self.assertFalse(output["seasons"]["2026-2027"])
        self.assertEqual(output["seasons"]["2025-2026"][0]["season"],"2025-2026")
        self.assertFalse(output["is_live"])
        self.assertFalse(output["confirmed_starters"])

    def test_two_seasons_and_provenance(self):
        now=datetime(2026,10,10,tzinfo=timezone.utc)
        o=create_snapshot(now,lambda _:Download(fixture()))
        self.assertEqual(len(o["seasons"]["2026-2027"]),1)
        self.assertEqual(len(o["seasons"]["2025-2026"]),1)
        self.assertIn("moneypuck.com/data.htm",o["source_page"])

    def test_fail_closed(self):
        with self.assertRaises(RuntimeError):
            create_snapshot(datetime(2026,10,10,tzinfo=timezone.utc),
                            lambda _: (_ for _ in ()).throw(TimeoutError()))


if __name__=="__main__":
    unittest.main()
