import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from modeles.simulations.nba_prior_espn import (
    parse_standings, previous_season_end_year, predict_nba, _prior_team
)
from modeles.simulations.multisports_independant import Event,_cache_event
NOW=datetime(2026,10,9,22,tzinfo=timezone.utc)

def raw_data():
    entries=[]
    for i in range(1,31):
        stats=[
            {"name":"wins","value":50 if i%2 else 30},
            {"name":"losses","value":32 if i%2 else 52},
            {"name":"avgPointsFor","value":117.0 if i%2 else 109.0},
            {"name":"avgPointsAgainst","value":108.5 if i%2 else 115.0},
            {"name":"differential","value":8.5 if i%2 else -6.0},
        ]
        entries.append({"team":{"id":str(i),"displayName":f"Team {i}","abbreviation":f"T{i}"},"stats":stats})
    return {"children":[{"standings":{"entries":entries[:15]}},
                        {"standings":{"entries":entries[15:]}}]}

def game(id,day,complete=False,h=1,a=2,hs=113,ats=100):
    return Event(str(id),"NBA",NOW+timedelta(days=day),str(h),str(a),
                 f"Team {h}",f"Team {a}",complete,hs if complete else None,
                 ats if complete else None)

class NBAESPNSnapshotTests(unittest.TestCase):
    def test_previous_nba_season_rollover(self):
        self.assertEqual(previous_season_end_year(NOW),2026)
        self.assertEqual(previous_season_end_year(datetime(2027,3,3,tzinfo=timezone.utc)),2026)
        self.assertEqual(previous_season_end_year(datetime(2027,10,3,tzinfo=timezone.utc)),2027)

    def test_parse_complete_standings(self):
        report=parse_standings(raw_data(),2026,NOW)
        self.assertEqual(len(report["teams"]),30)
        self.assertEqual(report["teams"]["1"]["wins"],50)
        self.assertEqual(report["teams"]["1"]["margin"],8.5)
        self.assertEqual(report["teams"]["2"]["margin"],-6.)
        self.assertEqual(report["status"],"real_previous_season_aggregate")

    def test_reject_partial_standings(self):
        broken=raw_data()
        broken["children"]=broken["children"][:1]
        with self.assertRaises(ValueError):
            parse_standings(broken,2026,NOW)

    def test_early_season_forecasts_from_prior_without_current_games(self):
        prior=parse_standings(raw_data(),2026,NOW-timedelta(minutes=10))
        cache={"leagues":{"NBA":{"events":[_cache_event(game(99,1))]}}}
        forecast=predict_nba(prior,cache,NOW)
        self.assertEqual(forecast["ready"],1)
        rec=forecast["matches"][0]
        self.assertEqual(rec["current_games"],{"home":0,"away":0})
        self.assertEqual(rec["status"],"shadow_prior_not_calibrated")
        self.assertAlmostEqual(sum(rec["probabilities"].values()),1,places=4)
        self.assertGreater(rec["probabilities"]["home_win"],.5)
        self.assertEqual(rec["previous_season"],2026)

    def test_future_publication_refused(self):
        future=parse_standings(raw_data(),2026,NOW+timedelta(hours=1))
        self.assertIsNone(_prior_team(future,"1",NOW))
        pred=predict_nba(future,{"leagues":{"NBA":{"events":[_cache_event(game(99,1))]}}},NOW)
        self.assertEqual(pred["ready"],0)

    def test_older_or_wrong_prior_rejected(self):
        stale=parse_standings(raw_data(),2026,NOW-timedelta(days=34))
        self.assertIsNone(_prior_team(stale,"1",NOW))
        other=parse_standings(raw_data(),2025,NOW-timedelta(days=1))
        self.assertIsNone(_prior_team(other,"1",NOW))

    def test_current_games_update_strength_without_future_leak(self):
        prior=parse_standings(raw_data(),2026,NOW-timedelta(hours=1))
        past=[game(i,-10+i*.4,True,1,2,121,101) for i in range(10)]
        future=game(99,1)
        cache={"leagues":{"NBA":{"events":[_cache_event(e) for e in past+[future]]}}}
        a=predict_nba(prior,cache,NOW)
        self.assertEqual(a["matches"][0]["current_games"],{"home":10,"away":10})
        cache["leagues"]["NBA"]["events"].append(_cache_event(game(987,5,True,1,2,180,0)))
        b=predict_nba(prior,cache,NOW)
        self.assertEqual(a,b)

    def test_no_priors_does_not_invent_scores(self):
        cache={"leagues":{"NBA":{"events":[_cache_event(game(99,1))]}}}
        pred=predict_nba({},cache,NOW)
        self.assertIsNone(pred["matches"][0]["probabilities"])
        self.assertEqual(pred["ready"],0)

    def test_reject_unsupported_clock(self):
        with self.assertRaises(ValueError):
            predict_nba({},{"leagues":{}},datetime(2026,10,9))
if __name__=="__main__":
    unittest.main()
