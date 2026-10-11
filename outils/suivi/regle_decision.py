#!/usr/bin/env python3
"""Règle de décision pré-enregistrée pour le journal de paris papier de Revue.

Écrite le 2026-10-11, AVANT d'avoir assez de résultats pour être tenté de
l'ajuster. Elle répond à une seule question : le journal papier
(docs/engine-v2-ledger.json, cotes françaises réellement observées, paris
figés avant le coup d'envoi) montre-t-il un avantage réel ?

Verdicts possibles :
- « insuffisant »  : moins de MIN_SETTLED paris réglés éligibles ;
- « abandon »      : au moins MIN_FOR_STOP paris et ROI négatif même en haut
                     de son intervalle de confiance à 95 % ;
- « prometteur »   : les QUATRE critères sont remplis ;
- « non concluant »: sinon.

v2 (2026-10-11) : la sélection des paris passe du modèle Revue à la
référence sharp (stratégie « sharp_ev_v1 » : cote française meilleure que
PS3838/Pinnacle sans marge, d'au moins 3 %). Adoptée avant tout résultat de
cette stratégie ; seuls ses paris comptent, les précédents sont archivés à part.

Toute modification de RULE = nouvelle version (RULE["version"]) ; le test
tests/test_regle_decision.py échoue si les seuils changent sans cela.
Les ventilations par ligue/marché sont exploratoires : choisir après coup le
segment qui « marche » est exactement le biais que cette règle interdit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from outils.suivi.historique_cotes_clv import closing_sample

RULE = {
    "version": "revue_decision_rule_v2",
    "adopted_on": "2026-10-11",
    "selection_rule": "sharp_ev_v1",  # seuls les paris de cette stratégie comptent
    "min_settled": 300,          # C1 volume
    "min_for_stop": 100,         # seuil minimal pour conclure à l'abandon
    "z": 1.96,                   # intervalles de confiance à 95 %
    "min_clv_samples": 150,      # C3 : nombre de cotes de clôture observées
}

CRITERIA = (
    ("volume", "Au moins 300 paris pré-match réglés à cote réellement observée"),
    ("roi", "ROI positif même en bas de son intervalle de confiance à 95 %"),
    ("clv", "Cote prise meilleure que la cote de clôture (CLV > 0, IC 95 %) sur au moins 150 paris"),
    ("calibration", "Probabilité de référence (PS3838/Pinnacle sans marge) plus juste que le marché français (Brier plus bas) sur les mêmes paris"),
)


def _time(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else None


def _num(value):
    if isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def eligible(bet: dict) -> str | None:
    """None si le pari compte ; sinon le motif d'exclusion."""
    if bet.get("selection_rule") != RULE["selection_rule"]:
        return "autre_strategie"
    return eligible_any_strategy(bet)


def eligible_any_strategy(bet: dict) -> str | None:
    """Contrôles d'intégrité communs, quelle que soit la stratégie de sélection."""
    if bet.get("status") not in ("won", "lost", "push"):
        return "non_regle"
    if bet.get("chronology") != "pre_valide":
        return "chronologie_non_validee"
    start, locked, quote = (_time(bet.get(k)) for k in ("start_utc", "locked_at", "quote_at"))
    if not start or not locked or not quote or not (quote <= locked < start):
        return "horodatage_invalide"
    if bet.get("market_rule_verified") is False or (
            bet.get("league") == "NHL" and bet.get("market_rule_verified") is not True):
        return "regle_de_marche_non_verifiee"
    price, stake = _num(bet.get("bookmaker_price")), _num(bet.get("paper_stake_units"))
    if price is None or not 1 < price <= 1000 or stake is None or stake <= 0:
        return "cote_ou_mise_invalide"
    if bet.get("status") != "push" and not bet.get("score"):
        return "resultat_sans_score"
    return None


def profit(bet: dict) -> float:
    stake, price = float(bet["paper_stake_units"]), float(bet["bookmaker_price"])
    return stake * (price - 1) if bet["status"] == "won" else -stake if bet["status"] == "lost" else 0.0


def mean_ci(values: list[float], z: float) -> dict | None:
    n = len(values)
    if n == 0:
        return None
    mean = sum(values) / n
    if n < 2:
        return {"n": n, "mean": round(mean, 4), "ci95": None}
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    half = z * sd / math.sqrt(n)
    return {"n": n, "mean": round(mean, 4), "ci95": [round(mean - half, 4), round(mean + half, 4)]}


def market_probability(bet: dict) -> float | None:
    """Probabilité du marché : consensus sans marge si observé, sinon 1/cote."""
    p = _num(bet.get("p_peer_books_no_vig"))
    if p is not None and 0 < p < 1:
        return p
    return 1 / float(bet["bookmaker_price"])


def brier_comparison(bets: list[dict]) -> dict:
    model, market = [], []
    for b in bets:
        if b["status"] == "push":
            continue
        p = _num(b.get("p_sharp_no_vig"))
        if p is None or not 0 < p < 1:
            continue
        y = 1.0 if b["status"] == "won" else 0.0
        model.append((p - y) ** 2)
        market.append((market_probability(b) - y) ** 2)
    n = len(model)
    if not n:
        return {"n": 0, "brier_reference": None, "brier_market": None, "difference": None}
    diff = mean_ci([a - b for a, b in zip(model, market)], RULE["z"])
    return {"n": n, "brier_reference": round(sum(model) / n, 4), "brier_market": round(sum(market) / n, 4),
            "difference": diff}


def cumulative(bets: list[dict]) -> list[dict]:
    rows, total = [], 0.0
    for b in sorted(bets, key=lambda x: (str(x.get("settled_at") or x.get("start_utc")), str(x.get("id")))):
        total += profit(b)
        rows.append({"date": str(b.get("start_utc"))[:10], "units": round(total, 3)})
    return rows


def segments(bets: list[dict], key) -> dict:
    out: dict = {}
    for b in bets:
        out.setdefault(key(b), []).append(b)
    return {k: {"n": len(v), "units": round(sum(profit(b) for b in v), 2),
                "roi": round(sum(profit(b) for b in v) / sum(float(b["paper_stake_units"]) for b in v), 4)}
            for k, v in sorted(out.items())}


def evaluate(ledger: dict, now: datetime) -> dict:
    bets = ledger.get("bets") or []
    excluded: dict[str, int] = {}
    kept = []
    for b in bets:
        reason = eligible(b) if isinstance(b, dict) else "invalide"
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
        else:
            kept.append(b)
    stakes = sum(float(b["paper_stake_units"]) for b in kept)
    units = sum(profit(b) for b in kept)
    roi = mean_ci([profit(b) / float(b["paper_stake_units"]) for b in kept], RULE["z"])
    clv_values = [s["clv_pct"] / 100 for s in (closing_sample(b) for b in kept) if s]
    clv = mean_ci(clv_values, RULE["z"])
    brier = brier_comparison(kept)
    n = len(kept)

    def above(stat):
        return bool(stat and stat.get("ci95") and stat["ci95"][0] > 0)

    checks = {
        "volume": {"ok": n >= RULE["min_settled"], "progress": f"{n}/{RULE['min_settled']}"},
        "roi": {"ok": above(roi), "value": roi},
        "clv": {"ok": bool(clv and clv["n"] >= RULE["min_clv_samples"] and above(clv)),
                "progress": f"{clv['n'] if clv else 0}/{RULE['min_clv_samples']}", "value": clv},
        "calibration": {"ok": bool(brier["difference"] and brier["difference"]["ci95"]
                                   and brier["difference"]["ci95"][1] < 0), "value": brier},
    }
    if roi and roi["ci95"] and n >= RULE["min_for_stop"] and roi["ci95"][1] < 0:
        verdict = "abandon"
    elif n < RULE["min_settled"]:
        verdict = "insuffisant"
    elif all(c["ok"] for c in checks.values()):
        verdict = "prometteur"
    else:
        verdict = "non concluant"
    pending = sum(1 for b in bets if isinstance(b, dict) and b.get("status") == "pending"
                  and b.get("selection_rule") == RULE["selection_rule"])
    previous = [b for b in bets if isinstance(b, dict) and b.get("selection_rule") != RULE["selection_rule"]
                and eligible_any_strategy(b) is None]
    return {
        "version": RULE["version"],
        "generated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "source": "docs/engine-v2-ledger.json",
        "ledger_started_at": ledger.get("started_at"),
        "rule": RULE,
        "criteria": [{"id": k, "label": label, **checks[k]} for k, label in CRITERIA],
        "verdict": verdict,
        "settled_eligible": n,
        "pending": pending,
        "excluded": excluded,
        "stake_units": round(stakes, 2),
        "profit_units": round(units, 2),
        "cumulative_units": cumulative(kept),
        "exploratory_segments": {
            "warning": "Exploratoire : ne jamais retenir après coup le segment qui a le mieux marché.",
            "by_league": segments(kept, lambda b: str(b.get("league"))),
            "by_market": segments(kept, lambda b: str(b.get("market"))),
        },
        "previous_strategy": {
            "label": "Archive : paris choisis par le modèle Revue (avant le 2026-10-11), hors règle v2",
            "settled": len(previous),
            "profit_units": round(sum(profit(b) for b in previous), 2),
        },
        "real_bets_enabled": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", default="docs/engine-v2-ledger.json")
    parser.add_argument("--output", default="docs/regle-decision-latest.json")
    args = parser.parse_args()
    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    report = evaluate(ledger, datetime.now(timezone.utc))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verdict : {report['verdict']} · {report['settled_eligible']} paris éligibles · "
          f"{report['profit_units']:+.2f} u · en attente {report['pending']}")


if __name__ == "__main__":
    main()
