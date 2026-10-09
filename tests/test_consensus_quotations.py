import unittest
from datetime import datetime,timedelta,timezone
from outils.consensus_quotations import (
    outcome_key,market_probs,peer_consensus
)
NOW=datetime(2026,10,9,19,tzinfo=timezone.utc)
def iso(t):return t.isoformat()
GAME={"_league":"PL","home":"Arsenal","away":"Leeds",
      "probabilities":{"home_win_90":.55,"draw_90":.24,"away_win_90":.21}}
def book(key,prices=(1.9,3.5,4.5),when=NOW):
    return {"key":key,"last_update":iso(when),"markets":[{
        "key":"h2h","last_update":iso(when),
        "outcomes":[
            {"name":"Arsenal","price":prices[0]},
            {"name":"Draw","price":prices[1]},
            {"name":"Leeds","price":prices[2]},
        ],
    }]}
def event():
    return {"bookmakers":[book("betclic_fr"),
                           book("winamax_fr",(1.86,3.5,4.6)),
                           book("pmu_fr",(1.88,3.6,4.7))]}
class ConsensusTests(unittest.TestCase):
    def test_outcome_identity(self):
        self.assertEqual(outcome_key({"name":"Arsenal"},"h2h",GAME),"home")
        self.assertEqual(outcome_key({"name":"Leeds"},"h2h",GAME),"away")
        self.assertEqual(outcome_key({"name":"Draw"},"h2h",GAME),"draw")
        self.assertEqual(outcome_key({"name":"Over","point":2.5},"totals",GAME),"over@2.5")
    def test_vig_free_sums_one(self):
        b=book("winamax_fr")
        x=market_probs(b,b["markets"][0],GAME,NOW)
        self.assertAlmostEqual(sum(x.values()),1)
    def test_exclude_target_book(self):
        e=event()
        c=peer_consensus(e,GAME,"h2h",{"name":"Arsenal"},
                         "betclic_fr",NOW)
        self.assertEqual(c["peer_count"],2)
        self.assertTrue(0<c["p_no_vig"]<1)
        self.assertNotIn("betclic_fr",c["bookmakers"])
    def test_missing_peer_is_not_consensus(self):
        c=peer_consensus({"bookmakers":[book("betclic_fr")]},
                         GAME,"h2h",{"name":"Arsenal"},
                         "betclic_fr",NOW)
        self.assertIsNone(c["p_no_vig"])
    def test_stale_peer_is_excluded(self):
        e=event();e["bookmakers"][1]=book("winamax_fr",when=NOW-timedelta(hours=2))
        c=peer_consensus(e,GAME,"h2h",{"name":"Arsenal"},
                         "betclic_fr",NOW)
        self.assertEqual(c["peer_count"],1)
        self.assertIsNone(c["p_no_vig"])
    def test_refuse_wrong_two_way_market(self):
        b=book("pmu_fr")
        b["markets"][0]["outcomes"]=b["markets"][0]["outcomes"][:2]
        self.assertIsNone(market_probs(b,b["markets"][0],GAME,NOW))
    def test_refuse_duplicate_side(self):
        b=book("pmu_fr")
        b["markets"][0]["outcomes"].append({"name":"Arsenal","price":3.2})
        self.assertIsNone(market_probs(b,b["markets"][0],GAME,NOW))
    def test_refuse_unknown_target(self):
        c=peer_consensus(event(),GAME,"h2h",{"name":"Other"},
                         "betclic_fr",NOW)
        self.assertIsNone(c["p_no_vig"])
    def test_totals_strict_same_line(self):
        game={"_league":"PL","home":"Arsenal","away":"Leeds","probabilities":GAME["probabilities"]}
        e={"bookmakers":[]}
        for name in ("betclic_fr","winamax_fr","pmu_fr"):
            b={"key":name,"last_update":iso(NOW),"markets":[{
                "key":"totals","last_update":iso(NOW),
                "outcomes":[{"name":"Over","point":2.5,"price":1.8},
                            {"name":"Under","point":2.5,"price":2.1}]
            }]}
            e["bookmakers"].append(b)
        out=peer_consensus(e,game,"totals",{"name":"Over","point":2.5},
                           "betclic_fr",NOW)
        self.assertIsNotNone(out["p_no_vig"])
        other=peer_consensus(e,game,"totals",{"name":"Over","point":3.5},
                             "betclic_fr",NOW)
        self.assertIsNone(other["p_no_vig"])
    def test_own_price_not_fair_price(self):
        e=event()
        high=peer_consensus(e,GAME,"h2h",{"name":"Arsenal"},
                            "betclic_fr",NOW)
        e["bookmakers"][0]["markets"][0]["outcomes"][0]["price"]=7
        after=peer_consensus(e,GAME,"h2h",{"name":"Arsenal"},
                             "betclic_fr",NOW)
        self.assertEqual(high["p_no_vig"],after["p_no_vig"])
if __name__=="__main__":unittest.main()
