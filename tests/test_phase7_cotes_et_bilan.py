"""Phase7: prevent false trading-odds or PnL from research snapshots."""
import unittest
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from outils.phase7_cotes_et_bilan import build,V
NOW=datetime(2026,10,10,22,tzinfo=timezone.utc)
def sample():
    q="2026-10-10T21:50:00Z";k="2026-10-11T01:00:00Z";lock="2026-10-10T21:55:00Z"
    radar={"version":"revue_pulsescore_six_hour_radar_v1","generated_at_utc":q,
       "status":"observed","provider":"PulseScore",
       "market_prices_are_live":False,"positive_ev_verified":False,
       "model_is_calibrated":False,"real_bets_enabled":False,
       "matches_observed":1,"market_rows_observed":1,
       "observations":[{"league":"NHL","event_id":"99","home":"BOS","away":"PHI","start_utc":k,
         "bookmakers":[{"bookmaker":"winamax_fr","markets":[{"market":"totals",
           "period_rule":"overtime_rule_unverified","quote_time_source":"fetch_observation",
           "quote_at":q,"outcomes":[
             {"selection":"over","line":5.5,"price":1.85},
             {"selection":"under","line":5.5,"price":2.02}]}]}]}]}
    row={"id":"NHL:99:nhl_total_unverified_period:under:5.5","league":"NHL",
         "event_id":"99","home":"BOS","away":"PHI","kickoff_utc":k,
         "market":"nhl_total_unverified_period","side":"under","line":5.5,
         "original_probability":.55,"revue_probability":.51,
         "locked_at_utc":lock,"source_model_lock_proven":False,
         "original_sql_identical":False,"same_market_rules_verified":False,"real_bet":False}
    source={"version":"revue_phase6_pregame_source_predictions_v1",
            "entries":{row["id"]:row}}
    paper={"status":"revue_independent_picks_hub_static_research_paper_only",
       "real_bets_enabled":False,"research_model_calibrated":False,
       "verified_real_ev":False,"live_bookmaker_prices":False,
       "paper_summary":{"total":2,"settled":1,"pending":1,"excluded":0,
                        "paper_profit_units":1.1},
       "paper_records":[
           {"id":"paper-a","real_bet":False,"status":"won",
            "quote_at_utc":"2026-10-10T17:00:00Z",
            "locked_at_utc":"2026-10-10T17:05:00Z",
            "start_utc":k,"market":"h2h","paper_stake_units":1,
            "decimal_odds":2.1,"paper_profit_units":1.1,"verified_pregame":True},
           {"id":"paper-b","real_bet":False,"status":"pending",
            "quote_at_utc":"2026-10-10T17:00:00Z",
            "locked_at_utc":"2026-10-10T17:05:00Z",
            "start_utc":k,"market":"h2h","paper_stake_units":1,
            "decimal_odds":1.8,"paper_profit_units":None}]}
    return radar,source,paper
class Tests(unittest.TestCase):
    def test_exact_archived_quote_never_called_live_ev(self):
        r=build(*sample(),NOW)
        self.assertEqual(r["quote_sources"]["market_rows"],1)
        self.assertEqual(r["phase6_join"]["source_selections_with_exact_archived_prices"],1)
        self.assertEqual(r["phase6_join"]["verified_bookable_market_prices"],0)
        self.assertEqual(r["verified_positive_EV_opportunities"],0)
        self.assertEqual(r["paper_performance"]["paper_roi_settled_only_pct"],110)
        self.assertFalse(r["profitable_strategy_proven"])
    def test_wrong_line_rejected(self):
        x=sample();x[0]["observations"][0]["bookmakers"][0]["markets"][0]["outcomes"][0]["line"]=6.5
        r=build(*x,NOW)
        self.assertEqual(r["phase6_join"]["source_selections_with_exact_archived_prices"],0)
    def test_wrong_teams_rejected(self):
        x=sample();x[0]["observations"][0]["home"]="NYI"
        r=build(*x,NOW)
        self.assertEqual(r["phase6_join"]["source_selections_with_exact_archived_prices"],0)
        self.assertIn("fixture_identity_or_start_differs",r["phase6_join"]["statuses"])
    def test_unverified_market_cannot_become_live_from_price(self):
        x=sample();m=x[0]["observations"][0]["bookmakers"][0]["markets"][0]
        m["period_rule"]="including_ot_confirmed"
        m["period_rule_source"]="provider_verified"
        r=build(*x,NOW)
        self.assertEqual(r["phase6_join"]["verified_bookable_market_prices"],0)
        self.assertEqual(r["phase6_join"]["verified_positive_ev"],0)
    def test_quote_after_kickoff_rejected(self):
        x=sample();x[0]["observations"][0]["bookmakers"][0]["markets"][0]["quote_at"]="2026-10-11T01:01:00Z"
        with self.assertRaises(ValueError):build(*x,NOW)
    def test_duplicate_market_selection_fails_closed(self):
        x=sample();m=x[0]["observations"][0]["bookmakers"][0]["markets"][0]
        m["outcomes"].append(deepcopy(m["outcomes"][0]))
        with self.assertRaises(ValueError):build(*x,NOW)
    def test_paper_pnl_tamper_rejected(self):
        x=sample();x[2]["paper_records"][0]["paper_profit_units"]=99
        with self.assertRaises(ValueError):build(*x,NOW)
    def test_unsettled_paper_profit_rejected(self):
        x=sample();x[2]["paper_records"][1]["paper_profit_units"]=1
        with self.assertRaises(ValueError):build(*x,NOW)
    def test_wrong_snapshot_claim_rejected(self):
        x=sample();x[0]["market_prices_are_live"]=True
        with self.assertRaises(ValueError):build(*x,NOW)
    def test_cfb_not_in_report(self):
        x=sample();x[0]["observations"][0]["league"]="CFB"
        r=build(*x,NOW)
        self.assertEqual(r["quote_sources"]["fixtures"],0)
        self.assertTrue(r["CFB_excluded"])
    def test_real_docs_if_available(self):
        from pathlib import Path
        import json
        d=Path(__file__).resolve().parents[1]/"docs"
        files=["pulsescore-radar-latest.json","phase6-pregame-ledger.json","picks-center-latest.json"]
        if not all((d/f).is_file() for f in files):self.skipTest("No real source snapshots")
        x=[json.loads((d/f).read_text()) for f in files]
        r=build(*x,datetime.now(timezone.utc))
        self.assertFalse(r["verified_live_quotes"])
        self.assertFalse(r["profitable_strategy_proven"])
        self.assertEqual(r["phase6_join"]["verified_bookable_market_prices"],0)
if __name__=="__main__":unittest.main()
