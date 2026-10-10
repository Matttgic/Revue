"""Tests for strictly pre-kickoff NHL Clairvoyance formula using MoneyPuck snapshots."""
import unittest
from datetime import date, datetime, timedelta, timezone

from modeles.simulations.nhl_independant import Game
from modeles.reproduction.clairvoyance_predictor import Game as ModelGame, nhl
from outils.clairvoyance_nhl_moneypuck_shadow import (
    predict_shadow, _most_used_goalie, _elo_from_scores
)

UTC=timezone.utc
NOW=datetime(2026,10,10,6,tzinfo=UTC)
YEAR="2026-2027"


def money():
    teams={"source":"MoneyPuck.com","source_page":"https://moneypuck.com/data.htm",
           "current_season":YEAR,"generated_at_utc":(NOW-timedelta(hours=2)).isoformat(),
           "status":{YEAR:{"status":"available","source_updated_utc":(NOW-timedelta(hours=3)).isoformat()}},
           "seasons":{YEAR:[
               {"team":"BOS","situation":"5on5","xg_share":0.56,"games_played":4},
               {"team":"NYR","situation":"5on5","xg_share":0.51,"games_played":4}]}}
    goalies={"source":"MoneyPuck.com","source_page":"https://moneypuck.com/data.htm",
            "current_season":YEAR,"generated_at_utc":(NOW-timedelta(hours=2)).isoformat(),
            "statuses":{YEAR:{"status":"available","source_updated_utc":(NOW-timedelta(hours=3)).isoformat()}},
            "seasons":{YEAR:[
              {"name":"Recent Goalie","team":"BOS","games_played":3,
               "ice_hours":2.5,"save_pct":0.92},
              {"name":"Second Goalie","team":"BOS","games_played":2,
               "ice_hours":4,"save_pct":0.98},
              {"name":"NYR Goalie","team":"NYR","games_played":4,
               "ice_hours":4,"save_pct":0.905}]}}
    return teams,goalies


def game(i,start,home="BOS",away="NYR",state="FUT",hg=None,ag=None):
    return Game(id=str(i),start_utc=start,home=home,away=away,state=state,
                home_goals=hg,away_goals=ag)


class ClairvoyanceNHLShadowTests(unittest.TestCase):
    def test_source_uses_most_games_not_best_save_or_starter(self):
        _,g=money()
        selected=_most_used_goalie(g["seasons"][YEAR],"BOS")
        self.assertEqual(selected["name"],"Recent Goalie")
        self.assertIsNone(_most_used_goalie(g["seasons"][YEAR],"BUF"))

    def test_model_match_on_equal_elo_and_genuine_moneypuck_inputs(self):
        t,g=money()
        event=game(5,NOW+timedelta(hours=12))
        d=predict_shadow([], [event],t,g,NOW,date(2026,10,10))
        self.assertEqual(len(d["games"]),1)
        row=d["games"][0]
        expected=nhl(ModelGame(espn_id="5",home_team="BOS",away_team="NYR"),
                     1500,1500,56.,51.,.92,.905)
        self.assertEqual(row["home_win"],expected["model_home_win_prob"])
        self.assertEqual(row["model_id"],"clairvoyance_nhl_backend_formula_with_revue_elo_proxy")
        self.assertFalse(row["calibrated"])
        self.assertFalse(row["source_reproduction_complete"])
        self.assertFalse(d["confirmed_starters"])
        self.assertIsNone(row["market_odds"])
        self.assertIsNone(row["betting_recommendation"])
        self.assertEqual(row["historical_goalie_proxy"]["selection_rule"],
                         "Most games played, not projected/confirmed starters")

    def test_only_future_games_no_kickoff_leakage(self):
        t,g=money()
        past=game(1,NOW-timedelta(minutes=5),state="LIVE")
        ontime=game(2,NOW)
        future=game(3,NOW+timedelta(hours=15))
        today=date(2026,10,10)
        rows=predict_shadow([], [past,ontime,future,future],t,g,NOW,today)["games"]
        self.assertEqual([r["event_id"] for r in rows],["3"])

    def test_source_after_kickoff_disqualifies_event(self):
        t,g=money()
        future=game(5,NOW+timedelta(hours=12))
        t["status"][YEAR]["source_updated_utc"]=(NOW+timedelta(hours=13)).isoformat()
        with self.assertRaises(ValueError):
            predict_shadow([], [future],t,g,NOW,date(2026,10,10))

    def test_wrong_season_rejected(self):
        t,g=money()
        t["current_season"]="2025-2026"
        with self.assertRaises(ValueError):
            predict_shadow([], [game(7,NOW+timedelta(hours=12))],
                           t,g,NOW,date(2026,10,10))

    def test_missing_team_xg_skips_instead_of_invents(self):
        t,g=money()
        t["seasons"][YEAR]=t["seasons"][YEAR][:1]
        result=predict_shadow([],[game(5,NOW+timedelta(hours=12))],
                              t,g,NOW,date(2026,10,10))
        self.assertEqual(result["games"],[])

    def test_missing_goalie_does_not_infer_starter(self):
        t,g=money()
        g["seasons"][YEAR]=g["seasons"][YEAR][:2]
        result=predict_shadow([],[game(5,NOW+timedelta(hours=12))],
                              t,g,NOW,date(2026,10,10))
        row=result["games"][0]
        self.assertIsNone(row["historical_goalie_proxy"]["away"])
        self.assertIsNone(row["betting_recommendation"])

    def test_elo_from_final_games_no_double_count(self):
        previous=[game(1,NOW-timedelta(days=5),state="OFF",hg=4,ag=1)]
        current=[game(2,NOW-timedelta(days=2),state="OFF",hg=1,ag=4),
                 game(3,NOW+timedelta(hours=5),state="OFF",hg=10,ag=1)]
        ratings=_elo_from_scores(previous,current,NOW)
        self.assertIn("BOS",ratings)
        self.assertNotEqual(ratings["BOS"],1500)
        # Game 3 is marked final in an invalid future: never used.
        another=_elo_from_scores(previous,current[:1],NOW)
        self.assertAlmostEqual(ratings["BOS"],another["BOS"])

    def test_historical_goals_no_bookmaker_phantom(self):
        t,g=money()
        rows=predict_shadow([],[game(7,NOW+timedelta(hours=12))],
                           t,g,NOW,date(2026,10,10))
        self.assertFalse(rows["bookmaker_odds_available"])
        self.assertEqual(rows["status"],"experimental_not_calibrated")
        self.assertIn("MoneyPuck.com",rows["sources"]["xg_goalies"])


if __name__=="__main__":
    unittest.main()
