"""Contract suite for source snapshot comparability and strict temporal identity."""
import unittest
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from outils.clairvoyance_real_output_gap import (
    calendar,join_events,model_rows,report,date,SPORTS,source_timing_risk)
AT=datetime(2026,10,10,16,30,tzinfo=timezone.utc)
BASE="2026-10-10T15:12:08+00:00"

def fixture():
    nhl=[{"id":2026020070,"home":"BOS","away":"PHI","date":"2026-10-10T17:00:00Z","state":"FUT"},
         {"id":2026020071,"home":"NJD","away":"VAN","date":"2026-10-10T19:30:00Z","state":"FUT"}]
    nba=[{"id":"401902645","home":"TOR","away":"LAC","date":"2026-10-10T22:30Z","state":"pre"}]
    nfl=[{"id":"401872981","home":"JAX","away":"PHI","date":"2026-10-11T13:30Z","state":"pre"}]
    pl=[{"id":"401879268","home":"Arsenal","away":"Leeds United","date":"2026-10-10T11:30Z","status":"post"}]
    data={"generated":BASE,"nhl":{"today":nhl,"tomorrow":[]},
          "nba":{"today":nba,"tomorrow":[]},"mlb":{"today":[],"tomorrow":[]},
          "bestBets":[
              {"sport":"NHL","game":"PHI @ BOS","pick":"BOS ML -135","prob":64.4,"date":"2026-10-10"},
              {"sport":"NHL","game":"VAN @ NJD","pick":"UNDER 6.5","prob":56.0,"date":"2026-10-10"},
              {"sport":"NHL","game":"PHI @ BOS","pick":"PHI +1.5 (-135)","prob":62.0,"date":"2026-10-10"},
          ]}
    originals={"data":data,
       "nba":{"generated_at":"2026-10-10 15:20 UTC","games":nba},
       "nfl":{"generated_at":"2026-10-10 15:25 UTC","weeks":{"Week 5":nfl}},
       "soccer":{"generated_at":"2026-10-10 15:30 UTC","leagues":{"pl":pl}}}
    revue={"events":[
      {"league":"NHL","event_id":"2026020070","home":"BOS","away":"PHI","start_utc":nhl[0]["date"],"research":[]},
      {"league":"NHL","event_id":"2026020071","home":"NJD","away":"VAN","start_utc":nhl[1]["date"],"research":[{"id":"x"}]},
      {"league":"NBA","event_id":"401902645","home":"Raptors","away":"Clippers","start_utc":"2026-10-10T22:30Z","research":[]},
      {"league":"NFL","event_id":"401872981","home":"Jaguars","away":"Eagles","start_utc":"2026-10-11T13:30Z","research":[]},
      {"league":"PL","event_id":"401879268","home":"Arsenal","away":"Leeds","start_utc":"2026-10-10T11:30Z","research":[]}
    ]}
    shadow={"generated_at_utc":"2026-10-10T13:45Z","games":[
        {"event_id":"2026020070","home":"BOS","away":"PHI","start_utc":nhl[0]["date"],
         "home_win":.652,"away_win":.348}]}
    nhl_model={"generated_at_utc":"2026-10-10T13:50Z","games":[
       {"event_id":"2026020071","home":"NJD","away":"VAN","start_utc":nhl[1]["date"],
        "probabilities":{"over_6_5":.677}}]}
    return originals,revue,shadow,nhl_model

class SourceGapTests(unittest.TestCase):
    def test_original_multi_source_duplicates_are_deduplicated_not_double_counted(self):
        a,revue,shadow,model=fixture()
        unique,meta,ambiguous=calendar(a,AT)
        self.assertEqual(len(unique),5)
        self.assertEqual(ambiguous,[])
        self.assertIn("NBA:401902645",unique)
        self.assertEqual(meta["nba"]["status"],"fresh")
        self.assertEqual(meta["data"]["status"],"fresh")

    def test_cross_sport_identity_uses_ids_and_kickoffs_not_guess_team_name(self):
        a,revue,shadow,model=fixture()
        sources,_,_=calendar(a,AT)
        joined,miss,rej,duplicates=join_events(sources,revue)
        self.assertEqual(len(joined),5)
        self.assertEqual(miss,{})
        self.assertEqual(rej,{})
        nba=next(x for x in joined if x["league"]=="NBA")
        self.assertFalse(nba["identical_names"])
        self.assertTrue(nba["id_and_kickoff_verified"])
        self.assertFalse(nba["model_output_parity_verified"])

    def test_kickoff_mismatch_excluded(self):
        a,revue,shadow,model=fixture()
        revue["events"][0]["start_utc"]="2026-10-11T17:00:00Z"
        joined,miss,rej,dup=join_events(calendar(a,AT)[0],revue)
        self.assertEqual(len(joined),4)
        self.assertEqual(rej["kickoff_mismatch"],1)

    def test_original_mismatched_conflicting_duplicate_ref_ids_rejected(self):
        a,revue,shadow,model=fixture()
        a["nba"]["games"]=[{**a["nba"]["games"][0],"date":"2026-10-12T22:30Z"}]
        _,_,bad=calendar(a,AT)
        self.assertIn("NBA:401902645",bad)

    def test_nhl_published_moneyline_and_totals_comparison_without_source_betting(self):
        a,revue,shadow,model=fixture()
        arr,counts,mean=model_rows(a["data"],shadow,model,date(BASE),AT)
        self.assertEqual(len(arr),2)
        self.assertEqual(counts["compared"],2)
        self.assertEqual(counts["unsupported_market_spread_or_prop"],1)
        self.assertEqual(arr[0]["difference_revue_minus_original_pp"],.8)
        self.assertEqual(arr[1]["difference_revue_minus_original_pp"],-23.7)
        self.assertEqual(mean,12.25)
        self.assertTrue(all(x["same_scheduled_fixture_and_market"] for x in arr))
        self.assertTrue(all(x["source_quote_is_french_live_verified"] is False for x in arr))

    def test_predictions_after_match_kickoff_cannot_be_relabelled_pregame(self):
        a,revue,shadow,model=fixture()
        late=deepcopy(a["data"])
        late["generated"]="2026-10-10T20:00:00Z"
        arr,counts,mean=model_rows(late,shadow,model,date(late["generated"]),AT)
        self.assertEqual(arr,[])
        self.assertEqual(counts["source_generated_after_kickoff"],2)
        self.assertEqual(mean,None)

    def test_original_public_roi_basis_excludes_late_and_unknown_locks(self):
        status=source_timing_risk({"basis":"all locks (including picks locked after the game started)",
             "basis_detail":{"settled_pre_start":1051,
                 "settled_locked_after_start_included":181,
                 "settled_unknown_timing_included":2614}})
        self.assertEqual(status["status"],"observed")
        self.assertEqual(status["observed_classified_total"],3846)
        self.assertEqual(status["non_pre_match_proven_or_unknown"],2795)
        self.assertTrue(status["may_not_be_claimed_as_reproducible_roi"])
        self.assertEqual(source_timing_risk({})["status"],"invalid_counts")

    def test_original_and_revue_full_data_namespaces_are_never_co_mingled(self):
        a,revue,shadow,model=fixture()
        r=report(a["data"],a["soccer"],a["nfl"],a["nba"],revue,shadow,model,AT)
        self.assertEqual(r["strict_event_matches"],5)
        self.assertEqual(r["source_fixture_total"],5)
        self.assertEqual(r["nhl_same_market_model_comparisons"],2)
        self.assertFalse(r["real_bets_enabled"])
        self.assertFalse(r["live_french_odds_verified"])
        self.assertFalse(r["exact_prediction_parity_verified"])
        self.assertTrue(r["original_history_profit_report_excluded"])
        self.assertEqual(set(r["by_league"]),set(SPORTS))

if __name__=="__main__":unittest.main()
