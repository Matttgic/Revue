"""PMU-only, one-request in-memory probe; export aggregate structure only."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
import json
import math
import os

from outils.collecte.diagnostic_nhl_player_odds import NoRedirect, CANONICAL_CATEGORIES
from outils.collecte.check_pulsescore_connection import KEYS
from outils.collecte.pulsescore_v2 import SOURCE, league_matches

URL = f"{SOURCE}/pmu/ice-hockey/leagues/NHL/events?page=1&limit=30"
CATEGORIES = ("goals", "shots", "points", "assists", "other")
# Only fixed public enum keys may appear in the report. Arbitrary strings in
# canonicalMarket could contain player names/IDs, so never echo them.
KNOWN = {**CANONICAL_CATEGORIES, "PLAYER_TO_SCORE_2_PLUS": "goals",
         "PLAYER_HATTRICK": "goals", "FIRST_GOALSCORER": "goals",
         "LAST_GOALSCORER": "goals", "PLAYER_SHOTS": "other",
         "PLAYER_TO_SCORE_OR_ASSIST": "other", "OTHER": "other",
         "OVER_UNDER": "other", "MATCH_RESULT": "other",
         "ASIAN_HANDICAP": "other", "EUROPEAN_HANDICAP": "other",
         "DOUBLE_CHANCE": "other", "DRAW_NO_BET": "other",
         "HOME_OVER_UNDER": "other", "AWAY_OVER_UNDER": "other"}


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def identifier(value):
    return (isinstance(value, str) and bool(value.strip())) or (type(value) is int and value >= 0)


def timestamp_valid(value):
    # Presence/parseability only, never proof of odds freshness. No inferred
    # timestamp from kickoff or from the time this diagnostic ran.
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.tzinfo is not None and stamp.utcoffset() is not None
    except ValueError:
        return False


def empty_stats():
    return dict.fromkeys(("markets", "markets_with_selections", "selections",
                         "valid_decimal_odds", "numeric_selection_lines", "numeric_market_lines",
                         "explicit_selection_player_ids", "explicit_market_player_ids",
                         "parseable_selection_update_times", "parseable_market_update_times",
                         "parseable_event_update_times", "selections_with_odds_line_player_id_update",
                         "non_full_time_markets"), 0)


def update(stats, market, event):
    stats["markets"] += 1
    stats["non_full_time_markets"] += market.get("period") != "FULL_TIME"
    stats["numeric_market_lines"] += numeric(market.get("line"))
    stats["explicit_market_player_ids"] += identifier(market.get("playerId"))
    market_time = any(timestamp_valid(market.get(k)) for k in ("updatedAt", "lastUpdate"))
    event_time = any(timestamp_valid(event.get(k)) for k in ("updatedAt", "lastUpdate"))
    stats["parseable_market_update_times"] += market_time
    stats["parseable_event_update_times"] += event_time
    selections = market.get("selections")
    selections = [s for s in selections if isinstance(s, dict)] if isinstance(selections, list) else []
    stats["markets_with_selections"] += bool(selections)
    stats["selections"] += len(selections)
    for selection in selections:
        odds = numeric(selection.get("odds")) and selection["odds"] > 1
        line = numeric(selection.get("line"))
        player = identifier(selection.get("playerId"))
        stamp = any(timestamp_valid(selection.get(k)) for k in ("updatedAt", "lastUpdate"))
        stats["valid_decimal_odds"] += odds
        stats["numeric_selection_lines"] += line
        stats["explicit_selection_player_ids"] += player
        stats["parseable_selection_update_times"] += stamp
        # Same selection, with explicit provenance. No cross-record merging,
        # extraction of IDs from names, or inference of a scorer line of 0.5.
        stats["selections_with_odds_line_player_id_update"] += odds and line and player and stamp


def diagnose(key, fetch=None, *, references=None):
    result = {"schema_version": 1, "bookmaker": "pmu_fr", "max_calls": 1,
              "calls": 0, "status": "missing_secret", "nhl_events": None,
              "has_next_page": None, "malformed_market_entries": None,
              "categories": None, "canonical_counts": None,
              "publication": "aggregate_structure_only_prices_blocked"}
    if not key:
        return result
    fetch = fetch or build_opener(NoRedirect()).open
    request = Request(URL, headers={"X-Secret": key, "Accept": "application/json"})
    result["calls"] = 1  # Count the attempt, even when denied or rate-limited.
    try:
        with fetch(request, timeout=22) as response:
            raw = response.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("size")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise ValueError("schema")
        events = [e for e in payload["events"] if isinstance(e, dict)
                  and isinstance(e.get("league"), str) and league_matches(e["league"], "", "NHL")]
        result.update(status="sampled", nhl_events=len(events),
                      has_next_page=payload.get("hasNextPage") if type(payload.get("hasNextPage")) is bool else None,
                      categories={c: empty_stats() for c in CATEGORIES}, canonical_counts={},
                      malformed_market_entries=0)
        for event in events:
            markets = event.get("markets")
            if not isinstance(markets, list):
                result["malformed_market_entries"] += 1
                continue
            for market in markets:
                if not isinstance(market, dict):
                    result["malformed_market_entries"] += 1
                    continue
                label = market.get("canonicalMarket")
                canonical = label if isinstance(label, str) and label in KNOWN else "UNRECOGNIZED"
                category = KNOWN.get(canonical, "other")
                update(result["categories"][category], market, event)
                stats = result["canonical_counts"].setdefault(canonical, empty_stats())
                update(stats, market, event)
        if references is not None:
            # Same in-memory payload, never a second PulseScore request.
            from outils.collecte.diagnostic_nhl_live_matching import analyze_payload
            result["matching"] = analyze_payload(payload, *references)
        # raw and payload remain in process memory only, never persisted/logged.
    except HTTPError as exc:
        result.update(status="http_error", http_status=exc.code)
        exc.close()
    except (URLError, TimeoutError, OSError):
        result["status"] = "network_error"
    except (ValueError, UnicodeError):
        result["status"] = "bad_schema"
    return result


def main():
    key = next((os.getenv(k) for k in KEYS if os.getenv(k)), None)
    report = diagnose(key)
    # Outside docs: no automatic site publication or commit step.
    Path("/tmp/nhl-pmu-structure.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PMU structure status={report['status']}; calls={report['calls']}/1; aggregates only")


if __name__ == "__main__":
    main()
