"""Read-only operations API and independently validated paper performance."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from fastapi.testclient import TestClient

from api_revue.app import create_app
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
T=lambda n:(NOW+timedelta(hours=n)).isoformat()

class OperationalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.write("engine-v2-ledger.json",{"version":1,"bets":[
            {"id":"paper-000001","league":"WNBA","event_id":"123","home":"Team A",
             "away":"Team B","start_utc":T(4),"locked_at":T(-2),"quote_at":T(-3),
             "model_at":T(-4),"chronology":"pre_valide","market":"h2h","side":"home",
             "outcome":"Team A","bookmaker":"betclic_fr","bookmaker_price":2.20,
             "paper_stake_units":1,"status":"won","score":{"home":91,"away":81},
             "settled_at":T(6),"paper_units_returned":2.2},
            {"id":"paper-000002","league":"NHL","event_id":"234","home":"BOS",
             "away":"PHI","start_utc":T(5),"locked_at":T(-2),"quote_at":T(-3),
             "model_at":T(-4),"chronology":"pre_valide","market":"totals","side":"over",
             "outcome":"Over","line":5.5,"bookmaker":"winamax_fr",
             "bookmaker_price":1.9,"paper_stake_units":1,"status":"market_rule_unverified"},
            {"id":"paper-000003","league":"MLB","event_id":"345","home":"C",
             "away":"D","start_utc":T(5),"locked_at":T(-2),"quote_at":T(-3),
             "model_at":T(-4),"chronology":"pre_valide","market":"h2h","side":"away",
             "outcome":"D","bookmaker":"pmu_fr","bookmaker_price":1.8,
             "paper_stake_units":1,"status":"pending"}
        ]})
        for name,age in [("match-center-latest.json",2),("engine-v2-latest.json",1),
                         ("multisports-latest.json",0.5),("health-latest.json",0.5),
                         ("nhl-official-stats-latest.json",26),("moneypuck-nhl-latest.json",24)]:
            data={"generated_at_utc":T(-age)}
            if name.startswith("match"):data["events"]=[{"event_id":"1"}]
            if name.startswith("engine"):data.update({"odds_status":"active_pulsescore","candidate_count":7})
            if name.startswith("health"):data["status"]="attention_required"
            self.write(name,data)
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))

    def write(self,name,data):
        (self.root/name).write_text(json.dumps(data),encoding="utf-8")

    def test_journal_has_21_compatible_fields_with_provenance_not_real_money(self):
        resp=self.client.get("/revue/ledger")
        self.assertEqual(resp.status_code,200,resp.text)
        self.assertIn("paper",resp.headers["x-revue-parity"])
        doc=resp.json()
        self.assertTrue(doc["paper_only"])
        self.assertEqual(doc["summary"]["total"],3)
        self.assertEqual(doc["summary"]["won"],1)
        self.assertEqual(doc["summary"]["settled"],1)
        self.assertEqual(doc["summary"]["excluded_or_unverified"],1)
        self.assertEqual(doc["summary"]["pending"],1)
        self.assertEqual(doc["summary"]["paper_profit_units"],1.2)
        self.assertEqual(doc["summary"]["paper_roi_pct"],120.0)
        self.assertEqual(doc["records"][1]["status"],"unverified")
        self.assertIsNone(doc["records"][1]["paper_profit_units"])
        self.assertTrue(all(not x["is_real_bet"] for x in doc["records"]))
        self.assertEqual(self.client.post("/revue/ledger",json={}).status_code,405)

    def test_operational_status_distinguishes_stale_from_missing(self):
        res=self.client.get("/revue/control")
        self.assertEqual(res.status_code,200,res.text)
        d=res.json()
        self.assertEqual(d["fresh_sources"],5)
        self.assertEqual(d["stale_sources"],1)
        self.assertEqual(d["sources"]["nhl_official"]["state"],"stale")
        self.assertEqual(d["match_center"]["snapshot_count"],1)
        self.assertEqual(d["odds_scanner"]["candidate_count"],7)
        self.assertTrue(d["not_live_provider_health"])
        (self.root/"engine-v2-latest.json").unlink()
        d=self.client.get("/revue/control").json()
        self.assertEqual(d["sources"]["scanner"]["state"],"unavailable")
        self.assertIsNone(d["odds_scanner"]["candidate_count"])

    def test_no_bad_result_or_temporal_leakage_in_roi(self):
        path=self.root/"engine-v2-ledger.json"
        d=json.loads(path.read_text())
        d["bets"][0]["paper_units_returned"]=9999
        self.write("engine-v2-ledger.json",d)
        z=self.client.get("/revue/ledger").json()
        self.assertEqual(z["summary"]["settled"],0)
        self.assertIsNone(z["summary"]["paper_roi_pct"])
        d["bets"][0]["paper_units_returned"]=2.2
        d["bets"][0]["quote_at"]=T(6)
        self.write("engine-v2-ledger.json",d)
        z=self.client.get("/revue/ledger").json()
        self.assertEqual(z["summary"]["settled"],0)
        self.assertEqual(z["records"][2]["status"],"unverified")
        d["bets"][0]["quote_at"]=T(-3)
        d["bets"][0]["settled_at"]=T(1)
        self.write("engine-v2-ledger.json",d)
        z=self.client.get("/revue/ledger").json()
        self.assertEqual(z["summary"]["settled"],0)

    def test_observed_integer_valued_float_scores_are_valid_but_fractions_not(self):
        path=self.root/"engine-v2-ledger.json"
        d=json.loads(path.read_text(encoding="utf-8"))
        d["bets"][0]["score"]={"home":91.0,"away":81.0}
        self.write("engine-v2-ledger.json",d)
        out=self.client.get("/revue/ledger").json()
        self.assertEqual(out["summary"]["settled"],1)
        self.assertEqual(out["records"][2]["score"],{"home":91,"away":81})
        d["bets"][0]["score"]={"home":91.5,"away":81.0}
        self.write("engine-v2-ledger.json",d)
        out=self.client.get("/revue/ledger").json()
        self.assertEqual(out["summary"]["settled"],0)
        self.assertEqual(out["summary"]["excluded_or_unverified"],2)

    def test_missing_broken_ledger_fails_closed(self):
        (self.root/"engine-v2-ledger.json").unlink()
        self.assertEqual(self.client.get("/revue/ledger").status_code,503)
        self.assertEqual(self.client.get("/revue/control").json()["paper_status"],"unavailable")
        self.write("engine-v2-ledger.json",{"version":1,"bets":[{"id":"paper-1","league":"NHL"}]})
        self.assertEqual(self.client.get("/revue/ledger").status_code,503)
        self.assertEqual(self.client.get("/openapi.json").status_code,200)

if __name__=="__main__":unittest.main()
