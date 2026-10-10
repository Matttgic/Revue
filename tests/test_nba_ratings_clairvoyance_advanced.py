import unittest
from datetime import datetime,timezone
from outils.nba_ratings_clairvoyance_advanced import build

NOW=datetime(2026,10,10,tzinfo=timezone.utc)

def prior():
    return {"season_end_year":2026,"status":"real_previous_season_aggregate",
       "teams":{str(i):{"abbr":f"T{i}","margin":i*.21-3,
           "wins":50,"losses":32} for i in range(1,31)}}

def advanced():
    return {f"T{i}":{"name":f"Team{i}","w":50,"l":32,
       "gp":82,"mov":i*.21-3,"srs":None,"ortg":115+i*.2,
       "drtg":109+i*.14,"pace":99,"net_rtg":6+i*.06}
       for i in range(1,31)}

class AdvancedNBATests(unittest.TestCase):
    def test_prior_regular_season_only(self):
        d=build(prior(),advanced(),{},{"T1":{"w":2,"l":0,"diff":9}},NOW,
                "2027 unavailable","2026 official")
        self.assertEqual(d["teams_with_previous_advanced"],30)
        self.assertEqual(d["teams_with_current_advanced"],0)
        t=d["teamRatings"]["teams"]["T1"]
        self.assertEqual(t["current"]["gp"],0)
        self.assertEqual(t["source"],"prior")
        self.assertEqual(t["prior"]["ortg"],115.2)
        self.assertEqual(t["prior"]["pace"],99)
    def test_current_standings_accepted_only_with_byteam_rows(self):
        curr={"T1":{**advanced()["T1"],"gp":3,"mov":7.5,"w":0,"l":0},
              "T2":{**advanced()["T2"],"gp":0,"w":0,"l":0}}
        d=build(prior(),advanced(),curr,{"T1":{"w":3,"l":0,"diff":7.5},
            "T2":{"w":2,"l":0,"diff":5}},NOW,"current","previous")
        self.assertEqual(d["teams_with_current_advanced"],1)
        self.assertEqual(d["teamRatings"]["teams"]["T1"]["current"]["gp"],3)
        self.assertEqual(d["teamRatings"]["teams"]["T1"]["source"],"prior+current")
        self.assertEqual(d["teamRatings"]["teams"]["T2"]["source"],"prior")
    def test_requires_advanced_previous(self):
        with self.assertRaises(ValueError):
            build(prior(),{}, {},{}, NOW, "", "")
    def test_30_team_seed_no_invented_club(self):
        d=build(prior(),advanced(),{}, {},NOW,"old","previous")
        self.assertEqual(len(d["eloSeed"]),30)
        self.assertEqual(set(d["eloSeed"]),set(advanced()))
if __name__=="__main__":unittest.main()
