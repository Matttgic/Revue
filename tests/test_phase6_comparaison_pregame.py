"""Phase 6: no cherry-picked historical comparisons or source-lock mislabelling."""
import unittest
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from outils.phase6_comparaison_pregame import build,VERSION,verify_ledger
NOW=datetime(2026,10,10,21,0,tzinfo=timezone.utc)
SHA="a"*40

def examples():
    source={
       "generated":"2026-10-10T20:45:00Z",
       "nhl":{"today":[{"id":2026020080,"home":"BOS","away":"PHI",
           "date":"2026-10-11T01:00:00Z","state":"FUT"}],"tomorrow":[]},
       "nba":{"today":[{"id":"401902645","home":"TOR","away":"LAC",
           "date":"2026-10-11T01:00:00Z","state":"pre","seasonType":1}],"tomorrow":[]},
       "mlb":{"today":[{"id":"401908031","home":"NYM","away":"ATL",
           "date":"2026-10-11T01:00:00Z","state":"pre"}],"tomorrow":[]},
       "bestBets":[
          {"sport":"NHL","game":"PHI @ BOS","pick":"PHI ML 110",
           "prob":45.0,"date":"2026-10-10"},
          {"sport":"NBA","game":"LAC @ TOR","pick":"TOR ML -115",
           "prob":52.0,"date":"2026-10-10"},
          {"sport":"MLB","game":"ATL @ NYM","pick":"NYM ML -130",
           "prob":54.0,"date":"2026-10-10"},
       ]}
    revue={"status":"experimental_revue_match_center",
           "generated_at_utc":"2026-10-10T20:47:00Z",
           "bookmaker_prices_are_live":False,"real_bets_enabled":False,
           "events":[{
               "key":"NHL:2026020080","league":"NHL","event_id":"2026020080",
               "home":"BOS","away":"PHI","start_utc":"2026-10-11T01:00:00Z",
               "research":[{"id":"clairvoyance_nhl_formula_revue_inputs",
                "source_generated_utc":"2026-10-10T20:47:00Z",
                "probabilities":{"home_win":.59,"away_win":.41}}]},
             {"key":"MLB:401908031","league":"MLB","event_id":"401908031",
               "home":"NYM","away":"ATL","start_utc":"2026-10-11T01:00:00Z",
               "research":[{"id":"revue_ensemble_mc_bayes_elo",
                "source_generated_utc":"2026-10-10T20:48:00Z",
                "probabilities":{"home_win":.57,"away_win":.43}}]}]}
    return source,{},revue

class Phase6Tests(unittest.TestCase):
    def test_first_observed_nhl_and_mlb_saved_without_source_sql_claim(self):
        src,soc,own=examples()
        ledger,report=build(src,soc,own,{},SHA,NOW)
        self.assertEqual(report["new_predictions_locked_this_run"],2)
        self.assertEqual(report["observed_output_comparisons"],2)
        self.assertEqual(report["by_sport"]["NBA"]["prospective_locked"],0)
        self.assertEqual(report["excluded_in_current_scan"]["nba_preseason_not_regular"],1)
        nhl=next(x for x in ledger["entries"].values() if x["league"]=="NHL")
        self.assertEqual(nhl["original_probability"],.45)
        self.assertEqual(nhl["revue_probability"],.41)
        self.assertEqual(nhl["probability_delta_revue_minus_source_pp"],-4.)
        self.assertFalse(nhl["source_model_lock_proven"])
        self.assertFalse(nhl["same_market_rules_verified"])
    def test_existing_source_snapshots_are_never_rewritten(self):
        source,soc,own=examples()
        first,report=build(source,soc,own,{},SHA,NOW)
        newer=deepcopy(source)
        newer["bestBets"][0]["prob"]=62
        own["events"][0]["research"][0]["probabilities"]["away_win"]=.49
        frozen,later=build(newer,soc,own,first,SHA,NOW+timedelta(minutes=2))
        self.assertEqual(frozen["entries"],first["entries"])
        self.assertEqual(later["new_predictions_locked_this_run"],0)
    def test_picks_with_live_label_never_locked(self):
        source,soc,own=examples()
        source["bestBets"][0]["pick"]="PHI ML 110 [LIVE]"
        ledger,report=build(source,soc,own,{},SHA,NOW)
        self.assertEqual(report["excluded_in_current_scan"]["live_selection"],1)
        self.assertEqual(report["new_predictions_locked_this_run"],1)
    def test_unavailable_revue_market_keeps_source_record(self):
        source,soc,own=examples()
        own["events"]=[]
        frozen,r=build(source,soc,own,{},SHA,NOW)
        self.assertEqual(r["new_predictions_locked_this_run"],2)
        self.assertEqual(r["observed_output_comparisons"],0)
        self.assertTrue(all(x["revue_probability"] is None for x in frozen["entries"].values()))
    def test_post_start_observation_is_not_backfilled(self):
        source,soc,own=examples()
        after=datetime(2026,10,11,1,tzinfo=timezone.utc)
        source["generated"]="2026-10-11T00:55:00Z"
        # same event, only because fixture now too close; document day mismatch as well.
        ledger,r=build(source,soc,{**own,"generated_at_utc":"2026-10-11T00:55:00Z"}, {},SHA,after)
        self.assertEqual(r["new_predictions_locked_this_run"],0)
    def test_wrong_identity_and_event_times_cannot_be_compared(self):
        for change in [
            lambda x:x["events"][0].update(home="FAKE"),
            lambda x:x["events"][0].update(start_utc="2026-10-11T04:00:00Z"),
            lambda x:x["events"][0]["research"][0].update(source_generated_utc="2026-10-11T00:55:00Z"),
        ]:
            src,soc,own=examples();change(own)
            _,r=build(src,soc,own,{},SHA,NOW)
            self.assertEqual(r["by_sport"]["NHL"]["with_revue_comparison"],0)
    def test_untimestamped_or_stale_sources_fail_closed(self):
        src,soc,own=examples()
        src["generated"]="2026-10-10T10:00:00Z"
        with self.assertRaises(ValueError):build(src,soc,own,{},SHA,NOW)
        src,soc,own=examples();own["bookmaker_prices_are_live"]=True
        with self.assertRaises(ValueError):build(src,soc,own,{},SHA,NOW)
    def test_ledger_cannot_be_relabelled_as_verified_original(self):
        src,soc,own=examples()
        frozen,_=build(src,soc,own,{},SHA,NOW)
        row=next(iter(frozen["entries"].values()))
        row["source_model_lock_proven"]=True
        with self.assertRaises(ValueError):verify_ledger(frozen,NOW)
    def test_duplicate_original_market_cannot_inflate(self):
        src,soc,own=examples()
        src["bestBets"].append(deepcopy(src["bestBets"][0]))
        _,r=build(src,soc,own,{},SHA,NOW)
        self.assertEqual(r["excluded_in_current_scan"]["duplicate_in_original_snapshot"],1)
        self.assertEqual(r["new_predictions_locked_this_run"],2)
    def test_source_sport_without_published_outputs_is_explicit_zero(self):
        src,soc,own=examples()
        src["bestBets"]=[src["bestBets"][0]]
        _,r=build(src,soc,own,{},SHA,NOW)
        self.assertEqual(r["by_sport"]["FOOTBALL"]["source_selections_in_latest_document"],0)
        self.assertEqual(r["by_sport"]["NBA"]["source_selections_in_latest_document"],0)
        self.assertEqual(r["by_sport"]["MLB"]["source_selections_in_latest_document"],0)

class NHLMarketCases(unittest.TestCase):
    def test_exact_total_line_compares_only_to_same_line(self):
        s,soc,own=examples()
        s["bestBets"]=[{"sport":"NHL","game":"PHI @ BOS","pick":"UNDER 5.5",
                        "prob":56.0,"date":"2026-10-10"}]
        total={"status":"prototype_non_calibre",
               "generated_at_utc":"2026-10-10T20:50:00Z",
               "games":[{"event_id":"2026020080","home":"BOS","away":"PHI",
                         "start_utc":"2026-10-11T01:00:00Z",
                         "probabilities":{"over_5_5":.49}}]}
        locked,r=build(s,soc,own,{},SHA,NOW,total)
        self.assertEqual(r["observed_output_comparisons"],1)
        val=next(iter(locked["entries"].values()))
        self.assertEqual(val["market"],"nhl_total_unverified_period")
        self.assertEqual(val["line"],5.5)
        self.assertEqual(val["revue_probability"],.51)
        self.assertFalse(val["same_market_rules_verified"])
        total["games"][0]["probabilities"]={"over_6_5":.49}
        _,r=build(s,soc,own,{},SHA,NOW,total)
        self.assertEqual(r["observed_output_comparisons"],0)
        self.assertEqual(r["prospective_predictions_locked"],1)

    def test_puckline_frozen_but_does_not_invent_counterpart(self):
        s,soc,own=examples()
        s["bestBets"]=[{"sport":"NHL","game":"PHI @ BOS",
                        "pick":"PHI +1.5 (-192.0)",
                        "prob":65.8,"date":"2026-10-10"}]
        locked,r=build(s,soc,own,{},SHA,NOW)
        self.assertEqual(r["prospective_predictions_locked"],1)
        self.assertEqual(r["observed_output_comparisons"],0)
        val=next(iter(locked["entries"].values()))
        self.assertEqual(val["line"],1.5)
        self.assertEqual(val["status"],"revue_puckline_model_unavailable")
        self.assertIsNone(val["revue_probability"])

if __name__=="__main__":unittest.main()
