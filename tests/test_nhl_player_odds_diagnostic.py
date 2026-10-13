import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from outils.collecte.diagnostic_nhl_player_odds import diagnose, NoRedirect, category


class DiagnosticTests(unittest.TestCase):
    def test_missing_secret_never_calls(self):
        def fail(*args, **kwargs):
            self.fail("network called")
        result = diagnose(None, fail)
        self.assertEqual(result["calls"], 0)
        self.assertTrue(all(r["status"] == "missing_secret" for r in result["books"].values()))

    def test_four_books_no_sensitive_payload_exported(self):
        calls = []
        def fetch(req, **kwargs):
            calls.append(req.full_url)
            return io.BytesIO(json.dumps({"events": [
                {"league": "NHL", "home": "private_name", "markets": [
                    {"canonicalMarket": "PLAYER_SHOTS", "selections": [{"odds": 9.876}]}]},
                {"league": "KHL", "markets": [{"canonicalMarket": "PLAYER_GOALS"}]}],
                "hasNextPage": True}).encode())
        result = diagnose("secret-test-only", fetch)
        self.assertEqual(result["calls"], 4)
        self.assertEqual(len(set(calls)), 4)
        for row in result["books"].values():
            self.assertEqual(row["nhl_events"], 1)
            self.assertEqual(row["player_label_candidates"], 1)
            self.assertTrue(all(m["status"] == "unverified" for m in row["markets"].values()))
            self.assertEqual(row["unverified_player_markets"], 1)
        text = json.dumps(result)
        for sensitive in ("private_name", "9.876", "secret-test-only", "PLAYER_SHOTS"):
            self.assertNotIn(sensitive, text)

    def test_errors_do_not_retry_or_leak(self):
        for error, status in [(HTTPError("private", 429, "private", {}, None), "http_error"),
                              (HTTPError("private", 403, "private", {}, None), "http_error"),
                              (URLError("secret-test-only"), "network_error")]:
            calls = []
            def fetch(*args, **kwargs):
                calls.append(1)
                raise error
            result = diagnose("secret-test-only", fetch)
            self.assertEqual(len(calls), 4)
            self.assertTrue(all(r["status"] == status for r in result["books"].values()))
            self.assertNotIn("secret-test-only", json.dumps(result))

    def test_bad_payload_and_empty_events(self):
        for payload, status in [([], "bad_schema"), ({"events": {}}, "bad_schema"),
                                ({"events": []}, "sampled")]:
            result = diagnose("test", lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
            self.assertTrue(all(r["status"] == status for r in result["books"].values()))
            self.assertTrue(all(all(m["status"] == "unverified" for m in r["markets"].values()) for r in result["books"].values()))

    def test_distinct_counts_per_book_and_no_selection_counting(self):
        # Synthetic examples test semantic rules; they are not provider evidence.
        keys = ["ANYTIME_GOALSCORER", "PLAYER_SHOTS_ON_GOAL", "PLAYER_POINTS", "PLAYER_ASSISTS"]
        def fetch(req, **kwargs):
            index = ["betclic", "winamax", "unibet-fr", "pmu"].index(req.full_url.split("/")[4])
            market = {"canonicalMarket": keys[index], "period": "FULL_TIME",
                      "selections": [{"playerId": "private-id", "odds": 9.876}] * 3}
            return io.BytesIO(json.dumps({"events": [{"league": "NHL", "markets": [market, market]}]}).encode())
        result = diagnose("test", fetch)
        for index, row in enumerate(result["books"].values()):
            for j, stats in enumerate(row["markets"].values()):
                self.assertEqual(stats["market_count"], 2 if index == j else 0)
                self.assertEqual(stats["status"], "category_observed" if index == j else "unverified")
            self.assertEqual(row["unverified_player_markets"], 0)
        self.assertNotIn("private-id", json.dumps(result))
        self.assertNotIn("9.876", json.dumps(result))

    def test_ambiguous_combined_team_and_period_markets_stay_unverified(self):
        for label in ["PLAYER_SHOTS", "PLAYER_TO_SCORE_OR_ASSIST", "PLAYER_POINTS_ASSISTS",
                      "OVER_UNDER", "OTHER", "PLAYER_SHOTS_ON_GOAL_EXTRA", None, {}, 42]:
            self.assertIsNone(category({"canonicalMarket": label, "period": "FULL_TIME",
                                        "rawName": "Player shots on goal"}))
        for period in [None, "FIRST_PERIOD", "FIRST_HALF", "UNKNOWN"]:
            self.assertIsNone(category({"canonicalMarket": "PLAYER_POINTS", "period": period}))

    def test_missing_secret_counts_are_unknown_not_zero(self):
        for row in diagnose(None)["books"].values():
            self.assertIsNone(row["unverified_player_markets"])
            self.assertTrue(all(m["market_count"] is None for m in row["markets"].values()))

    def test_valid_empty_sample_does_not_establish_absence(self):
        result = diagnose("test", lambda *a, **k: io.BytesIO(b'{"events": []}'))
        for row in result["books"].values():
            self.assertTrue(all(m == {"status": "unverified", "market_count": 0} for m in row["markets"].values()))

    def test_hard_budget_even_if_book_list_expands(self):
        calls = []
        def fetch(*args, **kwargs):
            calls.append(1)
            return io.BytesIO(b'{"events": []}')
        with patch("outils.collecte.diagnostic_nhl_player_odds.BOOKMAKERS",
                   {str(i): str(i) for i in range(7)}):
            result = diagnose("test", fetch)
        self.assertEqual(result["calls"], 5)
        self.assertEqual(len(calls), 5)
        self.assertEqual(result["books"]["5"]["status"], "budget_exhausted")

    def test_redirects_are_disabled(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.org"))
