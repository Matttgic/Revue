#!/usr/bin/env python3
"""Independent, verified ESPN final-score settlement for existing PAPER bets.

Uses Revue's timestamped, observed public scoreboard, never reverse-engineers
a result or retroactively creates a bet. NHL remains with its original
NHL-specific shootout/OT-aware settlement implementation.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import argparse
import json
from pathlib import Path

from outils.revue_engine_v2 import (
    _outcome_from_score, ledger_statistics, same_team, timestamp,
    verified_pre_match,
)

MAX_SCOREBOARD_AGE = timedelta(hours=6)
KICKOFF_TOLERANCE = timedelta(minutes=10)
SCORE_MIN_LAG = timedelta(minutes=55)
# These domestic soccer markets are scheduled 90-minute outcomes, while their
# competition round is not necessarily explicitly verified in the scoreboard.
# Avoid cup/knockout markets entirely, even if ESPN says "final".
SUPPORTED = {
    "NBA", "WNBA", "NCAAB", "NFL", "MLB",
    "PL", "LALIGA", "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS",
}
SOCCER = {"PL", "LALIGA", "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS"}


def _aware(value: object) -> datetime | None:
    result = timestamp(value)
    if result is None or result.tzinfo is None:
        return None
    return result.astimezone(timezone.utc)


def official_index(scoreboard: dict, now: datetime) -> tuple[dict, dict]:
    if now.tzinfo is None:
        raise ValueError("Timezone-aware clock required")
    now = now.astimezone(timezone.utc)
    stamp = _aware(scoreboard.get("generated_at_utc"))
    if (scoreboard.get("status") != "observed_scoreboard_not_streaming"
        or scoreboard.get("scores_are_live_stream") is not False
        or scoreboard.get("pricing_used") is not False
        or stamp is None or stamp > now + timedelta(minutes=2)
        or now - stamp > MAX_SCOREBOARD_AGE
        or not isinstance(scoreboard.get("events"), list)):
        raise ValueError("Scoreboard provenance is not recent and verified")
    by_key, skipped = {}, Counter()
    for r in scoreboard["events"]:
        if not isinstance(r, dict):
            skipped["invalid_row"] += 1
            continue
        league = r.get("league")
        if league not in SUPPORTED:
            skipped["unsupported_league"] += 1
            continue
        if r.get("state") != "final" or r.get("source") != "ESPN scoreboard":
            skipped["not_verified_final"] += 1
            continue
        observed = _aware(r.get("observed_at_utc"))
        kickoff = _aware(r.get("kickoff_utc"))
        hs, aws = r.get("home_score"), r.get("away_score")
        if (not observed or not kickoff or
            observed > stamp + timedelta(minutes=2) or observed > now or
            observed < kickoff + SCORE_MIN_LAG or
            isinstance(hs, bool) or isinstance(aws, bool) or
            not isinstance(hs, int) or not isinstance(aws, int) or
            not (0 <= hs <= 300 and 0 <= aws <= 300) or
            not isinstance(r.get("home"), str) or
            not isinstance(r.get("away"), str) or
            not r["home"].strip() or not r["away"].strip() or
            r["home"] == r["away"] or
            not str(r.get("event_id") or "").isdigit()):
            skipped["invalid_or_ambiguous_final"] += 1
            continue
        if league not in SOCCER and hs == aws:
            skipped["non_soccer_draw_not_settleable"] += 1
            continue
        key = (league, str(r["event_id"]))
        if key in by_key:
            # A key present twice is ambiguous even if one was a stale copy.
            by_key[key] = None
            skipped["duplicate_official_result"] += 1
        else:
            by_key[key] = r
    return by_key, dict(skipped)


def grade_existing(ledger: dict, scoreboard: dict, now: datetime) -> tuple[dict, dict]:
    """Only mutate untouched pending locks and only if all provenance gates pass."""
    if now.tzinfo is None:
        raise ValueError("Timezone-aware UTC clock required")
    if ledger.get("version") != 1 or not isinstance(ledger.get("bets"), list):
        raise ValueError("Unknown immutable paper ledger")
    indexed, rejected = official_index(scoreboard, now)
    out = deepcopy(ledger)
    checked = 0
    applied = 0
    seen = set()
    for bet in out["bets"]:
        if bet.get("status") != "pending":
            continue
        checked += 1
        league = bet.get("league")
        key = (league, str(bet.get("event_id") or ""))
        if (league not in SUPPORTED or not verified_pre_match(bet)
            or bet.get("market_rule_verified") is not True
            or not key[1].isdigit() or key in seen):
            rejected["excluded_or_unverified_bet"] = rejected.get("excluded_or_unverified_bet", 0) + 1
            continue
        seen.add(key)
        result = indexed.get(key)
        if result is None:
            rejected["no_matching_observed_final"] = rejected.get("no_matching_observed_final", 0) + 1
            continue
        start = _aware(bet.get("start_utc"))
        real_start = _aware(result.get("kickoff_utc"))
        if (start is None or real_start is None or
            abs(start-real_start) > KICKOFF_TOLERANCE or
            not same_team(bet.get("home", ""), result["home"], league) or
            not same_team(bet.get("away", ""), result["away"], league)):
            rejected["fixture_mismatch"] = rejected.get("fixture_mismatch", 0) + 1
            continue
        hs,aws = result["home_score"],result["away_score"]
        # A drawn soccer fixture is a 90-min three-way market.
        if league in SOCCER and bet["market"]=="h2h" and bet["side"] not in ("home","away","draw"):
            rejected["market_rule_invalid"] = rejected.get("market_rule_invalid", 0) + 1
            continue
        if bet["market"]=="totals" and (not isinstance(bet.get("line"), (int,float)) or
                                       isinstance(bet["line"],bool)):
            rejected["totals_line_invalid"] = rejected.get("totals_line_invalid", 0) + 1
            continue
        result_code = _outcome_from_score(bet, float(hs), float(aws))
        if result_code not in ("won","lost","push"):
            rejected["ungradeable_market"] = rejected.get("ungradeable_market", 0) + 1
            continue
        stake = bet.get("paper_stake_units")
        odds = bet.get("bookmaker_price")
        if (isinstance(stake, bool) or isinstance(odds, bool)
            or not isinstance(stake, (int,float)) or not 0 < stake <= 100000
            or not isinstance(odds, (int,float)) or not 1 < odds <= 1000):
            rejected["invalid_stake_or_quote"] = rejected.get("invalid_stake_or_quote",0)+1
            continue
        bet["status"] = result_code
        bet["settled_at"] = now.isoformat()
        bet["score"] = {"home":hs, "away":aws}
        bet["paper_units_returned"] = stake*(odds if result_code=="won" else 1 if result_code=="push" else 0)
        bet["settlement_source"] = "ESPN observed final, league and fixture identity verified"
        bet["score_observed_at_utc"] = result["observed_at_utc"]
        applied += 1
    stats = ledger_statistics(out)
    return out, {
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "status":"verified_paper_scoreboard_settlement_only",
        "scoreboard_snapshot_utc":scoreboard["generated_at_utc"],
        "eligible_leagues":sorted(SUPPORTED),
        "nhl_special_market_settlement":"existing_nhl_engine_only",
        "pending_reviewed":checked,"newly_settled":applied,
        "unchanged_paper_records":len(out["bets"])-applied,
        "settled_total":stats["graded_pre_start"],
        "paper_profit_units":stats["paper_profit_units"],
        "paper_roi_pct":stats["paper_roi_pct"],
        "rejected":rejected,
        "no_bets_created":True,
        "no_predictions_rewritten":True,
        "no_live_bookmaker_quotes":True,
        "note":"Officially observed final-score settlements only. Legacy unverified market rules, unknown match identity and NHL shootout accounting are not settled.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args = parser.parse_args()
    root=Path(args.docs)
    raw=json.loads((root/"engine-v2-ledger.json").read_text(encoding="utf-8"))
    scoreboard=json.loads((root/"scoreboard-revue-latest.json").read_text(encoding="utf-8"))
    updated,report=grade_existing(raw,scoreboard,datetime.now(timezone.utc))
    (root/"paper-score-settlement-latest.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
        encoding="utf-8")
    if updated!=raw:
        (root/"engine-v2-ledger.json").write_text(
            json.dumps(updated,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
            encoding="utf-8")
    print("Observed ESPN paper-only settlement:",report["newly_settled"],
          "new, total",report["settled_total"],
          "strictly preserving earlier locked predictions.")


if __name__=="__main__":
    main()
