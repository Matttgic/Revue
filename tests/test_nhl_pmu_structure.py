"""Synthetic payloads only; no API access or provider data in these tests."""
import io
import json
import unittest
from urllib.error import HTTPError, URLError
from outils.collecte.diagnostic_nhl_pmu_structure import diagnose, timestamp_valid, URL


class PMUStructureTests(unittest.TestCase):
    def run_payload(self, payload):
        calls = []
        def fetch(request, **kwargs):
            calls.append(request.full_url)
            return io.BytesIO(json.dumps(payload).encode())
        result = diagnose("synthetic-secret", fetch)
        self.assertEqual(calls, [URL])
        self.assertEqual(result["calls"], 1)
        return result

    def test_missing_secret_zero_calls_unknown_counts(self):
        result = diagnose(None, lambda *a, **k: self.fail("network"))
        self.assertEqual(result["calls"], 0)
        self.assertIsNone(result["categories"])

    def test_categories_structure_and_no_sensitive_output(self):
        selection = {"odds": 9.876, "line": 1.5, "playerId": "private-id",
                     "rawName": "Private Player", "updatedAt": "2026-10-13T01:02:03Z"}
        keys = ["ANYTIME_GOALSCORER", "PLAYER_TO_SCORE_2_PLUS", "PLAYER_HATTRICK",
                "PLAYER_SHOTS_ON_GOAL", "PLAYER_POINTS", "PLAYER_ASSISTS",
                "PLAYER_SHOTS", "PLAYER_TO_SCORE_OR_ASSIST", "Private Player private-id"]
        markets = [{"canonicalMarket": k, "period": "FULL_TIME", "selections": [selection]} for k in keys]
        result = self.run_payload({"events": [{"league": "NHL", "markets": markets}], "hasNextPage": True})
        for category, count in {"goals": 3, "shots": 1, "points": 1, "assists": 1, "other": 3}.items():
            stats = result["categories"][category]
            self.assertEqual(stats["markets"], count)
            self.assertEqual(stats["markets_with_selections"], count)
            self.assertEqual(stats["valid_decimal_odds"], count)
            self.assertEqual(stats["selections_with_odds_line_player_id_update"], count)
        self.assertEqual(result["canonical_counts"]["UNRECOGNIZED"]["markets"], 1)
        text = json.dumps(result)
        for forbidden in ["Private Player", "private-id", "synthetic-secret", "9.876", "1.5", "2026-10-13T01:02:03Z"]:
            self.assertNotIn(forbidden, text)

    def test_absent_invalid_fields_no_inference_or_cross_selection_join(self):
        market = {"canonicalMarket": "ANYTIME_GOALSCORER", "playerId": "market-private",
                  "line": 0.5, "updatedAt": "2026-10-13T01:00:00Z", "selections": [
                      {"odds": 2.0}, {"line": 0, "playerId": "other-private"},
                      {"odds": True, "line": False, "playerId": True, "updatedAt": "bad"},
                      {"odds": float("nan"), "line": float("inf"), "playerId": {}, "updatedAt": "2026-10-13"},
                      None]}
        result = self.run_payload({"events": [{"league": "NHL", "startTime": "2026-10-13T01:00:00Z", "markets": [market]}]})
        stats = result["categories"]["goals"]
        self.assertEqual(stats["selections"], 4)
        self.assertEqual(stats["valid_decimal_odds"], 1)
        self.assertEqual(stats["numeric_selection_lines"], 1)
        self.assertEqual(stats["explicit_selection_player_ids"], 1)
        self.assertEqual(stats["numeric_market_lines"], 1)
        self.assertEqual(stats["explicit_market_player_ids"], 1)
        self.assertEqual(stats["parseable_event_update_times"], 0)
        self.assertEqual(stats["selections_with_odds_line_player_id_update"], 0)

    def test_nhl_only_empty_malformed_and_periods(self):
        result = self.run_payload({"events": [
            {"league": "KHL", "markets": [{"canonicalMarket": "PLAYER_POINTS"}]},
            {"league": "NHL", "markets": [None, {"canonicalMarket": "PLAYER_POINTS", "period": "FIRST_PERIOD", "selections": {}}]},
            {"league": "NHL"}, None], "hasNextPage": "private-name"})
        self.assertEqual(result["nhl_events"], 2)
        self.assertIsNone(result["has_next_page"])
        self.assertEqual(result["malformed_market_entries"], 2)
        self.assertEqual(result["categories"]["points"]["non_full_time_markets"], 1)
        self.assertEqual(result["categories"]["points"]["markets_with_selections"], 0)

    def test_errors_no_retry_and_no_exception_payload(self):
        for error in [HTTPError("private-id", 429, "Private Player", {}, None),
                      HTTPError("private-id", 403, "Private Player", {}, None),
                      HTTPError("private-id", 302, "Private Player", {}, None),
                      URLError("synthetic-secret")]:
            calls = []
            def fetch(*a, **k):
                calls.append(1)
                raise error
            result = diagnose("synthetic-secret", fetch)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["calls"], 1)
            self.assertIsNone(result["canonical_counts"])
            self.assertNotIn("private", json.dumps(result).lower().replace("aggregate_structure_only_prices_blocked", ""))

    def test_bad_schema_and_response_size(self):
        for payload in [[], {"events": {}}, {"events": None}]:
            self.assertEqual(self.run_payload(payload)["status"], "bad_schema")
        result = diagnose("test", lambda *a, **k: io.BytesIO(b" " * 8_000_001))
        self.assertEqual(result["status"], "bad_schema")

    def test_timestamps_require_timezone(self):
        self.assertTrue(timestamp_valid("2026-10-13T03:00:00+02:00"))
        for value in [None, 123, "2026-10-13", "2026-10-13T03:00:00", "bad"]:
            self.assertFalse(timestamp_valid(value))
