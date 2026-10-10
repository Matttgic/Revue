"""No fabricated CI successes or untrusted GitHub Actions run URLs."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.github_actions_monitor import compile_runs
NOW=datetime(2026,10,10,14,tzinfo=timezone.utc)
def make(ident,conclusion="success",age=-60,workflow="Revue - API Clairvoyance contrats",status="completed"):
    return {"id":ident,"name":workflow,"status":status,"conclusion":conclusion,
            "head_branch":"main","head_sha":"a"*40,
            "html_url":"https://github.com/Matttgic/Revue/actions/runs/"+str(ident),
            "created_at":(NOW+timedelta(minutes=age)).isoformat(),
            "updated_at":(NOW+timedelta(minutes=age+2)).isoformat()}

class MonitorTests(unittest.TestCase):
    def test_success_failure_and_latest_are_separate(self):
        d=compile_runs({"workflow_runs":[make(3,"failure",-10),make(2,"success",-30),
                                           make(1,"success",-90,"Revue - Publier site mobile")]},NOW)
        self.assertEqual(d["observed_runs"],3)
        self.assertEqual(d["observed_failures"],1)
        g=next(x for x in d["workflows"] if "API Clairvoyance" in x["workflow"])
        self.assertEqual(g["latest"]["id"],3)
        self.assertEqual(g["last_success"]["id"],2)
        self.assertEqual(g["last_failure"]["id"],3)
        self.assertFalse(d["real_bets_enabled"])
        self.assertTrue(d["not_original_clairvoyance_daily_logs"])

    def test_malformed_url_branch_future_duplicates_never_accepted(self):
        bad=make(4);bad["html_url"]="https://evil.example/"
        branch=make(5);branch["head_branch"]="dev"
        future=make(6,age=20)
        d=compile_runs({"workflow_runs":[make(1),make(1),bad,branch,future,
                                             make(7,workflow="Other org")]},NOW)
        self.assertEqual(d["observed_runs"],1)

    def test_active_run_is_not_a_success(self):
        d=compile_runs({"workflow_runs":[make(8,None,-10,status="in_progress")]},NOW)
        self.assertIsNone(d["workflows"][0]["last_success"])
        self.assertEqual(d["workflows"][0]["latest"]["status"],"in_progress")

    def test_missing_history_fails_closed(self):
        with self.assertRaises(ValueError):compile_runs({},NOW)
        with self.assertRaises(ValueError):compile_runs({"workflow_runs":[]},NOW)
        with self.assertRaises(ValueError):compile_runs({"workflow_runs":[make(1)]},NOW.replace(tzinfo=None))
