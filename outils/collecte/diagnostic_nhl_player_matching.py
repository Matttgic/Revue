"""Offline private aggregation hook for an authorized PMU response in memory.

No network/secret access. Reads JSON on stdin only when explicitly invoked.
Never persist the payload; export only fixed reason counters and match rates.
The initial provider-to-observation contract must be verified on real data.
"""
import json
import sys
from pathlib import Path
from outils.collecte.nhl_player_matching import match_selection
from outils.collecte.pulsescore_v2 import league_matches


def summarize(payload, profiles, fixtures, **verified_mappings):
    result = {"status": "bad_schema", "api_calls": 0, "selections": 0,
              "matched": 0, "ambiguous": 0, "impossible": 0,
              "match_rate": None, "reasons": {}, "excluded_markets": 0,
              "malformed_entries": 0}
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        return result
    if (not isinstance(profiles, dict) or not isinstance(profiles.get("teams"), dict)
            or not isinstance(fixtures, dict) or not isinstance(fixtures.get("games"), list)):
        result["status"] = "missing_reference_data"
        return result
    players = [p for group in profiles["teams"].values() if isinstance(group, list)
               for p in group if isinstance(p, dict)]
    result["status"] = "analyzed_unvalidated_provider_contract"
    for event in payload["events"]:
        if not isinstance(event, dict) or not isinstance(event.get("league"), str):
            result["malformed_entries"] += 1
            continue
        if not league_matches(event["league"], "", "NHL"):
            continue
        markets = event.get("markets")
        if not isinstance(markets, list):
            result["malformed_entries"] += 1
            continue
        for market in markets:
            if not isinstance(market, dict):
                result["malformed_entries"] += 1
                continue
            if market.get("canonicalMarket") != "ANYTIME_GOALSCORER" or market.get("period") != "FULL_TIME":
                result["excluded_markets"] += 1
                continue
            selections = market.get("selections")
            if not isinstance(selections, list):
                result["malformed_entries"] += 1
                continue
            for selection in selections:
                # rawName is compared as the entire player name, never stripped
                # of phrases, parsed for IDs, or read from odds fields.
                observation = None if not isinstance(selection, dict) else {
                    "bookmaker": "pmu_fr", "canonical_market": market["canonicalMarket"],
                    "period": market["period"], "home": event.get("home"), "away": event.get("away"),
                    "start_utc": event.get("startTime"), "provider_event_id": event.get("eventId"),
                    "name": selection.get("rawName"), "team": selection.get("team"),
                    "provider_player_id": selection.get("playerId")}
                match = match_selection(observation, players, fixtures["games"], **verified_mappings)
                result["selections"] += 1
                result[match.status] += 1
                result["reasons"][match.reason] = result["reasons"].get(match.reason, 0) + 1
    if result["selections"]:
        result["match_rate"] = result["matched"] / result["selections"]
    return result


def main():
    try:
        raw = sys.stdin.buffer.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("size")
        report = summarize(json.loads(raw),
                           json.loads(Path("docs/nhl-players-latest.json").read_text()),
                           json.loads(Path("docs/nhl-model-latest.json").read_text()))
    except (ValueError, OSError, UnicodeError):
        report = {"status": "invalid_input_or_reference", "api_calls": 0}
    print(json.dumps(report))


if __name__ == "__main__":
    main()
