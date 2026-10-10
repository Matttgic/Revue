"""Prospective NHL shadow ledger: immutable locks, no lookahead, reliable grading."""
from datetime import datetime,timedelta,timezone
import copy
import unittest
from modeles.simulations.nhl_independant import Game
from outils.nhl_shadow_tracker import update_ledger,summarize,grade_brier,grade_logloss

NOW=datetime(2026,10,10,6,tzinfo=timezone.utc)
KICK=NOW+timedelta(hours=8)


def pred(kick=KICK,at=NOW):
    source_at=(at-timedelta(hours=2)).isoformat()
    return {
        "generated_at_utc":at.isoformat(),
        "status":"experimental_not_calibrated",
        "sources":{"source_updated_utc":{"teams":source_at,"goalies":source_at},
                   "source_snapshot_utc":{"teams":source_at,"goalies":source_at}},
        "games":[{"event_id":"NHL-101","home":"BOS","away":"NYR",
                  "start_utc":kick.isoformat(),"home_win":0.65,"shadow_only":True,
                  "calibrated":False,"model_id":"clairvoyance_nhl_backend_formula_with_revue_elo_proxy",
                  "xg_games_observed":{"home":4,"away":3},
                  "historical_goalie_proxy":{"home":None,"away":None}}]
    }


def finish(at,home=3,away=2):
    return Game(id="NHL-101",start_utc=KICK,home="BOS",away="NYR",
                state="OFF",home_goals=home,away_goals=away)


class ProspectiveLedgerTests(unittest.TestCase):
    def test_lock_then_grade_immutable(self):
        locked=update_ledger(None,pred(),[],NOW)
        self.assertEqual(len(locked["events"]),1)
        self.assertEqual(locked["events"][0]["status"],"pending")
        old=copy.deepcopy(locked["events"][0])
        changed=pred(at=NOW+timedelta(hours=1))
        changed["games"][0]["home_win"]=0.96
        again=update_ledger(locked,changed,[],NOW+timedelta(hours=1))
        self.assertEqual(again["events"][0],old)
        settled=update_ledger(again,pred(at=NOW+timedelta(hours=9)),
                              [finish(NOW+timedelta(hours=9))],NOW+timedelta(hours=9))
        row=settled["events"][0]
        self.assertEqual(row["status"],"settled")
        self.assertEqual(row["home_win_probability"],0.65)
        self.assertAlmostEqual(row["brier"],0.1225)
        self.assertEqual(summarize(settled,NOW)["settled"],1)
        self.assertIsNone(summarize(settled,NOW)["roi"])
        again=update_ledger(settled,pred(),[finish(NOW+timedelta(hours=9),home=0,away=6)],
                            NOW+timedelta(hours=10))
        self.assertEqual(again["events"][0],row)

    def test_research_candidate_locked_immutably_and_graded_paired(self):
        document=pred()
        document["games"][0]["research_low_sample_shrink"]={
            "model_id":"revue_nhl_low_sample_shrink_v1",
            "home_win":0.55,"calibrated":False,"shadow_only":True,
        }
        lock=update_ledger(None,document,[],NOW)
        initial=copy.deepcopy(lock["events"][0])
        self.assertEqual(initial["research_home_win_probability"],0.55)
        document["games"][0]["research_low_sample_shrink"]["home_win"]=0.99
        later=update_ledger(lock,document,[],NOW+timedelta(hours=1))
        self.assertEqual(later["events"][0],initial)
        graded=update_ledger(later,document,[finish(NOW)],NOW+timedelta(hours=9))
        row=graded["events"][0]
        self.assertAlmostEqual(row["brier"],(1-.65)**2)
        self.assertAlmostEqual(row["research_brier"],(1-.55)**2)
        scores=summarize(graded,NOW+timedelta(hours=9))
        self.assertEqual(scores["research_paired_locked"],1)
        self.assertEqual(scores["research_paired_settled"],1)
        self.assertAlmostEqual(scores["mean_brier_research"],.2025)
        self.assertAlmostEqual(scores["mean_brier_reference_on_paired"],.1225)
        self.assertAlmostEqual(scores["brier_delta_research_minus_reference"],.08)
        self.assertAlmostEqual(scores["mean_logloss_reference_on_paired"],-__import__("math").log(.65),places=6)
        self.assertAlmostEqual(scores["mean_logloss_research"],-__import__("math").log(.55),places=6)
        self.assertAlmostEqual(scores["coinflip_baseline_brier"],.25)
        self.assertAlmostEqual(scores["research_brier_skill_vs_coinflip_paired"],1-.2025/.25,places=6)
        self.assertEqual(scores["research_status"],"experimental_not_promoted")

    def test_fake_research_model_is_not_accepted(self):
        document=pred()
        document["games"][0]["research_low_sample_shrink"]={
            "model_id":"unverified_model","home_win":.99,
            "calibrated":False,"shadow_only":True
        }
        data=update_ledger(None,document,[],NOW)
        self.assertIsNone(data["events"][0]["research_home_win_probability"])

    def test_never_create_backdated_lock(self):
        late=pred(kick=NOW+timedelta(minutes=15))
        self.assertEqual(update_ledger(None,late,[],NOW)["events"],[])

    def test_source_future_does_not_lock(self):
        doc=pred()
        doc["sources"]["source_updated_utc"]["teams"]=(NOW+timedelta(minutes=1)).isoformat()
        self.assertEqual(update_ledger(None,doc,[],NOW)["events"],[])

    def test_invalid_prob_is_discarded(self):
        doc=pred();doc["games"][0]["home_win"]=float("nan")
        self.assertFalse(update_ledger(None,doc,[],NOW)["events"])
        doc=pred();doc["games"][0]["home_win"]=1.2
        self.assertFalse(update_ledger(None,doc,[],NOW)["events"])

    def test_no_final_no_settlement(self):
        ledger=update_ledger(None,pred(),[],NOW)
        ledger=update_ledger(ledger,pred(),[finish(NOW,2,2)],NOW+timedelta(hours=9))
        self.assertEqual(ledger["events"][0]["status"],"pending")

    def test_no_wrong_team_mapping(self):
        ledger=update_ledger(None,pred(),[],NOW)
        wrong=Game(id="NHL-101",start_utc=KICK,home="TOR",away="NYR",
                   state="OFF",home_goals=4,away_goals=2)
        ledger=update_ledger(ledger,pred(),[wrong],NOW+timedelta(hours=9))
        self.assertEqual(ledger["events"][0]["status"],"pending")

    def test_no_settlement_before_game_even_if_final_flag(self):
        ledger=update_ledger(None,pred(),[],NOW)
        ledger=update_ledger(ledger,pred(),[finish(NOW)],NOW+timedelta(hours=1))
        self.assertEqual(ledger["events"][0]["status"],"pending")

    def test_duplicate_ledger_events_rejected(self):
        l=update_ledger(None,pred(),[],NOW)
        l["events"].append(l["events"][0])
        with self.assertRaises(ValueError):
            update_ledger(l,pred(),[],NOW)

    def test_empty_performance_is_not_fake_win_rate(self):
        ledger=update_ledger(None,pred(),[],NOW)
        perf=summarize(ledger,NOW)
        self.assertEqual(perf["pending"],1)
        self.assertEqual(perf["settled"],0)
        self.assertEqual(perf["research_paired_locked"],0)
        self.assertIsNone(perf["mean_brier"])
        self.assertIsNone(perf["mean_logloss"])
        self.assertIsNone(perf["brier_skill_vs_coinflip"])
        self.assertAlmostEqual(perf["coinflip_baseline_logloss"],.693147,places=6)
        self.assertEqual(perf["statistical_status"],"insufficient_sample")
        self.assertEqual(perf["cash_bets"],0)

    def test_logloss_rejects_extreme_or_malformed_predictions(self):
        import math
        self.assertAlmostEqual(grade_logloss(.7,1),-math.log(.7))
        self.assertAlmostEqual(grade_logloss(.7,0),-math.log(.3))
        for bad in (0,1,float("nan"),float("inf"),-1,1.2):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                grade_logloss(bad,1)

    def test_grade_brier_binary(self):
        self.assertAlmostEqual(grade_brier(0.7,1),0.09)
        with self.assertRaises(ValueError):
            grade_brier(1.2,1)


if __name__=="__main__":unittest.main()
