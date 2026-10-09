"""Offline tests for real-ESPN-feature extraction with point-in-time provenance."""
import unittest
from datetime import datetime,timedelta,timezone
from modeles.simulations.football_espn_statistiques import (
    numeric,extract_boxscore,update_cache,calculate_team_features,build
)
from modeles.simulations.football_avance_independant import predict
from modeles.simulations.multisports_independant import Event

NOW=datetime(2026,10,9,20,tzinfo=timezone.utc)
def iso(d):return d.isoformat()
def make_stats(shots=15,sot=7):
    return {"boxscore":{"teams":[
        {"team":{"id":"100"},"statistics":[
            {"name":"totalShots","displayValue":str(shots)},
            {"name":"shotsOnTarget","displayValue":str(sot)},
            {"name":"possessionPct","displayValue":"57.1%"},
            {"name":"totalPasses","displayValue":"468"},
            {"name":"interceptions","displayValue":"12"},
        ]},
        {"team":{"id":"200"},"statistics":[
            {"name":"totalShots","displayValue":"11"},
            {"name":"shotsOnTarget","displayValue":"4"},
            {"name":"possessionPct","displayValue":"42.9%"},
            {"name":"totalPasses","displayValue":"401"},
            {"name":"interceptions","displayValue":"18"},
        ]}
    ]}}
def make_history(n=4):
    games=[]
    for i in range(n):
        games.append({"id":str(200+i),"league":"PL",
                      "start":iso(NOW-timedelta(days=5+i)),
                      "home_id":"100","away_id":"200",
                      "home":"Home","away":"Away",
                      "complete":True,"home_score":2,"away_score":1})
    return {"leagues":{"PL":{"events":games}}}
def make_future():
    return Event("500","PL",NOW+timedelta(days=1),"100","200",
                 "Home","Away",False,None,None)
def make_events():
    return [Event(str(300+i),"PL",NOW-timedelta(days=7+i),"100","200",
                "Home","Away",True,2,1) for i in range(6)]


class ESPNAdvancedTests(unittest.TestCase):
    def test_numeric_percent(self):
        self.assertEqual(numeric("49.5%"),49.5)
        self.assertIsNone(numeric("—"))
        self.assertIsNone(numeric("nan"))

    def test_exact_both_teams(self):
        rows=extract_boxscore(make_stats(),"100","200")
        self.assertEqual(rows["home"]["totalShots"],15.)
        self.assertEqual(rows["away"]["shotsOnTarget"],4.)
        self.assertEqual(rows["home"]["possessionPct"],57.1)
        self.assertIsNone(extract_boxscore(make_stats(),"999","200"))

    def test_shots_on_target_cannot_exceed_shots(self):
        self.assertIsNone(extract_boxscore(make_stats(shots=4,sot=8),"100","200"))

    def test_completed_events_only_and_budget(self):
        called=[]
        def fake(league,event):
            called.append(event)
            return make_stats()
        cache,status=update_cache(make_history(4),{"events":{}},NOW,
                                  fetch=fake,max_calls=3)
        self.assertEqual(len(called),3)
        self.assertEqual(status["cached_games"],3)
        self.assertEqual(status["responses_parsed"],3)
        self.assertEqual(status["errors"],{})

    def test_repeat_scan_reuses_previous(self):
        def fake(*args):return make_stats()
        cache1,_=update_cache(make_history(3),{},NOW,fetch=fake,max_calls=3)
        cache2,status=update_cache(make_history(3),cache1,NOW+timedelta(hours=1),
                                    fetch=lambda *x:self.fail("Should use cache"),
                                    max_calls=3)
        self.assertEqual(status["calls_attempted"],0)
        self.assertEqual(len(cache2["events"]),3)

    def test_minimum_three_games_per_team(self):
        cache,_=update_cache(make_history(2),{},NOW,fetch=lambda *x:make_stats(),max_calls=2)
        self.assertFalse(calculate_team_features(cache,NOW,min_games=3))
        cache,_=update_cache(make_history(4),cache,NOW,fetch=lambda *x:make_stats(),max_calls=4)
        f=calculate_team_features(cache,NOW)
        self.assertEqual(len(f),2)
        self.assertEqual(f["PL:100"]["games"],4)
        self.assertEqual(f["PL:100"]["sot_allowed_per_game"],4)
        self.assertEqual(f["PL:200"]["shots_allowed_per_game"],15)

    def test_future_observation_not_used_in_historical_prediction(self):
        cache,_=update_cache(make_history(4),{},NOW,fetch=lambda *x:make_stats(),max_calls=4)
        old=calculate_team_features(cache,NOW-timedelta(days=1))
        self.assertEqual(old,{})
        self.assertTrue(calculate_team_features(cache,NOW))

    def test_derived_shots_are_not_false_xg(self):
        cache,report=build(make_history(4),{},NOW,fetch=lambda *x:make_stats(),max_calls=4)
        self.assertFalse(report["xg_available"])
        self.assertFalse(report["opta_available"])
        self.assertEqual(report["statistics"]["responses_parsed"],4)
        self.assertEqual(len(report["teams"]),2)

    def test_football_uses_genuine_espn_aggregate(self):
        cache,report=build(make_history(4),{},NOW,fetch=lambda *x:make_stats(),max_calls=4)
        # Match stats become usable only AFTER their observation time.
        at=NOW+timedelta(minutes=1)
        shadow=predict("PL",make_events(),make_future(),at,
                       espn_features=report["teams"])
        base=predict("PL",make_events(),make_future(),at)
        self.assertTrue(shadow["espn_stats_used"])
        self.assertFalse(shadow["xg_used"])
        self.assertNotEqual(shadow["probabilities"],base["probabilities"])

    def test_spoofed_espn_xg_is_rejected(self):
        _,report=build(make_history(4),{},NOW,fetch=lambda *x:make_stats(),max_calls=4)
        fake=report["teams"].copy()
        for key in fake:
            fake[key]={**fake[key],"type":"Opta xG"}
        pred=predict("PL",make_events(),make_future(),NOW,espn_features=fake)
        self.assertFalse(pred["espn_stats_used"])

    def test_expired_public_observation_is_ignored(self):
        _,report=build(make_history(4),{},NOW,fetch=lambda *x:make_stats(),max_calls=4)
        old={k:{**v,"published_at":iso(NOW-timedelta(days=17))} for k,v in report["teams"].items()}
        pred=predict("PL",make_events(),make_future(),NOW,espn_features=old)
        self.assertFalse(pred["espn_stats_used"])


if __name__=="__main__":
    unittest.main()
