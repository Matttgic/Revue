import unittest
from modeles.reproduction.clairvoyance_moneypuck_parser import (
  normalize_team_record,numeric,integer,rate_per_hour,read_team_csv)

class MoneyPuckSourceCompatTests(unittest.TestCase):
    def test_numeric_percent(self):
        self.assertEqual(numeric("51.5%"),51.5)
        self.assertIsNone(numeric("N/A"))
        self.assertEqual(integer("9.8"),9)
    def test_5v5(self):
        row=normalize_team_record({
          "team":" bos ","situation":"5on5","gamesPlayed":"10",
          "iceTime":"120","shotsOnGoalFor":"60","shotsOnGoalAgainst":"50",
          "goalsFor":"5","goalsAgainst":"4",
          "xGoalsFor":"4.6","xGoalsAgainst":"4.2","xGoalsPercentage":"0.52"
        })
        self.assertEqual(row["team"],"BOS")
        self.assertEqual(row["situation"],"5on5")
        self.assertEqual(row["shots_for_60"],30)
        self.assertEqual(row["goals_for_60"],2.5)
        self.assertEqual(row["shooting_pct"],.0833)
        self.assertEqual(row["save_pct"],.92)
        self.assertEqual(row["x_goals_pct"],.52)
    def test_header_skipped(self):
        self.assertIsNone(normalize_team_record({"team":"team"}))
    def test_csv(self):
        rows=read_team_csv("team,situation,iceTime,xGoalsPercentage\n"
                           "NYR,5on5,300,0.51\n"
                           "BOS,all,200,0.49\n")
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["team"],"NYR")
    def test_no_raw_money_puck_external_data_required(self):
        self.assertIsNone(rate_per_hour("40",None))
        self.assertIsNone(rate_per_hour("-",40))
if __name__=="__main__":unittest.main()
