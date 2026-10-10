import unittest
from datetime import datetime,timezone
from outils.nba_ratings_clairvoyance_live import (
    current_espn_rows,previous_espn_rows,build_report
)
NOW=datetime(2026,10,10,2,tzinfo=timezone.utc)
def prior():
    return {"season_end_year":2026,"status":"real_previous_season_aggregate",
            "teams":{str(i):{"abbr":f"T{i}","wins":50,"losses":32,
                           "margin":i*.2-3} for i in range(1,31)}}
class LiveNBATests(unittest.TestCase):
    def test_espn_standings_zero_record_does_not_get_fake_diff(self):
        payload={"children":[{"standings":{"entries":[
            {"team":{"abbreviation":"BOS"},
             "stats":[{"name":"wins","value":0},{"name":"losses","value":0},
                      {"name":"avgPointsFor","value":115.0},{"name":"avgPointsAgainst","value":107.0}]},
            {"team":{"abbreviation":"ATL"},
             "stats":[{"name":"wins","value":3},{"name":"losses","value":2},
                      {"name":"avgPointsFor","value":111.2},{"name":"avgPointsAgainst","value":106.0}]}
        ]}}]}
        rows=current_espn_rows(payload)
        self.assertIsNone(rows["BOS"]["diff"])
        self.assertAlmostEqual(rows["ATL"]["diff"],5.2)
    def test_30_teams_source_rating_with_current_results(self):
        rows={"T1":{"w":5,"l":2,"diff":4.8},
              "T2":{"w":0,"l":0,"diff":None}}
        report=build_report(prior(),rows,NOW,"real ESPN")
        self.assertEqual(report["number_of_teams"],30)
        self.assertEqual(report["current_teams_with_standings"],2)
        a=report["teamRatings"]["teams"]
        self.assertEqual(a["T1"]["source"],"prior+current")
        self.assertEqual(a["T2"]["source"],"prior")
        self.assertEqual(report["eloSeed"]["T1"],a["T1"]["elo"])
        self.assertEqual(a["T1"]["prior"]["season"],2026)
        self.assertEqual(a["T1"]["current"]["season"],2027)
    def test_invalid_previous_year_rejected(self):
        sample=prior();sample["season_end_year"]=2025
        with self.assertRaises(ValueError):
            build_report(sample,{},NOW,"stale")
    def test_missing_previous_rows_not_faked(self):
        sample=prior();sample["teams"]={}
        with self.assertRaises(ValueError):
            previous_espn_rows(sample,2026)
    def test_no_current_feed_still_source_prior(self):
        out=build_report(prior(),{},NOW,"unavailable")
        self.assertEqual(out["number_of_teams"],30)
        self.assertEqual(out["current_teams_with_standings"],0)
        self.assertEqual({x["source"] for x in out["teamRatings"]["teams"].values()},{"prior"})
if __name__=="__main__":unittest.main()
