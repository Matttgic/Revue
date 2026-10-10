"""Prospective multisport tracking must never borrow future or mismatched outcomes."""
from datetime import datetime,timedelta,timezone
from copy import deepcopy
import unittest

from outils.prospectif_multisports_revue import lock,settle,performance,VERSION

NOW=datetime(2026,10,10,9,tzinfo=timezone.utc)
KICK=NOW+timedelta(hours=2)
SCORED=KICK+timedelta(hours=4)

def center():
    return {
        "status":"experimental_revue_match_center","real_bets_enabled":False,
        "bookmaker_prices_are_live":False,
        "events":[{"league":"NBA","event_id":"401","home":"Bulls","away":"Grizzlies",
                   "start_utc":KICK.isoformat(),
                   "research":[{"id":"revue_multisports_score_model",
                                "source_generated_utc":(NOW-timedelta(hours=1)).isoformat(),
                                "probabilities":{"home_win":.6,"away_win":.4}},
                               {"id":"revue_ensemble_mc_bayes_elo",
                                "source_generated_utc":(NOW-timedelta(minutes=30)).isoformat(),
                                "probabilities":{"home_win":.55,"away_win":.45}}]}]
    }

def official(score=(110,103),away="Grizzlies",state="final"):
    return {
        "generated_at_utc":SCORED.isoformat(),"status":"observed_scoreboard_not_streaming",
        "scores_are_live_stream":False,
        "events":[{"league":"NBA","event_id":"401","home":"Bulls","away":away,
                   "kickoff_utc":KICK.isoformat(),"home_score":score[0],"away_score":score[1],
                   "state":state,"observed_at_utc":SCORED.isoformat()}],
    }

class Tracker(unittest.TestCase):
    def test_two_models_locked_once_with_immutable_probabilities(self):
        book=lock(None,center(),NOW)
        self.assertEqual(book["version"],VERSION)
        self.assertEqual(len(book["events"]),1)
        self.assertEqual(book["events"][0]["models"]["revue_multisports_score_model"]["p_home"],.6)
        newer=center()
        newer["events"][0]["research"][0]["probabilities"]["home_win"]=.1
        newer["events"][0]["research"][0]["probabilities"]["away_win"]=.9
        next_book=lock(book,newer,NOW+timedelta(minutes=5))
        self.assertEqual(next_book,book)

    def test_settles_official_score_and_compares_models(self):
        book=lock(None,center(),NOW)
        pre=deepcopy(book)
        done=settle(book,official(),SCORED)
        self.assertEqual(done["events"][0]["status"],"settled")
        self.assertEqual(done["events"][0]["brier_by_model"]["revue_multisports_score_model"],.16)
        self.assertEqual(done["events"][0]["brier_by_model"]["revue_ensemble_mc_bayes_elo"],.2025)
        self.assertEqual(done["events"][0]["models"],pre["events"][0]["models"])
        self.assertEqual(book,pre)
        score=performance(done,SCORED)
        self.assertEqual(score["settled"],1)
        self.assertAlmostEqual(score["models"]["revue_multisports_score_model"]["mean_brier"],.16)
        self.assertIsNone(score["roi"])
        self.assertEqual(score["real_bets"],0)

    def test_never_settle_live_wrong_team_or_future_score(self):
        book=lock(None,center(),NOW)
        for feed in (official(state="in_progress"),official(away="Celtics")):
            self.assertEqual(settle(book,feed,SCORED)["events"][0]["status"],"pending")
        self.assertEqual(settle(book,official(),NOW+timedelta(minutes=1))["events"][0]["status"],"pending")

    def test_no_made_up_locks_if_not_at_least_twenty_minutes_before(self):
        self.assertEqual(len(lock(None,center(),KICK-timedelta(minutes=19))["events"]),0)
        data=center()
        data["events"][0]["research"][0]["source_generated_utc"]=(KICK+timedelta(minutes=10)).isoformat()
        data["events"][0]["research"][1]["source_generated_utc"]=(KICK+timedelta(minutes=10)).isoformat()
        self.assertEqual(len(lock(None,data,NOW)["events"]),0)

    def test_soccer_cfb_and_unscored_outcomes_excluded(self):
        data=center()
        for league in ("PL","CFB","UFC","ATP"):
            with self.subTest(league=league):
                data["events"][0]["league"]=league
                self.assertEqual(lock(None,data,NOW)["events"],[])
        data=center()
        data["events"][0]["research"][0]["probabilities"]={"home_win":.6,"away_win":.2}
        data["events"][0]["research"][1]["probabilities"]=None
        self.assertEqual(lock(None,data,NOW)["events"],[])

    def test_pending_games_and_nonpaired_samples_not_promoted(self):
        result=performance(lock(None,center(),NOW),NOW)
        self.assertEqual(result["pending"],1)
        self.assertEqual(result["models"],{})
        self.assertEqual(result["status"],"experimental_not_calibrated")

    def test_reject_bad_schema(self):
        with self.assertRaises(ValueError):
            lock({"version":"future","events":[]},center(),NOW)


if __name__=="__main__":unittest.main()
