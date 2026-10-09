"""Strict non-gambling unit tests of reconstructed Clairvoyance Python models."""
import unittest
from modeles.reproduction.clairvoyance_predictor import (
    Game, elo_home_probability,american_probability,american_quote,
    advantage_points, mlb, nhl,
)

class ReproductionTests(unittest.TestCase):
    def test_original_elo_neutral(self):
        self.assertGreater(elo_home_probability(1500,1500),.5)
        self.assertLess(elo_home_probability(1400,1600),.5)
        self.assertAlmostEqual(elo_home_probability(1500,1500,0),.5)

    def test_american_odds(self):
        self.assertAlmostEqual(american_probability(-150),.6)
        self.assertAlmostEqual(american_probability(+150),.4)
        self.assertEqual(american_quote(.6),-150)
        self.assertEqual(american_quote(.4),150)
        self.assertAlmostEqual(advantage_points(.6,150),20.)

    def test_original_mlb_elo_does_not_use_pitcher(self):
        game=Game("x","HOM","AWY",home_moneyline=-115,away_moneyline=110,
                  home_pitcher="P1",away_pitcher="P2")
        baseline=mlb(game,1520,1480)
        changed=mlb(Game(**{**game.__dict__,"home_pitcher":"OTHER"}),1520,1480)
        self.assertEqual(baseline["model_home_win_prob"],changed["model_home_win_prob"])
        self.assertNotEqual(baseline["home_pitcher"],changed["home_pitcher"])

    def test_original_nhl_goalie_not_confirmed(self):
        game=Game("nhl","HOM","AWY",home_moneyline=115,away_moneyline=-105)
        raw=nhl(game,1500,1500)
        weighted=nhl(game,1500,1500,55,50,.92,.90)
        self.assertGreater(weighted["model_home_win_prob"],raw["model_home_win_prob"])
        self.assertEqual(weighted["home_goalie_sv_pct"],.92)

    def test_mlb_missing_odds_gives_no_pick(self):
        result=mlb(Game("abc","A","B"),1500,1500)
        self.assertIsNone(result["recommendation"])
        self.assertIsNone(result["edge_pct"])

    def test_nhl_bounded_probability(self):
        a=nhl(Game("g","A","B"),1600,1400,100,1,.99,.75)
        b=nhl(Game("g","A","B"),1400,1600,1,100,.75,.99)
        self.assertEqual(a["model_home_win_prob"],.95)
        self.assertEqual(b["model_home_win_prob"],.05)

    def test_original_home_recommendation_precedence(self):
        # A deliberately wide overround can make both 'edges' look positive,
        # reproducing the reference's home-first branching exactly.
        g=Game("x","HOM","AWY",home_moneyline=250,away_moneyline=250)
        result=mlb(g,1500,1500)
        self.assertEqual(result["recommendation"],"HOM ML")

    def test_no_direct_use_of_live_betting(self):
        g=Game("x","A","B",home_moneyline=-110,away_moneyline=105)
        result=nhl(g)
        self.assertNotIn("placed",str(result).lower())
        self.assertNotIn("stake",str(result).lower())

if __name__=="__main__":
    unittest.main()
