import unittest
from datetime import datetime,timedelta,timezone
from outils.suivi_football_avance import (
    probabilities,grade,reconcile,summarize
)

NOW=datetime(2026,10,9,12,tzinfo=timezone.utc)
START=NOW+timedelta(hours=4)
def at(t):return t.isoformat()
def p():
    return {"home_win_90":.5,"draw_90":.3,"away_win_90":.2}
def b():
    return {"generated_at_utc":at(NOW-timedelta(minutes=15)),
            "competitions":{"PL":{"games":[
                {"event_id":"2026","home":"Team A","away":"Team B",
                 "start_utc":at(START),"probabilities":p()}]}}}
def s():
    return {"generated_at_utc":at(NOW-timedelta(minutes=10)),
            "competitions":{"PL":{"games":[{
                "event_id":"2026","home":"Team A","away":"Team B",
                "start_utc":at(START),"probabilities":{
                    "home_win_90":.56,"draw_90":.25,"away_win_90":.19},
                "espn_stats_used":True,"xg_used":False,
            }]}}}
def history(done=False):
    return {"leagues":{"PL":{"events":[{
        "id":"2026","complete":done,"home_score":2 if done else None,
        "away_score":1 if done else None
    }]}}}

class Tests(unittest.TestCase):
    def test_probs_validation(self):
        self.assertIsNone(probabilities({"home_win_90":2,"draw_90":0,"away_win_90":0}))
        self.assertIsNone(probabilities({"home_win_90":.5,"draw_90":.2,"away_win_90":.2}))
        self.assertAlmostEqual(sum(probabilities(p())),1)

    def test_baseline_shadow_pair_and_provenance(self):
        ledger,changes=reconcile({"events":{}},b(),s(),history(),NOW)
        self.assertEqual(changes["new_prematch_snapshots"],1)
        x=ledger["events"]["PL:2026"]
        self.assertTrue(x["espn_stats_used"])
        self.assertEqual(x["status"],"pending")
        self.assertEqual(x["baseline_1x2"],[.5,.3,.2])

    def test_duplicate_same_event_no_relock(self):
        ledger,_=reconcile({"events":{}},b(),s(),history(),NOW)
        ledger,changes=reconcile(ledger,b(),s(),history(),NOW+timedelta(minutes=1))
        self.assertEqual(changes["new_prematch_snapshots"],0)
        self.assertEqual(len(ledger["events"]),1)

    def test_too_close_to_kickoff_never_records(self):
        ledger,changes=reconcile({"events":{}},b(),s(),history(),
                                 START-timedelta(minutes=15))
        self.assertEqual(changes["new_prematch_snapshots"],0)
        self.assertEqual(ledger["events"],{})

    def test_timestamp_from_future_rejected(self):
        future=s()
        future["generated_at_utc"]=at(NOW+timedelta(minutes=1))
        ledger,changes=reconcile({"events":{}},b(),future,history(),NOW)
        self.assertEqual(changes["new_prematch_snapshots"],0)

    def test_no_duplicate_kickoff_mismatch(self):
        shadow=s()
        shadow["competitions"]["PL"]["games"][0]["start_utc"]=at(START+timedelta(hours=3))
        ledger,changes=reconcile({"events":{}},b(),shadow,history(),NOW)
        self.assertEqual(changes["new_prematch_snapshots"],0)

    def test_settlement_only_after_real_final(self):
        ledger,_=reconcile({"events":{}},b(),s(),history(),NOW)
        ledger,updates=reconcile(ledger,b(),s(),history(done=True),NOW)
        self.assertEqual(updates["newly_settled"],0)
        self.assertEqual(ledger["events"]["PL:2026"]["status"],"pending")
        later=START+timedelta(hours=4)
        ledger,updates=reconcile(ledger,b(),s(),history(done=True),later)
        self.assertEqual(updates["newly_settled"],1)
        self.assertEqual(ledger["events"]["PL:2026"]["status"],"graded")
        report=summarize(ledger,later)
        self.assertEqual(report["performance"]["ALL"]["n_settled"],1)
        self.assertLess(report["performance"]["ALL"]["brier_delta_candidate_minus_baseline"],0)

    def test_no_market_roi(self):
        ledger,_=reconcile({"events":{}},b(),s(),history(),NOW)
        report=summarize(ledger,NOW)
        self.assertEqual(report["performance"]["ALL"]["n_settled"],0)
        self.assertNotIn("roi",str(report).lower())

    def test_unverified_post_start_lock_excluded_from_metrics(self):
        ledger,_=reconcile({"events":{}},b(),s(),history(),NOW)
        ledger["events"]["PL:2026"]["locked_at_utc"]=at(START+timedelta(minutes=1))
        ledger,_=reconcile(ledger,b(),s(),history(done=True),START+timedelta(hours=3))
        self.assertEqual(ledger["events"]["PL:2026"]["status"],"invalid_chronology")
        self.assertEqual(summarize(ledger,NOW)["performance"]["ALL"]["n_settled"],0)

    def test_synthetic_source_cannot_turn_into_sports_betting(self):
        ledger,_=reconcile({"events":{}},b(),s(),history(),NOW)
        self.assertFalse(ledger["events"]["PL:2026"]["real_xg_used"])
        self.assertNotIn("odds",str(ledger).lower())
        self.assertNotIn("wager",str(ledger).lower())

if __name__=="__main__":unittest.main()
