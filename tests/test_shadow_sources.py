"""Offline contract tests for the read-only shadow collector."""
import unittest
from datetime import datetime, timezone, timedelta

from outils.collecte.shadow_sources import (
    same_fixture, pulse_h2h, betclic_h2h, pulse_events,
    source_state, summary, when, norm
)


def fixture_at(delta=24):
    return (datetime.now(timezone.utc) + timedelta(hours=delta)).isoformat()


class CommunityOddsShadowTests(unittest.TestCase):
    def test_same_fixture_requires_matching_teams_and_time(self):
        a = {"home": "Paris", "away": "Lyon", "startTime": fixture_at()}
        b = {"name": "Paris - Lyon", "date": a["startTime"]}
        self.assertTrue(same_fixture(a, b))
        self.assertFalse(same_fixture(a, {"name": "Paris - Monaco", "date": a["startTime"]}))
        self.assertFalse(same_fixture(a, {"name": "Paris - Lyon", "date": fixture_at(27)}))

    def test_parse_time_and_accents(self):
        self.assertEqual(norm("Équipe Saint-Étienne"), "equipesaintetienne")
        self.assertIsNone(when("invalid"))

    def test_pulse_extracts_only_fulltime_1x2(self):
        event = {"home": "Paris", "away": "Lyon",
                 "markets": [
                     {"canonicalMarket": "MATCH_RESULT", "rawName": "First half",
                      "selections": [{"canonicalOutcome": "HOME", "odds": 9}]},
                     {"canonicalMarket": "MATCH_RESULT", "rawName": "Resultat du match",
                      "selections": [
                          {"canonicalOutcome": "HOME", "odds": 1.9},
                          {"canonicalOutcome": "DRAW", "odds": 3.2},
                          {"canonicalOutcome": "AWAY", "odds": 4.1}]}
                 ]}
        self.assertEqual(pulse_h2h(event), {"home": 1.9, "draw": 3.2, "away": 4.1})

    def test_betclic_three_way(self):
        event = {"name": "Paris - Lyon",
                 "markets": [{"name": "Résultat du match",
                              "selections": [
                                  {"name": "Paris", "odds": 2.1},
                                  {"name": "Nul", "odds": 3.1},
                                  {"name": "Lyon", "odds": 3.8}]}]}
        self.assertEqual(betclic_h2h(event), {"home": 2.1, "draw": 3.1, "away": 3.8})
        event["markets"][0]["name"] = "Résultat du match (t. rég)"
        self.assertEqual(betclic_h2h(event), {"home": 2.1, "draw": 3.1, "away": 3.8})

    def test_absent_key_never_makes_network_request(self):
        report = {"sources": {"pulsescore": source_state()}}
        def no_network(*args, **kwargs):
            self.fail("No request should happen without key")
        self.assertEqual(pulse_events("", report, no_network), [])
        self.assertEqual(report["sources"]["pulsescore"]["status"], "missing_secret")

    def test_summary_never_claims_replacement(self):
        records = [{"version": "open_odds_shadow_v1", "date_utc": "2026-10-11",
                    "sources": {"pulsescore": {"status": "ok"},
                                "betclic_community": {"status": "error"},
                                "flashscore_community": {"status": "ok"}},
                    "comparison": {"same_market_1x2_matches": 2,
                                   "absolute_differences": [0.02, 0.04]}}]
        stats = summary(records)
        self.assertEqual(stats["days"], 1)
        self.assertEqual(stats["outcomes_compared"], 2)
        self.assertTrue(stats["no_replacement_proven"])
        self.assertEqual(stats["odds_difference_mean"], 0.03)
        stats = summary(records + [dict(records[0])])
        self.assertEqual(stats["days"], 1)
        self.assertEqual(stats["snapshots"], 2)


if __name__ == "__main__":
    unittest.main()
