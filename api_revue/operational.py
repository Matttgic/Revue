"""Revue operations and multisport PAPER journal.

These endpoints deliberately do not use Clairvoyance's private SQL history.
They aggregate only timestamped Revue files already distributed with the site.
Health = snapshot status, not proof the original provider or website is live.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from api_revue.fixtures import SourceUnavailable, timestamp

FILES = {
    "match_center": ("match-center-latest.json", 8),
    "scanner": ("engine-v2-latest.json", 8),
    "models": ("multisports-latest.json", 8),
    "health": ("health-latest.json", 8),
    "nhl_official": ("nhl-official-stats-latest.json", 24),
    "moneypuck": ("moneypuck-nhl-latest.json", 48),
}
PAPER_STATUSES = {"pending", "won", "lost", "push", "void", "market_rule_unverified"}
GRADED = {"won", "lost", "push"}
PARIS_CUTOFF = timedelta(minutes=20)


def _load_file(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Not a JSON object")
        return data
    except (OSError, ValueError) as exc:
        raise SourceUnavailable("Revue dataset missing or malformed: " + path.name) from exc


def _positive(value: object, field: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise SourceUnavailable("Invalid paper " + field)
    return float(value)


def _iso(value: object) -> str:
    try:
        return timestamp(value).isoformat()
    except (ValueError, TypeError) as exc:
        raise SourceUnavailable("Invalid paper event timestamp") from exc


def _score(value: object) -> bool:
    return (
        isinstance(value, dict)
        and type(value.get("home")) is int and type(value.get("away")) is int
        and 0 <= value["home"] <= 500 and 0 <= value["away"] <= 500
    )


def ledger_data(root: Path) -> dict:
    data = _load_file(root / "engine-v2-ledger.json")
    if data.get("version") != 1 or not isinstance(data.get("bets"), list):
        raise SourceUnavailable("Unknown Revue paper ledger version")
    records = []
    seen = set()
    for bet in data["bets"]:
        if not isinstance(bet, dict):
            raise SourceUnavailable("Malformed paper ledger record")
        ident = bet.get("id")
        if not isinstance(ident, str) or not ident.startswith("paper-") or ident in seen:
            raise SourceUnavailable("Missing/duplicate paper ID")
        seen.add(ident)
        league = bet.get("league")
        if not isinstance(league, str) or league.upper() == "CFB" or not league:
            # CFB was excluded from the project.
            continue
        home, away = bet.get("home"), bet.get("away")
        if not isinstance(home, str) or not isinstance(away, str) or not home or not away or home == away:
            raise SourceUnavailable("Malformed paper teams")
        start = timestamp(bet.get("start_utc"))
        locked = timestamp(bet.get("locked_at"))
        quote = timestamp(bet.get("quote_at"))
        model = timestamp(bet.get("model_at"))
        price = _positive(bet.get("bookmaker_price"), "decimal odds")
        if price <= 1.0:
            raise SourceUnavailable("Odds must be above one")
        stake = _positive(bet.get("paper_stake_units"), "units")
        raw_status = bet.get("status")
        safe_chronology = (
            bet.get("chronology") == "pre_valide"
            and quote <= locked and model <= locked
            and locked <= start - PARIS_CUTOFF
        )
        market = bet.get("market")
        line = bet.get("line")
        side = bet.get("side")
        valid_market = market in {"h2h", "totals"} and (
            (market == "h2h" and side in {"home", "away", "draw"})
            or (market == "totals" and side in {"over", "under"}
                and type(line) in (int, float) and math.isfinite(line) and line > 0)
        )
        reason = None
        if not safe_chronology:
            reason = "Chronologie pré-match non vérifiée"
        elif not valid_market:
            reason = "Marché incomplet"
        elif raw_status == "market_rule_unverified":
            reason = "Règles du marché non vérifiées"
        elif raw_status not in PAPER_STATUSES:
            reason = "Statut inconnu"
        if raw_status in GRADED:
            settled = bet.get("settled_at")
            if not _score(bet.get("score")) or not isinstance(settled, str) or timestamp(settled) < start:
                reason = "Résultat non vérifiable"
            elif raw_status == "won":
                gross = bet.get("paper_units_returned")
                if type(gross) not in (int, float) or not math.isfinite(gross) or abs(gross - stake * price) > 0.011:
                    reason = "Règlement fictif incohérent"
            elif raw_status == "lost" and abs(float(bet.get("paper_units_returned", 0))) > 0.011:
                reason = "Règlement fictif incohérent"
            elif raw_status == "push" and abs(float(bet.get("paper_units_returned", stake)) - stake) > 0.011:
                reason = "Règlement fictif incohérent"
        status = "unverified" if reason else raw_status
        profit = round((stake * (price - 1) if status == "won" else -stake if status == "lost" else 0.0), 4) if status in GRADED else None
        records.append({
            "id": ident, "league": league, "event_id": str(bet.get("event_id", "")),
            "home": home, "away": away,
            "start_utc": start.isoformat(), "locked_at_utc": locked.isoformat(),
            "quote_at_utc": quote.isoformat(), "market": market, "side": side,
            "line": line if valid_market and market == "totals" else None,
            "outcome": str(bet.get("outcome") or side or ""),
            "bookmaker": str(bet.get("bookmaker") or ""),
            "decimal_odds": price, "paper_stake_units": stake,
            "status": status, "original_status": raw_status,
            "exclusion_reason": reason,
            "score": bet.get("score") if status in GRADED else None,
            "paper_profit_units": profit, "is_real_bet": False,
            "verified_pre_match": safe_chronology,
        })
    records.sort(key=lambda x: (x["locked_at_utc"], x["id"]), reverse=True)
    settled = [r for r in records if r["status"] in GRADED]
    total_units = sum(r["paper_stake_units"] for r in settled)
    profit = sum(r["paper_profit_units"] for r in settled)
    return {
        "source": "Revue independent paper ledger, NOT Clairvoyance SQL",
        "paper_only": True, "real_bets_enabled": False,
        "statistics_scope": "Only pre-start eligible and verifiably settled simulations",
        "summary": {
            "total": len(records),
            "settled": len(settled),
            "won": sum(r["status"] == "won" for r in settled),
            "lost": sum(r["status"] == "lost" for r in settled),
            "push": sum(r["status"] == "push" for r in settled),
            "pending": sum(r["status"] == "pending" for r in records),
            "excluded_or_unverified": sum(r["status"] == "unverified" for r in records),
            "paper_profit_units": round(profit, 2),
            "paper_roi_pct": round(100 * profit / total_units, 2) if total_units else None,
            "paper_wagered_units": round(total_units, 2),
        },
        "records": records,
    }


def control_status(root: Path, now: datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("Clock must be timezone-aware")
    now = now.astimezone(timezone.utc)
    sources = {}
    docs = {}
    for key, (filename, max_age) in FILES.items():
        try:
            obj = _load_file(root / filename)
            at = timestamp(obj.get("generated_at_utc"))
            age = (now - at).total_seconds() / 60
            if age < -2:
                raise ValueError("Future source timestamp")
            age = max(0.0, age)
            state = "fresh" if age <= max_age * 60 else "stale"
            sources[key] = {
                "file": filename,
                "state": state,
                "age_minutes": round(age, 1),
                "generated_at_utc": at.isoformat(),
            }
            docs[key] = obj
        except (SourceUnavailable, ValueError, KeyError, TypeError):
            sources[key] = {"file": filename, "state": "unavailable",
                            "age_minutes": None, "generated_at_utc": None}
    try:
        paper = ledger_data(root)["summary"]
        paper_status = "available"
    except SourceUnavailable:
        paper_status, paper = "unavailable", None
    if all(s["state"] == "unavailable" for s in sources.values()) and paper is None:
        raise SourceUnavailable("No verified Revue operational source")
    scanner = docs.get("scanner", {})
    match = docs.get("match_center", {})
    health = docs.get("health", {})
    return {
        "generated_at_utc": now.isoformat(),
        "source": "Revue cached GitHub snapshots, NOT original Clairvoyance status",
        "not_live_provider_health": True, "real_bets_enabled": False,
        "sources": sources,
        "fresh_sources": sum(x["state"] == "fresh" for x in sources.values()),
        "stale_sources": sum(x["state"] == "stale" for x in sources.values()),
        "match_center": {
            "snapshot_count": len(match.get("events", [])) if isinstance(match.get("events"), list) else None,
            "generated_at_utc": sources["match_center"]["generated_at_utc"],
            "not_live": True,
        },
        "odds_scanner": {
            "status": scanner.get("odds_status"),
            "candidate_count": scanner.get("candidate_count"),
            "generated_at_utc": sources["scanner"]["generated_at_utc"],
            "candidates_are_not_verified_value_bets": True,
        },
        "health_report_status": health.get("status"),
        "paper_status": paper_status,
        "paper": paper,
    }
