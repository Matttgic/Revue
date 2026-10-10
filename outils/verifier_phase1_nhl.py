#!/usr/bin/env python3
"""Acceptance gate for Phase 1 NHL fidelity, using traceable Revue evidence.

Does not confuse verified formulas, same public MoneyPuck data, original
Clairvoyance published picks, or the model's PRIVATE SQL Elo values.
Status cannot become 'completed' without all end-to-end proof criteria.
"""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
import argparse,json,math
from pathlib import Path

VERSION="revue_clairvoyance_nhl_phase1_acceptance_v1"

def _num(v):
    return type(v) in (int,float) and math.isfinite(v)

def report(formulas:dict,forensics:dict,elo:dict,inputs:dict,prospective:dict,
           now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Timezone aware audit clock required")
    now=now.astimezone(timezone.utc)
    target=formulas.get("total_target_models")
    verified=formulas.get("verified_formula_parity_models")
    formula_ok=(formulas.get("status")=="expanded_defined_scope_not_entire_repository"
                and type(target) is int and type(verified) is int and
                target>0 and verified==target and
                formulas.get("formula_parity_percent")==100)
    same_xg=forensics.get("input_summary",{}).get("identical_5v5_xg_both_teams")
    fixtures=forensics.get("input_summary",{}).get("same_event_and_kickoff_nhl")
    money=forensics.get("model_summary",{}).get("moneyline",{})
    gap=money.get("mean_absolute_gap_pp")
    xg_ok=(forensics.get("status")=="nhl_forensics_verified_observation_alignment"
           and forensics.get("exact_prediction_replication_verified") is False
           and _num(same_xg) and _num(fixtures) and 0<=same_xg<=fixtures)
    elo_math=(elo.get("version")=="revue_elo_settlement_only_source_semantics_v1"
              and elo.get("status")=="source_elo_update_math_verified_private_state_unknown"
              and elo.get("reference_k_factor")==32 and
              elo.get("reference_initial_elo")==1500
              and elo.get("updates_only_on_settled_moneyline_picks") is True
              and elo.get("updates_every_completed_nhl_game") is False
              and elo.get("paper_ledger_modified") is False
              and elo.get("real_bets_enabled") is False)
    original_sql=(elo_math and elo.get("original_sql_elo_values_available") is True
                  and elo.get("identical_original_settled_pick_history_verified") is True
                  and elo.get("original_sql_ordering_verified") is True)
    inputs_matched=(inputs.get("status")=="source_data_parity_verified" and
                    inputs.get("completed_data_checks")==inputs.get("total_data_checks") and
                    inputs.get("total_data_checks",0)>0 and
                    inputs.get("full_model_output_parity_on_real_games") is True)
    outputs_equal=(forensics.get("exact_prediction_replication_verified") is True
                   and money.get("comparisons",0)>=20 and gap==0)
    published_model_identified=(forensics.get("backend_predictor_is_the_published_best_bet_model_verified") is True)
    sample=prospective.get("settled_games") if prospective.get("status")=="prospective_partial_input_nhl_comparison_no_bets" else None
    prospect_sufficient=(type(sample) is int and sample>=100 and
        prospective.get("models",{}).get("monte_carlo",{}).get("brier") is not None and
        prospective.get("models",{}).get("ensemble",{}).get("brier") is not None)
    gates={
        "public_formula_subset_same_input_parity":bool(formula_ok),
        "public_nhl_fixture_and_xg_alignment":bool(xg_ok),
        "source_elo_update_algorithm":bool(elo_math),
        "original_elo_sql_state_and_settlement_history":bool(original_sql),
        "same_as_original_licensed_or_private_inputs":bool(inputs_matched),
        "original_published_model_identity":bool(published_model_identified),
        "identical_published_probabilities":bool(outputs_equal),
        "prospective_nhl_100_outcomes_for_initial_quality":bool(prospect_sufficient),
    }
    missing=[k for k,v in gates.items() if not v]
    blockers={
        "original_elo_sql_state_and_settlement_history":
            "Original Elo depends on settled source moneyline picks. Private SQL, first ratings, selection and DB ordering are absent.",
        "same_as_original_licensed_or_private_inputs":
            "Need time-matched NHL team stats, goalie selection and paid/private source features. Live/premium terms and license must be respected.",
        "original_published_model_identity":
            "The public Python predictor may not be the published frontend Best Bets strategy; do not align different model outputs as if identical.",
        "identical_published_probabilities":
            "Match original and Revue on same IDs, markets, input snapshots and model configuration; observed differences remain.",
        "prospective_nhl_100_outcomes_for_initial_quality":
            "Continue locked pregame predictions and official NHL final settlement until at least 100 distinct evaluated outcomes.",
        "public_formula_subset_same_input_parity":
            "Restore source-commit pinned same-input formula tests; 44 checked formulas do not cover every original function.",
        "public_nhl_fixture_and_xg_alignment":
            "Reconcile published games and contemporaneous MoneyPuck NHL 5v5 shares using source timestamps.",
        "source_elo_update_algorithm":
            "Reproduce original public update K=32 after settled moneyline pick only; never replay Elo over all final games.",
    }
    return {
        "version":VERSION,"generated_at_utc":now.isoformat(),
        "status":"complete_verified" if not missing else "partially_verified_blocked_by_unavailable_original_inputs",
        "phase1_completed":not missing,
        "phase1_completion_is_not_functional_coverage_percent":True,
        "reference":"Purple-Wraith/clairvoyance-backend",
        "reference_proprietary_sql_available":bool(original_sql),
        "original_source_license_for_wholesale_copy_verified":False,
        "real_bets_enabled":False,
        "paid_api_requests":0,
        "checkpoint":{
            "verified_target_formulas":verified if formula_ok else None,
            "targeted_formula_total":target if formula_ok else None,
            "identical_public_5v5_xg_nhl_games":same_xg if xg_ok else None,
            "identical_public_kickoff_and_team_games":fixtures if xg_ok else None,
            "published_nhl_moneyline_comparisons":money.get("comparisons") if xg_ok else None,
            "published_nhl_moneyline_mean_gap_pp":gap if xg_ok else None,
            "eligible_revue_moneyline_source_elo_updates":
                elo.get("eligible_revue_settled_moneyline_updates") if elo_math else None,
            "prospective_frontend_locked_games":prospective.get("locked_games"),
            "prospective_frontend_settled_games":sample,
            "original_source_data_checks_done":inputs.get("completed_data_checks"),
            "original_source_data_checks_total":inputs.get("total_data_checks"),
        },
        "acceptance_gates":gates,
        "remaining_requirements":[{"gate":x,"why":blockers[x]} for x in missing],
        "attestation":"Functional laboratory workflows are not the same thing as a faithful end-to-end clone. No 100% percentage is claimed without SQL and model-output proof.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args=parser.parse_args()
    root=Path(args.docs)
    def read(x):
        return json.loads((root/x).read_text("utf8"))
    result=report(read("parite-modeles-clairvoyance.json"),
                  read("clairvoyance-nhl-forensics.json"),
                  read("clairvoyance-elo-source-audit.json"),
                  read("parite-donnees-clairvoyance.json"),
                  read("nhl-frontend-prospective-performance.json"),
                  datetime.now(timezone.utc))
    (root/"phase1-nhl-fidelity.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
        encoding="utf8")
    print("Clairvoyance NHL phase1 acceptance:",
          sum(result["acceptance_gates"].values()),"/",
          len(result["acceptance_gates"]),"verified; blocked by",
          len(result["remaining_requirements"]),"unverified controls.")


if __name__=="__main__":
    main()
