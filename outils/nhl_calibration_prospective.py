#!/usr/bin/env python3
"""Prospective NHL probability calibration research; never promotes betting picks.

Each model is trained only on its first 100 genuine settled, pre-kickoff locks.
An independent holdout begins *after* the final training settlement timestamp,
not at the time of the old games' kickoffs. The model and its cut-off are thus
chronologically reproducible from the immutable ledger. No synthetic outcomes,
no historical replay, no odds, no automatic deployment of calibrated prices.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import argparse
import json
import math
from pathlib import Path

from outils.nhl_point_in_time_audit import as_utc

TRAIN_MIN = 100
HOLDOUT_MIN = 40
SAMPLE_BINS = 5
REFERENCE_VERSION = "nhl_clairvoyance_moneypuck_shadow_v1"
RESEARCH_MODEL = "revue_nhl_low_sample_shrink_v1"
RIDGE = 0.1


def _valid_probability(p: object) -> bool:
    return isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) and 0 < p < 1


def _observations(events: list[dict], probability_field: str, now: datetime) -> list[dict]:
    rows = []
    for event in events:
        if event.get("status") != "settled" or event.get(probability_field) is None:
            continue
        p = event[probability_field]
        y = event.get("result")
        if not _valid_probability(p) or type(y) is not int or y not in (0, 1):
            raise ValueError("Invalid settled probability/result; refusing calibration")
        kickoff = as_utc(event["kickoff_utc"])
        locked = as_utc(event["locked_at_utc"])
        settled = as_utc(event["resolved_at_utc"])
        if not (locked <= kickoff - timedelta(minutes=20) and kickoff < settled <= now):
            raise ValueError("A settled forecast is not verifiably pre-kickoff and settled by now")
        home_goals, away_goals = event.get("home_goals"), event.get("away_goals")
        if (type(home_goals) is not int or type(away_goals) is not int or
            home_goals < 0 or away_goals < 0 or home_goals == away_goals or
            y != int(home_goals > away_goals)):
            raise ValueError("Official final goals disagree with recorded winner")
        rows.append({"id": str(event["event_id"]), "p": float(p), "y": y,
                     "kickoff": kickoff, "settled": settled})
    # Training may use outcomes only when they became available, NOT the game date.
    return sorted(rows, key=lambda r: (r["settled"], r["id"]))


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    q = math.exp(z)
    return q / (1.0 + q)


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _probability(p: float, parameters: dict) -> float:
    return max(0.000001, min(0.999999, _sigmoid(
        parameters["intercept"] + parameters["slope"] * _logit(p))))


def _loss(rows: list[dict], a: float, b: float) -> float:
    total = 0.0
    for r in rows:
        p = max(1e-12, min(1 - 1e-12, _sigmoid(a + b * _logit(r["p"]))))
        total -= r["y"] * math.log(p) + (1 - r["y"]) * math.log1p(-p)
    # Predeclared weak regularisation around the identity calibration.
    return total + RIDGE * (a * a + (b - 1) * (b - 1))


def _fit(rows: list[dict]) -> dict:
    if len(rows) < TRAIN_MIN:
        raise ValueError("Insufficient genuine outcomes for training")
    a, b = 0.0, 1.0
    for _ in range(50):
        ga, gb = 2 * RIDGE * a, 2 * RIDGE * (b - 1)
        haa, hab, hbb = 2 * RIDGE, 0.0, 2 * RIDGE
        for r in rows:
            x = _logit(r["p"])
            q = _sigmoid(a + b * x)
            w = q * (1 - q)
            e = q - r["y"]
            ga += e
            gb += e * x
            haa += w
            hab += w * x
            hbb += w * x * x
        det = haa * hbb - hab * hab
        if det <= 1e-12:
            raise ValueError("Degenerate calibration Hessian")
        da = (hbb * ga - hab * gb) / det
        db = (haa * gb - hab * ga) / det
        before = _loss(rows, a, b)
        step = 1.0
        accepted = False
        while step >= 1 / 1024:
            na = max(-3.0, min(3.0, a - step * da))
            nb = max(0.0, min(3.0, b - step * db))
            if _loss(rows, na, nb) <= before + 1e-10:
                accepted = True
                a, b = na, nb
                break
            step /= 2
        if not accepted or abs(step * da) + abs(step * db) < 1e-8:
            break
    return {"intercept": round(a, 8), "slope": round(b, 8),
            "regularization": RIDGE, "transform": "sigmoid(intercept + slope * logit(p))"}


def _brier(rows: list[dict], parameters: dict | None = None) -> float | None:
    if not rows:
        return None
    return round(sum(((_probability(r["p"], parameters) if parameters else r["p"]) - r["y"])**2
                     for r in rows) / len(rows), 6)


def _logloss(rows: list[dict], parameters: dict | None = None) -> float | None:
    if not rows:
        return None
    total = 0.0
    for row in rows:
        p = _probability(row["p"], parameters) if parameters else row["p"]
        total -= math.log(p if row["y"] else 1.0 - p)
    return round(total / len(rows), 6)


def _reliability(rows: list[dict]) -> list[dict]:
    buckets = [[] for _ in range(SAMPLE_BINS)]
    for row in rows:
        buckets[min(SAMPLE_BINS - 1, int(row["p"] * SAMPLE_BINS))].append(row)
    return [
        {"from": round(i / SAMPLE_BINS, 2), "to": round((i + 1) / SAMPLE_BINS, 2),
         "count": len(group),
         "predicted_mean": round(sum(r["p"] for r in group) / len(group), 4) if group else None,
         "observed_rate": round(sum(r["y"] for r in group) / len(group), 4) if group else None}
        for i, group in enumerate(buckets)
    ]


def _study(rows: list[dict], name: str) -> dict:
    n = len(rows)
    train = rows[:TRAIN_MIN]
    result = {
        "model": name,
        "settled_samples": n,
        "training_required": TRAIN_MIN,
        "holdout_required": HOLDOUT_MIN,
        "training_remaining": max(0, TRAIN_MIN - n),
        "raw_brier": _brier(rows),
        "raw_logloss": _logloss(rows),
        "reliability_bins": _reliability(rows),
        "calibration_status": "insufficient_training" if n < TRAIN_MIN else "awaiting_future_holdout",
        "parameters": None,
        "training_cutoff_utc": None,
        "training_samples": 0,
        "holdout_samples": 0,
        "holdout_metrics": None,
        "approved_for_betting": False,
    }
    if n < TRAIN_MIN:
        return result
    # The candidate is trained at the instant its 100th outcome became known.
    # Exclude all holdout kickoffs before that time, even if settled later.
    cutoff = train[-1]["settled"]
    held = [r for r in rows[TRAIN_MIN:] if r["kickoff"] > cutoff]
    parameters = _fit(train)
    result.update({
        "parameters": parameters, "training_cutoff_utc": cutoff.isoformat(),
        "training_samples": len(train), "holdout_samples": len(held),
    })
    if len(held) < HOLDOUT_MIN:
        result["holdout_remaining"] = HOLDOUT_MIN - len(held)
        return result
    raw_brier = _brier(held)
    adjusted_brier = _brier(held, parameters)
    raw_logloss = _logloss(held)
    adjusted_logloss = _logloss(held, parameters)
    base_rate = sum(r["y"] for r in train) / len(train)
    baseline_brier = round(sum((base_rate - r["y"])**2 for r in held) / len(held), 6)
    result["holdout_metrics"] = {
        "raw_brier": raw_brier, "calibrated_brier": adjusted_brier,
        "raw_logloss": raw_logloss, "calibrated_logloss": adjusted_logloss,
        "train_only_base_rate": round(base_rate, 6),
        "train_only_baseline_brier": baseline_brier,
        "brier_improvement": round(raw_brier - adjusted_brier, 6),
        "logloss_improvement": round(raw_logloss - adjusted_logloss, 6),
    }
    result["calibration_status"] = (
        "experimental_holdout_better" if adjusted_brier < min(raw_brier, baseline_brier)
        and adjusted_logloss < raw_logloss else "experimental_holdout_not_better"
    )
    return result


def build_report(ledger: dict, now: datetime) -> dict:
    if ledger.get("version") != REFERENCE_VERSION or not isinstance(ledger.get("events"), list):
        raise ValueError("Unknown or malformed NHL ledger")
    if now.tzinfo is None:
        raise ValueError("UTC-aware calculation timestamp required")
    events = ledger["events"]
    ids = [str(r["event_id"]) for r in events]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate NHL ledger event ID")
    studies = {
        "clairvoyance_formula": _study(_observations(events, "home_win_probability", now), "clairvoyance_formula"),
        "revue_prudent": _study(_observations(events, "research_home_win_probability", now), RESEARCH_MODEL),
    }
    return {
        "generated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "status": "prospective_research_only",
        "data_source": "docs/nhl-shadow-ledger.json (locked forecasts + official settled results)",
        "outcomes_are_real": True,
        "no_synthetic_training": True,
        "auto_promotion": False,
        "real_bets_enabled": False,
        "sportsbook_roi": None,
        "protocol": {
            "train_first_settled": TRAIN_MIN,
            "holdout_new_kickoffs_after_training": HOLDOUT_MIN,
            "calibration": "ridge-logistic on pre-match log-odds",
            "training_order": "first 100 outcomes sorted by official resolution timestamp",
            "holdout_start": "strictly after last training result became available",
            "reliability_bins": SAMPLE_BINS,
            "no_historical_replay": True,
            "note": "Exploratory diagnostic, not a deployable calibrator or statistical proof. Fixed validation rules; no automatic model selection.",
        },
        "models": studies,
    }


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--ledger", default="docs/nhl-shadow-ledger.json")
    cli.add_argument("--output", default="docs/nhl-calibration-latest.json")
    args = cli.parse_args()
    data = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    report = build_report(data, datetime.now(timezone.utc))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Prospective NHL calibration: "+
          ", ".join(f"{k}={v['settled_samples']} settled ({v['calibration_status']})"
                    for k, v in report["models"].items()))


if __name__ == "__main__":
    main()
