"""Synthetic-only tests. No provider or reference endpoint is ever called."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from outils.collecte.diagnostic_nhl_live_matching import run, analyze_payload, refresh_references

NOW = datetime(2026, 10, 13, 20, tzinfo=timezone.utc)
PLAYER = {"player_id": "private-espn", "name": "Émile Testeur", "team": "MTL", "current_team_observed": True}
GAME = {"event_id": "private-nhl", "home": "MTL", "away": "BUF", "start_utc": "2026-10-13T22:00:00Z"}
PROFILES = {"generated_at_utc": NOW.isoformat(), "teams": {"MTL": [PLAYER]}}
FIXTURES = {"generated_at_utc": NOW.isoformat(), "games": [GAME]}
PAYLOAD = {"events": [{"league": "NHL", "eventId": "private-pmu-event", "home": "Montreal Canadiens",
    "away": "Buffalo Sabres", "startTime": GAME["start_utc"], "markets": [{
        "canonicalMarket": "ANYTIME_GOALSCORER", "period": "FULL_TIME", "selections": [{
            "rawName": PLAYER["name"], "team": "MTL", "playerId": "private-pmu-player", "odds": 9.876}]}]}]}


class LiveMatchingTests(unittest.TestCase):
    def loader(self, now):
        return deepcopy(PROFILES), deepcopy(FIXTURES)

    def forbidden(self, *args, **kwargs):
        self.fail("Unexpected network/reference call")

    def test_disabled_default_even_with_key_and_missing_key(self):
        result = run(key="private-secret", fetch=self.forbidden, reference_loader=self.forbidden)
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(result["calls"], 0)
        self.assertIsNone(result["selections_analyzed"])
        self.assertIsNone(result["real_match_rate"])
        result = run(authorized=True, fetch=self.forbidden, reference_loader=self.forbidden)
        self.assertEqual(result["status"], "missing_secret")

    def test_one_payload_for_structure_and_matching_no_sensitive_output(self):
        calls = []
        def fetch(request, **kwargs):
            calls.append(request.full_url)
            self.assertEqual(request.get_header("X-secret"), "private-secret")
            return io.BytesIO(json.dumps(PAYLOAD).encode())
        result = run(authorized=True, key="private-secret", fetch=fetch, reference_loader=self.loader, now=NOW)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["calls"], 1)
        self.assertEqual(result["selections_analyzed"], 1)
        self.assertEqual(result["real_match_rate"], 1)
        self.assertEqual(result["diagnostic"]["categories"]["goals"]["markets"], 1)
        matching = result["diagnostic"]["matching"]
        self.assertEqual(matching["schema"]["contract_status"], "structurally_observed")
        self.assertEqual(matching["counts"]["matched"], 1)
        for secret in ["private-secret", "private-espn", "private-nhl", "private-pmu-event", "private-pmu-player", "9.876", "Émile", "Testeur"]:
            self.assertNotIn(secret, json.dumps(result, ensure_ascii=False))

    def test_reference_failure_stale_future_or_empty_blocks_api(self):
        for stamp in [None, (NOW-timedelta(hours=2)).isoformat(), (NOW+timedelta(seconds=1)).isoformat()]:
            profiles = {**PROFILES, "generated_at_utc": stamp}
            result = run(authorized=True, key="test", fetch=self.forbidden,
                         reference_loader=lambda now: (profiles, FIXTURES), now=NOW)
            self.assertEqual(result["status"], "reference_refresh_failed")
            self.assertEqual(result["calls"], 0)
        def fail(now):
            raise RuntimeError("private-secret")
        result = run(authorized=True, key="test", fetch=self.forbidden, reference_loader=fail)
        self.assertNotIn("private-secret", json.dumps(result))
        for teams in [{}, {"MTL": []}, {"MTL": 3}]:
            result = run(authorized=True, key="test", fetch=self.forbidden,
                         reference_loader=lambda now: ({**PROFILES, "teams": teams}, FIXTURES), now=NOW)
            self.assertEqual(result["calls"], 0)

    def test_http_errors_consume_attempt_once_without_retry(self):
        for code in [302, 403, 429]:
            calls = []
            def fetch(*args, **kwargs):
                calls.append(1)
                raise HTTPError("private-secret", code, "private-name", {}, None)
            result = run(authorized=True, key="test", fetch=fetch, reference_loader=self.loader, now=NOW)
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["calls"], 1)
            self.assertEqual(result["status"], "http_error")
            self.assertIsNone(result["real_match_rate"])
            self.assertNotIn("private-name", json.dumps(result))

    def test_alternative_names_observed_but_never_guessed(self):
        payload = deepcopy(PAYLOAD)
        selection = payload["events"][0]["markets"][0]["selections"][0]
        selection["playerName"] = selection.pop("rawName")
        result = analyze_payload(payload, PROFILES, FIXTURES)
        self.assertEqual(result["schema"]["selection_fields_valid"]["playerName"], 1)
        self.assertEqual(result["schema"]["selections_missing_name"], 1)
        self.assertEqual(result["schema"]["contract_status"], "partial_or_incompatible")
        self.assertEqual(result["counts"]["matched"], 0)
        self.assertEqual(result["counts"]["rejection_groups"]["missing_data"], 1)

    def test_rejections_separate_names_teams_dates_and_missing_data(self):
        for field, value, group in [("rawName", "Unknown Player", "names"), ("team", "DET", "teams"),
                                     ("rawName", None, "missing_data")]:
            payload = deepcopy(PAYLOAD)
            payload["events"][0]["markets"][0]["selections"][0][field] = value
            result = analyze_payload(payload, PROFILES, FIXTURES)
            self.assertEqual(result["counts"]["rejection_groups"][group], 1)
        for value in ["2026-10-13T22:00:00", "2026-10-14T22:00:00Z"]:
            payload = deepcopy(PAYLOAD)
            payload["events"][0]["startTime"] = value
            result = analyze_payload(payload, PROFILES, FIXTURES)
            self.assertEqual(result["counts"]["rejection_groups"]["dates"], 1)

    def test_homonyms_remain_ambiguous_and_other_markets_excluded(self):
        profiles = deepcopy(PROFILES)
        profiles["teams"]["MTL"].append({**PLAYER, "player_id": "other-private-id"})
        payload = deepcopy(PAYLOAD)
        payload["events"][0]["markets"].append({"canonicalMarket": "FIRST_GOALSCORER", "period": "FULL_TIME"})
        result = analyze_payload(payload, profiles, FIXTURES)
        self.assertEqual(result["counts"]["ambiguous"], 1)
        self.assertEqual(result["counts"]["rejection_groups"]["ambiguity"], 1)
        self.assertEqual(result["counts"]["excluded_markets"], 1)

    def test_no_selections_or_bad_schema_is_not_zero_percent(self):
        for payload in [{"events": []}, {"events": {}}, []]:
            result = analyze_payload(payload, PROFILES, FIXTURES)
            self.assertIsNone(result["counts"]["match_rate"])
            self.assertEqual(result["schema"]["contract_status"], "not_observed")

    def test_identity_only_reference_refresh(self):
        game = SimpleNamespace(id="private-nhl", home="MTL", away="BUF", start_utc=NOW+timedelta(hours=2))
        rows = [{"playerId": "private-1", "skaterFullName": "Émile Testeur", "teamAbbrevs": "MTL"},
                {"playerId": "private-2", "skaterFullName": "Autre Testeur", "teamAbbrevs": "BUF"},
                {"playerId": "private-3", "skaterFullName": "Trade Testeur", "teamAbbrevs": "MTL BUF"}]
        with patch("modeles.simulations.nhl_independant.download_season", return_value=[game]), patch(
                "modeles.simulations.nhl_joueurs_independant._fetch_espn_stats",
                return_value=(rows, {"errors": [], "teams_mapped": 32, "pages_attempted": 3})):
            profiles, fixtures = refresh_references(NOW)
        self.assertEqual(sum(len(v) for v in profiles["teams"].values()), 2)
        self.assertEqual(len(fixtures["games"]), 1)
        self.assertNotIn("probabilities", json.dumps(fixtures))
        self.assertNotIn("projected_rates", json.dumps(profiles))

    def test_manual_workflow_default_false_no_automatic_trigger(self):
        source = Path(".github/workflows/nhl-pmu-matching-validation.yml").read_text()
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("default: false", source)
        self.assertNotIn("schedule:", source)
        self.assertNotIn("pull_request:", source)
        self.assertNotIn("push:", source)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.authorize_one_call", source)
        self.assertNotIn("continue-on-error", source)

    def test_partial_reference_collection_blocks_before_pmu(self):
        game = SimpleNamespace(id="test", home="MTL", away="BUF", start_utc=NOW)
        for metadata in [{"errors": ["private-error"], "teams_mapped": 32},
                         {"errors": [], "teams_mapped": 0},
                         {"errors": [], "teams_mapped": 32, "pages_attempted": 13}]:
            with patch("modeles.simulations.nhl_independant.download_season", return_value=[game]), patch(
                    "modeles.simulations.nhl_joueurs_independant._fetch_espn_stats", return_value=([], metadata)):
                result = run(authorized=True, key="test", fetch=self.forbidden, now=NOW)
            self.assertEqual(result["status"], "reference_refresh_failed")
            self.assertEqual(result["calls"], 0)

    def test_unknown_team_invalid_date_and_alias_are_not_guessed(self):
        payload = deepcopy(PAYLOAD)
        payload["events"][0]["home"] = "Canadiens"
        payload["events"][0]["startDate"] = GAME["start_utc"]
        payload["events"][0]["startTime"] = "2026-10-13T22:00:00"
        result = analyze_payload(payload, PROFILES, FIXTURES)
        self.assertEqual(result["schema"]["events_unknown_teams"], 1)
        self.assertEqual(result["schema"]["events_invalid_date"], 1)
        self.assertEqual(result["schema"]["event_fields_valid"]["startDate"], 1)
        self.assertEqual(result["counts"]["matched"], 0)


class MarketIdentityStructureTests(unittest.TestCase):
    def test_market_identity_does_not_activate_fallback_or_mutate_payload(self):
        payload = deepcopy(PAYLOAD)
        market = payload["events"][0]["markets"][0]
        market["rawName"] = PLAYER["name"]
        market["private-field-name"] = "private-value"
        market["selections"][0]["rawName"] = "Oui"
        before = deepcopy(payload)
        report = analyze_payload(payload, PROFILES, FIXTURES)
        audit = report["schema"]
        self.assertEqual(report["counts"]["reasons"], {"player_not_found": 1})
        self.assertEqual(audit["market_objects"], 1)
        self.assertEqual(audit["market_selection_cardinality"]["one"], 1)
        candidates = audit["identity_candidates"]
        self.assertEqual(candidates["market"]["rawName"]["matched"], 1)
        self.assertEqual(candidates["selection"]["rawName"]["matched"], 0)
        self.assertEqual(payload, before)
        for value in [PLAYER["name"], "private-field-name", "private-value", "Oui", "9.876", "private-pmu-player"]:
            self.assertNotIn(value, json.dumps(report, ensure_ascii=False))

    def test_candidates_reject_approximation_ambiguity_and_context_conflicts(self):
        for label, profiles, change, reason in [
            ("Émile Testeu", PROFILES, {}, "player_not_found"),
            (PLAYER["name"], {"teams": {"MTL": [PLAYER, {**PLAYER, "player_id": "second"}]}}, {}, "multiple_players"),
            (PLAYER["name"], PROFILES, {"team": "BOS"}, "team_conflict"),
        ]:
            payload = deepcopy(PAYLOAD)
            market = payload["events"][0]["markets"][0]
            market["playerName"] = label
            market["selections"][0].update(change)
            report = analyze_payload(payload, profiles, FIXTURES)
            stats = report["schema"]["identity_candidates"]["market"]["playerName"]
            self.assertEqual(stats["reasons"], {reason: 1})
            self.assertEqual(stats["matched"], 0)

    def test_types_cardinality_and_scope_without_parsing_nested_values(self):
        payload = deepcopy(PAYLOAD)
        market = payload["events"][0]["markets"][0]
        market.update(rawName={"private": PLAYER["name"]}, name=None, playerName=True,
                      participantName=123, label=[], title="Private title")
        market["selections"].append({"rawName": "Unknown"})
        report = analyze_payload(payload, PROFILES, FIXTURES)
        audit = report["schema"]
        self.assertEqual(audit["market_selection_cardinality"]["many"], 1)
        for field, kind in zip(("rawName", "name", "playerName", "participantName", "label", "title"),
                               ("object", "null", "boolean", "number", "array", "string")):
            self.assertEqual(audit["identity_candidates"]["market"][field]["types"][kind], 1)
        self.assertEqual(audit["identity_candidates"]["market"]["title"]["candidate_selections"], 2)
        self.assertEqual(audit["identity_candidates"]["selection"]["rawName"]["present"], 2)
        self.assertNotIn("Private title", json.dumps(report))
