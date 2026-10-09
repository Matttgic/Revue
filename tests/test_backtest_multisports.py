"""Tests anti-leakage for ESPN score-only chronological model evaluation."""
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from outils.backtest_multisports import score_league,_multiclass_brier,generate
from modeles.simulations.multisports_independant import LEAGUES,Event


class BacktestTests(unittest.TestCase):
    def setUp(self):
        self.base=datetime(2026,9,1,16,tzinfo=timezone.utc)
        self.league=next(l for l in LEAGUES if l.key=="PL")
        self.events=[
            Event(str(i),"PL",self.base+timedelta(days=i),
                  "h","a","Home","Away",True,2 if i%2 else 1,1 if i%2 else 2)
            for i in range(26)
        ]

    def test_multiclass_brier(self):
        self.assertAlmostEqual(_multiclass_brier([1/3]*3,0),2/3)
        self.assertEqual(_multiclass_brier([1,0,0],0),0)
        self.assertEqual(_multiclass_brier([1,0,0],2),2)

    def test_train_then_test(self):
        x=score_league(self.league,self.events,min_train=4)
        self.assertEqual(x["status"],"backtest_prototype")
        self.assertGreater(x["n"],1)
        self.assertTrue(x["log_loss"]>=0)

    def test_future_games_cannot_change_earlier_backtest(self):
        original=score_league(self.league,self.events,min_train=4)
        # This future result should not change earlier evaluated matches.
        later=Event("future","PL",self.base+timedelta(days=90),
                    "h","a","Home","Away",True,15,0)
        extra=score_league(self.league,self.events+[later],min_train=4)
        self.assertEqual(extra["n"],original["n"]+1)
        self.assertEqual(extra["first"],original["first"])

    def test_insufficient_history_yields_no_stats(self):
        out=score_league(self.league,self.events[:2],min_train=10)
        self.assertEqual(out["status"],"pas_assez_de_donnees")
        self.assertNotIn("brier",out)

    def test_result_cache_not_cote_data(self):
        raw=[{
            "id":e.id,"league":e.league,"start":e.start.isoformat(),
            "home_id":e.home_id,"away_id":e.away_id,
            "home":e.home,"away":e.away,
            "complete":e.complete,"home_score":e.home_score,
            "away_score":e.away_score
        } for e in self.events]
        rep=generate({"leagues":{"PL":{"events":raw}}})
        self.assertGreater(rep["leagues"]["PL"]["n"],0)
        self.assertIn("Pas de cote",rep["limits"])
        self.assertNotIn("ROI",rep["leagues"]["PL"])


if __name__=="__main__":
    unittest.main()
