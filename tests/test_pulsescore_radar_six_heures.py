"""PulseScore short-horizon radar (Pro access), without paid calls in tests."""
import unittest
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from outils.collecte.pulsescore_radar_six_heures import compute,MAX_CALLS,HORIZON_HOURS,VERSION
from outils.collecte.pulsescore_v2 import BOOKMAKERS,SPORT_GROUPS,MAX_PAGES,MAX_CALLS as PULSE_MAX_CALLS

NOW=datetime(2026,10,10,19,tzinfo=timezone.utc)
ISO=lambda t:t.isoformat()
KICKOFF=NOW+timedelta(hours=3)
def models():
    return {"generated_at_utc":ISO(NOW-timedelta(minutes=11)),
            "status":"prototype_non_calibre",
            "competitions":{"PL":{"games":[{
                "event_id":"400123123","home":"Arsenal","away":"Leeds",
                "start_utc":ISO(KICKOFF),"status":"prototype_non_calibre",
                "probabilities":{"home_win_90":.61,"draw_90":.24,"away_win_90":.15},
            }]}}}
def odds():
    return {"PL":[{"id":"review:PL:400123123",
       "home_team":"Arsenal","away_team":"Leeds",
       "commence_time":ISO(KICKOFF),
       "bookmakers":[{"key":"betclic_fr","last_update":ISO(NOW),
         "markets":[{"key":"h2h","period":"FULL_TIME",
           "last_update":ISO(NOW),"observed_origin":"fetch_observation",
           "outcomes":[{"name":"Arsenal","price":1.65},
                       {"name":"Draw","price":4.0},
                       {"name":"Leeds","price":5.4}]}]}]}]}

class RadarTests(unittest.TestCase):
    def test_observed_quote_exact_source_and_strict_cap(self):
        captured=[]
        def fake(key,models_,now_,max_calls,days_horizon,balanced):
            captured.append((key,max_calls,days_horizon,balanced))
            return odds(),{"requests":5,"matched_events":1,"matched_leagues":{"PL":1},
                           "sports":["soccer"],"errors":{},"truncated":False}
        m=models();unchanged=deepcopy(m)
        result=compute(m,NOW,key="secret-key",scanner=fake)
        self.assertEqual(captured,[("secret-key",MAX_CALLS,6,True)])
        self.assertEqual(result["version"],VERSION)
        self.assertEqual(result["status"],"observed")
        self.assertEqual(result["matches_observed"],1)
        self.assertEqual(result["market_rows_observed"],1)
        self.assertEqual(result["observations"][0]["event_id"],"400123123")
        self.assertEqual(result["observations"][0]["bookmakers"][0]["markets"][0]["quote_at"],ISO(NOW))
        self.assertTrue(result["market_prices_are_live"] is False)
        self.assertTrue(result["positive_ev_verified"] is False)
        self.assertTrue(result["new_paper_bets_created"] is False)
        self.assertTrue(result["existing_paper_ledger_modified"] is False)
        self.assertNotIn("secret-key",str(result))
        self.assertEqual(m,unchanged)

    def test_no_key_no_paid_requests(self):
        def fail(*args,**kwargs):raise AssertionError("Unexpected provider API call")
        out=compute(models(),NOW,key="",scanner=fail)
        self.assertEqual(out["requests_used"],0)
        self.assertEqual(out["status"],"no_api_key")
        self.assertEqual(out["observations"],[])

    def test_stale_model_no_paid_requests(self):
        m=models();m["generated_at_utc"]=ISO(NOW-timedelta(hours=8))
        def fail(*args,**kwargs):raise AssertionError("Should not scan stale models")
        out=compute(m,NOW,key="secret",scanner=fail)
        self.assertEqual(out["status"],"model_stale_or_invalid")
        self.assertEqual(out["requests_used"],0)
        m=models();m["generated_at_utc"]=ISO(NOW+timedelta(hours=1))
        self.assertEqual(compute(m,NOW,key="secret",scanner=fail)["requests_used"],0)
        m=models();m["status"]="fabricated_calibrated"
        self.assertEqual(compute(m,NOW,key="secret",scanner=fail)["status"],"model_stale_or_invalid")

    def test_hard_api_budget_limit_rejects_unexpected_calls(self):
        for cap in (0,MAX_CALLS+1,1000):
            with self.assertRaises(ValueError):
                compute(models(),NOW,key="fake",max_calls=cap)
        def bad(*args,**kwargs):
            return {},{"requests":MAX_CALLS+1}
        with self.assertRaises(ValueError):
            compute(models(),NOW,key="fake",scanner=bad)

    def test_cap_covers_whole_catalogue_without_runaway(self):
        # Accès Pro illimité : le plafond couvre tout le catalogue, sans plus.
        self.assertEqual(MAX_CALLS,PULSE_MAX_CALLS)
        self.assertEqual(PULSE_MAX_CALLS,len(set(SPORT_GROUPS.values()))*len(BOOKMAKERS)*MAX_PAGES)
        self.assertEqual(HORIZON_HOURS,6)
        self.assertEqual(len(BOOKMAKERS),5)

    def test_real_provider_schema_exposes_source_without_claiming_ev(self):
        from pathlib import Path
        import json
        root=Path(__file__).resolve().parents[1]/"docs"
        d=json.loads((root/"multisports-latest.json").read_text("utf8"))
        self.assertIn("NHL",d["competitions"])
        self.assertIn("PL",d["competitions"])
        now=datetime.fromisoformat(d["generated_at_utc"].replace("Z","+00:00"))+timedelta(minutes=15)
        out=compute(d,now,key="",scanner=lambda *a,**k: (_ for _ in ()).throw(AssertionError))
        self.assertEqual(out["request_cap"],MAX_CALLS)
        self.assertFalse(out["real_bets_enabled"])
        self.assertFalse(out["model_is_calibrated"])

if __name__=="__main__":unittest.main()
