"""Regression safety gates for current NBA, NHL, MLB and football inputs."""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import json,unittest
from outils.controles.phase5_donnees_multisports import build,nba,nhl,mlb,football,clock
NOW=datetime(2026,10,10,22,tzinfo=timezone.utc)
T="2026-10-10T18:00:00Z"
def samples():
    n={"status":"source_formula_observed_regular_season_advanced",
       "source_verified_espn_parser":True,"generated_at_utc":T,
       "season_previous":2026,"season_current":2027,
       "teams_with_previous_advanced":1,"teams_with_current_advanced":0,
       "teamRatings":{"statsSeasonUsed":2026,"teams":{
           "BOS":{"prior":{"ortg":115,"drtg":113},"current":{"netRtg":None}}}}}
    mp={"source":"MoneyPuck.com","is_live":False,"generated_at_utc":T,
        "current_season":"2026-2027","status":{"2026-2027":{"status":"available"}},
        "seasons":{"2026-2027":[{"team":t,"situation":s,"xg_share":p}
           for t in ("BOS","PHI") for s,p in (("all",.52),("5on5",.55))]}}
    g={"source":"api.nhle.com/stats/rest/en","status":"verified_nhl_official_stats_snapshot",
       "season":"20262027","game_type_id":2,"generated_at_utc":T,
       "goalies":[{"season":"20262027","game_type_id":2,"team_abbrev":t,
                   "games_played":3,"overall_save_pct":.91} for t in ("BOS","PHI")]}
    shadow={"status":"backend_style_input_scenario_not_original_model_parity",
       "generated_at_utc":T,"original_sql_ratings_available":False,
       "has_verified_original_predictions":False,"real_bets_enabled":False,
       "games":[{"home":"BOS","away":"PHI","kickoff_utc":"2026-10-11T01:00:00Z",
                 "source_observed_by_frozen_model_time":True,
                 "raw_fraction_home_probability":.56}]}
    m={"status":"conditional_source_elo_fallback_sensitivity_not_original_reproduction",
       "generated_at_utc":T,"original_sql_ratings_verified_equal":False,
       "historical_sql_coverage_proven_identical":False,
       "market_moneylines_available":False,"diagnostic_revue_completed_espn_games":12,
       "games_comparable":1,"games":[{"original_sql_elo_inputs_verified_equal":False,
             "replayed_revue_home_probability":.55}]}
    f={"status":"real_boxscore_derived_not_opta","generated_at_utc":T,
       "xg_available":False,"opta_available":False,
       "teams":{"PL:10":{"type":"observed_shots_not_xg",
                         "shots_per_game":12,"sot_per_game":5}}}
    fs={"status":"shadow_experimental_never_auto_bet","generated_at_utc":T,
        "licensed_advanced_features":{"status":"no_authorized_source"},
        "espn_observed_features":{"genuine_xg":False,"teams":1},
        "competitions":{"PL":{"games":[{
            "xg_used":False,"espn_stats_used":True,"status":"shadow_non_calibre"}]}}}
    return {"nba":n,"mp":mp,"goalies":g,"nhl":shadow,"mlb":m,"football":f,"football_shadow":fs}
class Tests(unittest.TestCase):
    def test_honest_four_sport_summary(self):
        x=build(samples(),NOW)
        self.assertEqual(x["four_sports_with_observed_data"],4)
        self.assertEqual(x["sports_with_identical_original_deployed_inputs_verified"],0)
        self.assertEqual(x["sports"]["NHL"]["historical_pregame_compatible_scenarios"],1)
        self.assertEqual(x["sports"]["FOOTBALL"]["authorized_Opta_xG_fixtures"],0)
        self.assertFalse(x["real_bets_enabled"])
    def test_nba_no_preseason_as_current(self):
        x=samples()["nba"];x["teamRatings"]["statsSeasonUsed"]=2027
        with self.assertRaises(ValueError):nba(x,NOW)
        x=samples()["nba"];x["teams_with_current_advanced"]=30
        with self.assertRaises(ValueError):nba(x,NOW)
    def test_nhl_correct_season_and_no_tied_most_played(self):
        f=samples();f["goalies"]["game_type_id"]=3
        with self.assertRaises(ValueError):
            nhl(f["mp"],f["goalies"],f["nhl"],NOW)
        f=samples();f["goalies"]["goalies"].append(deepcopy(f["goalies"]["goalies"][0]))
        result=nhl(f["mp"],f["goalies"],f["nhl"],NOW)
        self.assertEqual(result["teams_with_both_situations_and_goalie"],1)
        self.assertEqual(result["historical_pregame_compatible_scenarios"],0)
    def test_no_after_kickoff_pre_match_data(self):
        f=samples();f["nhl"]["games"][0]["kickoff_utc"]="2026-10-10T18:05:00Z"
        self.assertEqual(nhl(f["mp"],f["goalies"],f["nhl"],NOW)["historical_pregame_compatible_scenarios"],0)
    def test_mlb_sql_and_count_cannot_be_forged(self):
        m=samples()["mlb"];m["original_sql_ratings_verified_equal"]=True
        with self.assertRaises(ValueError):mlb(m,NOW)
        m=samples()["mlb"];m["games_comparable"]=2
        with self.assertRaises(ValueError):mlb(m,NOW)
    def test_no_unlicensed_football_xg(self):
        x=samples();x["football"]["opta_available"]=True
        with self.assertRaises(ValueError):football(x["football"],x["football_shadow"],NOW)
        x=samples();x["football_shadow"]["competitions"]["PL"]["games"][0]["xg_used"]=True
        with self.assertRaises(ValueError):football(x["football"],x["football_shadow"],NOW)
    def test_future_data_and_naive_date(self):
        x=samples();x["mp"]["generated_at_utc"]="2026-10-12T18:00:00Z"
        with self.assertRaises(ValueError):build(x,NOW)
        with self.assertRaises(ValueError):clock("2026-10-10T18:00:00")
    def test_real_snapshots_when_present(self):
        p=Path(__file__).resolve().parents[1]/"docs"
        names={"nba":"clairvoyance-nba-advanced-ratings.json",
               "mp":"moneypuck-nhl-latest.json","goalies":"nhl-official-stats-latest.json",
               "nhl":"nhl-backend-source-style-latest.json",
               "mlb":"mlb-source-elo-gap.json",
               "football":"football-espn-team-features.json",
               "football_shadow":"football-advanced-shadow.json"}
        if not all((p/n).is_file() for n in names.values()):
            self.skipTest("Source snapshots absent")
        result=build({k:json.loads((p/v).read_text()) for k,v in names.items()},
                     datetime.now(timezone.utc))
        self.assertFalse(result["same_clairvoyance_published_predictions_verified"])
        self.assertFalse(result["Opta_xG_authorized_and_ingested"])
        self.assertEqual(result["paid_api_calls"],0)
if __name__=="__main__":unittest.main()
