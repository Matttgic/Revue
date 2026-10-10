"""NHL source-input comparison must never write frozen bets or backfill."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.nhl_source_input_gap import analyze
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
EARLY=(NOW-timedelta(hours=2)).isoformat()
MID=(NOW-timedelta(hours=1)).isoformat()
KICK=(NOW+timedelta(hours=3)).isoformat()

def fixture():
    t={"source":"MoneyPuck.com","current_season":"2026-2027",
       "generated_at_utc":EARLY,
       "status":{"2026-2027":{"status":"available","source_updated_utc":EARLY}},
       "seasons":{"2026-2027":[
         {"team":k,"situation":s,"xg_share":v}
         for k,s,v in [("BOS","5on5",.51),("PHI","5on5",.32),
                       ("BOS","all",.60),("PHI","all",.44)]]}}
    g={"source":"MoneyPuck.com","current_season":"2026-2027",
       "generated_at_utc":EARLY,
       "statuses":{"2026-2027":{"status":"available","source_updated_utc":EARLY}}}
    n={"source":"api.nhle.com/stats/rest/en",
       "status":"verified_nhl_official_stats_snapshot","generated_at_utc":MID,
       "season":"20262027","game_type_id":2,
       "goalies":[{"team_abbrev":k,"season":"20262027","game_type_id":2,
                   "games_played":4,"overall_save_pct":v,"player_name":k}
                  for k,v in [("BOS",.88),("PHI",.91)]]}
    s={"status":"experimental_not_calibrated","bookmaker_odds_available":False,
       "generated_at_utc":EARLY,
       "games":[{"event_id":"2026020070","home":"BOS","away":"PHI",
                 "start_utc":KICK,"home_elo_proxy":1530.0,"away_elo_proxy":1480.0,
                 "home_win":.65,"xg_5v5_share_pct":{"home":51.0,"away":32.0},
                 "historical_goalie_proxy":{"home":{"save_pct":.92},
                                            "away":{"save_pct":.90}}}]}
    return t,g,n,s

class NHLGapTests(unittest.TestCase):
    def test_diff_is_measured_not_original(self):
        d=analyze(*fixture(),NOW)
        self.assertEqual(d["games_comparable"],1)
        self.assertEqual(d["games_with_unique_nhl_official_goalie"],1)
        self.assertEqual(d["different_all_vs_5on5_team_rates"],2)
        self.assertNotEqual(d["games"][0]["xg_only_change_pp"],0)
        self.assertNotEqual(d["games"][0]["combined_change_pp"],0)
        self.assertGreater(d["mean_abs_delta_source_xg_input_scale_pp"],0)
        self.assertFalse(d["raw_moneypuck_fraction_scenario"]
                         ["original_database_raw_value_equality_verified"])
        g=d["games"][0]
        self.assertNotEqual(g["all_xg_only_home_probability"],
                            g["all_xg_raw_fraction_only_home_probability"])
        self.assertNotEqual(g["all_xg_and_official_goalie_home_probability"],
                            g["all_xg_raw_fraction_and_official_goalie_home_probability"])
        self.assertFalse(d["real_bets_enabled"])
        self.assertFalse(d["original_inputs_identical"])
        self.assertTrue(d["nhl_goalies_observed_after_frozen_forecast"])

    def test_ambiguous_starting_goalie_does_not_get_arbitrary_pick(self):
        f=fixture()
        f[2]["goalies"].append({"team_abbrev":"BOS","season":"20262027",
                                 "game_type_id":2,"games_played":4,
                                 "overall_save_pct":.95,"player_name":"Other"})
        d=analyze(*f,NOW)
        self.assertEqual(d["games_with_unique_nhl_official_goalie"],0)
        self.assertIsNone(d["games"][0]["combined_change_pp"])

    def test_pre_match_timestamp_leakage_rejected(self):
        f=fixture()
        f[2]["generated_at_utc"]=(NOW+timedelta(hours=1)).isoformat()
        with self.assertRaises(ValueError):analyze(*f,NOW)
        f=fixture()
        f[3]["games"][0]["start_utc"]=(NOW+timedelta(minutes=5)).isoformat()
        self.assertEqual(analyze(*f,NOW)["games_comparable"],0)

    def test_mutated_money_puck_version_not_misattributed_to_situation(self):
        f=fixture()
        f[0]["seasons"]["2026-2027"][0]["xg_share"]=.54
        d=analyze(*f,NOW)
        self.assertEqual(d["games_comparable"],0)
        self.assertEqual(d["skipped"]["different_team_snapshot"],1)

    def test_fraction_scenario_uses_source_divisor_again_and_preserves_original_shadow(self):
        from modeles.reproduction.clairvoyance_predictor import elo_home_probability
        f=fixture()
        f[3]["games"][0]["home_elo_proxy"]=1500.0
        f[3]["games"][0]["away_elo_proxy"]=1500.0
        f[3]["games"][0]["historical_goalie_proxy"]["home"]["save_pct"]=.90
        f[3]["games"][0]["historical_goalie_proxy"]["away"]["save_pct"]=.90
        result=analyze(*f,NOW)["games"][0]
        base=elo_home_probability(1500,1500,25)
        all_xg_fraction_diff=.60-.44
        expect_raw=round(base+(all_xg_fraction_diff/100)*.3,3)
        expect_percent=round(base+(60-44)/100*.3,3)
        self.assertAlmostEqual(result["all_xg_raw_fraction_only_home_probability"],expect_raw)
        self.assertAlmostEqual(result["all_xg_only_home_probability"],expect_percent)
        self.assertAlmostEqual(
            result["raw_fraction_vs_pct_points_scale_change_pp"],
            round(100*(expect_raw-expect_percent),2))
        self.assertFalse(result["is_new_frozen_prediction"])

    def test_ambiguous_goalie_excludes_scale_both_without_guessing(self):
        f=fixture()
        f[2]["goalies"].append({
            "team_abbrev":"BOS","season":"20262027","game_type_id":2,
            "games_played":4,"overall_save_pct":.90,"player_name":"Another"})
        d=analyze(*f,NOW)
        self.assertIsNone(d["games"][0]
                           ["all_xg_raw_fraction_and_official_goalie_home_probability"])
        self.assertIsNone(d["mean_abs_delta_source_scale_with_official_goalie_pp"])
        self.assertIsNotNone(d["mean_abs_delta_source_xg_input_scale_pp"])

    def test_season_provenance_fails_closed(self):
        f=fixture()
        f[2]["game_type_id"]=3
        with self.assertRaises(ValueError):analyze(*f,NOW)
        f=fixture()
        f[0]["source"]="unknown"
        with self.assertRaises(ValueError):analyze(*f,NOW)
        f=fixture()
        f[2]["goalies"][0]["overall_save_pct"]=2.0
        with self.assertRaises(ValueError):analyze(*f,NOW)

if __name__=="__main__":unittest.main()
