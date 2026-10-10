"""Revue picks hub: original-style browse/track, independently verified pregame."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.picks_center_revue import board
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
def t(hours):return (NOW+timedelta(hours=hours)).isoformat()

def fixture():
    base={"league":"PL","event_id":"1234","home":"Arsenal","away":"Leeds",
          "start_utc":t(4),"market":"h2h","side":"home","line":None,
          "p_model":.61,"market_rule_verified":True,"chronology":"pre_valide",
          "status":"EXPERIMENTAL_PAPER_ONLY","quote_at":t(-1),
          "model_at":t(-2),"outcome":"Arsenal"}
    a={**base,"bookmaker":"betclic_fr","bookmaker_price":1.87,"selection_id":"one"}
    b={**base,"bookmaker":"winamax_fr","bookmaker_price":1.91,"selection_id":"two"}
    raw={"mode":"PAPER_ONLY","generated_at_utc":t(-.5),"candidate_count":2,
         "candidates":[a,b]}
    settled={"id":"paper-000001","league":"PL","event_id":"13",
             "home":"Chelsea","away":"Leeds","start_utc":t(-5),
             "locked_at_utc":t(-7),"quote_at_utc":t(-7),
             "market":"h2h","side":"home","line":None,"outcome":"Chelsea",
             "bookmaker":"betclic_fr","decimal_odds":2.1,"paper_stake_units":1,
             "status":"won","paper_profit_units":1.1,"verified_pre_match":True,
             "score":{"home":2,"away":1},"is_real_bet":False}
    excluded={**settled,"id":"paper-000002","status":"unverified",
              "paper_profit_units":None,"exclusion_reason":"Invalid market rule"}
    pending={**settled,"id":"paper-000003","status":"pending",
             "paper_profit_units":None}
    journal={"source":"Revue independent paper ledger, NOT Clairvoyance SQL",
             "paper_only":True,"real_bets_enabled":False,"static_snapshot":True,
             "generated_at_utc":t(-1),
             "records":[settled,excluded,pending],
             "summary":{"total":3,"settled":1,"won":1,"lost":0,"push":0,
                        "pending":1,"excluded_or_unverified":1,
                        "paper_profit_units":1.1}}
    return raw,journal

class PicksHubTests(unittest.TestCase):
    def test_groups_identical_bookmaker_selection_and_rebuilds_roi(self):
        d=board(*fixture(),NOW)
        self.assertEqual(d["unique_research_selections"],1)
        self.assertEqual(d["upcoming_research_selections"],1)
        b=d["research_selections"][0]
        self.assertEqual(b["books_count"],2)
        self.assertEqual(b["best_observed_price"]["decimal_odds"],1.91)
        self.assertFalse(b["qualified_positive_ev"])
        self.assertFalse(d["verified_real_ev"])
        self.assertFalse(d["live_bookmaker_prices"])
        self.assertFalse(d["real_bets_enabled"])
        self.assertEqual(d["paper_summary"]["settled"],1)
        self.assertEqual(d["paper_summary"]["excluded"],1)
        self.assertEqual(d["paper_summary"]["paper_profit_units"],1.1)
        self.assertEqual(d["paper_summary"]["paper_roi_percent"],110)

    def test_reject_quote_after_start_or_future_model_leak(self):
        e,l=fixture()
        e["candidates"][0]["quote_at"]=t(4)
        e["candidates"][1]["model_at"]=t(5)
        d=board(e,l,NOW)
        self.assertEqual(d["unique_research_selections"],0)
        self.assertEqual(d["excluded_candidate_records"]["invalid_pregame_chronology"],2)

    def test_late_settled_grade_never_counts_profit(self):
        e,l=fixture()
        l["records"][0]["locked_at_utc"]=t(-3)
        with self.assertRaisesRegex(ValueError,"pregame"):board(e,l,NOW)

    def test_fake_real_bet_never_displays(self):
        e,l=fixture()
        l["records"][0]["is_real_bet"]=True
        with self.assertRaisesRegex(ValueError,"betting"):board(e,l,NOW)

    def test_invalid_market_rules_rejected_not_a_silent_ev_signal(self):
        e,l=fixture()
        e["candidates"][0]["market_rule_verified"]=False
        d=board(e,l,NOW)
        self.assertEqual(d["unique_research_selections"],1)
        self.assertEqual(d["research_selections"][0]["books_count"],1)
        self.assertEqual(d["excluded_candidate_records"]["source_market_or_probability_unverifiable"],1)

    def test_source_summary_must_match_records(self):
        e,l=fixture()
        l["summary"]["settled"]=2
        with self.assertRaisesRegex(ValueError,"contradicts"):board(e,l,NOW)

    def test_two_different_markets_are_not_compared(self):
        e,l=fixture()
        e["candidates"][1].update({"market":"totals","side":"over","line":2.5})
        d=board(e,l,NOW)
        self.assertEqual(d["unique_research_selections"],2)
        self.assertTrue(all(g["books_count"]==1 for g in d["research_selections"]))

    def test_candidate_postkickoff_label_is_archive_not_live(self):
        e,l=fixture()
        for row in e["candidates"]:row["start_utc"]=t(-.5)
        d=board(e,l,NOW)
        self.assertEqual(d["unique_research_selections"],1)
        self.assertEqual(d["upcoming_research_selections"],0)
        self.assertFalse(d["research_selections"][0]["visible_as_upcoming_at_export"])

    def test_cfb_is_never_added(self):
        e,l=fixture()
        for row in e["candidates"]:row["league"]="CFB"
        e["candidates"][0]["selection_id"]="cfb"
        e["candidates"][1]["selection_id"]="cfb2"
        l["records"][1]["league"]="CFB"
        l["summary"].update({"total":2,"excluded_or_unverified":0})
        d=board(e,l,NOW)
        self.assertEqual(d["unique_research_selections"],0)
        self.assertEqual(d["paper_summary"]["total"],2)

if __name__=="__main__":unittest.main()
