#!/usr/bin/env python3
"""Settle previously locked NHL SHADOW forecasts using official daily NHL scores.

Only grades existing locks; NEVER adds, replays, changes or backfills predictions.
Queries just the relevant NHL Eastern-calendar scoreboard dates, rather than
downloading every NHL team's two full-season schedules to obtain final scores.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from modeles.simulations.nhl_independant import Game, parse_game, _get_json
from outils.clairvoyance_nhl_moneypuck_shadow import as_utc
from outils.nhl_shadow_tracker import VERSION, summarize, update_ledger

EASTERN = ZoneInfo("America/New_York")
SCORE_URL = "https://api-web.nhle.com/v1/score"
MAX_DATES = 14


def due_scoreboard_dates(ledger: dict, as_of: datetime) -> list[str]:
    """Use NHL Eastern game dates, not the following Paris/UTC calendar day."""
    if as_of.tzinfo is None:
        raise ValueError("A timezone-aware as_of is mandatory")
    pending_dates = set()
    for item in ledger.get("events", []):
        if item.get("status") != "pending":
            continue
        kickoff = as_utc(item["kickoff_utc"])
        if kickoff >= as_of:
            continue
        pending_dates.add(kickoff.astimezone(EASTERN).date().isoformat())
    # Always favor recent completed games. Older unresolved dates remain in
    # the ledger and may be investigated; they never block current settlement.
    return sorted(pending_dates, reverse=True)[:MAX_DATES]


def download_results(dates: list[str], fetcher=_get_json) -> list[Game]:
    """Refuse invalid / mismatched scoreboard payloads; ignore live games."""
    by_id: dict[str, Game] = {}
    for day in dates:
        response = fetcher(f"{SCORE_URL}/{day}")
        if not isinstance(response, dict) or not isinstance(response.get("games"), list):
            raise ValueError(f"Invalid NHL scoreboard payload for {day}")
        # CurrentDate prevents silently grading a different day's scoreboard.
        if response.get("currentDate") != day:
            raise ValueError(f"NHL scoreboard returned unexpected date for {day}")
        for raw in response["games"]:
            if not isinstance(raw, dict):
                continue
            game = parse_game(raw)
            if game is None or not game.final:
                continue
            # Match ID collision (across scoreboards) must never change winner.
            old = by_id.get(game.id)
            if old is not None and old != game:
                raise ValueError(f"Conflicting official game results: {game.id}")
            by_id[game.id] = game
    return sorted(by_id.values(), key=lambda g: (g.start_utc, g.id))


def settle_existing(ledger: dict, schedule: list[Game], as_of: datetime) -> tuple[dict, dict]:
    """Reuse the immutability/fixture-matching rules of the existing tracker."""
    if ledger.get("version") != VERSION:
        raise ValueError("Unknown NHL ledger schema; refusing to mutate")
    if not isinstance(ledger.get("events"), list):
        raise ValueError("Invalid event ledger")
    unchanged_prediction = {"status": "settlement_only", "games": []}
    updated = update_ledger(ledger, unchanged_prediction, schedule, as_of)
    # No new predictions may enter during settlement.
    if len(updated["events"]) != len(ledger["events"]):
        raise AssertionError("Settlement unexpectedly changed lock count")
    existing = {str(e["event_id"]): e for e in ledger["events"]}
    for event in updated["events"]:
        old = existing[str(event["event_id"])]
        immutable = (
            "event_id", "home", "away", "kickoff_utc", "locked_at_utc",
            "source_prediction_at_utc", "home_win_probability",
            "away_win_probability", "research_home_win_probability",
            "research_model_id", "source_updated_utc", "source_snapshot_utc",
            "xg_games_observed", "historical_goalie_proxy", "model_id",
        )
        if any(event.get(k) != old.get(k) for k in immutable):
            raise AssertionError("Immutable pre-game forecast was modified")
        if old.get("status") == "settled" and event != old:
            raise AssertionError("Previously settled score was modified")
    return updated, summarize(updated, as_of)


def run(ledger: dict, as_of: datetime, fetcher=_get_json) -> tuple[dict, dict, list[str]]:
    days = due_scoreboard_dates(ledger, as_of)
    games = download_results(days, fetcher) if days else []
    updated, performance = settle_existing(ledger, games, as_of)
    return updated, performance, days


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default="docs/nhl-shadow-ledger.json")
    parser.add_argument("--performance", default="docs/nhl-shadow-performance.json")
    args = parser.parse_args()
    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        raise SystemExit("No existing immutable NHL ledger: refusing to invent predictions")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    updated, performance, days = run(ledger, now)
    if updated["events"] == ledger.get("events", []):
        print(f"NHL score check: {len(days)} day(s), no newly settled results; "
              "preserving the published immutable ledger and report.")
        return
    # Only publish after all requested scoreboards pass schema/mapping checks.
    payloads = ((ledger_path, updated), (Path(args.performance), performance))
    for path, data in payloads:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".new")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                             encoding="utf-8")
        temporary.replace(path)
    print(f"NHL official score days: {len(days)} | locks: {performance['locked_events']} | "
          f"settled: {performance['settled']} | pending: {performance['pending']} | "
          f"paired settled: {performance['research_paired_settled']}")


if __name__ == "__main__":
    main()
