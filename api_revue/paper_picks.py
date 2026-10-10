"""Read-only source-shaped pick endpoints backed by Revue PAPER records.

No real wagers are placed. The original Clairvoyance SQL IDs, American prices
and wager history are not available. Never use this adapter to claim exact
end-to-end equivalence with that database.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import json
import math
import re

from api_revue.fixtures import SourceUnavailable

VALID_STATUS = {"pending", "won", "lost", "push", "void"}
VALID_SPORT = {"NHL", "MLB"}
PAPER_ID = re.compile(r"^paper-([0-9]{6,})$")


def _dt(value: object) -> datetime:
    try:
        if not isinstance(value, str):
            raise ValueError("not a date")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone missing")
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError) as exc:
        raise SourceUnavailable("Invalid paper ledger timestamp") from exc


def _price_to_american(value: object) -> int:
    """Faithful American quote type, but NOT the original bookmaker's price.

    The source pick schema has integer American prices. The Revue paper book
    uses decimal prices; converting and rounding can cause slight deviations.
    """
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d <= Decimal("1.01"):
            raise ValueError("invalid decimal quote")
        return int((d - 1) * 100 + Decimal("0.5")) if d >= 2 else -int(
            100 / (d - 1) + Decimal("0.5")
        )
    except (InvalidOperation, ValueError, TypeError, ZeroDivisionError) as exc:
        raise SourceUnavailable("Invalid paper ledger odds") from exc


def paper_picks(directory: Path) -> list[dict]:
    path = directory / "engine-v2-ledger.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SourceUnavailable("Verified Revue paper pick ledger unavailable") from exc
    if doc.get("version") != 1 or not isinstance(doc.get("bets"), list):
        raise SourceUnavailable("Unsupported paper pick ledger format")

    # NHL IDs are NOT ESPN IDs. Expose an ESPN ID only if a separately verified
    # game-ID mapping has the matching teams and kickoff.
    mapping = {}
    try:
        id_doc = json.loads((directory / "parite-nhl-espn-id-map.json").read_text(encoding="utf-8"))
        if id_doc.get("status") == "verified_fixture_identity_pairs":
            for m in id_doc.get("mappings", []):
                key = str(m.get("nhl_game_id"))
                if key in mapping:
                    raise SourceUnavailable("Duplicate NHL/ESPN identity mapping")
                mapping[key] = m
    except (OSError, ValueError):
        pass

    rows = []
    seen = set()
    for bet in doc["bets"]:
        if not isinstance(bet, dict):
            raise SourceUnavailable("Malformed Revue paper pick")
        # Source supports NHL/MLB only. Unverified market rules and uncertain
        # chronology are NOT equivalent to pending/won/lost picks.
        if bet.get("league") not in VALID_SPORT or bet.get("status") not in VALID_STATUS:
            continue
        if bet.get("chronology") != "pre_valide":
            continue
        match = PAPER_ID.fullmatch(str(bet.get("id", "")))
        if not match:
            raise SourceUnavailable("Missing stable paper pick identifier")
        ident = int(match.group(1))
        if ident in seen:
            raise SourceUnavailable("Duplicate paper pick identifier")
        seen.add(ident)

        start = _dt(bet.get("start_utc"))
        locked = _dt(bet.get("locked_at"))
        quote = _dt(bet.get("quote_at"))
        if locked > start - timedelta(minutes=20) or quote > locked:
            # This is not a provable pregame quote; fail closed.
            continue
        market, side = bet.get("market"), bet.get("side")
        if market == "h2h" and side in {"home", "away"}:
            bet_type, selection, line = "moneyline", bet.get(side), None
        elif market == "totals" and side in {"over", "under"}:
            bet_type, selection, line = side, side, bet.get("line")
            if type(line) not in (int, float) or not math.isfinite(line) or line <= 0:
                raise SourceUnavailable("Invalid paper totals line")
        else:
            continue
        if not isinstance(selection, str) or not selection.strip():
            raise SourceUnavailable("Invalid paper pick selection")
        try:
            stake = float(bet["paper_stake_units"])
            if not math.isfinite(stake) or stake <= 0:
                raise ValueError("invalid stake")
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceUnavailable("Invalid paper stake") from exc
        odds = _price_to_american(bet.get("bookmaker_price"))
        home, away = bet.get("home"), bet.get("away")
        if not isinstance(home, str) or not isinstance(away, str) or not home or not away:
            raise SourceUnavailable("Invalid paper game teams")
        sport = bet["league"].lower()
        event_id = str(bet.get("event_id", ""))
        espn_id = event_id if sport == "mlb" and event_id.isdecimal() else None
        if sport == "nhl" and event_id in mapping:
            mp = mapping[event_id]
            try:
                if (mp.get("home") == home and mp.get("away") == away
                    and _dt(mp.get("start_utc")) == start
                    and str(mp.get("original_espn_id", "")).isdecimal()):
                    espn_id = str(mp["original_espn_id"])
            except SourceUnavailable:
                pass
        score = bet.get("score") if bet["status"] in {"won", "lost", "push"} else None
        settled_at = _dt(bet.get("settled_at")).isoformat() if score is not None else None
        row = {
            "id": ident, "sport": sport, "espn_game_id": espn_id,
            "game_date": start.date().isoformat(), "bet_type": bet_type,
            "selection": selection, "odds": odds, "amount": stake,
            "over_under": line, "status": bet["status"],
            "home_team": home, "away_team": away,
            "home_score": score.get("home") if isinstance(score, dict) else None,
            "away_score": score.get("away") if isinstance(score, dict) else None,
            "notes": "SIMULATION REVUE uniquement (unités fictives); odds US converties depuis décimales, ID SQL original inconnu",
            "settled_at": settled_at, "created_at": locked.isoformat(),
        }
        rows.append(row)
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows


def paper_pick_stats(rows: list[dict], *, sport: str | None = None,
                     bet_type: str | None = None) -> dict:
    """Original stats response FIELD SHAPE and US-odds payout maths.

    Not original Clairvoyance picks or financial P&L. Every monetary value
    here denotes non-cash paper units.
    """
    decided = [p for p in rows
               if p["status"] in {"won", "lost", "push"}
               and (sport is None or p["sport"] == sport.lower())
               and (bet_type is None or p["bet_type"] == bet_type.lower())]

    def payout(p: dict) -> float:
        if p["status"] == "push":
            return 0.0
        if p["status"] == "lost":
            return -p["amount"]
        odds = p["odds"]
        return p["amount"] * (odds / 100 if odds >= 0 else 100 / abs(odds))

    def calculate(items: list[dict]) -> dict:
        won = sum(p["status"] == "won" for p in items)
        lost = sum(p["status"] == "lost" for p in items)
        push = sum(p["status"] == "push" for p in items)
        wagered = sum(p["amount"] for p in items)
        profit = sum(payout(p) for p in items)
        return {
            "won": won, "lost": lost, "push": push,
            "win_rate": round(won / (won + lost) * 100, 1) if won + lost else None,
            "pnl": round(profit, 2),
            "roi": round(profit / wagered * 100, 1) if wagered else None,
        }

    summary = calculate(decided)
    wagered = sum(p["amount"] for p in decided)
    summary["roi"] = summary["roi"] if summary["roi"] is not None else 0.0
    summary["total_wagered"] = round(wagered, 2)
    by_sport, by_bet_type = {}, {}
    for field, group in (("sport", by_sport), ("bet_type", by_bet_type)):
        for name in sorted({p[field] for p in decided}):
            group[name] = calculate([p for p in decided if p[field] == name])
    return {"summary": summary, "by_sport": by_sport, "by_bet_type": by_bet_type}
