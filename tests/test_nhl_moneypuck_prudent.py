"""Check distinct prudent forecasts without changing original source-parity outputs."""
from datetime import date, datetime, timedelta, timezone
import unittest

from modeles.reproduction.clairvoyance_predictor import Game as PredictorGame, nhl
from modeles.simulations.nhl_independant import Game
from outils.nhl_moneypuck_prudent import (
    xg_shrunk, goalie_shrunk, prudent_forecast, XG_PRIOR_GAMES, MODEL_ID
)
from outils.clairvoyance_nhl_moneypuck_shadow import predict_shadow

NOW=datetime(2026,10,10,6,tzinfo=timezone.utc)
LABEL="2026-2027"
PREV="2025-2026"


def snapshots():
    team_rows=[
      {"team":"BOS","situation":"5on5","xg_share":.70,"games_played":3},
      {"team":"NYR","situation":"5on5","xg_share":.30,"games_played":3}
    ]
    past_rows=[
      {"team":"BOS","situation":"5on5","xg_share":.52,"games_played":82},
      {"team":"NYR","situation":"5on5","xg_share":.49,"games_played":82}
    ]
    teams={"source":"MoneyPuck.com","source_page":"https://moneypuck.com/data.htm",
           "current_season":LABEL,"generated_at_utc":(NOW-timedelta(hours=1)).isoformat(),
           "status":{LABEL:{"status":"available","source_updated_utc":(NOW-timedelta(hours=2)).isoformat()},
                     PREV:{"status":"available","source_updated_utc":(NOW-timedelta(days=20)).isoformat()}},
           "seasons":{LABEL:team_rows,PREV:past_rows}}
    goalies={"source":"MoneyPuck.com","source_page":"https://moneypuck.com/data.htm",
            "current_season":LABEL,"generated_at_utc":(NOW-timedelta(hours=1)).isoformat(),
            "statuses":{LABEL:{"status":"available","source_updated_utc":(NOW-timedelta(hours=2)).isoformat()}},
            "seasons":{LABEL:[
              {"name":"A","team":"BOS","games_played":3,"ice_hours":3,"save_pct":.96},
              {"name":"B","team":"NYR","games_played":3,"ice_hours":3,"save_pct":.81}]}}
    return teams,goalies


class PrudentNhlTests(unittest.TestCase):
    def test_xg_previous_season_prior(self):
        value,origin=xg_shrunk({"xg_share":.70,"games_played":3},
                               {"xg_share":.52,"games_played":82})
        self.assertEqual(origin,"previous_regular_season_5v5")
        self.assertAlmostEqual(value,(.70*3+.52*XG_PRIOR_GAMES)/(3+XG_PRIOR_GAMES))

    def test_absent_previous_season_uses_neutral_not_fabricated(self):
        value,origin=xg_shrunk({"xg_share":.7,"games_played":3},None)
        self.assertEqual(origin,"neutral_50pct")
        self.assertAlmostEqual(value,.54)

    def test_save_percentage_early_season_shrinks(self):
        self.assertGreater(goalie_shrunk({"save_pct":.81,"games_played":3}),.81)
        self.assertLess(goalie_shrunk({"save_pct":.96,"games_played":3}),.96)
        self.assertIsNone(goalie_shrunk(None))

    def test_invalid_observations_rejected(self):
        with self.assertRaises(ValueError):
            xg_shrunk({"xg_share":float("nan"),"games_played":2},None)
        with self.assertRaises(ValueError):
            xg_shrunk({"xg_share":.5,"games_played":0},None)
        self.assertIsNone(goalie_shrunk({"save_pct":float("nan"),"games_played":3}))

    def test_source_formula_unchanged_and_candidate_separate(self):
        teams,goalies=snapshots()
        event=Game(id="NHL-901",start_utc=NOW+timedelta(hours=12),
                   home="BOS",away="NYR",state="FUT")
        result=predict_shadow([], [event], teams, goalies, NOW, date(2026,10,10))
        self.assertEqual(len(result["games"]),1)
        row=result["games"][0]
        original=nhl(PredictorGame(espn_id=event.id,home_team="BOS",away_team="NYR"),
                     1500,1500,70.,30.,.96,.81)
        self.assertEqual(row["home_win"],original["model_home_win_prob"])
        alt=row["research_low_sample_shrink"]
        self.assertEqual(alt["model_id"],MODEL_ID)
        self.assertNotEqual(alt["home_win"],row["home_win"])
        self.assertLess(alt["home_win"],row["home_win"])
        self.assertFalse(alt["calibrated"])
        self.assertEqual(alt["previous_season_xg_prior"]["home"],"previous_regular_season_5v5")
        self.assertIsNone(row["betting_recommendation"])

    def test_previous_season_unavailable_no_false_prior(self):
        teams,goalies=snapshots()
        teams["status"][PREV]["status"]="unavailable"
        e=Game(id="NHL-903",start_utc=NOW+timedelta(hours=12),
               home="BOS",away="NYR",state="FUT")
        result=predict_shadow([], [e],teams,goalies,NOW,date(2026,10,10))
        alt=result["games"][0]["research_low_sample_shrink"]
        self.assertEqual(alt["previous_season_xg_prior"]["home"],"neutral_50pct")


if __name__=="__main__":
    unittest.main()
