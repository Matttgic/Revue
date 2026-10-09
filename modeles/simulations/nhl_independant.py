#!/usr/bin/env python3
"""Prototype NHL indépendant : Elo + taux de buts régularisés + Poisson.

Source de MATCHS UNIQUEMENT : NHL Web API (sans clé).
Aucun composant de Purple-Wraith n'est repris. Modèle non calibré : pas de conseil de mise.
Usage : python modeles/simulations/nhl_independant.py --date 2026-10-09
Tests : python -m unittest discover -s tests -p test_nhl_independant.py -v
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
API = "https://api-web.nhle.com/v1/club-schedule-season"
TEAMS = (
    "ANA BOS BUF CAR CBJ CGY CHI COL DAL DET EDM FLA LAK MIN MTL NJD "
    "NSH NYI NYR OTT PHI PIT SEA SJS STL TBL TOR UTA VAN VGK WPG WSH"
).split()
PRESEASON_GAMES = 12.0
HOME_FACTOR = 1.045
AWAY_FACTOR = 0.955
ELO_HOME_BONUS = 35.0
ELO_K = 18.0
MIN_GAME_QUALITY = 28


@dataclass(frozen=True)
class Game:
    id: str
    start_utc: datetime
    home: str
    away: str
    state: str
    home_goals: int | None = None
    away_goals: int | None = None
    shootout: bool = False

    @property
    def final(self) -> bool:
        return self.state in {"OFF", "FINAL"} and (
            self.home_goals is not None and self.away_goals is not None
        )


def parse_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp without timezone")
    return dt.astimezone(timezone.utc)


def parse_game(raw: dict) -> Game | None:
    """Parse one regular-season NHL schedule record, rejecting incomplete data."""
    if int(raw.get("gameType") or 0) != 2:
        return None
    home, away = raw.get("homeTeam") or {}, raw.get("awayTeam") or {}
    h, a = home.get("abbrev"), away.get("abbrev")
    if not isinstance(h, str) or not isinstance(a, str) or h == a:
        return None
    if not raw.get("id") or not raw.get("startTimeUTC"):
        return None
    state = str(raw.get("gameState") or "FUT").upper()
    def score(team):
        v = team.get("score")
        return int(v) if isinstance(v, (int, float)) and v >= 0 else None
    outcome = raw.get("gameOutcome") or {}
    return Game(
        id=str(raw["id"]),
        start_utc=parse_timestamp(raw["startTimeUTC"]),
        home=h,
        away=a,
        state=state,
        home_goals=score(home),
        away_goals=score(away),
        shootout=str(outcome.get("lastPeriodType") or "").upper() == "SO",
    )


def _get_json(url: str, retries: int = 2) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "RevueNHLResearch/0.1"})
    error = None
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, ValueError) as exc:
            error = exc
            if attempt + 1 < retries:
                time.sleep(attempt + 1)
    raise RuntimeError(f"NHL API indisponible : {url} : {error}")


def download_season(season: str) -> list[Game]:
    """Fetch each team schedule, dedupe by NHL game ID. Fail closed on partial ingest."""
    games: dict[str, Game] = {}
    problems: list[str] = []
    def one(team: str):
        response = _get_json(f"{API}/{team}/{season}")
        rows = response.get("games")
        if not isinstance(rows, list):
            raise ValueError(f"{team}: games missing")
        return team, rows
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = [pool.submit(one, team) for team in TEAMS]
        for fut in as_completed(futures):
            try:
                team, records = fut.result()
                for record in records:
                    game = parse_game(record)
                    if game:
                        if game.id in games:
                            prev = games[game.id]
                            # A final score always takes priority over an old/missing state.
                            if game.final or not prev.final:
                                games[game.id] = game
                        else:
                            games[game.id] = game
            except (RuntimeError, ValueError, KeyError, TypeError) as exc:
                problems.append(str(exc)[:180])
    if len(TEAMS) - len(problems) < MIN_GAME_QUALITY:
        raise RuntimeError(
            f"Données insuffisantes : {len(problems)} sources d'équipes échouées. "
            "Aucun pronostic publié. " + "; ".join(problems[:4])
        )
    if not games:
        raise RuntimeError("Pas de rencontres NHL récupérées")
    return sorted(games.values(), key=lambda g: (g.start_utc, g.id))


def season_code(target_date: date) -> str:
    first = target_date.year if target_date.month >= 8 else target_date.year - 1
    return f"{first}{first + 1}"


def prev_season(code: str) -> str:
    first = int(code[:4]) - 1
    return f"{first}{first + 1}"


def is_final_before(game: Game, as_of: datetime) -> bool:
    # Only for live predictions: historical as_of replays from current feed would leak.
    return game.final and game.start_utc < as_of


def _poisson(lam: float, max_goals: int = 22) -> list[float]:
    p = [math.exp(-lam)]
    for k in range(1, max_goals + 1):
        p.append(p[-1] * lam / k)
    # The tiny tail is normalized to keep reported probabilities well-formed.
    total = sum(p)
    return [v / total for v in p]


def _distribution(lh: float, la: float) -> tuple[float, float]:
    home, away = _poisson(lh), _poisson(la)
    home_win = sum(h * sum(away[:i]) for i, h in enumerate(home))
    draw = sum(h * a for h, a in zip(home, away))
    return home_win, draw


def _over(lam: float, line: float) -> float:
    # Half-integer lines only. Push/half-loss settlement needs separate modeling.
    if abs((line % 1) - 0.5) > 1e-8:
        raise ValueError("Only half-goal totals are supported")
    cutoff = math.floor(line)
    return max(0.0, min(1.0, 1 - sum(_poisson(lam)[: cutoff + 1])))


def _elo_probability(home: float, away: float) -> float:
    return 1 / (1 + 10 ** ((away - home - ELO_HOME_BONUS) / 400))


def _update_elo(ratings: dict[str, float], game: Game) -> None:
    """One update PER UNIQUE GAME, irrespective of number of published picks."""
    h, a = ratings[game.home], ratings[game.away]
    expected = _elo_probability(h, a)
    if game.home_goals == game.away_goals:
        actual = 0.5
    else:
        actual = 1.0 if game.home_goals > game.away_goals else 0.0
    ratings[game.home] = h + ELO_K * (actual - expected)
    ratings[game.away] = a + ELO_K * ((1 - actual) - (1 - expected))


def _score_for_goals(game: Game) -> tuple[int, int]:
    h, a = game.home_goals, game.away_goals
    if game.shootout and abs(h - a) == 1:
        # Shootout winner is credited with one official goal; sportsbook totals
        # normally exclude it. Keep the winning RESULT for Elo.
        if h > a:
            h -= 1
        else:
            a -= 1
    return h, a


def _team_rates(games: list[Game], fallback: float) -> dict[str, tuple[float, float]]:
    stats: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for g in games:
        h, a = _score_for_goals(g)
        stats[g.home][0] += h
        stats[g.home][1] += a
        stats[g.home][2] += 1
        stats[g.away][0] += a
        stats[g.away][1] += h
        stats[g.away][2] += 1
    return {team: (gf / n, ga / n) for team, (gf, ga, n) in stats.items() if n > 0}


def predict(games_prior: list[Game], games_current: list[Game],
            as_of: datetime, for_date: date, days: int = 2) -> list[dict]:
    """Only CURRENT scheduled games after now; no historical replay advertised."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone aware")
    prior = sorted((g for g in games_prior if is_final_before(g, as_of)),
                   key=lambda g: (g.start_utc, g.id))
    current = sorted((g for g in games_current if is_final_before(g, as_of)),
                     key=lambda g: (g.start_utc, g.id))
    unique = {}
    for g in prior + current:
        unique[g.id] = g
    prior = [g for g in prior if g.id in unique and unique[g.id] == g]
    current = [g for g in current if g.id in unique and unique[g.id] == g]
    completed = sorted(unique.values(), key=lambda g: (g.start_utc, g.id))
    league_gpg = (sum(sum(_score_for_goals(g)) for g in completed) /
                  (2 * len(completed))) if completed else 3.0
    league_gpg = max(1.5, min(4.5, league_gpg))
    prior_rates = _team_rates(prior, league_gpg)
    current_rates = _team_rates(current, league_gpg)
    counts = defaultdict(int)
    gf = defaultdict(int)
    ga = defaultdict(int)
    for g in current:
        h, a = _score_for_goals(g)
        gf[g.home] += h; ga[g.home] += a; counts[g.home] += 1
        gf[g.away] += a; ga[g.away] += h; counts[g.away] += 1
    elo: dict[str, float] = defaultdict(lambda: 1500.0)
    for game in prior:
        _update_elo(elo, game)
    # Regress past-season Elo to neutral before opening day (offseason shifts).
    for team in tuple(elo):
        elo[team] = 1500 + .70 * (elo[team] - 1500)
    for game in current:
        _update_elo(elo, game)

    def rates(team: str) -> tuple[float, float]:
        prior_gf, prior_ga = prior_rates.get(team, (league_gpg, league_gpg))
        n = counts[team]
        return (
            (gf[team] + PRESEASON_GAMES * prior_gf) / (n + PRESEASON_GAMES),
            (ga[team] + PRESEASON_GAMES * prior_ga) / (n + PRESEASON_GAMES),
        )

    output = []
    seen: set[str] = set()
    for game in sorted(games_current, key=lambda g: g.start_utc):
        if game.id in seen or game.final or game.start_utc <= as_of:
            continue
        seen.add(game.id)
        if not (for_date <= game.start_utc.astimezone(PARIS).date() < for_date + timedelta(days=days)):
            continue
        ah, dh = rates(game.home)
        aa, da = rates(game.away)
        lh = max(0.6, min(6.0, ah * da / league_gpg * HOME_FACTOR))
        la = max(0.6, min(6.0, aa * dh / league_gpg * AWAY_FACTOR))
        p_reg, p_tie = _distribution(lh, la)
        p_elo = _elo_probability(elo[game.home], elo[game.away])
        # OT/SO tie breaker approximated from strength rather than a fair coin.
        p_poisson_ml = p_reg + p_tie * p_elo
        p_home = 0.5 * p_poisson_ml + 0.5 * p_elo
        output.append({
            "event_id": game.id,
            "home": game.home,
            "away": game.away,
            "start_utc": game.start_utc.isoformat(),
            "start_paris": game.start_utc.astimezone(PARIS).isoformat(),
            "probabilities": {
                "home_win": round(p_home, 4),
                "away_win": round(1 - p_home, 4),
                "regulation_draw": round(p_tie, 4),
                "over_4_5": round(_over(lh + la, 4.5), 4),
                "over_5_5": round(_over(lh + la, 5.5), 4),
                "over_6_5": round(_over(lh + la, 6.5), 4),
            },
            "expected_goals": {"home": round(lh, 3), "away": round(la, 3)},
            "training_games": {"previous_season": len(prior), "current_season": len(current)},
            "note": "Probabilités expérimentales non calibrées ; pas de cote française intégrée.",
        })
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Date civile Europe/Paris, YYYY-MM-DD (défaut : aujourd'hui)")
    parser.add_argument("--output", default="docs/nhl-model-latest.json")
    parser.add_argument("--days", type=int, default=2, help="Nombre de jours parisiens à couvrir (1-7)")
    parser.add_argument("--fixture", help="JSON local {prior:[games], current:[games]} pour test hors réseau")
    args = parser.parse_args(argv)
    today = datetime.now(PARIS).date()
    target = date.fromisoformat(args.date) if args.date else today
    if not 1 <= args.days <= 7:
        parser.error("--days doit être entre 1 et 7")
    as_of = datetime.now(timezone.utc)
    if args.fixture:
        dataset = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        previous = [g for r in dataset["prior"] if (g := parse_game(r)) is not None]
        current = [g for r in dataset["current"] if (g := parse_game(r)) is not None]
    else:
        season = season_code(target)
        previous = download_season(prev_season(season))
        current = download_season(season)
    predictions = predict(previous, current, as_of, target, days=args.days)
    report = {
        "generated_at_utc": as_of.isoformat(),
        "date_paris": target.isoformat(),
        "days": args.days,
        "season": season_code(target),
        "model": "Revue NHL Independent v0.1 (Elo 50% + Poisson 50%)",
        "source": "NHL club-schedule-season API (recherche)",
        "status": "prototype_non_calibre",
        "bookmaker_quotes": None,
        "note": "Pas de conseils de pari. Aucun ROI/edge prouvé. Gardien et effectifs non inclus.",
        "games": predictions,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(predictions)} matchs futurs pour les {args.days} jours à partir de {target} (Paris) → {output}")
    for p in predictions:
        print(f"{p['start_paris']} | {p['away']} @ {p['home']} | "
              f"P(domicile)={p['probabilities']['home_win']:.1%} | "
              f"P(+5,5)={p['probabilities']['over_5_5']:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
