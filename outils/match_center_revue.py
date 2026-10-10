#!/usr/bin/env python3
"""Build an ORIGINAL read-only multisport match center from Revue's own feeds.

Do not copy Clairvoyance picks/data. Join on exact league + provider fixture ID,
verify teams and scheduled UTC kickoff, never infer bookmaker prices, winners or
EV from incomplete settlement rules or uncalibrated research forecasts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
HORIZON = timedelta(hours=72)
MAX_ODDS_AGE = timedelta(hours=24)
MAX_SOURCE_AGE = timedelta(hours=72)


def instant(s: object) -> datetime:
    if not isinstance(s, str):
        raise ValueError("Horodatage absent")
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Horodatage sans fuseau")
    return d.astimezone(timezone.utc)


def probability(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 1)


def game_key(league: object, event_id: object) -> str:
    return str(league).upper() + ":" + str(event_id)


def signature(home: str, away: str, start_utc: str) -> tuple:
    return (home.strip().casefold(), away.strip().casefold(), instant(start_utc))


def compatible(base: dict, incoming: dict) -> bool:
    try:
        return signature(base["home"], base["away"], base["start_utc"]) == signature(
            incoming["home"], incoming["away"], incoming["start_utc"])
    except (ValueError, KeyError, AttributeError, TypeError):
        return False


def valid_predictions(p: object) -> dict | None:
    if not isinstance(p, dict) or not p:
        return None
    fields = ("home_win_90", "draw_90", "away_win_90") if "draw_90" in p else ("home_win", "away_win")
    if not all(probability(p.get(k)) for k in fields):
        return None
    if abs(sum(p[k] for k in fields) - 1) > .025:
        return None
    result = {k: round(float(p[k]), 6) for k in fields}
    for k, v in p.items():
        if k not in fields and probability(v):
            result[k] = round(float(v), 6)
    return result


def model_snapshot(doc: dict, now: datetime, kickoff: datetime) -> bool:
    try:
        generated = instant(doc["generated_at_utc"])
        return generated <= now and generated < kickoff and now-generated <= MAX_SOURCE_AGE
    except (KeyError, ValueError, TypeError):
        return False


def collect_center(multisports: dict, scanner: dict, advanced: dict,
                   nhl: dict, ensemble: dict, now: datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("now timezone required")
    now = now.astimezone(timezone.utc)
    events: dict[str, dict] = {}
    rejected = {"source_future_or_stale": 0, "fixture_mismatch": 0, "odds_invalid_or_stale": 0}
    if not isinstance(multisports.get("competitions"), dict):
        raise ValueError("No Revue fixtures")
    if not model_snapshot(multisports, now, now+HORIZON+timedelta(seconds=1)):
        raise ValueError("Main fixture feed out of date or future dated")

    # Fixture inventory is authoritative for each bookmaker/model attachment.
    for league, competition in multisports["competitions"].items():
        if league == "CFB":
            continue
        for raw in competition.get("games") or []:
            try:
                start = instant(raw["start_utc"])
                if not now < start <= now+HORIZON:
                    continue
                key = game_key(league, raw["event_id"])
                if key in events:
                    raise ValueError(f"Duplicate event in fixture inventory: {key}")
                team_home, team_away = raw["home"], raw["away"]
                if not team_home or not team_away or team_home == team_away:
                    continue
                obs = {
                    "key": key, "league": str(league), "sport": competition.get("sport") or league,
                    "event_id": str(raw["event_id"]), "home": team_home, "away": team_away,
                    "start_utc": start.isoformat(),
                    "start_paris": start.astimezone(PARIS).isoformat(),
                    "local_day": start.astimezone(PARIS).date().isoformat(),
                    "research": [], "quotes": [], "market_status": "no_verified_quote",
                    "status": "upcoming",
                }
                p = valid_predictions(raw.get("probabilities"))
                if p and model_snapshot(multisports, now, start):
                    obs["research"].append({
                        "id":"revue_multisports_score_model",
                        "label":"Revue multisports",
                        "probabilities":p,
                        "calibrated":False,
                        "source_generated_utc":multisports["generated_at_utc"],
                    })
                obs["model_status"] = raw.get("status", "unknown")
                events[key] = obs
            except (KeyError, ValueError, TypeError):
                rejected["fixture_mismatch"] += 1
                continue

    def add_model(raw: dict, league: str, report: dict, model_id: str,
                  label: str, p: dict | None) -> None:
        key = game_key(league, raw.get("event_id"))
        row = events.get(key)
        if row is None:
            return
        if not compatible(row, raw):
            rejected["fixture_mismatch"] += 1
            return
        if not model_snapshot(report, now, instant(row["start_utc"])):
            rejected["source_future_or_stale"] += 1
            return
        valid = valid_predictions(p)
        if valid is None:
            return
        if any(item["id"] == model_id for item in row["research"]):
            return
        row["research"].append({
            "id": model_id, "label": label, "probabilities": valid,
            "calibrated":False, "source_generated_utc":report["generated_at_utc"],
        })

    for league, group in (advanced.get("competitions") or {}).items():
        for g in group.get("games") or []:
            add_model(g, league, advanced, "football_espn_advanced_shadow",
                      "Football avancé ESPN", g.get("probabilities"))

    for g in nhl.get("games") or []:
        # Clairvoyance input audit must have passed; this is not a real-pick feed.
        if (nhl.get("point_in_time_audit") or {}).get("status") != "verified_temporal_bounds":
            continue
        add_model(g, "NHL", nhl, "clairvoyance_nhl_formula_revue_inputs",
                  "Clairvoyance / formule NHL", {"home_win":g.get("home_win"),"away_win":g.get("away_win")})
        variant = g.get("research_low_sample_shrink") or {}
        if variant.get("model_id") == "revue_nhl_low_sample_shrink_v1":
            add_model(g, "NHL", nhl, "revue_nhl_low_sample_shrink_v1",
                      "Revue NHL prudent", {"home_win":variant.get("home_win"),"away_win":variant.get("away_win")})

    for league, group in (ensemble.get("leagues") or {}).items():
        for g in group.get("games") or []:
            add_model(g, league, ensemble, "revue_ensemble_mc_bayes_elo",
                      "Revue Monte-Carlo / Bayes / Elo", g.get("probabilities"))

    scanner_report = scanner.get("odds_board") or {}
    if scanner.get("mode") == "PAPER_ONLY":
        for fixture in scanner_report.get("events") or []:
            league = str(fixture.get("league", "")).upper()
            if league == "CFB":
                continue
            row = events.get(game_key(league, fixture.get("event_id")))
            if row is None:
                continue
            if not compatible(row, fixture):
                rejected["fixture_mismatch"] += 1
                continue
            kickoff = instant(row["start_utc"])
            for book in fixture.get("bookmakers") or []:
                b = book.get("bookmaker")
                if not isinstance(b, str) or not b.endswith("_fr"):
                    continue
                for market in book.get("markets") or []:
                    if market.get("market") != "h2h":
                        continue
                    try:
                        quote_at = instant(market["quote_at"])
                    except (KeyError, TypeError, ValueError):
                        rejected["odds_invalid_or_stale"] += 1
                        continue
                    if not (now-MAX_ODDS_AGE <= quote_at <= now and quote_at < kickoff):
                        rejected["odds_invalid_or_stale"] += 1
                        continue
                    rule = market.get("period_rule")
                    expected = ("home", "draw", "away") if league in (
                        "PL", "LALIGA", "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS", "UCL") else ("home", "away")
                    if rule not in ("90min", "game_result", "overtime_rule_unverified"):
                        continue
                    if expected == ("home", "draw", "away") and rule != "90min":
                        continue
                    by_selection = {}
                    for o in market.get("outcomes") or []:
                        name, price = o.get("selection"), o.get("price")
                        if (name in expected and isinstance(price, (int, float))
                                and not isinstance(price, bool) and math.isfinite(price)
                                and 1 < price <= 10000):
                            by_selection[name] = round(float(price), 3)
                    if set(by_selection) != set(expected):
                        rejected["odds_invalid_or_stale"] += 1
                        continue
                    row["quotes"].append({
                        "bookmaker":b, "market":"h2h", "rule":rule,
                        "quote_at_utc":quote_at.isoformat(), "outcomes":by_selection,
                        "rule_verified":rule in ("90min", "game_result"),
                    })
            row["quotes"].sort(key=lambda x:(x["bookmaker"],x["quote_at_utc"]))
            if row["quotes"]:
                row["market_status"] = "observed_price_not_live"

    output = sorted(events.values(), key=lambda r:(r["start_utc"],r["league"],r["event_id"]))
    for row in output:
        row["recommendation"] = None
        row["ev"] = None
        row["qualified_for_real_betting"] = False
        row["research"].sort(key=lambda r:r["id"])
    leagues = sorted({e["league"] for e in output})
    return {
        "generated_at_utc": now.isoformat(),
        "status":"experimental_revue_match_center",
        "source":"Revue first-party independently generated fixture/model/quote snapshots",
        "timezone":"Europe/Paris", "horizon_hours": int(HORIZON.total_seconds()/3600),
        "live_scores":False, "bookmaker_prices_are_live":False,
        "validated_value_bets":0, "real_bets_enabled":False,
        "metrics":{
            "upcoming_matches":len(output),
            "with_observed_bookmaker_quotes":sum(bool(e["quotes"]) for e in output),
            "with_research_model":sum(bool(e["research"]) for e in output),
            "leagues":len(leagues),
        },
        "leagues":leagues, "events":output, "rejections":rejected,
        "note":"All research probabilities uncalibrated. Market prices are historic observations, not live/bookable. NHL OT rules may be unverified. Do not compute EV, recommend bets or claim profitability.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",default="docs")
    p.add_argument("--output",default="docs/match-center-latest.json")
    args=p.parse_args()
    root=Path(args.input)
    mapping={
        "multisports":"multisports-latest.json",
        "scanner":"engine-v2-latest.json",
        "advanced":"football-advanced-shadow.json",
        "nhl":"nhl-clairvoyance-shadow-latest.json",
        "ensemble":"ensemble-mc-bayes-latest.json",
    }
    data={k:json.loads((root/v).read_text(encoding="utf-8")) for k,v in mapping.items()}
    result=collect_center(**data,now=datetime.now(timezone.utc))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Revue Match Center:",result["metrics"])


if __name__=="__main__":
    main()
