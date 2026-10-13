"""Read-only NHL coverage probe. Four requests, no retries, redirects or odds export.

This is deliberately not a player-odds adapter: a market label alone cannot
establish player identity, settlement rules or permission to republish prices.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError
import json
import os

from outils.collecte.pulsescore_v2 import BOOKMAKERS, SOURCE, league_matches
from outils.collecte.check_pulsescore_connection import KEYS

MARKETS = ("goals", "shots", "points", "assists")
MAX_CALLS = 5
# Exact semantic categories only, never substring or rawName guessing. These
# rules apply only when the API actually returns the key; they are not claims
# that these categories are offered by any bookmaker. PLAYER_SHOTS is ambiguous
# (attempts vs on-goal), as is PLAYER_TO_SCORE_OR_ASSIST (combined outcome).
CANONICAL_CATEGORIES = {
    "ANYTIME_GOALSCORER": "goals",
    "PLAYER_GOALS": "goals",
    "PLAYER_SHOTS_ON_GOAL": "shots",
    "PLAYER_POINTS": "points",
    "PLAYER_ASSISTS": "assists",
    "PLAYER_TO_ASSIST": "assists",
}


def category(market):
    """Identify a full-game category, not a verified tradable player quote."""
    label = market.get("canonicalMarket")
    if not isinstance(label, str) or market.get("period") != "FULL_TIME":
        return None
    return CANONICAL_CATEGORIES.get(label)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def diagnose(key, fetch=None):
    fetch = fetch or build_opener(NoRedirect()).open
    report = {"schema_version": 2, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "calls": 0, "max_calls": MAX_CALLS, "books": {},
              "publication": "blocked_pending_reuse_rights_and_market_validation"}
    for book, slug in BOOKMAKERS.items():
        row = {"status": "missing_secret", "nhl_events": None,
               "has_next_page": None, "player_label_candidates": 0,
               "unverified_player_markets": None,
               "markets": {m: {"status": "unverified", "market_count": None} for m in MARKETS}}
        report["books"][book] = row
        if not key:
            continue
        # NHL league name was observed for all four books in the existing survey.
        # No pagination: missing observations never imply global unavailability.
        if report["calls"] >= MAX_CALLS:
            row["status"] = "budget_exhausted"
            continue
        request = Request(f"{SOURCE}/{slug}/ice-hockey/leagues/NHL/events?page=1&limit=30",
                          headers={"X-Secret": key, "Accept": "application/json"})
        report["calls"] += 1
        try:
            with fetch(request, timeout=22) as response:
                payload = json.loads(response.read(8_000_001))
            if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
                raise ValueError("schema")
            events = [e for e in payload["events"] if isinstance(e, dict)
                      and isinstance(e.get("league"), str)
                      and league_matches(e["league"], "", "NHL")]
            row.update(status="sampled", nhl_events=len(events),
                       has_next_page=payload.get("hasNextPage") if isinstance(payload.get("hasNextPage"), bool) else None)
            row["unverified_player_markets"] = 0
            for stats in row["markets"].values():
                stats["market_count"] = 0
            for event in events:
                markets = event.get("markets", [])
                if not isinstance(markets, list):
                    continue
                for market in markets:
                    if not isinstance(market, dict):
                        continue
                    label = market.get("canonicalMarket")
                    player_candidate = isinstance(label, str) and (
                        label.startswith("PLAYER_") or "GOALSCORER" in label)
                    if player_candidate:
                        row["player_label_candidates"] += 1
                    identified = category(market)
                    if identified is not None:
                        stats = row["markets"][identified]
                        stats["market_count"] += 1
                        stats["status"] = "category_observed"
                    elif player_candidate:
                        row["unverified_player_markets"] += 1
            # Candidates are not verified odds. No names, prices, labels, IDs or
            # provider payloads are written to the public repository/artifact.
        except HTTPError as exc:
            row.update(status="http_error", http_status=exc.code)
            exc.close()
        except (URLError, TimeoutError, OSError):
            row["status"] = "network_error"
        except (ValueError, UnicodeError):
            row["status"] = "bad_schema"
    return report


def main():
    key = next((os.getenv(k) for k in KEYS if os.getenv(k)), None)
    report = diagnose(key)
    target = Path("docs/nhl-odds-diagnostic.json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NHL diagnostic: {report['calls']}/{MAX_CALLS} API calls; no odds exported")


if __name__ == "__main__":
    main()
