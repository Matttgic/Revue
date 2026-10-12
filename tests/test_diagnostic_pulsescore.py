"""Diagnostic PulseScore hors ligne : rattachement, échantillons, aucune clé publiée."""
import json
import unittest
from datetime import datetime, timedelta, timezone

from outils.collecte.diagnostic_pulsescore import run

NOW = datetime(2026, 10, 12, 9, tzinfo=timezone.utc)
START = NOW + timedelta(hours=6)


def models():
    return {"generated_at_utc": NOW.isoformat(), "competitions": {"PL": {"games": [{
        "event_id": "pl1", "home": "Arsenal", "away": "Leeds", "start_utc": START.isoformat(),
        "status": "prototype_non_calibre",
        "probabilities": {"home_win_90": .6, "draw_90": .2, "away_win_90": .2}}]}}}


def event(home, away, event_id):
    return {"eventId": event_id, "league": "England - Premier League", "home": home, "away": away,
            "startTime": START.isoformat(), "live": False, "markets": [
                {"canonicalMarket": "MATCH_RESULT", "period": "FULL_TIME", "rawName": "1X2",
                 "selections": [{"canonicalOutcome": "HOME", "odds": 1.9},
                                {"canonicalOutcome": "DRAW", "odds": 3.6},
                                {"canonicalOutcome": "AWAY", "odds": 4.2}]}]}


def fake_get(leagues_by_book=None):
    leagues_by_book = leagues_by_book or {}

    def get(prefix, sport, suffix, key, params):
        if suffix == "leagues":
            names = leagues_by_book.get((prefix, sport), [])
            return {"leagues": [{"name": n, "eventCount": 1} for n in names], "hasNextPage": False}
        if suffix.startswith("leagues/") and suffix.endswith("/events"):
            if "Premier%20League" in suffix:
                return {"events": [event("Arsenal FC", "Leeds United", "pl-" + prefix)]}
            return {"events": []}
        raise AssertionError(suffix)
    return get


class DiagnosticTests(unittest.TestCase):
    def test_matched_and_unmatched_names_are_reported_without_secret(self):
        def fake(prefix, sport, key, page):
            if sport != "soccer":
                return [], False
            if prefix == "ps3838":
                return [event("Arsenal FC", "Leeds United", "a"), event("Gunners", "Whites", "b")], False
            return [event("Arsenal", "Leeds", "c")], False
        listing = {("ps3838", "soccer"): ["Russia - Premier League", "England - Premier League",
                                           "Spain - La Liga", "Spain - La Liga 2"]}
        report = run("very-secret-key", models(), NOW, fetch=fake, sleep=lambda s: None,
                     get=fake_get(listing))
        self.assertNotIn("very-secret-key", json.dumps(report))
        ps = report["sources"]["ps3838"]["soccer"]
        self.assertEqual((ps["events_first_page"], ps["translatable"], ps["matched_to_revue"]), (2, 2, 1))
        self.assertEqual(ps["unmatched_examples"][0]["provider"], "Gunners - Whites")
        self.assertIn("PL: Arsenal - Leeds", ps["unmatched_examples"][0]["revue_same_slot"][0])
        self.assertIn("MATCH_RESULT|FULL_TIME", ps["markets"])
        self.assertEqual(report["sources"]["betclic_fr"]["soccer"]["matched_to_revue"], 1)
        self.assertEqual(report["revue_games_by_sport"], {"soccer": 1})
        pl = report["leagues"]["ps3838"]["soccer"]["tracked"]["PL"]
        # Indice de pays : la Premier League anglaise est testée en premier.
        self.assertEqual(pl["candidates"][0], "England - Premier League")
        self.assertEqual(pl["tested"][0]["matched_to_revue"], 1)
        self.assertEqual(report["leagues"]["ps3838"]["soccer"]["league_count"], 4)
        self.assertIn("Spain - La Liga", report["leagues"]["ps3838"]["soccer"]["tracked"]["LALIGA"]["candidates"])

    def test_errors_are_kept_per_source_and_missing_key_makes_no_call(self):
        def boom(prefix, sport, key, page):
            raise RuntimeError(f"HTTP 404 from PulseScore {prefix}/{sport}")
        report = run("k", models(), NOW, fetch=boom, sleep=lambda s: None, get=fake_get())
        self.assertEqual(report["sources"]["ps3838"]["soccer"]["error"], "HTTP 404 from PulseScore ps3838/soccer")
        calls = []
        report = run("", models(), NOW, fetch=lambda *a: calls.append(a), sleep=lambda s: None,
                     get=lambda *a: calls.append(a))
        self.assertEqual((report["status"], calls), ("missing_secret", []))


if __name__ == "__main__":
    unittest.main()
