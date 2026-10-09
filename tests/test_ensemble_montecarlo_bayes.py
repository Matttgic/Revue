"""Deterministic independent MC/Bayesian ensemble tests (no network)."""
import unittest
from datetime import datetime,timedelta,timezone
from modeles.simulations.ensemble_montecarlo_bayes import (
    MODEL,SIMULATIONS,WEIGHTS,predict,evaluate,build,_montecarlo)
from modeles.simulations.multisports_independant import Event,_cache_event

NOW=datetime(2026,10,9,21,tzinfo=timezone.utc)
def fixture(i,day,league="NFL",score=(24,17),home="101",away="102"):
    start=NOW+timedelta(days=day)
    return Event(str(i),league,start,str(home),str(away),
                 "Home","Away",score is not None,
                 None if score is None else score[0],
                 None if score is None else score[1])

def history(n=30,lg="NFL"):
    return [fixture(i,-n+i,lg,(19+i%13,16+i%9)) for i in range(n)]

class MonteCarloEnsembleTests(unittest.TestCase):
    def test_weights_normalized(self):
        self.assertAlmostEqual(sum(WEIGHTS.values()),1.)

    def test_invalid_sport_excluded(self):
        with self.assertRaises(ValueError):
            predict("CFB",[],fixture(99,1),NOW)

    def test_insufficient_training_no_fake_probability(self):
        p=predict("NBA",[],fixture(99,1,"NBA",None),NOW)
        self.assertEqual(p["status"],"insufficient_history")
        self.assertIsNone(p["probabilities"])

    def test_mc_repeat_is_deterministic(self):
        ev=history()
        candidate=fixture(99,1,"NFL",None)
        a=predict("NFL",ev,candidate,NOW)
        b=predict("NFL",list(reversed(ev)),candidate,NOW)
        self.assertEqual(a,b)
        self.assertEqual(a["components"]["iterations"],SIMULATIONS)
        self.assertAlmostEqual(sum(a["probabilities"].values()),1.,places=4)
        self.assertEqual(a["model"],MODEL)

    def test_future_results_not_used(self):
        candidate=fixture(99,1,"NFL",None)
        base=predict("NFL",history(),candidate,NOW)
        poison=fixture(200,2,"NFL",(105,0))
        after=predict("NFL",history()+[poison],candidate,NOW)
        self.assertEqual(base,after)

    def test_same_day_games_excluded_by_lag(self):
        candidate=fixture(99,1,"NFL",None)
        base=predict("NFL",history(),candidate,NOW)
        poison=fixture(200,-.1,"NFL",(105,0))
        after=predict("NFL",history()+[poison],candidate,NOW)
        self.assertEqual(base,after)

    def test_pre_match_clock_required(self):
        candidate=fixture(99,1,"NFL",None)
        with self.assertRaises(ValueError):
            predict("NFL",history(),candidate,candidate.start)
        with self.assertRaises(ValueError):
            predict("NFL",history(),candidate,datetime(2026,10,9))

    def test_sport_variants_probabilities(self):
        for league in ("NBA","WNBA","NCAAB","NFL","MLB"):
            with self.subTest(league=league):
                ev=history(24,league)
                p=predict(league,ev,fixture(99,1,league,None),NOW)
                self.assertEqual(p["status"],"shadow_non_calibre")
                ps=p["probabilities"]
                self.assertAlmostEqual(ps["home_win"]+ps["away_win"],1,places=4)
                self.assertTrue(0<ps["home_win"]<1)
                self.assertTrue(0<p["components"]["monte_carlo"]<1)
                self.assertIsNone(p.get("odds"))
                self.assertNotIn("profit",str(p).lower())

    def test_mc_min_iterations(self):
        p=fixture(99,1,"NFL",None)
        rows={"101":[(20.,13.)]*12,"102":[(14.,22.)]*12}
        with self.assertRaises(ValueError):
            _montecarlo("NFL",p,rows,21,1,samples=50)

    def test_walk_forward_three_models_common_sample(self):
        report=evaluate("NFL",history(36))
        self.assertGreater(report["n"],0)
        self.assertEqual(set(report["scores"]),
                         {"baseline","previous_shadow","ensemble"})
        self.assertGreaterEqual(report["scores"]["ensemble"]["brier_binary"],0)
        self.assertIn("delta_brier_vs_baseline",report)
        self.assertNotIn("roi",report)

    def test_tied_game_not_binary_settled(self):
        tied=[fixture(i,-20+i,"NFL",(17,17)) for i in range(20)]
        self.assertEqual(evaluate("NFL",tied)["n"],0)

    def test_build_compatible_with_existing_history(self):
        ev=history(30,"MLB")
        future=fixture("x",1,"MLB",None)
        data=build({"leagues":{"MLB":{"events":[_cache_event(e) for e in ev+[future]]}}},NOW)
        self.assertEqual(data["status"],"experimental_no_bets")
        self.assertEqual(data["exclusions"],["CFB"])
        self.assertEqual(len(data["leagues"]["MLB"]["games"]),1)
        self.assertTrue(data["leagues"]["MLB"]["games"][0]["probabilities"])
        self.assertNotIn("CFB",data["leagues"])

if __name__=="__main__":
    unittest.main()
