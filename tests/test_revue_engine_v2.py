"""Offline regression tests for strict pregame odds/paper settlement engine."""
import unittest
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from outils.revue_engine_v2 import (
    match_fixture,normalize,same_team,price_probabilities,same_market_book,
    quote_book_valid,market_recommendations,paper_locks,ledger_statistics,
    settle_ledger,execute,timestamp,_outcome_from_score,FR_BOOKS,ODDS_SPORTS,
)


NOW=datetime(2026,10,9,16,tzinfo=timezone.utc)
START=NOW+timedelta(hours=4)
AT=NOW-timedelta(minutes=4)
def iso(d):return d.isoformat()


def football():
    return {"event_id":"101","home":"Arsenal","away":"Leeds",
            "start_utc":iso(START),"status":"prototype_non_calibre",
            "probabilities":{"home_win_90":.64,"draw_90":.20,
                             "away_win_90":.16,"over_2_5":.58},
            "_league":"PL"}


def quotes(when=AT, league="PL", start=START):
    home,away=("Arsenal FC","Leeds United") if league=="PL" else ("Boston Bruins","New York Rangers")
    return {"id":"odds101","commence_time":iso(start),
            "home_team":home,"away_team":away,
            "bookmakers":[
                {"key":"betclic_fr","last_update":iso(when),"markets":[
                    {"key":"h2h","last_update":iso(when),"outcomes":[
                        {"name":home,"price":1.85},
                        {"name":away,"price":5.5},
                        {"name":"Draw","price":4.1},
                    ]},
                    {"key":"totals","last_update":iso(when),"outcomes":[
                        {"name":"Over","point":2.5,"price":2.2},
                        {"name":"Under","point":2.5,"price":1.7},
                    ]}
                ]},
                {"key":"pinnacle","last_update":iso(when),"markets":[
                    {"key":"h2h","outcomes":[
                        {"name":home,"price":1.72},{"name":away,"price":5.8},{"name":"Draw","price":4.0}]}
                ]}
            ]}


def models():
    return {"generated_at_utc":iso(AT),
            "competitions":{"PL":{"games":[{k:v for k,v in football().items() if k!="_league"}]}}}


class MatchingTests(unittest.TestCase):
    def test_french_books_are_explicit(self):
        self.assertEqual(FR_BOOKS,{"betclic_fr","netbet_fr","pmu_fr","unibet_fr","winamax_fr"})
        self.assertIn("icehockey_nhl",ODDS_SPORTS.values())

    def test_normalization(self):
        self.assertTrue(same_team("Arsenal","Arsenal FC"))
        self.assertTrue(same_team("BOS","Boston Bruins","NHL"))
        self.assertTrue(same_team("Eagles","Philadelphia Eagles"))
        self.assertFalse(same_team("Real Madrid","Real Sociedad"))

    def test_unique_time_and_teams(self):
        g=football()
        self.assertEqual(match_fixture(quotes(),[g],"PL")["event_id"],"101")
        self.assertIsNone(match_fixture(quotes(start=START+timedelta(hours=4)),[g],"PL"))
        self.assertIsNone(match_fixture(quotes(),[g,deepcopy(g)],"PL"))

    def test_market_outcomes(self):
        g=football()
        self.assertEqual(price_probabilities(g,"h2h",{"name":"Draw","price":4.0})[0],.20)
        self.assertEqual(price_probabilities(g,"h2h",{"name":"Arsenal FC"})[0],.64)
        self.assertAlmostEqual(price_probabilities(g,"totals",{"name":"Under","point":2.5})[0],.42)
        self.assertIsNone(price_probabilities(g,"totals",{"name":"Over","point":3.5}))

    def test_devig_sharp_same_market(self):
        sharp=quotes()["bookmakers"][1]
        ans=same_market_book(sharp,"h2h",{"name":"Arsenal FC"})
        self.assertTrue(0<ans<1)
        self.assertIsNone(same_market_book(sharp,"totals",{"name":"Over","point":2.5}))

    def test_timestamp_validation(self):
        self.assertIsNone(timestamp("2026-10-09T17:00:00"))
        self.assertIsNotNone(timestamp("2026-10-09T17:00:00Z"))

    def test_quote_expiry(self):
        b=quotes()["bookmakers"][0]
        self.assertEqual(quote_book_valid(b,b["markets"][0],NOW),AT)
        self.assertIsNone(quote_book_valid(b,b["markets"][0],NOW+timedelta(hours=2)))
        self.assertIsNone(quote_book_valid(b,b["markets"][0],NOW-timedelta(minutes=6)))


class PaperTests(unittest.TestCase):
    def test_model_matches_real_book_quotes(self):
        selections,notes=market_recommendations(models(),{"PL":[quotes()]},NOW)
        self.assertGreater(len(selections),0)
        self.assertTrue(all(s["chronology"]=="pre_valide" for s in selections))
        self.assertTrue(all(s["bookmaker"]=="betclic_fr" for s in selections))
        self.assertTrue(any(s["p_sharp_no_vig"] is not None for s in selections))

    def test_stale_pinnacle_not_used_as_consensus(self):
        event=quotes()
        event["bookmakers"][1]["last_update"]=iso(NOW-timedelta(hours=3))
        out,_=market_recommendations(models(),{"PL":[event]},NOW)
        self.assertTrue(out)
        self.assertTrue(all(c["p_sharp_no_vig"] is None for c in out))

    def test_late_quote_refused(self):
        selections,notes=market_recommendations(models(),{"PL":[quotes(when=START+timedelta(hours=1))]},NOW)
        self.assertEqual(selections,[])

    def test_late_model_refused(self):
        m=models()
        m["generated_at_utc"]=iso(NOW+timedelta(minutes=1))
        self.assertEqual(market_recommendations(m,{"PL":[quotes()]},NOW)[0],[])

    def test_incompatible_two_way_football_refused(self):
        e=quotes()
        for book in e["bookmakers"]:
            book["markets"][0]["outcomes"]=[x for x in book["markets"][0]["outcomes"] if x["name"]!="Draw"]
        actual=market_recommendations(models(),{"PL":[e]},NOW)[0]
        self.assertFalse(any(x["market"]=="h2h" for x in actual))
        self.assertTrue(all(x["market"]=="totals" for x in actual))

    def test_only_paper_and_no_duplicate_event(self):
        selections,_=market_recommendations(models(),{"PL":[quotes()]},NOW)
        ledger={"version":1,"bets":[]}
        paper_locks(selections,ledger,NOW)
        self.assertEqual(len(ledger["bets"]),1)
        self.assertEqual(ledger["bets"][0]["status"],"pending")
        self.assertEqual(ledger["bets"][0]["chronology"],"pre_valide")
        paper_locks(selections,ledger,NOW)
        self.assertEqual(len(ledger["bets"]),1)

    def test_not_before_game_final(self):
        selections,_=market_recommendations(models(),{"PL":[quotes()]},NOW)
        ledger={"bets":[]}
        paper_locks(selections,ledger,NOW)
        history={"leagues":{"PL":{"events":[
            {"id":"101","complete":True,"home_score":3,"away_score":1}
        ]}}}
        settle_ledger(ledger,history,NOW)
        self.assertEqual(ledger["bets"][0]["status"],"pending")
        settle_ledger(ledger,history,START+timedelta(hours=5))
        self.assertEqual(ledger["bets"][0]["status"],"won")
        self.assertAlmostEqual(
            ledger_statistics(ledger)["paper_roi_pct"],
            100 * (ledger["bets"][0]["bookmaker_price"]-1))

    def test_soccer_draw_correct(self):
        b={"market":"h2h","side":"draw"}
        self.assertEqual(_outcome_from_score(b,2,2),"won")
        self.assertEqual(_outcome_from_score(b,2,1),"lost")

    def test_totals_push(self):
        self.assertEqual(_outcome_from_score({"market":"totals","side":"over","line":5},3,2),"push")
        self.assertEqual(_outcome_from_score({"market":"totals","side":"under","line":5.5},2,1),"won")

    def test_nhl_shootout_totals(self):
        old=NOW-timedelta(days=2)
        ledger={"bets":[{
            "id":"paper-001","event_id":"nhl-1","league":"NHL","market":"totals",
            "side":"over","line":5.5,"start_utc":iso(old),
            "status":"pending","chronology":"pre_valide",
            "bookmaker_price":1.8,"paper_stake_units":1,
            "locked_at":iso(old-timedelta(hours=3)),
            "quote_at":iso(old-timedelta(hours=3,minutes=4)),
            "model_at":iso(old-timedelta(hours=4))
        }]}
        settle_ledger(ledger,{},NOW,lambda *args:(4,2,"SO"))
        # Official SO score 4-2 (2-goal margin, impossible shootout margin)
        self.assertEqual(ledger["bets"][0]["status"],"won")
        self.assertEqual(ledger_statistics(ledger)["graded_pre_start"],1)

    def test_nhl_shootout_excludes_goal(self):
        old=NOW-timedelta(days=2)
        ledger={"bets":[{
            "id":"paper-002","event_id":"nhl-2","league":"NHL","market":"totals",
            "side":"over","line":5.5,"start_utc":iso(old),
            "status":"pending","chronology":"pre_valide",
            "bookmaker_price":1.8,"paper_stake_units":1,
            "locked_at":iso(old-timedelta(hours=3)),
            "quote_at":iso(old-timedelta(hours=3,minutes=4)),
            "model_at":iso(old-timedelta(hours=4))
        }]}
        settle_ledger(ledger,{},NOW,lambda *args:(4,3,"SO"))
        self.assertEqual(ledger["bets"][0]["status"],"won") # 3-3 => 6 > 5.5
        self.assertEqual(ledger["bets"][0]["score"],{"home":4,"away":3})
        self.assertEqual(ledger["bets"][0]["status"],"won")

    def test_unknown_shootout_unsettled(self):
        old=NOW-timedelta(days=2)
        ledger={"bets":[{
            "id":"paper-002","event_id":"nhl-2","league":"NHL","market":"totals",
            "side":"under","line":5.5,"start_utc":iso(old),
            "status":"pending","chronology":"pre_valide",
            "bookmaker_price":1.8,"paper_stake_units":1,
            "locked_at":iso(old-timedelta(hours=3)),
            "quote_at":iso(old-timedelta(hours=3,minutes=4)),
            "model_at":iso(old-timedelta(hours=4))
        }]}
        settle_ledger(ledger,{},NOW,lambda *args:(3,2))
        self.assertEqual(ledger["bets"][0]["status"],"pending")

    def test_missing_key_fails_closed(self):
        data=models()
        paper={"version":1,"bets":[]}
        report,ledger=execute(data,{"leagues":{}},paper,NOW,api_key="")
        self.assertEqual(report["odds_status"],"disabled_no_key")
        self.assertEqual(report["candidate_count"],0)
        self.assertEqual(report["paper"]["n_paper"],0)

    def test_spoofed_prevalid_late_record_excluded(self):
        data={"bets":[{
            "status":"won","chronology":"pre_valide",
            "locked_at":iso(NOW),
            "start_utc":iso(NOW-timedelta(hours=1)),
            "quote_at":iso(NOW-timedelta(hours=2)),
            "model_at":iso(NOW-timedelta(hours=2)),
            "paper_units_returned":3.5,"paper_stake_units":1,
        }]}
        stats=ledger_statistics(data)
        self.assertEqual(stats["graded_pre_start"],0)
        self.assertEqual(stats["excluded_unsafe_timestamps"],1)

    def test_stale_model_does_not_spend_paid_calls(self):
        from unittest.mock import patch
        stale=models()
        stale["generated_at_utc"]=iso(NOW-timedelta(hours=10))
        with patch("outils.revue_engine_v2.download_odds") as calls:
            report,_=execute(stale,{"leagues":{}},{"bets":[]},NOW,
                             api_key="private_test_key")
            calls.assert_not_called()
        self.assertEqual(report["odds_status"],"disabled_stale_model")

    def test_no_unverified_historical_roi(self):
        data={"bets":[{
            "status":"won","chronology":"indetermine",
            "paper_units_returned":1000,"paper_stake_units":1
        }]}
        stats=ledger_statistics(data)
        self.assertEqual(stats["graded_pre_start"],0)
        self.assertIsNone(stats["paper_roi_pct"])
        self.assertEqual(stats["excluded_unsafe_timestamps"],1)


if __name__=="__main__":
    unittest.main()
