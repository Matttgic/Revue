"""Original admin contract cannot fabricate unavailable SQL logs.

Real Revue GitHub workflow history has an independent source-linked path.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from fastapi.testclient import TestClient
from api_revue.app import create_app
from outils.github_actions_monitor import compile_runs
NOW=datetime(2026,10,10,14,tzinfo=timezone.utc)

def make():
    return {"workflow_runs":[{
        "id":123,"name":"Revue - Publier site mobile","status":"completed",
        "conclusion":"success","head_branch":"main","head_sha":"a"*40,
        "html_url":"https://github.com/Matttgic/Revue/actions/runs/123",
        "created_at":(NOW-timedelta(minutes=9)).isoformat(),
        "updated_at":(NOW-timedelta(minutes=8)).isoformat(),
    },{
        "id":122,"name":"Revue - API Clairvoyance contrats","status":"completed",
        "conclusion":"failure","head_branch":"main","head_sha":"a"*40,
        "html_url":"https://github.com/Matttgic/Revue/actions/runs/122",
        "created_at":(NOW-timedelta(minutes=19)).isoformat(),
        "updated_at":(NOW-timedelta(minutes=18)).isoformat()
    }]}

class AdminHttpTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.report=compile_runs(make(),NOW)
        self.write()
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))

    def write(self):
        (self.root/"github-workflows-latest.json").write_text(
            json.dumps(self.report),encoding="utf-8")

    def test_source_admin_status_is_honest_about_missing_sql_and_cron(self):
        r=self.client.get("/admin/status")
        self.assertEqual(r.status_code,200,r.text)
        self.assertIn("NOT original",r.headers["x-revue-parity"])
        data=r.json()
        self.assertEqual(set(data["scrapers"]),{
            "espn_mlb","espn_nhl","nhl_edge","moneypuck","settlement"})
        self.assertTrue(all(v is None for v in data["scrapers"].values()))
        self.assertIsNone(data["next_pipeline_run"])
        self.assertEqual(data["revue_github_actions"]["observed_failures"],1)
        self.assertFalse(data["original_daily_log_database_available"])

    def test_original_sql_logs_stay_empty_and_read_only(self):
        r=self.client.get("/admin/logs",params={"limit":20,"scraper":"moneypuck"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(),[])
        self.assertIn("not original",r.headers["x-revue-parity"].lower())
        self.assertEqual(self.client.get("/admin/logs?limit=501").status_code,422)
        self.assertEqual(self.client.post("/admin/pipeline").status_code,405)
        self.assertEqual(self.client.post("/admin/scrape/nhl").status_code,405)

    def test_real_revue_history_filter_and_pagination(self):
        r=self.client.get("/revue/workflows")
        self.assertEqual(r.status_code,200,r.text)
        d=r.json()
        self.assertEqual(d["known_workflows"],2)
        self.assertEqual(d["observed_failures"],1)
        self.assertTrue(d["not_original_clairvoyance_daily_logs"])
        self.assertTrue(all(x["is_clairvoyance_original_run"] is False for x in d["runs"]))
        only=self.client.get("/revue/workflows",params={
            "workflow":"Revue - Publier site mobile","limit":1}).json()
        self.assertEqual(only["filtered_count"],1)
        self.assertEqual(len(only["runs"]),1)
        self.assertEqual(self.client.get("/revue/workflows?limit=0").status_code,422)
        self.assertEqual(self.client.get("/revue/workflows?limit=501").status_code,422)

    def test_missing_or_stale_evidence_is_not_reclassified_success(self):
        (self.root/"github-workflows-latest.json").unlink()
        self.assertEqual(self.client.get("/revue/workflows").status_code,503)
        data=self.client.get("/admin/status").json()
        self.assertIsNone(data["revue_github_actions"])
        self.assertEqual(data["scrapers"]["moneypuck"],None)
        self.report["generated_at_utc"]=(NOW-timedelta(hours=15)).isoformat()
        self.write()
        self.assertEqual(self.client.get("/revue/workflows").status_code,503)

if __name__=="__main__":unittest.main()
