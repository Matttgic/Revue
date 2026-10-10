"""Official MLB Stats API probable pitcher evidence: pregame only; never a confirmed starter."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.mlb_official_pitchers import team_name,eligible_game,collect

NOW=datetime(2026,10,11,0,tzinfo=timezone.utc)
KICK=(NOW+timedelta(hours=3)).isoformat()
def fixture():
 return {"status":"experimental_revue_match_center","real_bets_enabled":False,
  "bookmaker_prices_are_live":False,"events":[
   {"league":"MLB","event_id":"401999999","home":"Dodgers","away":"Brewers",
    "start_utc":KICK}]}
def game():
 return {"gamePk":810111,"gameType":"D","gameDate":KICK,
    "status":{"abstractGameState":"Preview"},
    "teams":{"home":{"team":{"id":119,"name":"Los Angeles Dodgers"},
      "probablePitcher":{"id":12345,"fullName":"Pitcher A"}},
     "away":{"team":{"id":158,"name":"Milwaukee Brewers"},
      "probablePitcher":{"id":67890,"fullName":"Pitcher B"}}}}
class MLBProbables(unittest.TestCase):
 def test_official_probable_both_sides_no_model_changes(self):
  result=collect(fixture(),[{"dates":[{"games":[game()]}]}],NOW)
  self.assertEqual(result["ESPN_fixtures_matched"],1)
  self.assertEqual(result["probable_pitcher_sides"],2)
  self.assertEqual(result["confirmed_starting_pitchers"],0)
  self.assertFalse(result["model_recomputed"])
  self.assertFalse(result["real_bets_enabled"])
  r=result["rows"][0]
  self.assertEqual(r["home_pitcher"]["status"],"probable_unconfirmed")
  self.assertFalse(r["starting_pitchers_independently_confirmed"])
 def test_team_mismatch_never_joins(self):
  g=game();g["teams"]["away"]["team"]["name"]="New York Yankees"
  self.assertEqual(collect(fixture(),[{"dates":[{"games":[g]}]}],NOW)["ESPN_fixtures_matched"],0)
 def test_kickoff_mismatch_never_joins(self):
  g=game();g["gameDate"]=(NOW+timedelta(hours=4)).isoformat()
  self.assertEqual(collect(fixture(),[{"dates":[{"games":[g]}]}],NOW)["ESPN_fixtures_matched"],0)
 def test_duplicated_official_schedules_ambiguous(self):
  g=game()
  result=collect(fixture(),[{"dates":[{"games":[g,deepcopy(g)]}]}],NOW)
  self.assertEqual(result["ESPN_fixtures_matched"],0)
 def test_after_first_pitch_excluded(self):
  r=collect(fixture(),[{"dates":[{"games":[game()]}]}],NOW+timedelta(hours=4))
  self.assertEqual(len(r["rows"]),0)
 def test_missing_probable_person_is_not_confirmed(self):
  g=game();g["teams"]["home"]["probablePitcher"]={"id":123}
  g["teams"]["away"]["probablePitcher"]=None
  result=collect(fixture(),[{"dates":[{"games":[g]}]}],NOW)
  self.assertEqual(result["probable_pitcher_sides"],0)
  self.assertEqual(result["ESPN_fixtures_matched"],1)
 def test_doubleheader_different_kickoffs(self):
  g=game();g2=deepcopy(g);g2["gamePk"]=810112
  g2["gameDate"]=(NOW+timedelta(hours=6)).isoformat()
  result=collect(fixture(),[{"dates":[{"games":[g,g2]}]}],NOW)
  self.assertEqual(result["ESPN_fixtures_matched"],1)
 def test_reject_non_mlb_exhibitions_and_finished_games(self):
  g=game();g["gameType"]="S"
  self.assertIsNone(eligible_game(g))
  g=game();g["status"]["abstractGameState"]="Final"
  self.assertIsNone(eligible_game(g))
 def test_strict_team_names(self):
  self.assertEqual(team_name("Chicago White Sox"),"White Sox")
  self.assertEqual(team_name("Arizona Diamondbacks"),"Diamondbacks")
  self.assertEqual(team_name("Athletics"),"Athletics")
  self.assertIsNone(team_name("Unknown FC"))
 def test_excludes_league_without_confirmed_prices(self):
  g=fixture();g["bookmaker_prices_are_live"]=True
  with self.assertRaises(ValueError):collect(g,[{"dates":[{"games":[game()]}]}],NOW)
if __name__=="__main__":unittest.main()
