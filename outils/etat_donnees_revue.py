#!/usr/bin/env python3
"""Audit all observable Revue data layers, without provider calls or fabricated readiness.

Scores feed a real-snapshot paper ledger; bookmaker odds are OBSERVED
historical quotes, not confirmed live/bookable prices. Uncalibrated forecasts
are always research regardless of their apparent numeric confidence.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


FILES = {
    "calendrier":"multisports-latest.json",
    "matchs":"match-center-latest.json",
    "cotes":"engine-v2-latest.json",
    "radar_6h":"pulsescore-radar-latest.json",
    "calibration":"revue-model-quality-latest.json",
    "couvertures":"revue-crossbook-latest.json",
    "resultats":"scoreboard-revue-latest.json",
    "journal":"revue-control-ledger-latest.json",
    "selection":"picks-center-latest.json",
    "nhl_stats":"nhl-official-stats-latest.json",
    "nhl_moneypuck":"moneypuck-nhl-latest.json",
    "nhl_gardiens":"moneypuck-goalies-latest.json",
    "nhl_frontend":"nhl-frontend-observed-latest.json",
    "nhl_espgardiens":"nhl-espn-goalies-latest.json",
    "nhl_modeles_suivis":"nhl-frontend-prospective-performance.json",
    "reglements":"paper-score-settlement-latest.json",
}
AGE_LIMIT_HOURS = {
    "calendrier":8,"matchs":3,"cotes":7,"radar_6h":4,
    "calibration":3,"couvertures":3,"resultats":3,
    "journal":3,"selection":3,"nhl_stats":30,
    "nhl_moneypuck":48,"nhl_gardiens":48,"nhl_frontend":24,
    "nhl_espgardiens":8,"nhl_modeles_suivis":12,
    "reglements":3,
}
EXPECTED_STATUS = {
    "calendrier":"prototype_non_calibre",
    "matchs":"experimental_revue_match_center",
    "resultats":"observed_scoreboard_not_streaming",
    "selection":"revue_independent_picks_hub_static_research_paper_only",
    "nhl_stats":"verified_nhl_official_stats_snapshot",
    "radar_6h":"observed",
    "calibration":"prospective_probabilities_descriptive_not_calibrated",
    "couvertures":"math_only_quotes_observed_no_bookable_confirmation",
    "nhl_frontend":"prospective_research_partial_input_frontend_not_parity",
    "nhl_espgardiens":"espn_probable_goalies_observed_not_part_of_model",
    "nhl_modeles_suivis":"prospective_partial_input_nhl_comparison_no_bets",
    "reglements":"verified_paper_scoreboard_settlement_only",
}
EXPECTED_ODDS = {"active_pulsescore","active_the_odds_api","no_odds_returned",
                 "disabled_no_key","disabled_stale_model"}


def parse_time(x):
    if not isinstance(x,str):return None
    try:
        t=datetime.fromisoformat(x.replace("Z","+00:00"))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except ValueError:
        return None


def layer(name,doc,now):
    if doc is None:
        return {"file":FILES[name],"status":"missing","fresh":False,"updated_at_utc":None}
    if not isinstance(doc,dict):
        return {"file":FILES[name],"status":"invalid","fresh":False,"updated_at_utc":None}
    stamp=parse_time(doc.get("generated_at_utc"))
    if stamp is None or stamp>now+timedelta(minutes=2):
        return {"file":FILES[name],"status":"invalid_timestamp","fresh":False,
                "updated_at_utc":doc.get("generated_at_utc")}
    elapsed=max(0,(now-stamp).total_seconds()/3600)
    fresh=elapsed<=AGE_LIMIT_HOURS[name]
    valid = doc.get("status")==EXPECTED_STATUS[name] if name in EXPECTED_STATUS else True
    if name=="cotes":
        valid=(doc.get("mode")=="PAPER_ONLY" and
               doc.get("odds_status") in EXPECTED_ODDS and
               isinstance(doc.get("odds_board"),dict))
    if name=="radar_6h":
        valid=(valid and doc.get("version")=="revue_pulsescore_six_hour_radar_v1"
               and doc.get("provider")=="PulseScore"
               and doc.get("horizon_hours")==6
               and type(doc.get("request_cap")) is int
               and 1<=doc["request_cap"]<=8
               and type(doc.get("requests_used")) is int
               and 0<=doc["requests_used"]<=doc["request_cap"]
               and doc.get("market_prices_are_live") is False
               and doc.get("positive_ev_verified") is False
               and doc.get("real_bets_enabled") is False
               and doc.get("existing_paper_ledger_modified") is False
               and isinstance(doc.get("observations"),list))
    if name=="calibration":
        valid=(valid and doc.get("version")=="revue_prospective_paper_calibration_v1"
               and doc.get("real_bets_enabled") is False
               and doc.get("fitted_or_recalibrated_model") is False
               and doc.get("verified_positive_ev") is False
               and doc.get("bookmaker_baseline_includes_vig") is True
               and isinstance(doc.get("total"),dict))
    if name=="couvertures":
        flags=doc.get("risk_flags") or {}
        valid=(valid and doc.get("version")=="revue_quotations_crossbook_coverage_v1"
               and flags.get("real_bets_enabled") is False
               and flags.get("claim_guaranteed_profit") is False
               and flags.get("actual_prices_bookable_verified") is False
               and flags.get("paid_api_calls_for_this_audit")==0
               and isinstance(doc.get("potential_snapshot_covers"),list))
    if name=="journal":
        valid=(doc.get("paper_only") is True and doc.get("real_bets_enabled") is False
               and isinstance(doc.get("summary"),dict))
    if name=="nhl_moneypuck" or name=="nhl_gardiens":
        valid=doc.get("source")=="MoneyPuck.com" and doc.get("is_live") is False
    if name=="nhl_frontend":
        valid=valid and doc.get("real_bets_enabled") is False and doc.get("odds_and_value_bets_enabled") is False
    if name=="nhl_espgardiens":
        valid=valid and doc.get("used_in_prediction_model") is False and (
            doc.get("source")=="ESPN NHL scoreboard, separate from official NHL IDs"
            and doc.get("real_bets_enabled") is False)
    if name=="nhl_modeles_suivis":
        valid=valid and doc.get("real_bets_enabled") is False and (
            doc.get("roi") is None and doc.get("same_game_comparison") is True)
    if name=="reglements":
        valid=valid and doc.get("no_bets_created") is True
    if name=="resultats":
        valid=valid and doc.get("pricing_used") is False and isinstance(doc.get("events"),list)
    return {"file":FILES[name],
            "status":"invalid_provenance" if not valid else "fresh" if fresh else "stale",
            "fresh":bool(fresh and valid),"updated_at_utc":stamp.isoformat(),
            "age_hours":round(elapsed,2),"max_age_hours":AGE_LIMIT_HOURS[name]}


def report(documents:dict,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Timezone-aware audit clock required")
    now=now.astimezone(timezone.utc)
    stages={name:layer(name,documents.get(name),now) for name in FILES}
    d=lambda key: documents.get(key) if stages[key]["status"] in ("fresh","stale") else None
    matches=d("matchs") or {}
    score=d("resultats") or {}
    odds=d("cotes") or {}
    model=d("calendrier") or {}
    journal=d("journal") or {}
    nhl=d("nhl_frontend") or {}
    picks=d("selection") or {}
    goalie_reports=d("nhl_espgardiens") or {}
    comparison=d("nhl_modeles_suivis") or {}
    radar=d("radar_6h") or {}
    calibration=d("calibration") or {}
    crossbook=d("couvertures") or {}
    data={
        "matchs_futurs_observes":int(matches.get("metrics",{}).get("upcoming_matches") or 0),
        "matchs_avec_cotes_historiques":int(matches.get("metrics",{}).get("with_observed_bookmaker_quotes") or 0),
        "matchs_avec_modeles_recherche":int(matches.get("metrics",{}).get("with_research_model") or 0),
        "championnats_calendrier":len(model.get("competitions") or {}),
        "sources_sportives_ok":int(model.get("overview",{}).get("feeds_ok") or 0),
        "scoreboard_matchs_finaux":int(score.get("final") or 0),
        "scoreboard_matchs_en_cours":int(score.get("in_progress") or 0),
        "scoreboard_sources_ok":int(score.get("requests",{}).get("ok") or 0),
        "scoreboard_sources_erreur":int(score.get("requests",{}).get("failed") or 0),
        "simulations":int(journal.get("summary",{}).get("total") or 0),
        "simulations_reglees":int(journal.get("summary",{}).get("settled") or 0),
        "simulations_en_attente":int(journal.get("summary",{}).get("pending") or 0),
        "simulations_exclues":int(journal.get("summary",{}).get("excluded_or_unverified") or 0),
        "simulations_roi_fictif_pct":journal.get("summary",{}).get("paper_roi_pct"),
        "selection_experimentale":int(picks.get("unique_research_selections") or 0),
        "nhl_frontend_previsions":int(nhl.get("games_emitted") or 0),
        "nhl_espgardiens_confirms":int(goalie_reports.get("verified_current_starters") or 0),
        "nhl_espgardiens_probables":int(goalie_reports.get("projected_starters") or 0),
        "nhl_modeles_pronostics_verrouilles":int(comparison.get("locked_games") or 0),
        "nhl_modeles_resultats_verifies":int(comparison.get("settled_games") or 0),
        "bookmakers_fr_declares":len(odds.get("bookmakers_fr") or []),
        "radar_6h_matched":int(radar.get("matches_observed") or 0),
        "radar_6h_calls_used":int(radar.get("requests_used") or 0),
        "radar_6h_calls_cap":int(radar.get("request_cap") or 0),
        "calibration_echantillon_qualifie":int(calibration.get("total",{}).get("count") or 0),
        "calibration_matchs_distincts":int(calibration.get("total",{}).get("distinct_events") or 0),
        "marche_complets_controles":int(crossbook.get("complete_cross_book_markets_checked") or 0),
        "couvertures_math_observees":int(crossbook.get("potential_snapshot_cover_count") or 0),
        "cotes_fournisseur":odds.get("odds_status") or "unknown",
    }
    essential=("calendrier","matchs","cotes","resultats","journal","selection")
    missing=[x for x in essential if not stages[x]["fresh"]]
    blockers=[
        "Aucun modèle de paris validé/calibré sur des résultats prospectifs suffisants.",
        "Cotes des bookmakers seulement observées à un instant passé : disponibilité à la mise NON vérifiée.",
        "Cotation Pinacle/échelle de marché et comparaisons EV non validées de bout en bout.",
        "Gardiens titulaires et blessures NHL non confirmés ; variables NHL Edge originales manquantes.",
        "Données et classements SQL privés de Clairvoyance non disponibles : reproduction exacte des picks non démontrée.",
    ]
    if missing:blockers.insert(0,"Actualisation requise : "+", ".join(missing)+".")
    if stages["cotes"]["fresh"] and data["bookmakers_fr_declares"]==0:
        blockers.insert(0,"Aucun bookmaker français enregistré dans le dernier scanner.")
    if data["scoreboard_sources_erreur"]>0 and stages["resultats"]["fresh"]:
        blockers.insert(0,"Au moins une source de scores publics en échec sur le dernier contrôle.")
    return {
        "generated_at_utc":now.isoformat(),
        "status":"data_sources_audited_not_live_betting_ready",
        "realtime_bookmaker_availability_verified":False,
        "verified_positive_ev_opportunities":0,
        "uncalibrated_models_are_not_betting_advice":True,
        "original_clairvoyance_end_to_end_parity":False,
        "real_bets_enabled":False,
        "paid_api_requests_for_this_audit":0,
        "all_essential_snapshots_fresh":not missing,
        "fresh_essential_layers":sum(stages[x]["fresh"] for x in essential),
        "essential_layer_count":len(essential),
        "layers":stages,
        "facts":data,
        "remaining_blockers":blockers,
        "user_summary":"Les matchs, les cotes observées, les résultats et le bilan sont suivis indépendamment. Seules des validations complètes permettraient de présenter un pari jouable.",
        "scope":"Snapshot metadata + verified paper outcomes only; not a real-time provider status check.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args=parser.parse_args()
    root=Path(args.docs)
    docs={}
    for key,filename in FILES.items():
        src=root/filename
        try:
            docs[key]=json.loads(src.read_text(encoding="utf-8")) if src.exists() else None
        except (ValueError,OSError):
            docs[key]=None
    out=report(docs,datetime.now(timezone.utc))
    (root/"etat-donnees-latest.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print("Revue data quality:",out["fresh_essential_layers"],"/",
          out["essential_layer_count"],"essential snapshots fresh. No paid odds calls.")


if __name__=="__main__":main()
