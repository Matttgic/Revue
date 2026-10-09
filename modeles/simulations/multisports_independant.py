#!/usr/bin/env python3
"""Revue multisports v0.1 — independently implemented Elo + scoring models.

Fetch real ESPN event schedules/results. No third-party repository code/data copied.
Estimates are NOT calibrated and must NOT be treated as profitable picks.
No odds: no claims of EV or betting recommendations.

Run:
  python modeles/simulations/multisports_independant.py --days 3
  python -m unittest discover -s tests -p 'test_multisports_independant.py' -v
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
BASE = "https://site.api.espn.com/apis/site/v2/sports"
# Each league is an independently retrieved feed. Unsupported sources never
# get fake predictions. These leagues offer real fixtures when in season.
@dataclass(frozen=True)
class League:
    key: str
    label: str
    sport: str
    provider: str
    style: str
    min_history: int
    history_days: int
    window_days: int = 1


LEAGUES = (
    League("NBA", "NBA", "Basket", "basketball/nba", "points", 6, 30),
    League("WNBA", "WNBA", "Basket", "basketball/wnba", "points", 6, 45),
    League("NCAAB", "NCAA Basketball", "Basket", "basketball/mens-college-basketball", "points", 4, 35),
    League("NFL", "NFL", "Football américain", "football/nfl", "points", 3, 60),
    League("MLB", "MLB", "Baseball", "baseball/mlb", "runs", 6, 32),
    League("PL", "Premier League", "Football", "soccer/eng.1", "soccer", 3, 55),
    League("LALIGA", "La Liga", "Football", "soccer/esp.1", "soccer", 3, 55),
    League("SERIEA", "Serie A", "Football", "soccer/ita.1", "soccer", 3, 55),
    League("BUNDESLIGA", "Bundesliga", "Football", "soccer/ger.1", "soccer", 3, 55),
    League("LIGUE1", "Ligue 1", "Football", "soccer/fra.1", "soccer", 3, 55),
    League("MLS", "MLS", "Football", "soccer/usa.1", "soccer", 3, 55),
    League("UCL", "Ligue des champions", "Football", "soccer/uefa.champions", "soccer", 2, 75),
)
# Honest unsupported list: this is not a working scraper for these competitions.
UNSUPPORTED = (
    {"key": "SHL", "label": "SHL (Suède)", "reason": "Flux indépendant et droits de données à connecter"},
    {"key": "LIIGA", "label": "Liiga (Finlande)", "reason": "Flux indépendant et droits de données à connecter"},
    {"key": "NL", "label": "National League (Suisse)", "reason": "Flux indépendant et droits de données à connecter"},
    {"key": "EXTRALIGA", "label": "Extraliga (Tchéquie)", "reason": "Flux indépendant et droits de données à connecter"},
    {"key": "ATP", "label": "Tennis ATP", "reason": "Calendrier, format par set et scores de joueurs à connecter"},
    {"key": "WTA", "label": "Tennis WTA", "reason": "Calendrier, format par set et scores de joueuses à connecter"},
    {"key": "UFC", "label": "UFC", "reason": "Flux de combats et modèle individuel à connecter"},
)
ESPN_HEADERS = {"Accept": "application/json"}  # avoid custom User-Agent (often causes ESPN 403)


@dataclass(frozen=True)
class Event:
    id: str
    league: str
    start: datetime
    home_id: str
    away_id: str
    home: str
    away: str
    complete: bool
    home_score: float | None
    away_score: float | None

    @property
    def scored(self) -> bool:
        return self.complete and self.home_score is not None and self.away_score is not None


def _number(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    return num if math.isfinite(num) and num >= 0 else None


def parse_event(record: dict, key: str) -> Event | None:
    """Parse ESPN scoreboard events with an explicit completed flag and kickoff."""
    if not isinstance(record, dict) or record.get("id") is None:
        return None
    try:
        start = datetime.fromisoformat(record["date"].replace("Z", "+00:00"))
        if start.tzinfo is None:
            return None
        competition = (record.get("competitions") or [])[0]
        players = competition.get("competitors") or []
        home = next(p for p in players if p.get("homeAway") == "home")
        away = next(p for p in players if p.get("homeAway") == "away")
        ht, at = home["team"], away["team"]
        home_id = str(ht.get("id") or ht.get("abbreviation") or "")
        away_id = str(at.get("id") or at.get("abbreviation") or "")
        if not home_id or not away_id or home_id == away_id:
            return None
        h = ht.get("shortDisplayName") or ht.get("displayName") or ht.get("abbreviation") or home_id
        a = at.get("shortDisplayName") or at.get("displayName") or at.get("abbreviation") or away_id
        status = record.get("status") or competition.get("status") or {}
        completed = (status.get("type") or {}).get("completed") is True
        # API status can be absent from event but supplied in competitions[0].
        if not completed:
            completed = (competition.get("status") or {}).get("type", {}).get("completed") is True
        return Event(
            id=str(record["id"]), league=key, start=start.astimezone(timezone.utc),
            home_id=home_id, away_id=away_id, home=str(h), away=str(a),
            complete=completed,
            home_score=_number(home.get("score")) if completed else None,
            away_score=_number(away.get("score")) if completed else None,
        )
    except (IndexError, KeyError, StopIteration, TypeError, ValueError, AttributeError):
        return None


def _fetch(url: str) -> dict:
    req = Request(url, headers=ESPN_HEADERS)
    last = None
    for attempt in range(2):
        try:
            with urlopen(req, timeout=16) as response:
                obj = json.loads(response.read().decode("utf-8"))
                if not isinstance(obj, dict) or not isinstance(obj.get("events"), list):
                    raise ValueError("ESPN: events missing")
                return obj
        except (HTTPError, URLError, TimeoutError, ValueError) as err:
            last = err
            if attempt == 0:
                time.sleep(0.3)
    raise RuntimeError(str(last))


def _windows(start: date, end: date, max_days: int) -> list[tuple[date, date]]:
    out = []
    while start <= end:
        stop = min(start + timedelta(days=max_days - 1), end)
        out.append((start, stop))
        start = stop + timedelta(days=1)
    return out


def query_url(league: League, start: date, end: date) -> str:
    # ESPN site scoreboard accepts a single ESPN date (YYYYMMDD).
    # Date ranges sent as YYYYMMDD-YYYYMMDD returned HTTP 400 in live CI.
    if start != end:
        raise ValueError("ESPN scoreboard requires one date per request")
    params = {"dates": start.strftime("%Y%m%d"),
              "limit": 600}
    return BASE + "/" + league.provider + "/scoreboard?" + urlencode(params)


def _cache_event(g: Event) -> dict:
    return {
        "id": g.id, "league": g.league, "start": g.start.isoformat(),
        "home_id": g.home_id, "away_id": g.away_id,
        "home": g.home, "away": g.away, "complete": g.complete,
        "home_score": g.home_score, "away_score": g.away_score,
    }


def _read_cached_event(row: dict) -> Event | None:
    try:
        start = datetime.fromisoformat(row["start"].replace("Z", "+00:00"))
        if start.tzinfo is None:
            return None
        return Event(
            id=str(row["id"]), league=str(row["league"]),
            start=start.astimezone(timezone.utc),
            home_id=str(row["home_id"]), away_id=str(row["away_id"]),
            home=str(row["home"]), away=str(row["away"]),
            complete=bool(row["complete"]),
            home_score=_number(row.get("home_score")) if row["complete"] else None,
            away_score=_number(row.get("away_score")) if row["complete"] else None,
        )
    except (KeyError, AttributeError, TypeError, ValueError):
        return None


def load_league(league: League, now: datetime, days: int,
                history: dict | None = None) -> tuple[list[Event], dict, dict]:
    """Scoreboards are queried BY DATE, with immutable completed days cached.

    Past results from successful queries are saved in a small, transparent JSON
    across GitHub Actions runs. Yesterday / today / future are always re-fetched;
    older days are fetched only if they were never successfully downloaded.
    """
    day = now.astimezone(PARIS).date()
    begin = day - timedelta(days=league.history_days)
    until = day + timedelta(days=days + 1)
    dates = [begin + timedelta(days=i) for i in range((until - begin).days + 1)]
    history = history if isinstance(history, dict) else {}
    previously_scanned = set(history.get("days_ok") or [])
    all_events: dict[str, Event] = {}
    for row in history.get("events") or []:
        ev = _read_cached_event(row)
        if ev and ev.league == league.key:
            dt = ev.start.astimezone(PARIS).date()
            if begin - timedelta(days=1) <= dt <= until + timedelta(days=1):
                all_events[ev.id] = ev

    failures: list[str] = []
    requests_ok = 0
    cached_skips = 0
    for requested in dates:
        day_key = requested.isoformat()
        # Old successful snapshots are fixed; preserve the published source
        # score exactly. Recent and upcoming dates are refreshable.
        if requested < day - timedelta(days=2) and day_key in previously_scanned:
            cached_skips += 1
            continue
        try:
            # One date per ESPN request. Multi-day ranges returned HTTP 400.
            payload = _fetch(query_url(league, requested, requested))
            requests_ok += 1
            previously_scanned.add(day_key)
            for item in payload["events"]:
                game = parse_event(item, league.key)
                if game:
                    observed_date = game.start.astimezone(PARIS).date()
                    if abs((observed_date - requested).days) <= 1:
                        prev = all_events.get(game.id)
                        if prev is None or game.scored or not prev.scored:
                            all_events[game.id] = game
        except RuntimeError as exc:
            failures.append(f"{day_key}:{str(exc)[:80]}")

    # Limit snapshots to current training horizon rather than archiving
    # full ESPN responses, personal data or vendor pricing.
    all_events = {
        gid: event for gid, event in all_events.items()
        if begin - timedelta(days=1) <= event.start.astimezone(PARIS).date()
        <= until + timedelta(days=1)
    }
    previously_scanned = {
        s for s in previously_scanned
        if begin <= date.fromisoformat(s) <= until
    }
    total = len(dates)
    successes = requests_ok + cached_skips
    status = "ok" if successes == total else "partial" if successes else "failed"
    events = sorted(all_events.values(), key=lambda e: (e.start, e.id))
    feed = {
        "status": status, "requests_ok": requests_ok, "requests_total": total,
        "cache_hits": cached_skips, "requests_failed": len(failures),
        "errors": failures[:4], "events": len(events),
        "range_min": events[0].start.astimezone(PARIS).date().isoformat() if events else None,
        "range_max": events[-1].start.astimezone(PARIS).date().isoformat() if events else None,
    }
    cache = {
        "days_ok": sorted(previously_scanned),
        "events": [_cache_event(g) for g in events],
    }
    return events, feed, cache

def _logistic(elo_home: float, elo_away: float, home_advantage: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_away - elo_home - home_advantage) / 400))


def _poisson(lam: float, cutoff: int = 23) -> list[float]:
    lam = max(0.3, min(lam, 25.0))
    values = [math.exp(-lam)]
    for i in range(1, cutoff + 1):
        values.append(values[-1] * lam / i)
    total = sum(values)
    return [x / total for x in values]


def _soccer_1x2(lh: float, la: float) -> tuple[float, float, float]:
    a, b = _poisson(lh), _poisson(la)
    p1 = sum(p * sum(b[:i]) for i, p in enumerate(a))
    px = sum(x * y for x, y in zip(a, b))
    return p1, px, max(0.0, 1.0 - p1 - px)


def _over(lam: float, line: float) -> float:
    if abs(line % 1 - 0.5) > 1e-6:
        raise ValueError("Only half-point totals supported")
    k = math.floor(line)
    return max(0.0, min(1.0, 1 - sum(_poisson(lam)[:k + 1])))


def calculate(league: League, events: list[Event], now: datetime, days: int) -> list[dict]:
    """Fit observations available now; future games never update Elo or goals."""
    if now.tzinfo is None:
        raise ValueError("now must have timezone")
    events = list({e.id: e for e in events}.values())
    training = sorted((e for e in events if e.scored and e.start < now),
                      key=lambda e: (e.start, e.id))
    future = sorted((e for e in events if not e.complete and e.start > now),
                    key=lambda e: (e.start, e.id))
    today = now.astimezone(PARIS).date()
    end = today + timedelta(days=days)
    target = [e for e in future if today <= e.start.astimezone(PARIS).date() < end]
    ratings: dict[str, float] = defaultdict(lambda: 1500.0)
    totals: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    base = {"soccer": 1.45, "points": 85.0, "runs": 4.5}[league.style]
    scored_avg = (sum(e.home_score + e.away_score for e in training) / (len(training) * 2)
                  if training else base)
    if league.style == "points":
        # NBA/football use distinct scoring scales. Learn from matches and
        # shrink toward data rather than applying an NBA prior to NFL.
        base = scored_avg
    else:
        base = 0.5 * base + 0.5 * scored_avg
    for e in training:
        nh, na = ratings[e.home_id], ratings[e.away_id]
        p = _logistic(nh, na, 30.0)
        outcome = 0.5 if e.home_score == e.away_score else (1.0 if e.home_score > e.away_score else 0.0)
        diff = 22 * (outcome - p)
        ratings[e.home_id] = nh + diff
        ratings[e.away_id] = na - diff
        totals[e.home_id][0] += e.home_score
        totals[e.home_id][1] += e.away_score
        totals[e.home_id][2] += 1
        totals[e.away_id][0] += e.away_score
        totals[e.away_id][1] += e.home_score
        totals[e.away_id][2] += 1
    out = []
    for e in target:
        hc, ac = totals[e.home_id][2], totals[e.away_id][2]
        # A minimum sample per team: no fake strong confidence from zero games.
        if hc < league.min_history or ac < league.min_history:
            out.append({
                "event_id": e.id, "home": e.home, "away": e.away,
                "start_utc": e.start.isoformat(),
                "status": "historique_insuffisant",
                "training_games": {"home": int(hc), "away": int(ac)},
                "probabilities": None, "odds": None,
            })
            continue
        prior_games = 8.0
        gf_h = (totals[e.home_id][0] + prior_games * base) / (hc + prior_games)
        ga_h = (totals[e.home_id][1] + prior_games * base) / (hc + prior_games)
        gf_a = (totals[e.away_id][0] + prior_games * base) / (ac + prior_games)
        ga_a = (totals[e.away_id][1] + prior_games * base) / (ac + prior_games)
        elo = _logistic(ratings[e.home_id], ratings[e.away_id],
                        50.0 if league.style == "points" else 30.0)
        if league.style == "soccer":
            lh = max(.25, min(4.0, (gf_h * ga_a / max(.2, base)) * 1.06))
            la = max(.25, min(4.0, (gf_a * ga_h / max(.2, base)) * .94))
            p1, px, p2 = _soccer_1x2(lh, la)
            # Elo used as a modest Bayesian-style tilt, preserve draw mass.
            p_home = .75 * p1 + .25 * (1 - px) * elo
            p_away = 1 - px - p_home
            probabilities = {
                "home_win_90": round(p_home, 4),
                "draw_90": round(px, 4),
                "away_win_90": round(p_away, 4),
                "over_2_5": round(_over(lh + la, 2.5), 4),
            }
            expected = {"home": round(lh, 2), "away": round(la, 2)}
        else:
            # Elo win probability only; point totals are rough expected values,
            # not an over/under bet and not a pricing model.
            probabilities = {
                "home_win": round(elo, 4),
                "away_win": round(1 - elo, 4),
            }
            expected = {
                "home": round(gf_h * ga_a / max(.2, base), 1),
                "away": round(gf_a * ga_h / max(.2, base), 1),
            }
        out.append({
            "event_id": e.id, "home": e.home, "away": e.away,
            "start_utc": e.start.isoformat(), "status": "prototype_non_calibre",
            "probabilities": probabilities, "expected_score": expected,
            "odds": None, "training_games": {"home": int(hc), "away": int(ac)},
        })
    return out


def load_nhl_reference(path: Path, now: datetime, days: int) -> tuple[list[dict], dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        timestamp = datetime.fromisoformat(data["generated_at_utc"].replace("Z", "+00:00"))
        age = (now - timestamp).total_seconds()
        if age < -300 or age > 24 * 3600:
            return [], {"status": "stale", "message": "Dernier calcul NHL trop ancien"}
        data_rows = []
        end = now.astimezone(PARIS).date() + timedelta(days=days)
        for g in data.get("games", []):
            start = datetime.fromisoformat(g["start_utc"])
            if start <= now or start.astimezone(PARIS).date() >= end:
                continue
            data_rows.append({
                "event_id": str(g["event_id"]), "home": g["home"], "away": g["away"],
                "start_utc": g["start_utc"], "status": "prototype_non_calibre",
                "probabilities": g["probabilities"], "expected_score": g["expected_goals"],
                "odds": None, "training_games": g.get("training_games", {}),
            })
        return data_rows, {"status": "ok", "events": len(data_rows),
                            "source": "Revue NHL independent (API NHL)"}
    except (OSError, ValueError, KeyError, TypeError) as err:
        return [], {"status": "failed", "message": str(err)[:120]}


def load_optional_sports(path: Path, now: datetime, days: int) -> tuple[dict, dict]:
    """Ingest ATP/WTA/UFC/Liiga outputs only when recent and properly tagged."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        timestamp = datetime.fromisoformat(data["generated_at_utc"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Timestamp without timezone")
        if (now-timestamp).total_seconds() > 24*3600 or timestamp > now+timedelta(minutes=5):
            return {}, {"status": "stale", "message": "Flux périmé"}
        allowed = {"ATP", "WTA", "UFC", "LIIGA", "TENNIS"}
        competitions = {}
        for key, entry in (data.get("competitions") or {}).items():
            if key not in allowed or not isinstance(entry, dict):
                continue
            source_games = entry.get("games") or []
            if not isinstance(source_games, list):
                continue
            games = []
            for g in source_games:
                try:
                    start = datetime.fromisoformat(g["start_utc"].replace("Z", "+00:00"))
                    if start.tzinfo is None or start <= now:
                        continue
                    if start.astimezone(PARIS).date() >= now.astimezone(PARIS).date()+timedelta(days=days):
                        continue
                    games.append(g)
                except (ValueError, TypeError, KeyError):
                    continue
            competitions[key] = {
                "name": str(entry.get("name") or key),
                "sport": str(entry.get("sport") or key),
                "model": str(entry.get("model") or "non calibré"),
                "status": entry.get("status", "failed"),
                "games": games,
            }
        return competitions, {"status": "ok", "competitions": len(competitions)}
    except (OSError, KeyError, ValueError, TypeError) as err:
        return {}, {"status": "failed", "message": str(err)[:120]}


def build_snapshot(when: datetime, days: int, only: set[str] | None = None,
                   nhl_file: Path | None = None, cache_store: dict | None = None,
                   optional_file: Path | None = None) -> dict:
    if not 1 <= days <= 7:
        raise ValueError("days must be 1..7")
    if only and not only.issubset({x.key for x in LEAGUES} | {"NHL", "ATP", "WTA", "UFC", "LIIGA", "TENNIS"}):
        raise ValueError("Unknown sport selection")
    selected = [v for v in LEAGUES if not only or v.key in only]
    feeds = {}
    by_league = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(load_league, league, when, days,
                            (cache_store or {}).get(league.key)): league for league in selected}
        for done in as_completed(jobs):
            league = jobs[done]
            try:
                events, feed, refreshed_cache = done.result()
                if cache_store is not None:
                    cache_store[league.key] = refreshed_cache
                games = calculate(league, events, when, days)
            except Exception as err:
                feed = {"status": "failed", "errors": [str(err)[:150]]}
                games = []
            feeds[league.key] = feed
            by_league[league.key] = {
                "name": league.label, "sport": league.sport, "model": league.style,
                "status": feed["status"], "games": games,
            }
    if not only or "NHL" in only:
        rows, check = load_nhl_reference(nhl_file or Path("docs/nhl-model-latest.json"), when, days)
        feeds["NHL"] = check
        by_league["NHL"] = {
            "name": "NHL", "sport": "Hockey", "model": "Elo + Poisson NHL",
            "status": check["status"], "games": rows,
        }
    optional, optional_diag = load_optional_sports(optional_file or Path("docs/individual-latest.json"), when, days)
    for key, record in optional.items():
        if only is None or key in only:
            by_league[key] = record
            feeds[key] = {"status": record["status"], "events": len(record["games"])}
    unsupported = [] if only else [
        {**item, "status": "source_non_connectee"} for item in UNSUPPORTED if item["key"] not in by_league
    ]
    return {
        "generated_at_utc": when.astimezone(timezone.utc).isoformat(),
        "date_paris": when.astimezone(PARIS).date().isoformat(),
        "days": days,
        "status": "prototype_non_calibre",
        "disclaimer": "Probabilités de recherche non calibrées. Sans cotes françaises ni EV. Aucun conseil de pari.",
        "competitions": by_league,
        "sources_non_connectees": unsupported,
        "overview": {
            "feeds_ok": sum(1 for s in feeds.values() if s["status"] == "ok"),
            "feeds_partial": sum(1 for s in feeds.values() if s["status"] == "partial"),
            "feeds_failed": sum(1 for s in feeds.values() if s["status"] not in ("ok", "partial")),
            "fixtures": sum(len(d["games"]) for d in by_league.values()),
            "predicted": sum(sum(g["probabilities"] is not None for g in d["games"])
                             for d in by_league.values()),
            "league_feed_diagnostics": feeds,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3, help="Nombre de jours Europe/Paris, 1-7")
    parser.add_argument("--leagues", help="Liste de ligues séparées par virgules (ex : NBA,NFL,PL,NHL)")
    parser.add_argument("--output", default="docs/multisports-latest.json")
    parser.add_argument("--nhl-file", default="docs/nhl-model-latest.json")
    parser.add_argument("--history-file", default="docs/multisports-history.json")
    parser.add_argument("--individual-file", default="docs/individual-latest.json")
    args = parser.parse_args(argv)
    selected = set(x.strip().upper() for x in args.leagues.split(",")) if args.leagues else None
    cache_file = Path(args.history_file)
    try:
        previous_cache = json.loads(cache_file.read_text(encoding="utf-8"))
        if not isinstance(previous_cache, dict) or previous_cache.get("version") != 1:
            previous_cache = {}
    except (OSError, ValueError):
        previous_cache = {}
    league_cache = previous_cache.get("leagues", {}) if isinstance(previous_cache.get("leagues"), dict) else {}
    # User removed CFB: do not keep its old cached fixtures in new snapshots.
    league_cache.pop("CFB", None)
    try:
        report = build_snapshot(
            datetime.now(timezone.utc), args.days, selected,
            Path(args.nhl_file), cache_store=league_cache,
            optional_file=Path(args.individual_file),
        )
    except ValueError as err:
        parser.error(str(err))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"version": 1, "leagues": league_cache},
                                     ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    overview = report["overview"]
    print(f"Multisports : {overview['fixtures']} matchs, {overview['predicted']} probabilités; "
          f"{overview['feeds_ok']} sources OK, {overview['feeds_partial']} partielles, "
          f"{overview['feeds_failed']} indisponibles → {output}")
    for key, v in report["competitions"].items():
        print(f"  {key:<12} {v['status']:<12} {len(v['games'])} rencontres")
    # A partial snapshot is still useful, but do not conceal a total outage.
    return 0 if overview["feeds_ok"] + overview["feeds_partial"] > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
