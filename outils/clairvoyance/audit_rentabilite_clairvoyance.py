#!/usr/bin/env python3
"""Audit indépendant de la rentabilité affichée par Clairvoyance.

Lit, dans un checkout temporaire en lecture seule du dépôt public
Purple-Wraith/clairvoyance-backend, le registre docs/picks_backup.json et les
calendriers horodatés, puis répond à deux questions :

1. le pari a-t-il été verrouillé AVANT le coup d'envoi ? (classificateur
   reproduit dans modeles/reproduction/clairvoyance_lock_timing.py) ;
2. la cote utilisée pour compter les unités est-elle une cote de marché
   observée, ou une cote par défaut (-110) / « juste » du modèle (1/p) ?

Seuls des agrégats sont publiés : aucun pari ni fichier source n'est recopié.
Un ROI sur des cotes non observées n'est pas un rendement atteignable.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import subprocess

from modeles.reproduction.clairvoyance_lock_timing import (
    DENVER, classify, is_parlay, iso_millis, match_key, sport_code,
)

# Fichiers calendrier du source : (fichier, conteneur, clé domicile, clé extérieur)
SCHEDULES = (
    ("shl_schedule.json", "games", "homeName", "awayName"),
    ("liiga_schedule.json", "games", "homeName", "awayName"),
    ("nla_schedule.json", "games", "homeName", "awayName"),
    ("extraliga_schedule.json", "games", "homeName", "awayName"),
    ("nhl_schedule.json", "games", "home", "away"),
    ("cfb_schedule.json", "weeks", "home", "away"),
    ("nfl_schedule.json", "weeks", "home", "away"),
)
HISTORY = "game_start_history.json"
SOCCER = {"PL", "LIGA", "BUND", "SERIEA", "MLS", "CL", "WC"}
HOCKEY = {"NHL", "SHL", "LIIGA", "NLA", "EXTRALIGA", "KHL", "NCAAH"}
VERSION = "revue_clairvoyance_profitability_audit_v2"
# Un verrouillage daté de plus de 300 jours AVANT le match est impossible pour
# une prévision réelle : saisie a posteriori ou horodatage reconstruit.
BACKFILL_DAYS = 300


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def start_index(docs: Path) -> dict:
    """Historique d'abord, calendriers vivants ensuite (même priorité que le source)."""
    index: dict = {}
    history = _read(docs / HISTORY) or {}
    for key, value in (history.get("games") or {}).items():
        try:
            index[key] = float(value)
        except (TypeError, ValueError):
            continue
    for name, container, home_key, away_key in SCHEDULES:
        data = _read(docs / name) or {}
        raw = data.get(container) or ([] if container == "games" else {})
        games = raw if container == "games" else [
            g for week in raw.values() for g in (week or [])]
        for game in games:
            if not isinstance(game, dict):
                continue
            ms = iso_millis(game.get("date"))
            home, away = game.get(home_key), game.get(away_key)
            if ms is None or not home or not away:
                continue
            day = datetime.fromtimestamp(ms / 1000, DENVER).date().isoformat()
            index[match_key(day, home, away)] = ms
    return index


def decimal_odds(pick: dict):
    try:
        value = float(pick.get("decOdds"))
        if value > 1:
            return value
    except (TypeError, ValueError):
        pass
    try:
        ml = float(str(pick.get("ml")).replace("+", ""))
    except (TypeError, ValueError):
        return None
    if ml == 0 or -100 < ml < 100:
        return None
    return 1 + ml / 100 if ml > 0 else 1 + 100 / abs(ml)


def stated_probability(pick: dict):
    try:
        value = float(pick.get("winProb"))
    except (TypeError, ValueError):
        return None
    if value > 1:
        value /= 100
    return value if 0 < value < 1 else None


def price_provenance(pick: dict, odds: float) -> str:
    """market = cote réellement observée ; le reste n'est pas un prix atteignable prouvé."""
    label = pick.get("priceSource")
    if label in ("market", "estimated", "assumed"):
        return label
    p = stated_probability(pick)
    if p and abs(odds - 1 / p) < 0.01:
        return "model_fair_1_over_p"
    if str(pick.get("ml")).strip() in ("-110", "-110.0"):
        return "default_minus_110"
    return "unlabelled"


def family(pick: dict) -> str:
    sport, kind = sport_code(pick), str(pick.get("betType") or "").upper()
    if sport in ("CFB", "NFL") and kind in ("SPREAD", "OU"):
        return "us_football_spread_total"
    if sport in SOCCER:
        return "soccer_1x2" if kind == "ML" else "soccer_total_or_handicap"
    if sport in HOCKEY:
        return "hockey_handicap" if kind in ("SPREAD", "PL", "RL") else "hockey_" + (kind.lower() or "unknown")
    return (sport or "unknown").lower() + "_" + (kind.lower() or "unknown")


def backfilled(pick: dict) -> bool:
    try:
        locked = datetime.fromtimestamp(float(pick.get("lockedAt")) / 1000, timezone.utc).date()
        played = date.fromisoformat(str(pick.get("date"))[:10])
    except (TypeError, ValueError, OverflowError, OSError):
        return False
    return (played - locked).days > BACKFILL_DAYS


def summary(rows: list[dict]) -> dict | None:
    n = len(rows)
    if not n:
        return None
    returns = [(r["odds"] - 1) if r["won"] else -1.0 for r in rows]
    mean = sum(returns) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in returns) / (n - 1)) if n > 1 else 0.0
    half = 1.96 * sd / math.sqrt(n)
    stated = [r["p"] for r in rows if r["p"] is not None]
    return {
        "n": n,
        "win_rate": round(sum(r["won"] for r in rows) / n, 4),
        "mean_implied_probability": round(sum(1 / r["odds"] for r in rows) / n, 4),
        "mean_stated_probability": round(sum(stated) / len(stated), 4) if stated else None,
        "units": round(sum(returns), 2),
        "roi": round(mean, 4),
        "roi_95ci": [round(mean - half, 4), round(mean + half, 4)],
        "roi_ci_excludes_zero": (mean - half) > 0 or (mean + half) < 0,
    }


def collect(picks: list, index: dict) -> list[dict]:
    rows = []
    for pick in picks:
        if not isinstance(pick, dict) or pick.get("outcome") not in ("win", "loss"):
            continue
        if is_parlay(pick):
            continue
        odds = decimal_odds(pick)
        if odds is None:
            continue
        rows.append({
            "timing": classify(pick, index),
            "price": price_provenance(pick, odds),
            "family": family(pick),
            "sport": sport_code(pick) or "unknown",
            "odds": odds,
            "won": pick["outcome"] == "win",
            "p": stated_probability(pick),
            "date": str(pick.get("date") or ""),
            "backfilled": backfilled(pick),
        })
    return rows


def group(rows, key) -> dict:
    out: dict = {}
    for value in sorted({key(r) for r in rows}):
        out[value] = summary([r for r in rows if key(r) == value])
    return out


def audit(picks: list, index: dict, source_commit: str | None, now: datetime) -> dict:
    rows = collect(picks, index)
    pre = [r for r in rows if r["timing"] == "pre"]
    market = [r for r in pre if r["price"] == "market"]
    dates = sorted(r["date"] for r in rows if r["date"])
    market_dates = sorted(r["date"] for r in market if r["date"])
    return {
        "version": VERSION,
        "generated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "reference": "Purple-Wraith/clairvoyance-backend",
        "reference_file": "docs/picks_backup.json",
        "reference_commit": source_commit,
        "period": [dates[0], dates[-1]] if dates else None,
        "as_published_all_settled": summary(rows),
        "by_lock_timing": group(rows, lambda r: r["timing"]),
        "lock_stamp_over_300_days_before_game": summary([r for r in rows if r["backfilled"]]),
        "pre_start_by_price_provenance": group(pre, lambda r: r["price"]),
        "pre_start_default_minus_110_by_family": group(
            [r for r in pre if r["price"] == "default_minus_110"], lambda r: r["family"]),
        "pre_start_market_priced_by_sport": group(market, lambda r: r["sport"]),
        "pre_start_market_priced_period": [market_dates[0], market_dates[-1]] if market_dates else None,
        "verdict": {
            "profitability_demonstrated": bool(
                market and summary(market)["roi_ci_excludes_zero"] and summary(market)["roi"] > 0),
            "reason": ("Only picks locked before kickoff AND priced at an observed market quote can "
                       "support a return claim. Default -110 or model-fair (1/p) prices are not "
                       "attainable prices; late and unknown-timing locks are not forecasts."),
        },
        "no_pick_copied": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="checkout clairvoyance-backend en lecture seule")
    parser.add_argument("--output", default="docs/clairvoyance-rentabilite-audit.json")
    args = parser.parse_args()
    source = Path(args.source)
    picks = _read(source / "docs" / "picks_backup.json")
    if not isinstance(picks, list):
        raise SystemExit("docs/picks_backup.json absent ou illisible dans " + str(source))
    try:
        commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                         text=True, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    report = audit(picks, start_index(source / "docs"), commit, datetime.now(timezone.utc))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pre = report["by_lock_timing"].get("pre") or {}
    market = report["pre_start_by_price_provenance"].get("market") or {}
    print("Publié:", report["as_published_all_settled"]["roi"], "| pré-match:", pre.get("roi"),
          "| pré-match cote marché:", market.get("roi"), market.get("roi_95ci"), "n=", market.get("n"))


if __name__ == "__main__":
    main()
