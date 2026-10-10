"""Game dossiers: pregame identity checks, source odds comparisons, archival history."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.revue_match_dossiers import compile_dossiers,make_market_view
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
def t(hours):return (NOW+timedelta(hours=hours)).isoformat()
def base():
    src={"status":"experimental_revue_match_center","real_bets_enabled":False,
         "bookmaker_prices_are_live":False,"validated_value_bets":0,
         "generated_at_utc":t(-1),
         "events":[{"event_id":"4123","league":"PL","sport":"Football",
          "home":"Arsenal","away":"Leeds","start_utc":t(4),
          "research":[{"id":"demo","label":"Experiment",
                         "probabilities":{"home_win_90":.6},"calibrated":False,
                         "source_generated_utc":t(-2)}],
          "quotes":[
            {"market":"h2h","bookmaker":"winamax_fr","rule":"90min","rule_verified":True,
             "quote_at_utc":t(-2),"outcomes":{"home":1.8,"draw":3.7,"away":4.2}},
            {"market":"h2h","bookmaker":"betclic_fr","rule":"90min","rule_verified":True,
             "quote_at_utc":t(-3),"outcomes":{"home":1.9,"draw":3.5,"away":4.1}},
            {"market":"h2h","bookmaker":"another_fr","rule":"incl_ot","rule_verified":False,
             "quote_at_utc":t(-2),"outcomes":{"home":1.01,"away":20.0}}],
          "totals_quotes":[
            {"market":"totals","bookmaker":"winamax_fr","rule":"90min",
             "rule_verified":True,"quote_at_utc":t(-2),
             "lines":[{"line":2.5,"over":1.95,"under":1.85}]},
            {"market":"totals","bookmaker":"betclic_fr","rule":"90min",
             "rule_verified":True,"quote_at_utc":t(-2),
             "lines":[{"line":2.5,"over":1.97,"under":1.83}]}],
          "player_profiles":[]} ]}
    history={"version":1,"leagues":{"PL":{"events":[
      {"id":"301","league":"PL","start":t(-50),"home":"Arsenal","away":"Leeds",
       "home_score":2.0,"away_score":0.0,"complete":True},
      {"id":"302","league":"PL","start":t(-30),"home":"Leeds","away":"Arsenal",
       "home_score":1,"away_score":1,"complete":True},
      {"id":"303","league":"PL","start":t(10),"home":"Leeds","away":"Arsenal",
       "home_score":5,"away_score":0,"complete":True},
    ]}}}
    paper={"version":"revue_multisport_pre_match_v1","events":[{"key":"PL:4123","league":"PL","event_id":"4123",
           "home":"Arsenal","away":"Leeds","kickoff_utc":t(4),
           "locked_at_utc":t(-1),"status":"pending","result":None,"score":None,
           "real_bet":False,"staked_units":0,
           "models":{"demo":{"p_home":.6,"source_generated_utc":t(-2)}}}]}
    return src,history,paper
class DossierTests(unittest.TestCase):
    def test_join_source_history_price_groups_and_real_frozen_ledger(self):
        d=compile_dossiers(*base(),NOW)
        self.assertEqual(d["count"],1)
        self.assertEqual(d["historical_finals_in_available_archive"],2)
        self.assertEqual(d["with_locked_forecasts"],1)
        self.assertEqual(d["with_descriptive_team_history"],1)
        x=d["games"][0]
        self.assertEqual(x["home_history"]["wins"],1)
        self.assertEqual(x["home_history"]["draws"],1)
        self.assertEqual(x["home_history"]["games"],2)
        self.assertTrue(x["home_history"]["not_pre_game_verified"])
        self.assertEqual(x["locked_forecast"]["models"]["demo"]["p_home"],.6)
        self.assertEqual(d["with_comparable_markets"],1)
        prices=x["historical_odds"]
        self.assertEqual(prices["verified_comparable_groups"],2)
        self.assertEqual(len(prices["observations"]),5)
        g=next(x for x in prices["market_groups"] if x["market"]=="h2h")
        self.assertEqual(g["books_compared"],2)
        self.assertEqual(g["best_observed_prices"]["home"]["price"],1.9)
        self.assertEqual(g["best_observed_prices"]["draw"]["price"],3.7)
        self.assertNotIn("incl_ot",[p["rule"] for p in prices["market_groups"]])
        self.assertFalse(d["bookmaker_prices_are_live"])
        self.assertFalse(d["original_clairvoyance_equivalence_verified"])

    def test_price_after_start_20_minutes_cutoff_is_rejected(self):
        m=base()[0]["events"][0].copy()
        m["quotes"]=[{**m["quotes"][0],"quote_at_utc":t(4)}]
        p=make_market_view(m,datetime.fromisoformat(t(4)))
        self.assertEqual(p["invalid_quote_count"],1)
        self.assertEqual(len(p["observations"]),2)
        self.assertEqual(p["verified_comparable_groups"],1)

    def test_market_rules_never_pooled_and_no_fake_arbitrage(self):
        src,h,p=base()
        src["events"][0]["quotes"][0]["rule"]="incl_ot"
        d=compile_dossiers(src,h,p,NOW)
        markets=d["games"][0]["historical_odds"]["market_groups"]
        self.assertEqual(len([x for x in markets if x["market"]=="h2h"]),2)
        self.assertTrue(all(x["no_arbitrage_or_ev_claim"] for x in markets))

    def test_ledger_fixture_mismatch_or_future_feature_never_attaches(self):
        src,h,p=base()
        p["events"][0]["home"]="Wrong Team"
        self.assertIsNone(compile_dossiers(src,h,p,NOW)["games"][0]["locked_forecast"])
        p=base()[2];p["events"][0]["models"]["demo"]["source_generated_utc"]=t(1)
        self.assertIsNone(compile_dossiers(src,h,p,NOW)["games"][0]["locked_forecast"])

    def test_corrupt_future_history_and_duplicate_event_fails_closed(self):
        src,h,p=base()
        src["generated_at_utc"]=t(7)
        with self.assertRaises(ValueError):compile_dossiers(src,h,p,NOW)
        src=base()[0];src["events"].append(src["events"][0])
        with self.assertRaises(ValueError):compile_dossiers(src,h,p,NOW)

    def test_real_bets_and_nhl_unconfirmed_lineups(self):
        src,h,p=base()
        src["real_bets_enabled"]=True
        with self.assertRaises(ValueError):compile_dossiers(src,h,p,NOW)
        src=base()[0]
        src["events"][0]["player_profiles"]=[{"name":"Player A","lineup_status":"confirmed"}]
        with self.assertRaises(ValueError):compile_dossiers(src,h,p,NOW)

if __name__=="__main__":unittest.main()
