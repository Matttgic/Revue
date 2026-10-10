"""HTTP pick contracts: simulated only; no forged source SQL or real bets."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from fastapi.testclient import TestClient
from api_revue.app import create_app

NOW = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
START = NOW + timedelta(hours=3)

class PaperPickHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.client = TestClient(create_app(root=self.directory, clock=lambda: NOW))
        self.bets = [
            {"id": "paper-000001", "league": "NHL", "status": "won",
             "chronology": "pre_valide", "start_utc": START.isoformat(),
             "quote_at": (NOW - timedelta(hours=2)).isoformat(),
             "locked_at": (NOW - timedelta(hours=1)).isoformat(),
             "home": "BOS", "away": "PHI", "event_id": "2026020070",
             "market": "h2h", "side": "home", "bookmaker_price": 2.50,
             "paper_stake_units": 2, "score": {"home": 4, "away": 2},
             "settled_at": (START + timedelta(hours=3)).isoformat()},
            {"id": "paper-000002", "league": "MLB", "status": "lost",
             "chronology": "pre_valide", "start_utc": START.isoformat(),
             "quote_at": (NOW - timedelta(hours=2)).isoformat(),
             "locked_at": (NOW - timedelta(hours=1)).isoformat(),
             "home": "Dodgers", "away": "Padres", "event_id": "401907994",
             "market": "totals", "side": "under", "line": 7.5,
             "bookmaker_price": 1.80, "paper_stake_units": 1,
             "score": {"home": 5, "away": 4},
             "settled_at": (START + timedelta(hours=3)).isoformat()},
            {"id": "paper-000003", "league": "NHL", "status": "market_rule_unverified",
             "chronology": "pre_valide"},
            {"id": "paper-000004", "league": "CFB", "status": "won",
             "chronology": "pre_valide"},
        ]
        self.store()
        (self.directory / "parite-nhl-espn-id-map.json").write_text(json.dumps({
            "status": "verified_fixture_identity_pairs",
            "mappings": [{"nhl_game_id": "2026020070",
                          "original_espn_id": "401892469", "home": "BOS",
                          "away": "PHI", "start_utc": START.isoformat()}]
        }))

    def store(self):
        (self.directory / "engine-v2-ledger.json").write_text(
            json.dumps({"version": 1, "bets": self.bets}), encoding="utf-8")

    def test_field_contract_id_mapping_filters_and_read_only(self):
        response = self.client.get("/picks/")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("paper ledger", response.headers["x-revue-parity"])
        rows = response.json()
        self.assertEqual(len(rows), 2)
        expected = {"id", "sport", "espn_game_id", "game_date", "bet_type",
                    "selection", "odds", "amount", "over_under", "status",
                    "home_team", "away_team", "home_score", "away_score",
                    "notes", "settled_at", "created_at"}
        self.assertEqual(set(rows[0]), expected)
        self.assertEqual(rows[0]["espn_game_id"], "401892469")
        self.assertEqual(rows[0]["odds"], 150)
        self.assertEqual(rows[0]["amount"], 2)
        self.assertIn("SIMULATION", rows[0]["notes"])
        self.assertEqual(self.client.get("/picks/", params={"sport":"MLB"}).json()[0]["id"], 2)
        self.assertEqual(self.client.get("/picks/", params={"status":"pending"}).json(), [])
        self.assertEqual(self.client.get("/picks/1").json()["id"], 1)
        self.assertEqual(self.client.get("/picks/999").status_code, 404)
        self.assertEqual(self.client.post("/picks/", json={}).status_code, 405)
        self.assertEqual(self.client.patch("/picks/1/void").status_code, 405)

    def test_stats_same_field_shape_and_paper_payout(self):
        res = self.client.get("/picks/stats")
        self.assertEqual(res.status_code, 200, res.text)
        doc = res.json()
        self.assertEqual(set(doc), {"summary", "by_sport", "by_bet_type"})
        self.assertEqual(doc["summary"], {
            "won": 1, "lost": 1, "push": 0, "win_rate": 50.0,
            "pnl": 2.0, "roi": 66.7, "total_wagered": 3.0})
        self.assertEqual(doc["by_sport"]["mlb"]["lost"], 1)
        self.assertEqual(doc["by_bet_type"]["moneyline"]["won"], 1)
        self.assertEqual(self.client.get("/picks/stats", params={"sport":"NHL"}).json()["summary"]["won"], 1)

    def test_unknown_or_corrupt_ledger_fails_closed(self):
        (self.directory / "engine-v2-ledger.json").unlink()
        self.assertEqual(self.client.get("/picks/").status_code, 503)
        self.store()
        self.bets[0]["quote_at"] = (START + timedelta(hours=1)).isoformat()
        self.store()
        self.assertEqual([x["id"] for x in self.client.get("/picks/").json()], [2])
        self.bets[0]["quote_at"] = (NOW - timedelta(hours=2)).isoformat()
        self.bets[0]["paper_stake_units"] = -100
        self.store()
        self.assertEqual(self.client.get("/picks/").status_code, 503)

if __name__ == "__main__":
    unittest.main()
