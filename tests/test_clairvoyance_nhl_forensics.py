"""Temporal and source-provenance guards for independent NHL input comparison."""
import copy,unittest
from datetime import datetime,timezone,timedelta
from outils.clairvoyance_nhl_forensics import make,strict_input_match,extract_xg_note
T=datetime(2026,10,10,15,30,tzinfo=timezone.utc)
def time(hours=0):return (T+timedelta(hours=hours)).isoformat()
def fixture():
    names={"AAA":.51,"BBB":.32,"CCC":.62,"DDD":.41,"EEE":.57,"FFF":.45}
    games=[];models=[];compares=[];picks=[]
    for i,(home,away) in enumerate([("AAA","BBB"),("CCC","DDD"),("EEE","FFF")]):
        eid=str(2026020070+i)
        kickoff=time(6+i)
        games.append({"id":int(eid),"home":home,"away":away,"date":kickoff,"state":"FUT"})
        models.append({"event_id":eid,"home":home,"away":away,"start_utc":kickoff,
                       "xg_5v5_share_pct":{"home":names[home]*100,"away":names[away]*100}})
        picks.append({"sport":"NHL","game":away+" @ "+home,"pick":home+" ML -105",
                      "prob":.61*100,"note":f"xGF%: {home} {names[home]*100:.1f} / {away} {names[away]*100:.1f}"})
        for market,side,line,p,q in [
            ("moneyline_including_overtime","home",None,.61,.43+i*.03),
            ("full_game_total","under",5.5,.56,.43+i*.1)]:
            compares.append({"status":"compared","key":"NHL:"+eid,
                 "home":home,"away":away,"kickoff_utc":kickoff,
                 "original_observed_at_utc":time(-1),"revue_observed_at_utc":time(-2),
                 "market":market,"side":side,"line":line,"original_probability":p,
                 "revue_probability":q})
    data={"generated":time(-1),"bestBets":picks,
          "nhl":{"today":games,"tomorrow":[]},
          "mp":{"teams":{k:{"5on5":{"xgfPct":v}} for k,v in names.items()}}}
    shadow={"generated_at_utc":time(-2),"status":"experimental_not_calibrated",
            "bookmaker_odds_available":False,"games":models}
    gap={"status":"public_original_source_fixture_and_nhl_output_diagnostic",
         "real_bets_enabled":False,"exact_prediction_parity_verified":False,
         "source_inputs":{"data":{"observed_at_utc":time(-1)}},
         "nhl_source_vs_revue":compares}
    return data,shadow,gap

class NHLForensics(unittest.TestCase):
    def test_real_model_features_same_xg_but_changed_probabilities(self):
        out=make(*fixture(),T)
        self.assertEqual(out["status"],"nhl_forensics_verified_observation_alignment")
        self.assertEqual(out["input_summary"]["identical_5v5_xg_both_teams"],3)
        self.assertEqual(out["input_summary"]["published_pick_xg_notes_equal_reference_input"],3)
        self.assertEqual(out["model_summary"]["moneyline"]["comparisons"],3)
        self.assertEqual(out["model_summary"]["identical_xg_but_moneyline_gap_over_5pp"],3)
        self.assertEqual(out["model_summary"]["totals"]["comparisons"],3)
        self.assertEqual(out["model_summary"]["repeated_reference_probability_clusters"][0]["distinct_games"],3)
        self.assertEqual(out["model_summary"]["repeated_reference_probability_clusters"][0]["original_probability"],.56)
        self.assertFalse(out["exact_prediction_replication_verified"])
        self.assertFalse(out["backend_predictor_is_the_published_best_bet_model_verified"])
        self.assertFalse(out["betting_recommendations_verified"])
        self.assertEqual(len(out["match_diagnostics"]),6)

    def test_picks_missing_xg_not_invented(self):
        d,s,g=fixture()
        del d["mp"]["teams"]["AAA"]
        d["bestBets"][0]["note"]="No confirmed feature"
        o=make(d,s,g,T)
        self.assertEqual(o["input_summary"]["missing_5v5_xg"],1)
        self.assertEqual(o["input_summary"]["published_pick_xg_notes_usable"],2)
        self.assertEqual(o["model_summary"]["identical_xg_but_moneyline_gap_over_5pp"],2)

    def test_same_published_source_snapshot_is_mandatory(self):
        d,s,g=fixture()
        g["source_inputs"]["data"]["observed_at_utc"]=time(-3)
        out=make(d,s,g,T)
        self.assertEqual(out["source_input_guard"],"different_observation_snapshots")
        self.assertEqual(out["match_diagnostics"],[])
        self.assertFalse(out["exact_prediction_replication_verified"])

    def test_merged_shadow_at_another_time_is_not_a_same_input_test(self):
        d,s,g=fixture()
        s["generated_at_utc"]=time(-2.5)
        self.assertEqual(strict_input_match(d,s,g,T),"different_observation_snapshots")

    def test_stale_and_future_observations_rejected(self):
        d,s,g=fixture()
        d["generated"]=time(-100)
        self.assertEqual(make(d,s,g,T)["status"],"nhl_forensics_waiting_same_observation")
        d,s,g=fixture()
        d["generated"]=time(1)
        self.assertEqual(make(d,s,g,T)["status"],"nhl_forensics_waiting_same_observation")

    def test_only_original_matching_event_identity_and_kickoff(self):
        d,s,g=fixture()
        s["games"][0]["start_utc"]=time(11)
        result=make(d,s,g,T)
        self.assertEqual(result["input_summary"]["same_event_and_kickoff_nhl"],2)
        self.assertEqual(result["model_summary"]["all"]["comparisons"],4)

    def test_note_rejected_for_different_team(self):
        bad={"note":"xGF%: XXX 52.0 / BBB 55.0"}
        self.assertIsNone(extract_xg_note(bad,"AAA","BBB"))

    def test_change_xg_does_not_conflate_model_gap_with_data_gap(self):
        d,s,g=fixture()
        s["games"][0]["xg_5v5_share_pct"]["home"]=10
        out=make(d,s,g,T)
        self.assertEqual(out["input_summary"]["different_5v5_xg"],1)
        self.assertEqual(out["model_summary"]["identical_xg_but_moneyline_gap_over_5pp"],2)

    def test_ambiguous_id_never_joined(self):
        d,s,g=fixture()
        d["nhl"]["tomorrow"].append(copy.deepcopy(d["nhl"]["today"][0]))
        out=make(d,s,g,T)
        self.assertEqual(out["input_summary"]["ambiguous_reference_event_ids"],1)
        self.assertEqual(out["model_summary"]["all"]["comparisons"],4)

if __name__=="__main__":unittest.main()
