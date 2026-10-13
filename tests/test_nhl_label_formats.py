"""Synthetic formats only: no provider requests, identities or accepted fallback."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from outils.collecte.diagnostic_nhl_label_formats import words, candidates, analyze_formats, METHODS, observe, counters
from test_nhl_live_matching import PAYLOAD, PROFILES, FIXTURES, PLAYER, NOW
from outils.collecte.diagnostic_nhl_live_matching import analyze_payload, run
import io


class LabelFormatTests(unittest.TestCase):
    def test_independent_methods_and_boundaries(self):
        names = [words("Émile Testeur"), words("Alice Autre")]
        cases = {
            "ÉMILE Testeur": {"full_exact", "full_word_contained"},
            "Émile Testeur - marque un but": {"full_word_contained"},
            "Testeur, Émile": {"reversed_full"},
            "E. Testeur": {"initials_surname"},
            "Testeur": {"surname_only"},
            "Émile TesteurXYZ": set(),
            "XÉmile Testeur": set(),
            "Émile Testeu": set(),
            "Oui": set(),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                hits = candidates(words(text), names)
                self.assertEqual({m for m, rows in hits.items() if rows}, expected)

    def test_homonyms_multiple_names_and_duplicate_rows_are_ambiguous(self):
        names = [words("Émile Testeur"), words("Eric Testeur"), words("Alice Autre")]
        for text, method in [("E. Testeur", "initials_surname"), ("Testeur", "surname_only"),
                             ("Émile Testeur ou Alice Autre", "full_word_contained")]:
            self.assertEqual(len(candidates(words(text), names)[method]), 2)
        duplicate = [names[0], names[0]]
        self.assertEqual(len(candidates(names[0], duplicate)["full_exact"]), 2)

    def test_aggregate_outcomes_and_nontext_values(self):
        stats = counters()
        names = [words("Émile Testeur"), words("Eric Testeur")]
        for value in ("Émile Testeur", "E. Testeur", "Testeur", "Introuvable", None, True, 123, {"name": "Émile Testeur"}):
            observe(value, names, stats)
        self.assertEqual(stats["texts"], 8)
        self.assertEqual(stats["missing_or_nontext"], 4)
        self.assertEqual(stats["methods"]["full_exact"], {"unique": 1, "ambiguous": 0, "impossible": 7})
        self.assertEqual(stats["methods"]["initials_surname"], {"unique": 0, "ambiguous": 1, "impossible": 7})
        self.assertEqual(stats["methods"]["surname_only"], {"unique": 0, "ambiguous": 1, "impossible": 7})
        for value in ("Oui/Non", "YES", "NO", "Oui", "Non", "Yes/No"):
            observe(value, names, stats)
        self.assertEqual(stats["generic_yes_no"], 6)
        for method in METHODS:
            self.assertEqual(sum(stats["methods"][method].values()), 14)

    def test_compound_names_have_explicit_token_rules(self):
        name = words("Jean-Pierre De Test")
        self.assertEqual(candidates(words("J. P. D. Test"), [name])["initials_surname"], [0])
        self.assertEqual(candidates(words("Pierre De Test Jean"), [name])["reversed_full"], [0])
        self.assertEqual(candidates(words("Test Jean-Pierre De"), [name])["reversed_full"], [])

    def test_private_report_units_generic_and_description(self):
        payload = deepcopy(PAYLOAD)
        market = payload["events"][0]["markets"][0]
        market["rawName"] = PLAYER["name"] + " - marque un but"
        market["private-field"] = "private-value"
        market["selections"] = [{"rawName": "Oui"}, {"rawName": "Non"}]
        before = deepcopy(payload)
        report = analyze_payload(payload, PROFILES, FIXTURES)
        fmt = report["schema"]["label_formats"]["all_references"]
        m, s = fmt["market"]["rawName"], fmt["selection"]["rawName"]
        self.assertEqual(m["texts"], 1)
        self.assertEqual(m["full_name_with_extra_text"], 1)
        self.assertEqual(m["full_name_with_bet_description"], 1)
        self.assertEqual(m["methods"]["full_word_contained"]["unique"], 1)
        self.assertEqual(s["texts"], 2)
        self.assertEqual(s["generic_yes_no"], 2)
        for method in METHODS:
            self.assertEqual(sum(m["methods"][method].values()), 1)
            self.assertEqual(s["methods"][method]["impossible"], 2)
        self.assertEqual(report["counts"]["matched"], 0)
        self.assertEqual(payload, before)
        encoded = json.dumps(report, ensure_ascii=False)
        for private in [PLAYER["name"], "private-field", "private-value", "marque un but", "private-espn", "9.876"]:
            self.assertNotIn(private, encoded)

    def test_scope_and_malformed_data(self):
        payload = deepcopy(PAYLOAD)
        payload["events"][0]["home"] = "unknown"
        report = analyze_formats(payload, PROFILES)
        self.assertEqual(report["all_references"]["selection"]["rawName"]["methods"]["full_exact"]["unique"], 1)
        self.assertEqual(report["event_teams"]["selection"]["rawName"]["methods"]["full_exact"]["impossible"], 1)
        for payload in [None, {}, {"events": [None, {"league": "KHL"}]}]:
            report = analyze_formats(payload, PROFILES)
            self.assertEqual(report["all_references"]["market"]["rawName"]["texts"], 0)
        payload = deepcopy(PAYLOAD)
        market = payload["events"][0]["markets"][0]
        market["rawName"] = {"nested": PLAYER["name"]}
        market["selections"] = None
        stats = analyze_formats(payload, PROFILES)["all_references"]["market"]["rawName"]
        self.assertEqual(stats["missing_or_nontext"], 1)
        self.assertEqual(stats["methods"]["full_exact"]["impossible"], 1)

    def test_one_response_shared_and_authorization_still_required(self):
        calls = []
        def fetch(*args, **kwargs):
            calls.append(1)
            return io.BytesIO(json.dumps(PAYLOAD).encode())
        run(key="private", fetch=fetch)
        self.assertEqual(calls, [])
        report = run(authorized=True, key="private", fetch=fetch,
                     reference_loader=lambda now: (PROFILES, FIXTURES), now=NOW)
        self.assertEqual(calls, [1])
        self.assertIn("label_formats", report["diagnostic"]["matching"]["schema"])
        workflow = Path('.github/workflows/nhl-pmu-matching-validation.yml').read_text()
        self.assertIn('default: false', workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.authorize_one_call", workflow)
        self.assertNotIn('schedule:', workflow)
        self.assertIn('test_nhl_label_formats.py', workflow)
