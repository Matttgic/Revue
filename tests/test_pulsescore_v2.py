"""Offline tests for PulseScore Pro normalized sportsbook feed integration."""
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from outils.pulsescore_v2 import (
    BOOKMAKERS,translate_market,translate_event,scan,_side,_request,
)
from outils.revue_engine_v2 import execute


NOW=datetime(2026,10,9,17,tzinfo=timezone.utc)
def when(d):return d.isoformat()


def event():
    return {
        "eventId":"ps-17","sport":"soccer","league":"England Premier League",
        "home":"Arsenal","away":"Leeds United","startTime":when(NOW+timedelta(hours=5)),
        "live":False,"markets":[
            {"canonicalMarket":"MATCH_RESULT","period":"FULL_TIME",
             "isActive":True,"rawName":"Full Time Result",
             "selections":[
                 {"canonicalOutcome":"HOME","odds":1.95,"isActive":True},
                 {"canonicalOutcome":"DRAW","odds":4.20,"isActive":True},
                 {"canonicalOutcome":"AWAY","odds":4.50,"isActive":True},
             ]},
            {"canonicalMarket":"OVER_UNDER","period":"FULL_TIME",
             "rawName":"Goals Over/Under","selections":[
                 {"canonicalOutcome":"OVER","line":2.5,"odds":2.10},
                 {"canonicalOutcome":"UNDER","line":2.5,"odds":1.75},
             ]},
        ]
    }


def models():
    return {"generated_at_utc":when(NOW-timedelta(minutes=7)),
            "competitions":{"PL":{"games":[{
                "event_id":"premier123","home":"Arsenal","away":"Leeds",
                "start_utc":when(NOW+timedelta(hours=5)),
                "status":"prototype_non_calibre",
                "probabilities":{"home_win_90":.64,"draw_90":.20,
                                 "away_win_90":.16,"over_2_5":.58}
            }]}}}


class PulseScoreTests(unittest.TestCase):
    def test_all_five_fr_feeds_declared(self):
        self.assertEqual(set(BOOKMAKERS),{"betclic_fr","winamax_fr","unibet_fr","netbet_fr","pmu_fr"})
        self.assertEqual(BOOKMAKERS["unibet_fr"],"unibet-fr")

    def test_canonical_side_names(self):
        self.assertEqual(_side("HOME","Arsenal","Leeds"),"Arsenal")
        self.assertEqual(_side("DRAW","Arsenal","Leeds"),"Draw")
        self.assertEqual(_side("UNDER","Arsenal","Leeds"),"Under")
        self.assertIsNone(_side("FIRST_GOAL","Arsenal","Leeds"))

    def test_market_convert_fulltime_h2h(self):
        translated=translate_market(event()["markets"][0],event(),NOW)
        self.assertEqual(translated["key"],"h2h")
        self.assertEqual([o["name"] for o in translated["outcomes"]],
                         ["Arsenal","Draw","Leeds United"])
        self.assertEqual(translated["observed_origin"],"fetch_observation")

    def test_totals_convert_same_line(self):
        market=translate_market(event()["markets"][1],event(),NOW)
        self.assertEqual(market["key"],"totals")
        self.assertEqual(len(market["outcomes"]),2)
        self.assertEqual(market["outcomes"][0]["point"],2.5)

    def test_reject_half_and_player(self):
        e=event()
        wrong=dict(e["markets"][1])
        wrong["period"]="FIRST_HALF"
        self.assertIsNone(translate_market(wrong,e,NOW))
        wrong["period"]="FULL_TIME"
        wrong["rawName"]="Player goals Over/Under"
        self.assertIsNone(translate_market(wrong,e,NOW))

    def test_late_or_live_refused(self):
        e=event()
        e["live"]=True
        self.assertIsNone(translate_event(e,"betclic_fr",NOW))
        e["live"]=False
        e["startTime"]=when(NOW-timedelta(minutes=4))
        self.assertIsNone(translate_event(e,"betclic_fr",NOW))

    def test_provider_last_update_kept(self):
        e=event()
        e["markets"][0]["updatedAt"]=when(NOW-timedelta(minutes=8))
        q=translate_event(e,"betclic_fr",NOW)
        self.assertEqual(q["bookmakers"][0]["markets"][0]["observed_origin"],"provider")
        self.assertEqual(q["bookmakers"][0]["markets"][0]["last_update"],when(NOW-timedelta(minutes=8)))

    def test_multiple_feeds_merge_into_revue_event(self):
        calls=[]
        def fake(book,sport,key,page):
            calls.append((book,sport,page))
            self.assertEqual(sport,"soccer")
            return [event()],False
        odds,meta=scan("secret",models(),NOW,fetch=fake,max_calls=32)
        self.assertEqual(meta["requests"],5)
        self.assertEqual(meta["matched_leagues"]["PL"],1)
        self.assertEqual(len(odds["PL"][0]["bookmakers"]),5)
        self.assertEqual(odds["PL"][0]["id"],"review:PL:premier123")

    def test_budget_cap_works(self):
        def fake(book,sport,key,page):
            return [event()],True
        odds,meta=scan("secret",models(),NOW,max_calls=3,fetch=fake)
        self.assertEqual(meta["requests"],3)
        self.assertTrue(meta["truncated"])

    def test_no_future_with_probability_means_no_calls(self):
        m=models()
        m["competitions"]["PL"]["games"][0]["probabilities"]=None
        with patch("outils.pulsescore_v2._request") as req:
            odds,meta=scan("secret",m,NOW)
            req.assert_not_called()
        self.assertEqual(meta["requests"],0)
        self.assertFalse(odds)

    def test_engine_prioritizes_pulse_over_other_api(self):
        one=translate_event(event(),"betclic_fr",NOW)
        with patch("outils.pulsescore_v2.scan",return_value=(
             {"PL":[one]}, {"requests":1,"errors":{},"matched_events":1})):
            with patch("outils.revue_engine_v2.download_odds") as odds_call:
                report,ledger=execute(models(),{"leagues":{}},{"version":1,"bets":[]},NOW,
                    api_key="other_test_secret",pulsescore_key="pulse_test_secret")
                odds_call.assert_not_called()
        self.assertEqual(report["odds_status"],"active_pulsescore")
        self.assertGreaterEqual(len(ledger["bets"]),1)
        self.assertTrue(all(b["status"]=="pending" for b in ledger["bets"]))

    def test_invalid_budget_refused(self):
        with self.assertRaises(ValueError):
            scan("secret",models(),NOW,max_calls=34,fetch=lambda *args:([],False))


if __name__=="__main__":
    unittest.main()
