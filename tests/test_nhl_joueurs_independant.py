"""Tests offline du modèle de profils NHL; aucune donnée fictive utilisée en production."""
import unittest
from datetime import datetime,timedelta,timezone
from modeles.simulations.nhl_joueurs_independant import (
    profile,parse_rows,poisson_over,run,score_player,season_id,
)


class TestNHLJoueurs(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,9,15,tzinfo=timezone.utc)
        self.previous=[
            {"playerId":101,"skaterFullName":"Test Forward","teamAbbrevs":"BOS",
             "gamesPlayed":80,"goals":40,"assists":35,"points":75,"shots":280},
            {"playerId":102,"skaterFullName":"Test Forward II","teamAbbrevs":"NYR",
             "gamesPlayed":80,"goals":16,"assists":20,"points":36,"shots":160},
            {"playerId":103,"skaterFullName":"Old Team","teamAbbrevs":"BOS",
             "gamesPlayed":40,"goals":10,"assists":15,"points":25,"shots":90}
        ]
        self.current=[
            {"playerId":101,"skaterFullName":"Test Forward","teamAbbrevs":"BOS",
             "gamesPlayed":2,"goals":1,"assists":1,"points":2,"shots":8},
            {"playerId":103,"skaterFullName":"Old Team","teamAbbrevs":"MTL",
             "gamesPlayed":2,"goals":0,"assists":0,"points":0,"shots":3},
        ]

    def test_parse_stats_and_teams(self):
        rows=parse_rows(self.previous)
        self.assertEqual(rows["101"]["goals"],40)
        self.assertIn("BOS",rows["101"]["teams"])

    def test_season_year(self):
        self.assertEqual(season_id(self.now),20262027)

    def test_shrinkage_uses_previous_data(self):
        previous=parse_rows(self.previous)["101"]
        current=parse_rows(self.current)["101"]
        p=profile(previous,current)
        self.assertGreater(p["goals"],.1)
        self.assertLess(p["goals"],.9)
        self.assertAlmostEqual(p["goals"],(1+16*.5)/18)

    def test_poisson_anytime_goal_and_shots(self):
        self.assertAlmostEqual(poisson_over(0,.5),0)
        self.assertGreater(poisson_over(3,1.5),poisson_over(3,3.5))

    def test_invalid_line_is_refused(self):
        with self.assertRaises(ValueError):
            poisson_over(3,2)
        with self.assertRaises(ValueError):
            poisson_over(-1,.5)

    def test_player_is_not_claimed_confirmed(self):
        p=score_player(parse_rows(self.previous)["101"],parse_rows(self.current)["101"],"BOS")
        self.assertEqual(p["availability"],"NON_VERIFIEE")
        self.assertTrue(p["current_team_observed"])
        self.assertIn("but",p["metrics"])

    def test_old_team_not_trusted_if_transfer(self):
        prev=parse_rows(self.previous)["103"]
        curr=parse_rows(self.current)["103"]
        self.assertIsNone(score_player(prev,curr,"BOS"))

    def test_prior_only_teams_still_unverified(self):
        prev=parse_rows(self.previous)["102"]
        p=score_player(prev,None,"NYR")
        self.assertFalse(p["current_team_observed"])

    def test_end_to_end_filters_future_team(self):
        fixtures={"games":[
            {"event_id":"123","home":"BOS","away":"NYR",
             "start_utc":(self.now+timedelta(days=1)).isoformat()},
            {"event_id":"124","home":"DET","away":"SEA",
             "start_utc":(self.now-timedelta(days=1)).isoformat()}
        ]}
        result=run(fixtures,self.previous,self.current,self.now)
        self.assertEqual(sorted(result["teams"]),["BOS","NYR"])
        self.assertEqual(result["teams"]["BOS"][0]["name"],"Test Forward")
        self.assertNotIn("DET",result["teams"])

    def test_no_fake_players_if_none_known(self):
        res=run({"games":[{"event_id":1,"home":"BOS","away":"NYR",
                             "start_utc":(self.now+timedelta(days=1)).isoformat()}]},
                [],[],self.now)
        self.assertEqual(res["teams"]["BOS"],[])


if __name__=="__main__":
    unittest.main()
