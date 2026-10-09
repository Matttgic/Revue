"""The odds panel tests: all valid book prices, no theoretical EV needed."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.tableau_cotes import build_board,selections
from test_revue_engine_v2 import quotes,models,NOW,START

class OddsBoardTests(unittest.TestCase):
    def test_all_books_not_only_EV_candidates(self):
        report=build_board(models(),{"PL":[quotes()]},NOW)
        self.assertEqual(report["events_count"],1)
        e=report["events"][0]
        self.assertEqual(e["event_id"],"101")
        self.assertEqual([x["bookmaker"] for x in e["bookmakers"]],["betclic_fr"])
        market=e["bookmakers"][0]["markets"][0]
        self.assertEqual(market["market"],"h2h")
        self.assertEqual([x["price"] for x in market["outcomes"]],[1.85,4.1,5.5])
        self.assertNotIn("ev_model",str(report))
        self.assertNotIn("p_model",str(report))

    def test_totals_preserve_both_sides_and_line(self):
        b=build_board(models(),{"PL":[quotes()]},NOW)
        ts=next(x for x in b["events"][0]["bookmakers"][0]["markets"]
                if x["market"]=="totals")
        self.assertEqual([i["selection"] for i in ts["outcomes"]],["over","under"])
        self.assertEqual([i["line"] for i in ts["outcomes"]],[2.5,2.5])

    def test_stale_market_disallowed(self):
        b=build_board(models(),{"PL":[quotes(NOW-timedelta(hours=4))]},NOW)
        self.assertEqual(b["events_count"],0)

    def test_no_invalid_price_or_fictitious_draw(self):
        game=models()["competitions"]["PL"]["games"][0]
        e=deepcopy(quotes())
        e["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]=0
        self.assertEqual(selections(e["bookmakers"][0]["markets"][0],game,"PL"),[])
        e["bookmakers"][0]["markets"][0]["outcomes"]=e["bookmakers"][0]["markets"][0]["outcomes"][:2]
        self.assertEqual(selections(e["bookmakers"][0]["markets"][0],game,"PL"),[])

    def test_no_matching_events_disallowed(self):
        e=quotes()
        e["home_team"]="Another club"
        b=build_board(models(),{"PL":[e]},NOW)
        self.assertEqual(b["events_count"],0)

    def test_cfb_not_in_board(self):
        r=build_board(models(),{"CFB":[quotes()]},NOW)
        self.assertEqual(r["events"],[])

    def test_nhl_unknown_ot_marked_unverified(self):
        nhl_model={"generated_at_utc":NOW.isoformat(),"competitions":{
            "NHL":{"games":[{"event_id":"201","home":"Boston Bruins",
             "away":"New York Rangers","start_utc":START.isoformat(),
             "probabilities":{"home_win":.55,"away_win":.45}}]}}}
        event=quotes(league="NHL")
        # Three-way soccer market is unsuitable for NHL.
        event["bookmakers"][0]["markets"][0]["outcomes"]=[
            {"name":"Boston Bruins","price":1.8},
            {"name":"New York Rangers","price":2.05}]
        b=build_board(nhl_model,{"NHL":[event]},NOW)
        self.assertEqual(b["events_count"],1)
        self.assertTrue(all(m["period_rule"]=="overtime_rule_unverified"
                        for m in b["events"][0]["bookmakers"][0]["markets"]))
        self.assertEqual(b["events"][0]["bookmakers"][0]["markets"][0]["market"],"h2h")

    def test_future_quote_timestamp_not_valid(self):
        e=quotes(NOW+timedelta(minutes=1))
        b=build_board(models(),{"PL":[e]},NOW)
        self.assertEqual(b["events_count"],0)

if __name__=="__main__":unittest.main()
