"""Phase 4: compare published Clairvoyance observations with Revue research.
Strict chronology, matched identities and no claims about the original SQL data.
Existing forecasts and fictional bet ledgers are never modified.
"""
from __future__ import annotations
import argparse, json, math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

VERSION="revue_phase4_published_evidence_v1"
LEAD=timedelta(minutes=20)

def stamp(value):
    if not isinstance(value,str): raise ValueError("Timestamp missing")
    try: d=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise ValueError("Timestamp invalid") from exc
    if d.tzinfo is None: raise ValueError("Naive timestamp")
    return d.astimezone(timezone.utc)

def prob(v):
    if type(v) not in (int,float) or not math.isfinite(v) or not 0<v<1:
        raise ValueError("Invalid probability")
    return float(v)

def safety(g,s,now):
    if now.tzinfo is None: raise ValueError("Naive clock")
    if (g.get("status")!="public_original_source_fixture_and_nhl_output_diagnostic"
        or g.get("reference_repository")!="Purple-Wraith/clairvoyance-backend"
        or g.get("real_bets_enabled") is not False
        or g.get("live_french_odds_verified") is not False
        or g.get("exact_prediction_parity_verified") is not False
        or g.get("point_in_time_feature_parity_verified") is not False
        or g.get("original_history_profit_report_excluded") is not True
        or not isinstance(g.get("nhl_source_vs_revue"),list)):
        raise ValueError("Untrusted reference observations")
    if (s.get("version")!="revue_nhl_backend_source_style_v1"
        or s.get("status")!="backend_style_input_scenario_not_original_model_parity"
        or s.get("has_verified_original_predictions") is not False
        or s.get("original_sql_ratings_available") is not False
        or s.get("public_deployment_configuration_verified") is not False
        or s.get("reference_uses_same_frontend_best_bets_model_verified") is not False
        or s.get("real_bets_enabled") is not False
        or s.get("frozen_ledger_unchanged") is not True
        or not isinstance(s.get("games"),list)):
        raise ValueError("Untrusted or overstated NHL scenarios")
    if stamp(g["generated_at_utc"])>now+timedelta(minutes=2):
        raise ValueError("Future reference report")
    if stamp(s["generated_at_utc"])>now+timedelta(minutes=2):
        raise ValueError("Future scenario report")

def build(gap,scenarios,now):
    safety(gap,scenarios,now)
    scenario_time=stamp(scenarios["generated_at_utc"])
    lookup={}; duplicates=set()
    for s in scenarios["games"]:
        if not isinstance(s,dict):continue
        key=str(s.get("event_id",""))
        if not key.isdecimal():continue
        if key in lookup:duplicates.add(key)
        lookup[key]=s
    for key in duplicates:lookup.pop(key,None)
    rows=[]; counts=Counter(); seen=set()
    for r in gap["nhl_source_vs_revue"]:
        if not isinstance(r,dict) or r.get("league")!="NHL":continue
        key=r.get("key"); market=r.get("market"); side=r.get("side")
        if not isinstance(key,str) or not key.startswith("NHL:"):
            counts["invalid_identity"]+=1;continue
        unique=(key,market,side,str(r.get("line")))
        if unique in seen:
            counts["duplicate_selection"]+=1;continue
        seen.add(unique)
        if market not in ("moneyline_including_overtime","full_game_total") or side not in ("home","away","over","under"):
            counts["unsupported_market"]+=1;continue
        if (market=="moneyline_including_overtime" and side not in ("home","away")) or (market=="full_game_total" and side not in ("over","under")):
            counts["wrong_market_side"]+=1;continue
        try:
            kick=stamp(r["kickoff_utc"])
            observed=stamp(r["original_observed_at_utc"])
            ours_at=stamp(r["revue_observed_at_utc"])
            source_p=prob(r["original_probability"])
        except (KeyError,ValueError,TypeError):
            counts["bad_observation"]+=1;continue
        status="observed_before_kickoff_both"
        own_p=None; delta=None
        if observed>kick-LEAD:status="original_snapshot_too_late"
        elif ours_at>kick-LEAD:status="revue_snapshot_too_late"
        elif r.get("status")!="compared":status="no_same_market_revue_output"
        elif r.get("same_scheduled_fixture_and_market") is not True:status="fixture_or_market_unverified"
        else:
            try:
                own_p=prob(r["revue_probability"])
                delta=round((own_p-source_p)*100,2)
                asserted=r["difference_revue_minus_original_pp"]
                if type(asserted) not in (int,float) or not math.isfinite(asserted) or abs(delta-asserted)>.02:
                    raise ValueError("Stored difference does not match probabilities")
            except (KeyError,ValueError,TypeError):
                status="invalid_probability_difference"; own_p=None; delta=None
        counts[status]+=1
        scen=None
        x=lookup.get(key.split(":",1)[1])
        if (status=="observed_before_kickoff_both" and market=="moneyline_including_overtime"
            and x is not None and x.get("home")==r.get("home")
            and x.get("away")==r.get("away")
            and scenario_time<=kick-LEAD
            and x.get("source_observed_by_frozen_model_time") is True
            and x.get("frozen_prediction_overwritten") is False
            and x.get("actual_original_best_bet_reproduced") is False
            and x.get("original_sql_elo_and_raw_xg_verified") is False):
            try:
                if stamp(x["kickoff_utc"])!=kick:raise ValueError("Different kickoff")
                raw=prob(x["raw_fraction_home_probability"])
                pct=prob(x["percentage_point_home_probability"])
                if side=="away":raw,pct=1-raw,1-pct
                scen={
                    "xg_fraction_probability":round(raw,5),
                    "xg_percentage_points_probability":round(pct,5),
                    "fraction_distance_to_source_pp":round(abs(raw-source_p)*100,2),
                    "percentage_distance_to_source_pp":round(abs(pct-source_p)*100,2),
                    "scenario_difference_pp":round(abs(raw-pct)*100,2),
                    "original_sql_inputs_verified":False,
                    "published_model_identical_verified":False,
                    "starter_confirmed":False,
                }
            except (KeyError,TypeError,ValueError):pass
        rows.append({
            "key":key,"home":r.get("home"),"away":r.get("away"),
            "kickoff_utc":kick.isoformat(),"market":market,"side":side,
            "line":r.get("line"),"status":status,
            "reference_observed_utc":observed.isoformat(),
            "revue_observed_utc":ours_at.isoformat(),
            "reference_p":round(source_p,5),
            "revue_p":round(own_p,5) if own_p is not None else None,
            "delta_pp":delta,"hypotheses":scen,
            "reference_model_lock_verified":False,
            "market_settlement_rule_verified":False,
        })
    accepted=[r for r in rows if r["status"]=="observed_before_kickoff_both"]
    hypotheses=[r for r in accepted if r["hypotheses"] is not None]
    return {
        "version":VERSION,"status":"published_output_diagnostic_not_original_parity",
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "reference_gap_generated_at_utc":gap["generated_at_utc"],
        "scenario_generated_at_utc":scenarios["generated_at_utc"],
        "reference_selections":len(gap["nhl_source_vs_revue"]),
        "strict_fixture_matches":gap.get("strict_event_matches"),
        "observed_probability_comparisons":len(accepted),
        "matched_input_hypotheses":len(hypotheses),
        "mean_abs_delta_pp":round(sum(abs(x["delta_pp"]) for x in accepted)/len(accepted),2) if accepted else None,
        "exclusion_reasons":dict(sorted(counts.items())),
        "rows":rows,
        "original_sql_inputs_verified":False,
        "published_original_model_identical_verified":False,
        "actual_original_prediction_parity_verified":False,
        "original_forecast_lock_time_verified":False,
        "market_settlement_rules_verified":False,
        "real_bets_enabled":False,"roi_claimed":False,
        "original_history_reused":False,"paid_api_calls":0,
        "note":"Deux instantanés observés avant match autorisent seulement une comparaison descriptive. Ils ne prouvent ni le verrouillage original des prévisions, ni la parité des données SQL/modèles, ni des prix de bookmaker valides. Les hypothèses d'unités xG sont des scénarios Revue."
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--gap",default="docs/clairvoyance-real-output-gap.json")
    parser.add_argument("--scenarios",default="docs/nhl-backend-source-style-latest.json")
    parser.add_argument("--output",default="docs/phase4-evidence-latest.json")
    args=parser.parse_args()
    data=build(json.loads(Path(args.gap).read_text(encoding="utf-8")),
               json.loads(Path(args.scenarios).read_text(encoding="utf-8")),
               datetime.now(timezone.utc))
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Phase4:",data["observed_probability_comparisons"],"published comparisons,",
          data["matched_input_hypotheses"],"input scenarios; real parity NOT VERIFIED")

if __name__=="__main__":main()
