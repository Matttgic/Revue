"""Independent football advanced shadow model tests, no licensed datasets copied."""
import unittest
from datetime import datetime,timedelta,timezone
from dataclasses import replace
from modeles.simulations.multisports_independant import Event,_cache_event
from modeles.simulations.football_avance_independant import (
    validate_licensed_snapshots,feature_at,_dixon_coles,
    predict,evaluate,build
)


NOW=datetime(2026,10,9,12,tzinfo=timezone.utc)
def game(id,day,h="100",a="200",hs=2,ats=1,league="PL"):
    return Event(str(id),league,NOW+timedelta(days=day),
                 str(h),str(a),"Home","Away",hs is not None,
                 hs,ats)
def histories(n=18):
    return [game(i,-n+i,hs=(i%4),ats=((i+1)%3)) for i in range(n)]


class FootballAdvancedTests(unittest.TestCase):
    def test_probabilities_sum_to_one(self):
        p=_dixon_coles(1.7,1.15)
        self.assertAlmostEqual(sum(p[:3]),1,places=8)
        self.assertTrue(all(0<=v<=1 for v in p))

    def test_draw_adjustment_matters(self):
        a=_dixon_coles(1.2,1.2,rho=0)
        b=_dixon_coles(1.2,1.2,rho=-.06)
        self.assertNotAlmostEqual(a[1],b[1])

    def test_authorization_required(self):
        index,status=validate_licensed_snapshots({
            "authorized":False,"permission_reference":"someone","snapshots":[]})
        self.assertEqual(index,{})
        self.assertEqual(status["status"],"no_authorized_source")

    def test_invalid_feature_rejected(self):
        index,status=validate_licensed_snapshots({
            "authorized":True,"permission_reference":"valid agreement",
            "snapshots":[{"league":"PL","team_id":"100",
                          "games":-50,"xg_for_per90":2,
                          "xg_against_per90":.9,"power_rating":90,
                          "published_at":NOW.isoformat(),"source":"test"}]})
        self.assertEqual(index,{})
        self.assertEqual(status["rejected"],1)

    def test_stale_features_refused(self):
        raw={"authorized":True,"permission_reference":"contract",
             "snapshots":[{"league":"PL","team_id":"100","games":20,
                "xg_for_per90":2.2,"xg_against_per90":1.0,
                "power_rating":80,"published_at":(NOW-timedelta(days=20)).isoformat(),"source":"test"}]}
        index,_=validate_licensed_snapshots(raw)
        self.assertIsNone(feature_at(index,"PL","100",NOW))

    def test_no_lookahead_feature_refused(self):
        raw={"authorized":True,"permission_reference":"contract",
             "snapshots":[{"league":"PL","team_id":"100","games":20,
                "xg_for_per90":3.0,"xg_against_per90":.5,
                "power_rating":98,"published_at":(NOW+timedelta(minutes=1)).isoformat(),"source":"test"}]}
        index,_=validate_licensed_snapshots(raw)
        self.assertIsNone(feature_at(index,"PL","100",NOW))

    def test_no_fake_prediction_without_history(self):
        g=game("f",1,hs=None,ats=None)
        x=predict("PL",[],g,NOW)
        self.assertIsNone(x["probabilities"])
        self.assertEqual(x["status"],"historique_insuffisant")

    def test_scores_only_prediction(self):
        future=game("f",1,hs=None,ats=None)
        p=predict("PL",histories(),future,NOW)
        self.assertFalse(p["xg_used"])
        self.assertEqual(p["status"],"shadow_non_calibre")
        q=p["probabilities"]
        self.assertAlmostEqual(q["home_win_90"]+q["draw_90"]+q["away_win_90"],1,places=4)
        self.assertTrue(0<q["over_2_5"]<1)

    def test_licensed_features_change_output_and_are_attributed(self):
        fixtures=histories()
        future=game("next",1,hs=None,ats=None)
        base=predict("PL",fixtures,future,NOW)
        raw={"authorized":True,"permission_reference":"test private",
             "snapshots":[]}
        for team,xg,power in (("100",3.1,95),("200",.85,30)):
            raw["snapshots"].append({"league":"PL","team_id":team,"games":20,
                "xg_for_per90":xg,"xg_against_per90":1,
                "power_rating":power,"published_at":(NOW-timedelta(days=1)).isoformat(),"source":"test"})
        index,_=validate_licensed_snapshots(raw)
        out=predict("PL",fixtures,future,NOW,index)
        self.assertTrue(out["xg_used"])
        self.assertNotEqual(out["probabilities"],base["probabilities"])
        self.assertIn("features_published_at",out)

    def test_one_team_feature_no_partial_blend(self):
        fixtures=histories()
        future=game("next",1,hs=None,ats=None)
        raw={"authorized":True,"permission_reference":"test",
             "snapshots":[{"league":"PL","team_id":"100","games":20,
                "xg_for_per90":3.1,"xg_against_per90":1,
                "power_rating":95,"published_at":(NOW-timedelta(days=1)).isoformat(),"source":"test"}]}
        index,_=validate_licensed_snapshots(raw)
        out=predict("PL",fixtures,future,NOW,index)
        self.assertFalse(out["xg_used"])

    def test_post_kickoff_result_does_not_affect_previous(self):
        future=game("future",1,hs=None,ats=None)
        hist=histories()
        base=predict("PL",hist,future,NOW)
        later=game("after",5,hs=25,ats=0)
        other=predict("PL",hist+[later],future,NOW)
        self.assertEqual(base,other)

    def test_build_from_real_cache_schema(self):
        past=histories()
        fixture=game("future",1,hs=None,ats=None)
        cache={"leagues":{"PL":{"events":[_cache_event(e) for e in past+[fixture]]}}}
        r=build(cache,{},NOW,3)
        self.assertEqual(r["licensed_advanced_features"]["status"],"no_authorized_source")
        self.assertEqual(r["competitions"]["PL"]["games"][0]["status"],"shadow_non_calibre")
        self.assertEqual(r["status"],"shadow_experimental_never_auto_bet")

    def test_brier_walk_forward_never_claims_roi(self):
        x=evaluate("PL",histories(28))
        if x["n"]:
            self.assertGreaterEqual(x["shadow"]["brier"],0)
            self.assertIn("baseline",x)
            self.assertNotIn("roi",x)


if __name__=="__main__":
    unittest.main()
