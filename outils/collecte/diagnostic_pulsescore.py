#!/usr/bin/env python3
"""Diagnostic PulseScore : pourquoi un bookmaker ne se rattache pas aux matchs Revue.

Pour chaque source (bookmakers français + référence PS3838) et chaque sport,
lit UNE page d'événements et publie : nombre d'événements, combien sont
convertibles, combien se rattachent à un match Revue, un échantillon des noms
d'équipes et de ligues, l'inventaire des marchés (canonicalMarket, period,
rawName) et, pour les événements non rattachés, les matchs Revue du même
créneau, pour comparer les graphies.

Aucune clé, aucun en-tête, aucune cote n'est écrite dans le rapport.
Lancement manuel uniquement (workflow « Revue - Diagnostic PulseScore »).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import quote

from outils.collecte.pulsescore_v2 import (
    SCAN_BOOKS, SPORT_GROUPS, MIN_INTERVAL_PER_BOOK, _get_json, _request, translate_event,
)
from outils.suivi.revue_engine_v2 import match_fixture, timestamp, ODDS_SPORTS

KEYS = ("PULSESCORE_API_KEY", "PULSESCORE_PRO_KEY", "PULSE_SCORE_API_KEY")
HORIZON = timedelta(hours=48)
SAMPLES = 6
# Repérage large des ligues suivies dans le catalogue de chaque bookmaker ;
# les indices de pays servent seulement à tester en premier les plus probables.
LEAGUE_TOKENS = {
    "NFL": (["nfl"], []), "MLB": (["mlb", "major league"], []), "NHL": (["nhl"], []),
    "PL": (["premier league"], ["england", "angleterre"]),
    "LALIGA": (["laliga", "la liga", "liga espa", "primera division", "espagne", "spain"], ["spain", "espagne"]),
    "SERIEA": (["serie a", "italie", "italy"], ["italy", "italie"]),
    "BUNDESLIGA": (["bundesliga", "allemagne", "germany"], ["germany", "allemagne"]),
    "LIGUE1": (["ligue 1", "france"], ["france"]),
    "MLS": (["mls", "major league soccer"], ["usa", "etats", "états"]),
}
MAX_LEAGUE_PAGES = 8
TESTED_PER_LEAGUE = 3


def _names(items: list) -> list[str]:
    out = []
    for item in items:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            for field in ("name", "league", "leagueName", "title"):
                if isinstance(item.get(field), str) and item[field]:
                    out.append(item[field])
                    break
    return out


def _list_payload(data: dict) -> list:
    for field in ("leagues", "data", "items", "results", "events"):
        if isinstance(data.get(field), list):
            return data[field]
    return []


def candidates(names: list[str], revue_league: str) -> list[str]:
    tokens, hints = LEAGUE_TOKENS[revue_league]
    found = [n for n in names if any(t in n.lower() for t in tokens)]
    return sorted(found, key=lambda n: (not any(h in n.lower() for h in hints), len(n), n))


def revue_games(models: dict, now: datetime) -> dict[str, list[dict]]:
    """Matchs Revue à venir (avec probabilités), groupés par sport PulseScore."""
    by_sport: dict[str, list[dict]] = {}
    for league, entry in (models.get("competitions") or {}).items():
        if league not in SPORT_GROUPS or league not in ODDS_SPORTS:
            continue
        for g in entry.get("games") or []:
            start = timestamp(g.get("start_utc"))
            if start and now < start <= now + HORIZON and isinstance(g.get("probabilities"), dict):
                by_sport.setdefault(SPORT_GROUPS[league], []).append({**g, "_league": league})
    return by_sport


def summarize(records: list[dict], book_key: str, games: list[dict], now: datetime) -> dict:
    markets = Counter()
    raw_names = Counter()
    translatable = matched = 0
    unmatched = []
    for raw in records:
        for m in raw.get("markets") or []:
            markets[f"{m.get('canonicalMarket')}|{m.get('period')}"] += 1
            raw_names[str(m.get("rawName") or "")] += 1
        quote = translate_event(raw, book_key, now)
        if not quote:
            continue
        translatable += 1
        hit = None
        for league in sorted({g["_league"] for g in games}):
            hit = hit or match_fixture(quote, [g for g in games if g["_league"] == league], league)
        if hit:
            matched += 1
        elif len(unmatched) < SAMPLES:
            start = timestamp(quote["commence_time"])
            near = [f"{g['_league']}: {g['home']} - {g['away']} ({g['start_utc'][:16]})"
                    for g in games
                    if start and abs(timestamp(g["start_utc"]) - start) <= timedelta(hours=3)][:4]
            unmatched.append({"provider": f"{raw.get('home')} - {raw.get('away')}",
                              "league": raw.get("league"), "start": str(quote["commence_time"])[:16],
                              "revue_same_slot": near})
    return {
        "events_first_page": len(records),
        "translatable": translatable,
        "matched_to_revue": matched,
        "sample_events": [{"league": r.get("league"), "home": r.get("home"), "away": r.get("away"),
                           "start": str(r.get("startTime") or r.get("startDate"))[:16]}
                          for r in records[:SAMPLES]],
        "markets": dict(markets.most_common(15)),
        "raw_market_names": [name for name, _ in raw_names.most_common(20)],
        "unmatched_examples": unmatched,
    }


def league_survey(key: str, book_key: str, prefix: str, sport: str, games: list[dict],
                  now: datetime, get, pace) -> dict:
    """Liste les ligues du bookmaker, puis teste l'endpoint par ligue pour les ligues suivies."""
    names, first = [], None
    for page in range(1, MAX_LEAGUE_PAGES + 1):
        pace(prefix)
        data = get(prefix, sport, "leagues", key, {"page": page, "limit": 100})
        items = _list_payload(data)
        if first is None:
            first = {"top_level_keys": sorted(data)[:15],
                     "first_item": items[0] if items and isinstance(items[0], (str, dict)) else None}
            if isinstance(first["first_item"], dict):
                first["first_item"] = {k: v for k, v in first["first_item"].items()
                                       if not isinstance(v, (list, dict))}
        names += _names(items)
        if not items or data.get("hasNextPage") is not True:
            break
    out = {"listing": first, "league_count": len(names), "tracked": {}}
    if sport != "soccer":
        out["all_names"] = names[:80]
    for revue_league in [lg for lg, sp in SPORT_GROUPS.items() if sp == sport and lg in LEAGUE_TOKENS]:
        found = candidates(names, revue_league)
        tests = []
        for name in found[:TESTED_PER_LEAGUE]:
            pace(prefix)
            try:
                data = get(prefix, sport, f"leagues/{quote(name, safe='')}/events", key,
                           {"page": 1, "limit": 50})
            except Exception as err:
                tests.append({"name": name, "error": str(err)})
                continue
            records = data.get("events") if isinstance(data.get("events"), list) else []
            summary = summarize(records, book_key, [g for g in games if g["_league"] == revue_league], now)
            tests.append({"name": name, "events": summary["events_first_page"],
                          "translatable": summary["translatable"],
                          "matched_to_revue": summary["matched_to_revue"]})
        out["tracked"][revue_league] = {"candidates": found[:12], "tested": tests}
    return out


def run(key: str, models: dict, now: datetime, fetch=_request, sleep=time.sleep,
        get=_get_json) -> dict:
    games = revue_games(models, now)
    report = {"generated_at_utc": now.isoformat(), "horizon_hours": int(HORIZON.total_seconds() // 3600),
              "revue_games_by_sport": {s: len(v) for s, v in sorted(games.items())},
              "revue_samples": {s: [f"{g['_league']}: {g['home']} - {g['away']} ({g['start_utc'][:16]})"
                                    for g in v[:SAMPLES]] for s, v in sorted(games.items())},
              "sources": {}}
    if not key:
        report["status"] = "missing_secret"
        return report
    last: dict[str, float] = {}

    def pace(prefix: str) -> None:
        wait = last.get(prefix, 0.0) + MIN_INTERVAL_PER_BOOK - time.monotonic()
        if wait > 0:
            sleep(wait)
        last[prefix] = time.monotonic()

    report["leagues"] = {}
    for sport in sorted(set(SPORT_GROUPS.values())):
        for book_key, prefix in SCAN_BOOKS.items():
            pace(prefix)
            cell = report["sources"].setdefault(book_key, {})
            try:
                records, _ = fetch(prefix, sport, key, 1)
            except Exception as err:  # message déjà nettoyé par _request (pas d'URL ni de clé)
                cell[sport] = {"error": str(err)}
                continue
            cell[sport] = summarize(records, book_key, games.get(sport, []), now)
            try:
                report["leagues"].setdefault(book_key, {})[sport] = league_survey(
                    key, book_key, prefix, sport, games.get(sport, []), now, get, pace)
            except Exception as err:
                report["leagues"].setdefault(book_key, {})[sport] = {"error": str(err)}
    report["status"] = "done"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="docs/multisports-latest.json")
    parser.add_argument("--output", default="docs/pulsescore-diagnostic-latest.json")
    args = parser.parse_args()
    key = next((os.environ.get(k) for k in KEYS if os.environ.get(k)), "")
    models = json.loads(Path(args.models).read_text(encoding="utf-8"))
    report = run(key, models, datetime.now(timezone.utc))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Diagnostic PulseScore :", report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
