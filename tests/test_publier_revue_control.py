"""Static export reuses independently tested paper ledger calculations."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from outils.publier_revue_control import generate,publish
NOW=datetime(2026,10,10,13,tzinfo=timezone.utc)
def t(hours):return (NOW+timedelta(hours=hours)).isoformat()

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"engine-v2-ledger.json").write_text(json.dumps({
            "version":1,
            "bets":[{"id":"paper-000001","league":"WNBA","event_id":"xyz",
                "home":"Liberty","away":"Dream","start_utc":t(4),
                "locked_at":t(-2),"quote_at":t(-3),"model_at":t(-4),
                "chronology":"pre_valide","market":"h2h","side":"away",
                "outcome":"Dream","bookmaker":"betclic_fr","bookmaker_price":2.17,
                "paper_stake_units":1,"status":"won","score":{"home":83,"away":85},
                "settled_at":t(6),"paper_units_returned":2.17},
                {"id":"paper-000002","league":"NHL","event_id":"abc",
                "home":"BOS","away":"PHI","start_utc":t(4),
                "locked_at":t(-2),"quote_at":t(-3),"model_at":t(-4),
                "chronology":"pre_valide","market":"h2h","side":"home",
                "outcome":"BOS","bookmaker":"winamax_fr","bookmaker_price":1.7,
                "paper_stake_units":1,"status":"market_rule_unverified"}]
        }),encoding="utf-8")
        (self.root/"health-latest.json").write_text(json.dumps({
          "generated_at_utc":t(-1),"status":"attention_required"}),encoding="utf-8")

    def test_consistent_with_backend_and_exclusion(self):
        ledger,state=generate(self.root,NOW)
        self.assertTrue(ledger["paper_only"])
        self.assertFalse(ledger["real_bets_enabled"])
        self.assertEqual(ledger["summary"]["total"],2)
        self.assertEqual(ledger["summary"]["settled"],1)
        self.assertEqual(ledger["summary"]["excluded_or_unverified"],1)
        self.assertEqual(ledger["summary"]["paper_profit_units"],1.17)
        self.assertEqual(ledger["summary"]["paper_roi_pct"],117.0)
        self.assertEqual(state["sources"]["health"]["state"],"fresh")
        self.assertTrue(state["not_live_provider_health"])
        self.assertTrue(state["static_snapshot"])

    def test_publish_files_without_modifying_original_ledger(self):
        before=(self.root/"engine-v2-ledger.json").read_bytes()
        files=publish(self.root,NOW)
        self.assertEqual(before,(self.root/"engine-v2-ledger.json").read_bytes())
        for f in files:
            d=json.loads(f.read_text())
            self.assertTrue(d["static_snapshot"])

    def test_ledger_missing_refuses_to_publish(self):
        (self.root/"engine-v2-ledger.json").unlink()
        with self.assertRaises(Exception):publish(self.root,NOW)
        self.assertFalse((self.root/"revue-control-ledger-latest.json").exists())
