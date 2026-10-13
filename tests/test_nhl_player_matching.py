"""All identities and provider observations below are deliberately synthetic."""
from copy import deepcopy
from collections import Counter
import json
import unittest
from outils.collecte.nhl_player_matching import match_selection, name_key
from outils.collecte.diagnostic_nhl_player_matching import summarize


PLAYER = {"player_id": "espn-test-1", "name": "Pierre-Émile D'Exemple", "team": "MTL", "current_team_observed": True}
GAME = {"event_id": "nhl-test-1", "home": "MTL", "away": "BUF", "start_utc": "2026-10-13T22:30:00Z"}
OBS = {"bookmaker": "pmu_fr", "canonical_market": "ANYTIME_GOALSCORER", "period": "FULL_TIME",
       "name": PLAYER["name"], "team": "MTL", "home": "Montreal Canadiens", "away": "Buffalo Sabres",
       "start_utc": GAME["start_utc"]}


def scenarios():
    cases = []
    def add(status, observation=None, players=None, games=None, **mappings):
        cases.append((status, observation or deepcopy(OBS), players or [deepcopy(PLAYER)], games or [deepcopy(GAME)], mappings))
    add("matched")
    add("matched", {**OBS, "name": "PIERRE EMILE DEXEMPLE"})
    add("matched", {**OBS, "name": "Pierre–Émile D’Exemple"})
    add("matched", {**OBS, "name": "P. E. D'Exemple"}, aliases={PLAYER["player_id"]: ["P. E. D'Exemple"]})
    add("matched", {**OBS, "team": None})
    add("matched", {**OBS, "name": None, "provider_player_id": "pmu-test"}, player_crosswalk={"pmu-test": PLAYER["player_id"]})
    add("matched", {**OBS, "provider_player_id": PLAYER["player_id"]})  # name, not ID-number equality
    add("ambiguous", {**OBS, "team": None}, [PLAYER, {**PLAYER, "player_id": "espn-test-2", "team": "BUF"}])
    add("ambiguous", players=[PLAYER, {**PLAYER, "player_id": "espn-test-2"}])
    add("ambiguous", games=[GAME, deepcopy(GAME)])
    add("ambiguous", players=[PLAYER, {**PLAYER, "team": "BUF"}])
    for patch in [{"canonical_market": "FIRST_GOALSCORER"}, {"bookmaker": "other"},
                  {"team": "DET"}, {"home": "BUF", "away": "MTL"},
                  {"start_utc": "2026-10-14T22:30:00Z"}, {"start_utc": "2026-10-13T22:30:00"},
                  {"name": None}, {"home": "Canadiens"}, {"name": "P. D'Exemple"},
                  {"name": None, "provider_player_id": PLAYER["player_id"]}]:
        add("impossible", {**OBS, **patch})
    add("impossible", {**OBS, "provider_player_id": "pmu-test"}, player_crosswalk={"pmu-test": "different-espn-id"})
    add("impossible", players=[{**PLAYER, "current_team_observed": False}])
    return cases


class MatchingTests(unittest.TestCase):
    def test_synthetic_scenarios_and_totals(self):
        counts = Counter()
        for expected, obs, players, games, mapping in scenarios():
            with self.subTest(expected=expected, observation=obs):
                result = match_selection(obs, players, games, **mapping)
                self.assertEqual(result.status, expected)
                counts[result.status] += 1
                if expected != "matched":
                    self.assertIsNone(result.player_id)
                    self.assertIsNone(result.event_id)
        self.assertEqual(counts, {"matched": 7, "ambiguous": 4, "impossible": 12})

    def test_verified_id_disambiguates_but_conflicts_reject(self):
        players = [PLAYER, {**PLAYER, "player_id": "espn-test-2"}]
        obs = {**OBS, "provider_player_id": "pmu-test"}
        self.assertEqual(match_selection(obs, players, [GAME], player_crosswalk={"pmu-test": "espn-test-2"}).player_id, "espn-test-2")
        self.assertEqual(match_selection({**obs, "name": "Other Person"}, players, [GAME], player_crosswalk={"pmu-test": "espn-test-2"}).status, "impossible")
        self.assertEqual(match_selection({**OBS, "provider_event_id": "pmu-event"}, [PLAYER], [GAME], event_crosswalk={"pmu-event": "wrong-event"}).status, "impossible")

    def test_time_tolerance_and_timezone(self):
        self.assertEqual(match_selection({**OBS, "start_utc": "2026-10-14T00:30:00+02:00"}, [PLAYER], [GAME]).status, "matched")
        self.assertEqual(match_selection({**OBS, "start_utc": "2026-10-13T22:45:01Z"}, [PLAYER], [GAME]).status, "impossible")

    def test_invalid_inputs_and_no_fuzzy_or_suffix_stripping(self):
        for patch in [{"name": 42}, {"provider_player_id": {}}, {"provider_event_id": True},
                      {"period": "FIRST_PERIOD"}, {"name": "Pierre Emile DExemple Jr"}]:
            self.assertEqual(match_selection({**OBS, **patch}, [PLAYER], [GAME]).status, "impossible")
        self.assertEqual(match_selection(None, [PLAYER], [GAME]).status, "impossible")
        self.assertNotEqual(name_key("Alex Example Jr"), name_key("Alex Example"))

    def test_aggregate_diagnostic_no_sensitive_fields_or_network(self):
        payload = {"events": [{"league": "NHL", "home": OBS["home"], "away": OBS["away"],
            "startTime": OBS["start_utc"], "eventId": "private-event", "markets": [
                {"canonicalMarket": "FIRST_GOALSCORER", "period": "FULL_TIME", "selections": [{"rawName": PLAYER["name"]}]},
                {"canonicalMarket": "ANYTIME_GOALSCORER", "period": "FULL_TIME", "selections": [
                    {"rawName": PLAYER["name"], "team": "MTL", "playerId": "private-id", "odds": 9.876},
                    {"rawName": "Unknown Person"}, None]}]}]}
        report = summarize(payload, {"teams": {"MTL": [PLAYER]}}, {"games": [GAME]})
        self.assertEqual(report["matched"], 1)
        self.assertEqual(report["impossible"], 2)
        self.assertEqual(report["excluded_markets"], 1)
        self.assertEqual(report["match_rate"], 1/3)
        self.assertEqual(report["api_calls"], 0)
        for value in [PLAYER["name"], PLAYER["player_id"], GAME["event_id"], "private-id", "private-event", "9.876"]:
            self.assertNotIn(value, json.dumps(report))

    def test_missing_reference_empty_and_malformed_payloads(self):
        self.assertEqual(summarize({}, {}, {})["status"], "bad_schema")
        self.assertEqual(summarize({"events": []}, {}, {})["status"], "missing_reference_data")
        result = summarize({"events": []}, {"teams": {}}, {"games": []})
        self.assertIsNone(result["match_rate"])
        self.assertEqual(result["selections"], 0)

    def test_alias_collision_is_rejected_and_diagnostic_counts_ambiguity(self):
        players = [PLAYER, {**PLAYER, "player_id": "espn-test-2", "name": "Other Person"}]
        aliases = {"espn-test-2": [PLAYER["name"]]}
        self.assertEqual(match_selection(OBS, players, [GAME], aliases=aliases).status, "ambiguous")
        homonyms = [PLAYER, {**PLAYER, "player_id": "espn-test-2", "team": "BUF"}]
        payload = {"events": [{"league": "NHL", "home": OBS["home"], "away": OBS["away"],
            "startTime": OBS["start_utc"], "markets": [{"canonicalMarket": "ANYTIME_GOALSCORER",
            "period": "FULL_TIME", "selections": [{"rawName": PLAYER["name"]}]}]}]}
        result = summarize(payload, {"teams": {"MTL": homonyms}}, {"games": [GAME]})
        self.assertEqual(result["ambiguous"], 1)
        self.assertEqual(result["matched"], 0)
        self.assertEqual(result["match_rate"], 0)
