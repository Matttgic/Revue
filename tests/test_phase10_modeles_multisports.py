"""Phase 10: ESPN-only prospective models reject mismatches, leakage and fake EV."""
import copy,json,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.phase10_modeles_multisports import build,VERSION,STATUS,NBA_ABBR
from outils.match_center_revue import instant

NOW=datetime(2026,10,10,20,tzinfo=timezone.utc)
OBS=(NOW-timedelta(hours=1)).isoformat()
KICK=(NOW+timedelta(hours=12)).isoformat()
def game(league,ident,h,a,prob=None):
 return {"league":league,"event_id":str(ident),"home":h,"away":a,
         "start_utc":KICK,"probabilities":prob}
def sample():
 nb=game("NBA","1","Hawks","Celtics")
 mb=game("MLB","2","Guardians","White Sox")
 fb=game("PL","3","Arsenal","Chelsea")
 allgames=[nb,mb,fb]
 center={"status":"experimental_revue_match_center","generated_at_utc":OBS,
         "real_bets_enabled":False,"bookmaker_prices_are_live":False,
         "validated_value_bets":0,"events":allgames}
 pp={"home_win":.64,"away_win":.36}
 nba={"status":"shadow_nba_prior_only","generated_at_utc":OBS,
      "previous_season_end_year":2026,
      "matches":[{**nb,"status":"shadow_prior_not_calibrated","probabilities":pp}]}
 rates={"status":"source_formula_observed_regular_season_advanced",
        "generated_at_utc":OBS,"season_previous":2026,"season_current":2027,
        "teams_with_previous_advanced":30,"teams_with_current_advanced":0,
        "teamRatings":{"statsMode":"prior","teams":{"ATL":{},"BOS":{}}},
        "eloSeed":{"ATL":1600,"BOS":1680}}
 mlb={"status":"conditional_source_elo_fallback_sensitivity_not_original_reproduction",
      "generated_at_utc":OBS,"diagnostic_elo_cutoff_utc":OBS,
      "original_sql_ratings_verified_equal":False,"market_moneylines_available":False,
      "games":[{**mb,"revue_historical_games_home":23,"revue_historical_games_away":27,
           "replayed_revue_home_probability":.55,
           "original_sql_elo_inputs_verified_equal":False,"market_moneylines_available":False}]}
 baseline={"generated_at_utc":OBS,"competitions":{"PL":{"games":[
     {**fb,"probabilities":{"home_win_90":.4,"draw_90":.29,
                           "away_win_90":.31,"over_2_5":.55},
      "training_games":{"home":7,"away":5}}]}}}
 advanced={"status":"shadow_experimental_never_auto_bet",
           "generated_at_utc":OBS,
           "licensed_advanced_features":{"records":0},
           "espn_observed_features":{"genuine_xg":False},
           "competitions":{"PL":{"games":[{**fb,"status":"shadow_non_calibre",
             "probabilities":{"home_win_90":.38,"draw_90":.31,"away_win_90":.31,"over_2_5":.57},
             "training_games":{"home":6,"away":5},
             "xg_used":False,"espn_stats_used":True}]}}}
 return center,baseline,nba,rates,mlb,advanced

class ModelTests(unittest.TestCase):
 def test_three_sports_and_no_money_or_ev(self):
  result=build(*sample(),NOW)
  self.assertEqual(result["version"],VERSION)
  self.assertEqual(result["status"],STATUS)
  self.assertEqual(result["metrics"]["candidates"],5)
  self.assertEqual(result["metrics"]["models_by_league"],{"NBA":3,"MLB":1,"PL":1})
  self.assertFalse(result["real_bets_enabled"])
  self.assertFalse(result["calibrated"])
  self.assertEqual(result["verified_positive_EV"],0)
  self.assertFalse(result["prices_are_currently_bookable"])
  self.assertTrue(result["no_historical_backfill"])
  for row in result["models"]:
   self.assertFalse(row["calibrated"])
   self.assertIsNone(row["EV"])
   self.assertIsNone(row["betting_recommendation"])
   p=row["probabilities"]
   total=sum(p.get(k,0) for k in (("home_win_90","draw_90","away_win_90") if row["league"]=="PL"
                                     else ("home_win","away_win")))
   self.assertAlmostEqual(total,1,places=5)
 def test_away_team_mismatch_never_joined(self):
  values=sample();values[2]["matches"][0]["away"]="Lakers"
  r=build(*values,NOW)
  self.assertNotIn("revue_nba_espn_previous_standings_prior_v1",
                    {x["model_id"] for x in r["models"]})
 def test_no_past_or_near_kickoff_predictions(self):
  values=sample()
  for e in values[0]["events"]:e["start_utc"]=(NOW+timedelta(minutes=15)).isoformat()
  self.assertEqual(build(*values,NOW)["metrics"]["candidates"],0)
 def test_no_licensed_xg_fabrication(self):
  values=sample();values[5]["espn_observed_features"]["genuine_xg"]=True
  ids={x["model_id"] for x in build(*values,NOW)["models"]}
  self.assertNotIn("revue_football_espn_shots_log_pool_v1",ids)
 def test_model_disagreement_causes_abstention(self):
  values=sample();values[5]["competitions"]["PL"]["games"][0]["probabilities"]={
    "home_win_90":.9,"draw_90":.05,"away_win_90":.05}
  ids={x["model_id"] for x in build(*values,NOW)["models"]}
  self.assertNotIn("revue_football_espn_shots_log_pool_v1",ids)
  self.assertEqual(build(*values,NOW)["metrics"]["decisions"].get("football_models_disagree_abstain"),1)
 def test_source_after_start_is_not_attached(self):
  values=sample();values[4]["diagnostic_elo_cutoff_utc"]=(NOW+timedelta(days=5)).isoformat()
  r=build(*values,NOW)
  self.assertNotIn("revue_mlb_espn_history_elo_v1",{x["model_id"] for x in r["models"]})
 def test_nba_advanced_wrong_year_only_one_prior(self):
  values=sample();values[3]["season_current"]=2028
  nba=[x for x in build(*values,NOW)["models"] if x["league"]=="NBA"]
  self.assertEqual([x["model_id"] for x in nba],["revue_nba_espn_previous_standings_prior_v1"])
 def test_models_disappear_when_sources_are_stale(self):
  values=sample();values[0]["generated_at_utc"]=(NOW-timedelta(days=8)).isoformat()
  with self.assertRaises(ValueError):build(*values,NOW)
 def test_unsafe_match_center_rejected(self):
  values=sample();values[0]["bookmaker_prices_are_live"]=True
  with self.assertRaises(ValueError):build(*values,NOW)
 def test_cfb_never_added(self):
  values=sample()
  values[0]["events"].append(game("CFB","999","A","B"))
  r=build(*values,NOW)
  self.assertEqual(r["metrics"]["candidates"],5)
  self.assertTrue(r["CFB_excluded"])
 def test_previous_nba_labels_are_explicit_no_guess(self):
  self.assertEqual(len(NBA_ABBR),30)
  self.assertEqual(NBA_ABBR["76ers"],"PHI")
  self.assertEqual(NBA_ABBR["Trail Blazers"],"POR")
 def test_existing_real_snapshots_have_all_three_sports(self):
  d=Path(__file__).resolve().parents[1]/"docs"
  paths=("match-center-latest.json","multisports-latest.json","nba-prior-shadow.json",
         "clairvoyance-nba-advanced-ratings.json","mlb-source-elo-gap.json",
         "football-advanced-shadow.json")
  if not all((d/p).exists() for p in paths):self.skipTest("Real snapshot absent")
  items=[json.loads((d/p).read_text(encoding="utf8")) for p in paths]
  now=instant(items[0]["generated_at_utc"])+timedelta(minutes=1)
  r=build(*items,now)
  self.assertGreater(r["metrics"]["models_by_league"].get("NBA",0),0)
  self.assertGreater(r["metrics"]["models_by_league"].get("MLB",0),0)
  self.assertGreater(sum(v for k,v in r["metrics"]["models_by_league"].items() if k in
         {"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL"}),0)
  self.assertTrue(all(x["probabilities"] for x in r["models"]))
  self.assertEqual(r["verified_positive_EV"],0)


 def test_phase10_matches_only_exact_teams_and_clocks_in_match_center(self):
  from outils.match_center_revue import collect_center
  p=sample()
  model_report=build(*p,NOW)
  base=p[1];advanced=p[5]
  fixture_data={"generated_at_utc":OBS,"competitions":{
   "PL":{"sport":"Football","games":base["competitions"]["PL"]["games"]}}}
  scanner={"mode":"PAPER_ONLY","odds_board":{"events":[]}}
  nhl={"generated_at_utc":OBS,"games":[]}
  ensemble={"generated_at_utc":OBS,"leagues":{}}
  def attach(report):
   return collect_center(fixture_data,scanner,advanced,nhl,ensemble,NOW,
                         model_candidates=report)
  good=attach(model_report)
  event=good["events"][0]
  self.assertIn("revue_football_espn_shots_log_pool_v1",{x["id"] for x in event["research"]})
  self.assertIsNone(event["ev"])
  self.assertFalse(event["qualified_for_real_betting"])
  changed=copy.deepcopy(model_report)
  football=[x for x in changed["models"] if x["league"]=="PL"][0]
  football["home"]="Wrong club"
  result=attach(changed)
  self.assertNotIn("revue_football_espn_shots_log_pool_v1",
     {x["id"] for x in result["events"][0]["research"]})
  changed=copy.deepcopy(model_report);changed["verified_positive_EV"]=1
  self.assertEqual(good["status"],"experimental_revue_match_center")
  rejected=attach(changed)
  self.assertNotIn("revue_football_espn_shots_log_pool_v1",
     {x["id"] for x in rejected["events"][0]["research"]})

if __name__=="__main__":unittest.main()
