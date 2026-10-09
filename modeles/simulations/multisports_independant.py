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
    window_days: int = 7


LEAGUES = (
    League("NBA", "NBA", "Basket", "basketball/nba", "points", 6, 30),
    League("WNBA", "WNBA", "Basket", "basketball/wnba", "points", 6, 45),
    League("NCAAB", "NCAA Basketball", "Basket", "basketball/mens-college-basketball", "points", 4, 35),
    League("NFL", "NFL", "Football américain", "football/nfl", "points", 3, 60),
    League("CFB", "NCAA Football", "Football américain", "football/college-football", "points", 3, 35),
    League("MLB", "MLB", "Baseball", "baseball/mlb", "runs", 6, 32),
    League("PL", "Premier League", "Football", "soccer/eng.1", "soccer", 5, 75),
    League("LALIGA", "La Liga", "Football", "soccer/esp.1", "soccer", 5, 75),
    League("SERIEA", "Serie A", "Football", "soccer/ita.1", "soccer", 5, 75),
    League("BUNDESLIGA", "Bundesliga", "Football", "soccer/ger.1", "soccer", 5, 75),
    League("LIGUE1", "Ligue 1", "Football", "soccer/fra.1", "soccer", 5, 75),
    League("MLS", "MLS", "Football", "soccer/usa.1", "soccer", 5, 75),
    League("UCL", "Ligue des champions", "Football", "soccer/uefa.champions", "soccer", 5, 75),
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
    # ESPN uses YYYYMMDD-YYYYMMDD for ranges.
    params = {"dates": start.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"),
              "limit": 600}
    return BASE + "/" + league.provider + "/scoreboard?" + urlencode(params)


def load_league(league: League, now: datetime, days: int) -> tuple[list[Event], dict]:
    """Never silently report a successful feed when all requests errored."""
    day = now.astimezone(PARIS).date()
    intervals = _windows(day - timedelta(days=league.history_days),
                         day + timedelta(days=days + 1), league.window_days)
    all_events: dict[str, Event] = {}
    failures = []
    responses = 0
    first_dates = []
    for start, end in intervals:
        try:
            payload = _fetch(query_url(league, start, end))
            raw = payload["events"]
            responses += 1
            for v in raw:
                parsed = parse_event(v, league.key)
                if parsed:
                    # exclude unwanted ESPN default date fallback outside requested range
                    dt = parsed.start.astimezone(PARIS).date()
                    if start - timedelta(days=1) <= dt <= end + timedelta(days=1):
                        previous = all_events.get(parsed.id)
                        if previous is None or (parsed.scored and not previous.scored):
                            all_events[parsed.id] = parsed
                        first_dates.append(dt)
        except RuntimeError as exc:
            failures.append(f"{start}:{str(exc)[:90]}")
    # Using a partial history could skew season strength; report exactly how much.
    status = "ok" if responses == len(intervals) else "partial" if responses else "failed"
    return sorted(all_events.values(), key=lambda e: (e.start, e.id)), {
        "status": status, "requests_ok": responses, "requests_total": len(intervals),
        "errors": failures[:4], "events": len(all_events),
        "range_min": min(first_dates).isoformat() if first_dates else None,
        "range_max": max(first_dates).isoformat() if first_dates else None,
    }


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


def build_snapshot(when: datetime, days: int, only: set[str] | None = None,
                   nhl_file: Path | None = None) -> dict:
    if not 1 <= days <= 7:
        raise ValueError("days must be 1..7")
    if only and not only.issubset({x.key for x in LEAGUES} | {"NHL"}):
        raise ValueError("Unknown sport selection")
    selected = [v for v in LEAGUES if not only or v.key in only]
    feeds = {}
    by_league = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(load_league, league, when, days): league for league in selected}
        for done in as_completed(jobs):
            league = jobs[done]
            try:
                events, feed = done.result()
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
    unsupported = [] if only else [
        {**item, "status": "source_non_connectee"} for item in UNSUPPORTED
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
    args = parser.parse_args(argv)
    selected = set(x.strip().upper() for x in args.leagues.split(",")) if args.leagues else None
    try:
        report = build_snapshot(
            datetime.now(timezone.utc), args.days, selected, Path(args.nhl_file)
        )
    except ValueError as err:
        parser.error(str(err))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
