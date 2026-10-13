import io
import json
import unittest
from urllib.error import HTTPError, URLError
from outils.collecte.diagnostic_nhl_player_odds import diagnose, NoRedirect


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
            self.assertEqual(set(row["markets"].values()), {"unverified"})
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
            self.assertTrue(all(set(r["markets"].values()) == {"unverified"} for r in result["books"].values()))

    def test_redirects_are_disabled(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.org"))
