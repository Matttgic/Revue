"""Offline tests for PulseScore Pro normalized sportsbook feed integration."""
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
from outils.collecte.pulsescore_v2 import (
    BOOKMAKERS,MAX_CALLS,MIN_INTERVAL_PER_BOOK,REFERENCE_BOOKS,
    translate_market,translate_event,scan,_side,_request,
)
from outils.suivi.revue_engine_v2 import execute,FR_BOOKS


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
        self.assertEqual(set(BOOKMAKERS),{"betclic_fr","winamax_fr","unibet_fr","pmu_fr"})
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
        with patch("outils.collecte.pulsescore_v2._request") as req, \
             patch("outils.collecte.pulsescore_v2._get_json") as catalogue:
            odds,meta=scan("secret",m,NOW)
            req.assert_not_called()
            catalogue.assert_not_called()
        self.assertEqual(meta["requests"],0)
        self.assertFalse(odds)

    def test_engine_prioritizes_pulse_over_other_api(self):
        one=translate_event(event(),"betclic_fr",NOW)
        sharp=event()
        sharp["markets"]=[{**sharp["markets"][0],"selections":[
            {"canonicalOutcome":"HOME","odds":1.80},{"canonicalOutcome":"DRAW","odds":3.90},
            {"canonicalOutcome":"AWAY","odds":4.80}]}]
        one["bookmakers"]+=translate_event(sharp,"ps3838",NOW)["bookmakers"]
        with patch("outils.collecte.pulsescore_v2.scan",return_value=(
             {"PL":[one]}, {"requests":1,"errors":{},"matched_events":1})):
            with patch("outils.suivi.revue_engine_v2.download_odds") as odds_call:
                report,ledger=execute(models(),{"leagues":{}},{"version":1,"bets":[]},NOW,
                    api_key="other_test_secret",pulsescore_key="pulse_test_secret")
                odds_call.assert_not_called()
        self.assertEqual(report["odds_status"],"active_pulsescore")
        self.assertGreaterEqual(len(ledger["bets"]),1)
        self.assertTrue(all(b["status"]=="pending" for b in ledger["bets"]))

    def test_invalid_budget_refused(self):
        with self.assertRaises(ValueError):
            scan("secret",models(),NOW,max_calls=MAX_CALLS+1,fetch=lambda *args:([],False))


    def test_balanced_radar_fairly_covers_three_sports_with_eight_calls(self):
        m=models()
        for league,delta in (("NHL",3),("NFL",4)):
            m["competitions"][league]={"games":[{
                "event_id":league+"-fixture","home":"Home","away":"Away",
                "start_utc":when(NOW+timedelta(hours=delta)),
                "status":"prototype_non_calibre",
                "probabilities":{"home_win":.55,"away_win":.45}
            }]}
        calls=[]
        def fake(book,sport,key,page):
            calls.append((sport,book,page))
            return [],False
        odds,summary=scan("safe-test",m,NOW,max_calls=8,days_horizon=6,
                          fetch=fake,balanced=True)
        self.assertEqual(summary["requests"],8)
        self.assertEqual(summary["allocation_mode"],"sport_balanced")
        self.assertEqual(len(summary["calls_by_sport"]),3)
        self.assertEqual(sorted(summary["calls_by_sport"].values()),[2,3,3])
        self.assertEqual(set(summary["calls_by_sport"]),{"soccer","ice-hockey","american-football"})
        self.assertEqual(odds,{})
        self.assertTrue(summary["truncated"])
        calls.clear()
        _,original=scan("safe-test",m,NOW,max_calls=8,days_horizon=6,fetch=fake)
        self.assertEqual(original["allocation_mode"],"sport_priority")
        self.assertEqual(original["requests"],8)
        self.assertLess(len(original["calls_by_sport"]),3)



class ReferenceAndPacingTests(unittest.TestCase):
    def test_ps3838_is_reference_only_and_feeds_sharp_probability(self):
        def fake(book,sport,key,page):
            e=event()
            if book=="ps3838":
                # Autre graphie d'équipe : la correspondance doit rester souple.
                e={**e,"eventId":"ps3838-1","home":"Arsenal FC"}
                e["markets"]=[{**e["markets"][0],"selections":[
                    {"canonicalOutcome":"HOME","odds":1.80},
                    {"canonicalOutcome":"DRAW","odds":3.90},
                    {"canonicalOutcome":"AWAY","odds":4.80}]}]
            return [e],False
        odds,meta=scan("secret",models(),NOW,fetch=fake)
        self.assertEqual(set(REFERENCE_BOOKS),{"ps3838"})
        self.assertNotIn("ps3838",FR_BOOKS)
        self.assertEqual(meta["matched_by_book"].get("ps3838"),1)
        self.assertIn("ps3838",{b["key"] for b in odds["PL"][0]["bookmakers"]})
        with patch("outils.collecte.pulsescore_v2.scan",return_value=(odds,meta)):
            report,ledger=execute(models(),{"leagues":{}},{"version":1,"bets":[]},NOW,
                                  pulsescore_key="pulse_test_secret")
        cands=report["candidates"]
        self.assertTrue(cands)
        self.assertTrue(all(c["bookmaker"] in FR_BOOKS for c in cands))
        self.assertTrue(all(b["bookmaker"] in FR_BOOKS for b in ledger["bets"]))
        home=[c for c in cands if c["market"]=="h2h" and c["side"]=="home"]
        self.assertTrue(home)
        inv=[1/1.80,1/3.90,1/4.80]
        for c in home:
            self.assertEqual(c["sharp_source"],"ps3838")
            self.assertAlmostEqual(c["p_sharp_no_vig"],inv[0]/sum(inv),places=4)

    def test_live_requests_respect_one_request_per_second_per_book(self):
        clock=[0.0];calls={}
        def fake_request(book,sport,key,page):
            calls.setdefault(book,[]).append(clock[0])
            return [],True
        def sleep(seconds):
            self.assertGreater(seconds,0)
            clock[0]+=seconds
        def no_catalogue(book,sport,suffix,key,params):
            calls.setdefault(book,[]).append(clock[0])
            raise RuntimeError("HTTP 404 from PulseScore")
        with patch("outils.collecte.pulsescore_v2._request",side_effect=fake_request), \
             patch("outils.collecte.pulsescore_v2._get_json",side_effect=no_catalogue), \
             patch("outils.collecte.pulsescore_v2.time.monotonic",side_effect=lambda:clock[0]):
            _,meta=scan("secret",models(),NOW,sleep=sleep)
        # Catalogue indisponible : retour à la pagination, cadence toujours tenue.
        self.assertEqual(len(meta["fallback_paging"]),5)
        self.assertGreater(meta["requests"],len(calls))
        for book,times in calls.items():
            for a,b in zip(times,times[1:]):
                self.assertGreaterEqual(b-a,MIN_INTERVAL_PER_BOOK-1e-9,book)


class LeagueModeTests(unittest.TestCase):
    def fake_get(self,listing,seen):
        def get(book,sport,suffix,key,params):
            seen.append((book,suffix))
            if suffix=="leagues":
                return {"leagues":listing(book),"hasNextPage":False}
            return {"events":[event()],"hasNextPage":False}
        return get

    def test_tracked_leagues_only_and_no_duplicate_quotes(self):
        seen=[]
        def listing(book):
            if book=="ps3838":
                return [{"name":"Egypt - Premier League"},{"name":"England - Premier League"}]
            # Deux noms reconnus chez le même bookmaker renvoient le même match.
            return [{"name":"Premier League","country":"Angleterre"},
                    {"name":"Angleterre Premier League"},{"name":"Liga MX","country":"Mexique"}]
        odds,meta=scan("k",models(),NOW,get=self.fake_get(listing,seen),fetch=lambda *a:self.fail("pagination"))
        self.assertEqual(meta["collection_mode"],"league")
        self.assertEqual(meta["fallback_paging"],[])
        queried={(b,x) for b,x in seen if x!="leagues"}
        self.assertIn(("ps3838","leagues/England%20-%20Premier%20League/events"),queried)
        self.assertFalse(any("Egypt" in x or "Liga%20MX" in x for _,x in queried))
        books=[b["key"] for b in odds["PL"][0]["bookmakers"]]
        self.assertEqual(len(set(books)),len(books))
        self.assertEqual(len(books),5)
        self.assertEqual(meta["matched_by_book"],{b:1 for b in [*BOOKMAKERS,"ps3838"]})

    def test_missing_league_falls_back_to_paging(self):
        seen=[];paged=[]
        def fetch(book,sport,key,page):
            paged.append(book)
            return [event()],False
        odds,meta=scan("k",models(),NOW,get=self.fake_get(lambda book:[],seen),fetch=fetch)
        self.assertEqual(len(meta["fallback_paging"]),5)
        self.assertEqual(len(paged),5)
        self.assertEqual(len(odds["PL"][0]["bookmakers"]),5)


class RateLimitTests(unittest.TestCase):
    def test_429_is_retried_after_waiting_then_succeeds(self):
        import io,json as _json
        from urllib.error import HTTPError
        from email.message import Message
        from outils.collecte.pulsescore_v2 import _get_json
        headers=Message();headers["Retry-After"]="3"
        answers=[HTTPError("u",429,"Too Many Requests",headers,None),
                 io.BytesIO(_json.dumps({"leagues":[]}).encode())]
        def fake_urlopen(request,timeout):
            item=answers.pop(0)
            if isinstance(item,Exception):raise item
            item.__enter__=lambda self=item:self
            return item
        waits=[]
        with patch("outils.collecte.pulsescore_v2.urlopen",side_effect=fake_urlopen), \
             patch("outils.collecte.pulsescore_v2.time.sleep",side_effect=waits.append):
            self.assertEqual(_get_json("pmu","soccer","leagues","k",{"page":1}),{"leagues":[]})
        self.assertEqual(waits,[3.0])

    def test_429_gives_up_after_retries_without_leaking_url(self):
        from urllib.error import HTTPError
        from outils.collecte.pulsescore_v2 import _get_json,RETRIES_429
        calls=[]
        def always_429(request,timeout):
            calls.append(request.full_url)
            raise HTTPError(request.full_url,429,"Too Many Requests",None,None)
        with patch("outils.collecte.pulsescore_v2.urlopen",side_effect=always_429), \
             patch("outils.collecte.pulsescore_v2.time.sleep"):
            with self.assertRaises(RuntimeError) as ctx:
                _get_json("pmu","soccer","leagues","k",{"page":1})
        self.assertEqual(len(calls),RETRIES_429+1)
        self.assertEqual(str(ctx.exception),"HTTP 429 from PulseScore pmu/soccer")

if __name__=="__main__":
    unittest.main()
