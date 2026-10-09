import unittest
from datetime import datetime,timedelta,timezone
from modeles.simulations.equipes_avance_multisports import (
    SPORTS,history_before,predict,score_metrics,evaluate,build)
from modeles.simulations.multisports_independant import Event,_cache_event
NOW=datetime(2026,10,9,18,tzinfo=timezone.utc)
def fixture(i,day,league="NBA",score=(102,94)):
    return Event(str(i),league,NOW+timedelta(days=day),"h","a","Home","Away",
                 score is not None,score[0] if score else None,
                 score[1] if score else None)
def games(n=20,league="NBA"):
    return [fixture(i,-n+i,league,(90+i%15,85+i%9)) for i in range(n)]
class MultiTeamTests(unittest.TestCase):
    def test_league_cover(self):
        self.assertEqual(set(SPORTS),{"NBA","WNBA","NCAAB","NFL","MLB"})
    def test_cfb_not_in_experimental_models(self):
        self.assertNotIn("CFB", SPORTS)
    def test_history_lag(self):
        g=fixture(1,-.1)
        self.assertEqual(history_before([g],"NBA",NOW),[])
        self.assertEqual(len(history_before([fixture(2,-1)],"NBA",NOW)),1)
    def test_no_early_history(self):
        x=predict("NBA",[],fixture(99,1,score=None),NOW)
        self.assertIsNone(x["probabilities"])
    def test_probabilities_normalized(self):
        for league in SPORTS:
            x=predict(league,games(20,league),fixture(99,1,league,None),NOW)
            self.assertEqual(x["status"],"shadow_non_calibre")
            self.assertAlmostEqual(sum(x["probabilities"].values()),1,places=4)
            self.assertTrue(0<x["probabilities"]["home_win"]<1)
    def test_future_result_no_leak(self):
        t=fixture(99,1,score=None)
        before=predict("NBA",games(20),t,NOW)
        evil=fixture(555,5,score=(999,0))
        after=predict("NBA",games(20)+[evil],t,NOW)
        self.assertEqual(before,after)
    def test_ties_do_not_contribute_two_way_grade(self):
        x=evaluate("NFL",[fixture(i,-20+i,"NFL",(12,12)) for i in range(20)])
        self.assertEqual(x["n"],0)
    def test_brier_logloss_sane(self):
        x=score_metrics([(.9,1),(.7,1),(.2,0)])
        self.assertTrue(x["brier_binary"]<.1)
        self.assertTrue(x["logloss_binary"]>0)
    def test_backtest_when_enough_history(self):
        x=evaluate("NBA",games(35))
        self.assertGreater(x["n"],0)
        self.assertIn("baseline",x)
        self.assertNotIn("roi",str(x).lower())
    def test_build_real_cache_shape(self):
        cache={"leagues":{"NBA":{"events":[_cache_event(x) for x in
               games(20)+[fixture(99,1,score=None)]]}}}
        report=build(cache,NOW,days=3)
        self.assertEqual(report["leagues"]["NBA"]["games"][0]["status"],"shadow_non_calibre")
        self.assertEqual(report["leagues"]["MLB"]["games"],[])
        self.assertEqual(report["mode"],"SHADOW_NO_BET")
    def test_reject_naive_clock(self):
        with self.assertRaises(ValueError):
            build({},datetime(2026,10,9,12))
    def test_reject_unknown_sport(self):
        with self.assertRaises(ValueError):
            predict("LIGUE1",[],fixture(99,1),NOW)
if __name__=="__main__":unittest.main()
