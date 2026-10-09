#!/usr/bin/env python3
"""Named Clairvoyance model-parity scoreboard, NOT overall project completion.

13 core source functions + 8 rate/analytics + 8 EU hockey models; CFB excluded.
A function is 'verified' ONLY when a GitHub CI parity report compares actual
output to source from a pinned Clairvoyance commit. Other Revue innovations
and numeric backtests cannot boost this percentage.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

MODELS=(
    ("backend_mlb_elo","MLB · Elo / marché moneyline","app/services/predictor.py","predict_mlb_game"),
    ("backend_nhl_elo_moneypuck_goalie","NHL · Elo / xG / gardien","app/services/predictor.py","predict_nhl_game"),
    ("frontend_nhl_mc","NHL · Monte-Carlo","docs/app.html","nhlMC"),
    ("frontend_nhl_ensemble","NHL · Ensemble","docs/app.html","nhlEns"),
    ("frontend_nba_mc","NBA · Monte-Carlo","docs/app.html","nbaMC"),
    ("frontend_nba_bayes","NBA · Bayes","docs/app.html","nbaGetBayes"),
    ("frontend_nba_ensemble","NBA · Ensemble","docs/app.html","nbaEns"),
    ("frontend_nfl_mc","NFL · Monte-Carlo","docs/app.html","nflMC"),
    ("frontend_nfl_bayes","NFL · Bayes","docs/app.html","_nflBayes"),
    ("frontend_nfl_ensemble","NFL · Ensemble","docs/app.html","nflEns"),
    ("frontend_soccer_xg","Football · xG","docs/app.html","_socXG"),
    ("frontend_soccer_mc","Football · Monte-Carlo","docs/app.html","_soccerMC"),
    ("frontend_soccer_market_blend","Football · Pondération du marché","docs/app.html","_socMarketBlend"),
    ("frontend_soccer_poisson_over","Football · Proba over analytique","docs/app.html","_poissonOverProb"),
    ("frontend_soccer_poisson_pmf","Football · Masse de Poisson","docs/app.html","_socPoissonPmf"),
    ("frontend_soccer_margin_dist","Football · Distribution de marge","docs/app.html","_socMarginDist"),
    ("frontend_soccer_spread_prob","Football · Handicap asiatique","docs/app.html","_socSpreadProb"),
    ("frontend_liiga_rates","Liiga · Pondération inter-saisons","docs/app.html","_liigaBlendedRates"),
    ("frontend_nla_rates","Hockey suisse · Pondération des taux","docs/app.html","_nlaBlendedRates"),
    ("frontend_extraliga_rates","Hockey tchèque · Pondération des taux","docs/app.html","_extraligaBlendedRates"),
    ("frontend_shl_rates","SHL · Pondération des taux","docs/app.html","_shlBlendedRates"),
    ("frontend_liiga_mc","Liiga · Simulation de score Poisson et handicap","docs/app.html","liigaMC"),
    ("frontend_nla_mc","Suisse NL · Simulation de score Poisson et handicap","docs/app.html","nlaMC"),
    ("frontend_extraliga_mc","Tchéquie Extraliga · Simulation de score Poisson","docs/app.html","extraligaMC"),
    ("frontend_shl_mc","SHL · Simulation de score Poisson et handicap","docs/app.html","shlMC"),
    ("frontend_liiga_ensemble","Liiga · Ensemble Bayes/Poisson/marché","docs/app.html","liigaEns"),
    ("frontend_nla_ensemble","Suisse NL · Ensemble Bayes/Poisson/marché","docs/app.html","nlaEns"),
    ("frontend_extraliga_ensemble","Extraliga · Ensemble Bayes/Poisson/marché","docs/app.html","extraligaEns"),
    ("frontend_shl_ensemble","SHL · Ensemble Bayes/Poisson/marché","docs/app.html","shlEns"),
)

def generate(reference_parity:dict,audit:dict,as_of:datetime,
             frontend_parity:dict|None=None)->dict:
    verified=set(reference_parity.get("verified_modules") or [])
    same=(reference_parity.get("status")=="predictor_formula_parity_verified"
          and (reference_parity.get("exact_equality_tests_passed") or 0)>0)
    js=frontend_parity or {}
    source_unchanged=bool(same and js.get("reference_commit")
                    and js.get("reference_commit")==reference_parity.get("reference_commit"))
    verified_js=set(js.get("verified_modules") or []) if (
        source_unchanged and js.get("status")=="frontend_function_output_parity_verified"
        and (js.get("exact_equality_tests_passed") or 0)>0) else set()
    listed={x["name"] for x in audit.get("frontend_model_symbols",{}).get("model_symbols",[])}
    entries=[]
    for model_id,label,source,fn in MODELS:
        is_verified=(same and source!="docs/app.html" and model_id in verified or
                     source=="docs/app.html" and model_id in verified_js and fn in listed)
        is_indexed=source!="docs/app.html" or fn in listed
        entries.append({
            "id":model_id,"label":label,"original_function":fn,
            "source_file":source,
            "source_indexed":is_indexed,
            "status":"exact_formula_parity_verified" if is_verified else
                     "pending_implementation_or_parity",
            "verified_source_commit":(js.get("reference_commit") if source=="docs/app.html"
                                   else reference_parity.get("reference_commit"))
                        if is_verified else None,
            "reproduced_with_same_data":False,
            "verified_with_original_datasets":False,
        })
    n_verified=sum(item["status"]=="exact_formula_parity_verified"
                   for item in entries)
    n_total=len(entries)
    first=entries[:13]
    first_count=sum(e["status"]=="exact_formula_parity_verified" for e in first)
    follow=entries[13:21]
    second_count=sum(e["status"]=="exact_formula_parity_verified" for e in follow)
    game_models=entries[21:]
    third_count=sum(e["status"]=="exact_formula_parity_verified" for e in game_models)
    return {
        "generated_at_utc":as_of.astimezone(timezone.utc).isoformat(),
        "name":"Clairvoyance Model Reproduction — 29 original functions (13 core + 8 auxiliary + 8 Euro-hockey models)",
        "status":"expanded_defined_scope_not_entire_repository",
        "phases":{
            "primary_13":{"verified":first_count,"target":13,
                          "percent":round(100*first_count/13)},
            "extended_8":{"verified":second_count,"target":len(follow),
                          "percent":round(100*second_count/max(1,len(follow)))},
            "eu_hockey_game_models_8":{"verified":third_count,"target":len(game_models),
                           "percent":round(100*third_count/max(1,len(game_models)))}
        },
        "excluded":["CFB"],
        "total_target_models":n_total,
        "verified_formula_parity_models":n_verified,
        "remaining_unverified":n_total-n_verified,
        "formula_parity_percent":round(100*n_verified/n_total),
        "overall_repository_reproduction_percent":None,
        "prediction_parity_on_live_data_percent":None,
        "original_source_commit":reference_parity.get("reference_commit"),
        "exact_equality_tests_passed":(reference_parity.get("exact_equality_tests_passed",0)
                                      + (js.get("exact_equality_tests_passed",0) if verified_js else 0)),
        "models":entries,
        "notes":[
            "Percentage covers ONLY 29 explicitly listed original source functions: 13 primary, 8 analytical/rate functions and 8 EU hockey match models. NOT full Clairvoyance.",
            "Source-side mathematical parity is verified on test inputs; real data parity and profit are NOT verified.",
            "Revue's original models, Monte-Carlo/Bayes experiments, pages and API integrations are EXCLUDED.",
            "Progress can increase only after direct source-vs-reproduction parity tests on pinned source versions.",
            "CFB intentionally excluded at the user's request.",
        ],
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--parity",default="docs/parite-clairvoyance-predictor.json")
    parser.add_argument("--audit",default="docs/clairvoyance-code-audit.json")
    parser.add_argument("--frontend-parity",default="docs/parite-clairvoyance-frontend.json")
    parser.add_argument("--output",default="docs/parite-modeles-clairvoyance.json")
    args=parser.parse_args()
    frontend_path=Path(args.frontend_parity)
    frontend=(json.loads(frontend_path.read_text(encoding="utf-8"))
              if frontend_path.is_file() else None)
    result=generate(json.loads(Path(args.parity).read_text(encoding="utf-8")),
                    json.loads(Path(args.audit).read_text(encoding="utf-8")),
                    datetime.now(timezone.utc),frontend)
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STRICT PARITY",result["verified_formula_parity_models"],"/",
          result["total_target_models"],"=",result["formula_parity_percent"],
          "% (29 named functions, NOT whole repo)")

if __name__=="__main__":
    main()
