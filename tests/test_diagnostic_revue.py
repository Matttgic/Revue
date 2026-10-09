import unittest
from datetime import datetime,timedelta,timezone
from outils.diagnostic_revue import build,verify_component
NOW=datetime(2026,10,9,20,tzinfo=timezone.utc)
def ts(d):return d.isoformat()
def sources():
    s={"generated_at_utc":ts(NOW-timedelta(hours=1))}
    return {
        "multisports":{**s,"overview":{"feeds_ok":19,"fixtures":174}},
        "scanner":{**s,"odds_status":"active_pulsescore",
                   "paper":{"n_paper":14,"graded_pre_start":0,
                            "excluded_unsafe_timestamps":10},
                   "coverage":{"requested":[],"api_errors":{}}},
        "football_shadow":{**s,"licensed_advanced_features":{"records":0}},
        "teams_shadow":{**s,"leagues":{"NBA":{},"NFL":{}}},
        "football_boxscores":{**s,"teams":{"a":{},"b":{}}},
        "code_audit":{"counts":{"files":376}},
    }
class DiagnosticTests(unittest.TestCase):
    def test_timestamp_fresh(self):
        a=verify_component("multisports",{"generated_at_utc":ts(NOW)},NOW)
        self.assertEqual(a["status"],"fresh")
    def test_missing_and_future(self):
        self.assertEqual(verify_component("multisports",None,NOW)["status"],"missing")
        self.assertEqual(verify_component("multisports",
           {"generated_at_utc":ts(NOW+timedelta(hours=2))},NOW)["status"],"future_timestamp")
    def test_stale_model(self):
        self.assertEqual(verify_component("multisports",
           {"generated_at_utc":ts(NOW-timedelta(hours=11))},NOW)["status"],"stale")
    def test_no_claim_about_opta_or_profit(self):
        x=build(sources(),NOW)
        self.assertFalse(x["facts"]["opta_connected"])
        self.assertFalse(x["facts"]["fully_calibrated"])
        self.assertFalse(x["facts"]["real_bets_enabled"])
    def test_quote_feed_errors_are_reported(self):
        d=sources()
        d["scanner"]["coverage"]["api_errors"]={"book":"429"}
        x=build(d,NOW)
        self.assertTrue(any("bookmaker feeds" in t for t in x["warnings"]))
    def test_quarantine_count(self):
        x=build(sources(),NOW)
        self.assertTrue(any("10 paper entries" in t for t in x["warnings"]))
    def test_no_key_marks_warning(self):
        d=sources()
        d["scanner"]["odds_status"]="disabled_no_key"
        x=build(d,NOW)
        self.assertTrue(any("disabled_no_key" in t for t in x["warnings"]))
    def test_source_counts(self):
        x=build(sources(),NOW)
        self.assertEqual(x["facts"]["source_files_audited"],376)
        self.assertEqual(x["facts"]["football_espn_teams"],2)
if __name__=="__main__":unittest.main()
