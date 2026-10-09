import unittest
from datetime import datetime,timedelta,timezone
from outils.historique_cotes_clv import observe,closing_sample,report,valid_hockey_period
NOW=datetime(2026,10,9,19,tzinfo=timezone.utc)
START=NOW+timedelta(hours=3)
def iso(t):return t.isoformat()
def ledger(k="PL",type="h2h"):
    return {"bets":[{
        "selection_id":"PL:100:betclic","league":k,"event_id":"100",
        "home":"Arsenal","away":"Leeds",
        "start_utc":iso(START),
        "locked_at":iso(NOW-timedelta(minutes=5)),
        "bookmaker":"betclic_fr",
        "bookmaker_price":1.9,
        "market":type,"side":"home" if type=="h2h" else "over",
        "line":None if type=="h2h" else 2.5,
        "status":"pending","market_rule_verified":True
    }]}
def odds(now=NOW,price=1.95,book="betclic_fr"):
    return {"PL":[{
        "id":"review:PL:100","home_team":"Arsenal","away_team":"Leeds",
        "commence_time":iso(START),
        "bookmakers":[{
            "key":book,"last_update":iso(now),
            "markets":[{"key":"h2h","last_update":iso(now),
                        "outcomes":[{"name":"Arsenal","price":price},
                                    {"name":"Draw","price":3.1},
                                    {"name":"Leeds","price":5.0}]}]
        }]
    }]}
class OddsTrajectoryTests(unittest.TestCase):
    def test_first_quote_tracked(self):
        d=ledger()
        counts=observe(d,odds(),NOW)
        self.assertEqual(counts["new_observations"],1)
        self.assertEqual(d["bets"][0]["odds_history"][0]["price"],1.95)
    def test_no_duplicate_from_same_scan(self):
        d=ledger();observe(d,odds(),NOW)
        counts=observe(d,odds(NOW+timedelta(minutes=3)),NOW+timedelta(minutes=3))
        self.assertEqual(counts["new_observations"],0)
    def test_real_price_change_is_recorded(self):
        d=ledger();observe(d,odds(),NOW)
        later=NOW+timedelta(minutes=3)
        counts=observe(d,odds(later,price=1.8),later)
        self.assertEqual(counts["new_observations"],1)
        self.assertEqual(len(d["bets"][0]["odds_history"]),2)
    def test_different_book_never_joins(self):
        d=ledger()
        counts=observe(d,odds(book="pmu_fr"),NOW)
        self.assertEqual(counts["new_observations"],0)
    def test_wrong_market_refused(self):
        d=ledger(type="totals")
        counts=observe(d,odds(),NOW)
        self.assertEqual(counts["new_observations"],0)
    def test_closing_window(self):
        d=ledger();b=d["bets"][0]
        at=START-timedelta(minutes=40)
        b["odds_history"]=[{"observed_at":iso(at),
                          "quote_at":iso(at),
                          "price":1.7,
                          "bookmaker":"betclic_fr","same_market_line":True}]
        c=closing_sample(b)
        self.assertEqual(c["observed_close_odds"],1.7)
        self.assertGreater(c["clv_pct"],0)
    def test_older_observation_not_false_close(self):
        d=ledger();b=d["bets"][0]
        b["odds_history"]=[{"observed_at":iso(START-timedelta(hours=2)),
            "price":1.7,"bookmaker":"betclic_fr","same_market_line":True}]
        self.assertIsNone(closing_sample(b))
    def test_after_kickoff_not_close(self):
        d=ledger();b=d["bets"][0]
        b["odds_history"]=[{"observed_at":iso(START+timedelta(minutes=1)),
            "price":1.7,"bookmaker":"betclic_fr","same_market_line":True}]
        self.assertIsNone(closing_sample(b))
    def test_market_uncertain_no_clv(self):
        d=ledger();b=d["bets"][0]
        b["market_rule_verified"]=False
        observe(d,odds(),NOW)
        self.assertIsNone(closing_sample(b))
        self.assertEqual(report(d,NOW)["n_tracked"],0)
    def test_valid_legacy_non_hockey_market_is_tracked(self):
        d=ledger()
        del d["bets"][0]["market_rule_verified"]
        self.assertEqual(observe(d,odds(),NOW)["new_observations"],1)
        self.assertEqual(report(d,NOW)["n_tracked"],1)
    def test_old_nhl_market_remains_excluded(self):
        d=ledger(k="NHL")
        del d["bets"][0]["market_rule_verified"]
        self.assertEqual(report(d,NOW)["n_tracked"],0)

    def test_no_roi_from_price_movement(self):
        d=ledger()
        result=report(d,NOW)
        self.assertIsNone(result["mean_clv_pct"])
        self.assertEqual(result["n_close_proxy_samples"],0)
    def test_nhl_explicit_period_needed(self):
        self.assertFalse(valid_hockey_period({"period":"FULL_TIME"}))
        self.assertTrue(valid_hockey_period({"period":"GAME_INCLUDING_OVERTIME"}))
if __name__=="__main__":unittest.main()
