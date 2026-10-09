"""Prospective pair locking, temporal anti-leakage and score settlement."""
import unittest
from datetime import datetime,timedelta,timezone
from copy import deepcopy
from outils.suivi_ensemble import (
    normalize_two_way,score_pair,step,summarize,PREGAME_BUFFER
)
NOW=datetime(2026,10,9,21,tzinfo=timezone.utc)
KICK=NOW+timedelta(hours=3)
def iso(t):return t.isoformat()

def production():
    return {"generated_at_utc":iso(NOW-timedelta(minutes=2)),
            "competitions":{"NFL":{"games":[{
                "event_id":"ID1","home":"Home","away":"Away",
                "start_utc":iso(KICK),
                "probabilities":{"home_win":.6,"away_win":.4}
            }]}}}

def new_model():
    return {"generated_at_utc":iso(NOW-timedelta(minutes=1)),
            "leagues":{"NFL":{"games":[{
                "event_id":"ID1","home":"Home","away":"Away",
                "start_utc":iso(KICK),"status":"shadow_non_calibre",
                "probabilities":{"home_win":.65,"away_win":.35}
            }]}}}

def results(h=21,a=16,complete=True):
    return {"leagues":{"NFL":{"events":[{
        "id":"ID1","complete":complete,"home_score":h,"away_score":a
    }]}}}

class ProspectiveEnsembleTests(unittest.TestCase):
    def test_normalize_rejects_invalid_probabilities(self):
        self.assertIsNone(normalize_two_way({"home_win":1.2,"away_win":-.2}))
        self.assertIsNone(normalize_two_way({"home_win":.5,"away_win":.2}))
        self.assertIsNone(normalize_two_way({"home_win":float("nan"),"away_win":.5}))
        self.assertAlmostEqual(sum(normalize_two_way({"home_win":.6,"away_win":.4})),1)

    def test_correct_loss_for_home_win(self):
        a=score_pair((.6,.4),1)
        b=score_pair((.65,.35),1)
        self.assertLess(b["brier"],a["brier"])
        self.assertLess(b["logloss"],a["logloss"])

    def test_locks_both_model_snapshots_prematch(self):
        ledger,info=step({"events":{}},production(),new_model(),results(),NOW)
        self.assertEqual(info["added"],1)
        item=ledger["events"]["NFL:ID1"]
        self.assertEqual(item["status"],"pending")
        self.assertEqual(item["baseline"],[.6,.4])
        self.assertEqual(item["ensemble"],[.65,.35])
        self.assertNotIn("odds",str(item).lower())

    def test_no_duplicate_before_kickoff(self):
        a,_=step({"events":{}},production(),new_model(),results(),NOW)
        b,change=step(a,production(),new_model(),results(),NOW+timedelta(minutes=1))
        self.assertEqual(change["added"],0)
        self.assertEqual(len(b["events"]),1)

    def test_no_predictions_added_after_buffer(self):
        when=KICK-timedelta(minutes=15)
        ledger,info=step({"events":{}},production(),new_model(),results(),when)
        self.assertEqual(info["added"],0)
        self.assertFalse(ledger["events"])

    def test_future_publication_is_refused(self):
        model=new_model()
        model["generated_at_utc"]=iso(NOW+timedelta(minutes=1))
        a,change=step({"events":{}},production(),model,results(),NOW)
        self.assertEqual(change["added"],0)

    def test_wrong_team_is_refused(self):
        model=new_model()
        model["leagues"]["NFL"]["games"][0]["away"]="Other"
        a,change=step({"events":{}},production(),model,results(),NOW)
        self.assertEqual(change["added"],0)

    def test_cfb_never_locked(self):
        prod=production()
        exp=new_model()
        prod["competitions"]["CFB"]=prod["competitions"].pop("NFL")
        exp["leagues"]["CFB"]=exp["leagues"].pop("NFL")
        led,change=step({"events":{}},prod,exp,{},NOW)
        self.assertEqual(change["added"],0)

    def test_settlement_only_when_final_and_after_kickoff(self):
        ledger,_=step({"events":{}},production(),new_model(),results(),NOW)
        mid=KICK+timedelta(hours=1)
        led,info=step(ledger,production(),new_model(),results(21,16,False),mid)
        self.assertEqual(info["graded"],0)
        led,info=step(led,production(),new_model(),results(),mid)
        self.assertEqual(info["graded"],1)
        row=summarize(led,mid)["summary"]["NFL"]
        self.assertEqual(row["settled"],1)
        self.assertLess(row["delta_brier_candidate_vs_baseline"],0)

    def test_nfl_draw_is_not_marked_away(self):
        ledger,_=step({"events":{}},production(),new_model(),results(),NOW)
        led,info=step(ledger,production(),new_model(),results(21,21),KICK+timedelta(hours=2))
        self.assertEqual(info["draws_skipped"],1)
        self.assertEqual(led["events"]["NFL:ID1"]["status"],"draw_unsettled_2way")
        self.assertEqual(summarize(led,KICK)["summary"]["NFL"]["settled"],0)

    def test_post_kickoff_lock_invalid(self):
        ledger,_=step({"events":{}},production(),new_model(),results(),NOW)
        ledger["events"]["NFL:ID1"]["locked_at_utc"]=iso(KICK+timedelta(minutes=1))
        led,info=step(ledger,production(),new_model(),results(),KICK+timedelta(hours=1))
        self.assertEqual(info["graded"],0)
        self.assertEqual(led["events"]["NFL:ID1"]["status"],"invalid_chronology")

    def test_cannot_auto_promote(self):
        ledger,_=step({"events":{}},production(),new_model(),results(),NOW)
        report=summarize(ledger,NOW)
        self.assertFalse(report["promotion_allowed"])
        self.assertEqual(report["thresholds_before_independent_research_review"]["minimum_prospective_settled"],150)
        self.assertEqual(report["summary"]["ALL"]["pending"],1)

if __name__=="__main__":
    unittest.main()
