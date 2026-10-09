#!/usr/bin/env python3
"""Chronological score-only backtests of Revue multisport probability models.

No bookmaker odds; Brier/log-loss only. Uses game results whose SCHEDULED
start is at least 8 hours earlier, avoids knowing a just-started match's final
score in a retrospective replay. Single fixture as a masked future event.
Caches only currently published ESPN historic scoreboard matches (no odds).
"""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import json
import math
from pathlib import Path
from collections import defaultdict
from modeles.simulations.multisports_independant import (
    LEAGUES, _read_cached_event, calculate
)

MIN_DELAY=timedelta(hours=8)


def _clip(p):
    return max(1e-8,min(1-1e-8,float(p)))


def _multiclass_brier(pred:list[float],label:int) -> float:
    # sum of squares over all 3 probabilities / standard sum convention
    return sum((v-(1 if i==label else 0))**2 for i,v in enumerate(pred))


def _logloss(p:float)->float:
    return -math.log(_clip(p))


def score_league(league,events,min_train=10):
    """Frozen as-of replays. No model fitting on scored outcomes."""
    settled=sorted((e for e in events if e.scored),
                   key=lambda g:(g.start,g.id))
    records=[]
    missing=0
    for game in settled:
        old=[x for x in settled if x.start <= game.start-MIN_DELAY and x.id!=game.id]
        if len(old)<min_train:
            continue
        # Mask the target result from the model and explicitly provide only old games
        masked=replace(game,complete=False,home_score=None,away_score=None)
        asof=game.start-timedelta(seconds=2)
        out=calculate(league,old+[masked],asof,days=1)
        item=next((x for x in out if x.get("event_id")==game.id),None)
        if not item or not item.get("probabilities"):
            missing+=1
            continue
        p=item["probabilities"]
        if league.style=="soccer":
            truth=0 if game.home_score>game.away_score else 2 if game.home_score<game.away_score else 1
            prediction=[p["home_win_90"],p["draw_90"],p["away_win_90"]]
            true_p=prediction[truth]
            brier=_multiclass_brier(prediction,truth)
            base=2/3
            base_log=math.log(3)
        else:
            if game.home_score==game.away_score:
                continue
            truth=int(game.home_score>game.away_score)
            prediction=_clip(p["home_win"])
            true_p=prediction if truth else 1-prediction
            brier=(prediction-truth)**2
            base=.25
            base_log=math.log(2)
        records.append({
            "event_id":game.id,"date":game.start.date().isoformat(),
            "p":round(true_p,5),"brier":brier,"logloss":_logloss(true_p),
            "baseline_brier":base,"baseline_logloss":base_log,
        })
    if not records:
        return {"status":"pas_assez_de_donnees","n":0,"excluded_insufficient":missing}
    brier=sum(x["brier"] for x in records)/len(records)
    log=sum(x["logloss"] for x in records)/len(records)
    b0=sum(x["baseline_brier"] for x in records)/len(records)
    l0=sum(x["baseline_logloss"] for x in records)/len(records)
    return {
        "status":"backtest_prototype",
        "n":len(records),
        "first":records[0]["date"],"last":records[-1]["date"],
        "brier":round(brier,5),"log_loss":round(log,5),
        "baseline_brier":round(b0,5),"baseline_log_loss":round(l0,5),
        "delta_brier_vs_uniform":round(brier-b0,5),
        "delta_logloss_vs_uniform":round(log-l0,5),
        "excluded_insufficient":missing,
        "note":"Benchmark uniforme seulement, PAS le consensus bookmaker.",
    }


def generate(cache:dict)->dict:
    out={}
    leagues=(cache.get("leagues") or {})
    for league in LEAGUES:
        raw=(leagues.get(league.key) or {}).get("events") or []
        games=[]
        for entry in raw:
            event=_read_cached_event(entry)
            if event and event.league==league.key:
                games.append(event)
        out[league.key]={"sport":league.sport,"label":league.label,
                         "raw_cache":len(games),
                         **score_league(league,games)}
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"backtest_sur_scores_uniquement",
        "basis":"Données matchs terminés dans les caches ESPN, historique tronqué par source.",
        "no_lookahead":"Match évalué comme futur ; événements de formation débutés >=8 heures avant le coup d'envoi. Pas d'accès aux cotes originales.",
        "limits":"Pas de cote disponible, pas de ROI, pas de CLV ; benchmark uniforme, pas le marché. Peut contenir biais de sélection/calendrier de l'API.",
        "leagues":out,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="docs/multisports-history.json")
    p.add_argument("--output",default="docs/backtests-multisports.json")
    args=p.parse_args()
    path=Path(args.history)
    if not path.exists():
        raise SystemExit("Pas encore d'historique ESPN sauvegardé")
    d=json.loads(path.read_text(encoding="utf-8"))
    result=generate(d)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for key,row in result["leagues"].items():
        print(f"{key:<12} n={row['n']:<4} Brier={row.get('brier','NC')} LogLoss={row.get('log_loss','NC')}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
