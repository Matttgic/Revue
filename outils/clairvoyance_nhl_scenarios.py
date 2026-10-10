"""Independent original-backend NHL model sensitivity on real observed match inputs.

This is NOT proof that public Clairvoyance 'bestBets' use its SQL backend
predictor (there is a distinct frontend). The source predictor replica is used
as a transparent instrument to perturb Revue's documented Elo, MoneyPuck 5v5
and historical goalie-proxy inputs one dimension at a time, without fitting
against a published final probability.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,math
from modeles.reproduction.clairvoyance_predictor import Game,nhl

VERSION="revue_nhl_backend_input_sensitivity_v1"
def dt(value):
    if not isinstance(value,str):raise ValueError("Missing date")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Timezone required")
    return t.astimezone(timezone.utc)
def valid(v,lo=None,hi=None):
    return type(v) in (int,float) and math.isfinite(v) and (
        lo is None or v>=lo) and (hi is None or v<=hi)
def model_prob(row,he,ae,hg,ag,hsv,asv):
    fixture=Game(espn_id=row["event_id"],home_team=row["home"],away_team=row["away"])
    return nhl(fixture,home_elo=he,away_elo=ae,home_xgoals_pct=hg,
               away_xgoals_pct=ag,home_goalie_sv_pct=hsv,
               away_goalie_sv_pct=asv)["model_home_win_prob"]

def investigate(forensic,shadow):
    if forensic.get("version")!="nhl_input_gap_forensics_v1" or (
        forensic.get("status")!="nhl_forensics_verified_observation_alignment") or (
        forensic.get("exact_prediction_replication_verified") is not False) or (
        shadow.get("status")!="experimental_not_calibrated") or (
        shadow.get("bookmaker_odds_available") is not False):
        raise ValueError("Source-snapshot validation must succeed before scenario analysis")
    rows={str(x.get("event_id")):x for x in shadow.get("games",[]) if isinstance(x,dict)}
    comparisons=[]
    for gap in forensic["match_diagnostics"]:
        if gap.get("market")!="moneyline_including_overtime":continue
        ident=str(gap["event_id"]);shadow_row=rows.get(ident)
        if not shadow_row or shadow_row["home"]!=gap["home"] or shadow_row["away"]!=gap["away"]:
            continue
        if gap.get("xg_identity")!="same_xg_both_teams":continue
        try:
            kick=dt(gap["kickoff_utc"])
            if dt(shadow_row["start_utc"])!=kick or dt(shadow["generated_at_utc"])>=kick:
                continue
        except (KeyError,ValueError,TypeError):continue
        eh,ea=shadow_row.get("home_elo_proxy"),shadow_row.get("away_elo_proxy")
        hg,ag=(gap.get("reference_5v5_xg_pct") or {}).get("home"),(
            gap.get("reference_5v5_xg_pct") or {}).get("away")
        goalies=shadow_row.get("historical_goalie_proxy") or {}
        hsv=(goalies.get("home") or {}).get("save_pct")
        asv=(goalies.get("away") or {}).get("save_pct")
        target=gap.get("reference_probability")
        if not(all(valid(x) for x in (eh,ea,hg,ag,hsv,asv,target)) and
               all(valid(x,0,100) for x in (hg,ag)) and
               all(valid(x,0,1) for x in (hsv,asv,target)) and
               valid(eh,900,2100) and valid(ea,900,2100)):
            continue
        base=model_prob(shadow_row,eh,ea,hg,ag,hsv,asv)
        observed=shadow_row.get("home_win")
        if not valid(observed,0,1) or abs(base-observed)>.002:
            # Fail closed; scenario math may be using a different formula.
            continue
        side=gap["side"]
        if side not in ("home","away"):continue
        sign=1 if side=="home" else -1
        def side_p(p):return p if side=="home" else 1-p
        scenarios={
            "observed_revue_inputs":base,
            "equal_elo_1500":model_prob(shadow_row,1500,1500,hg,ag,hsv,asv),
            "equal_goalies_091":model_prob(shadow_row,eh,ea,hg,ag,.91,.91),
            "neutral_xg_50_50":model_prob(shadow_row,eh,ea,50,50,hsv,asv),
            "equal_elo_equal_goalies":model_prob(shadow_row,1500,1500,hg,ag,.91,.91),
        }
        details={name:{"model_probability":round(side_p(p),3),
                      "absolute_gap_to_published_pp":round(abs(side_p(p)-target)*100,2),
                      "change_from_observed_revue_pp":round((side_p(p)-side_p(base))*100,2)}
                 for name,p in scenarios.items()}
        comparisons.append({
            "event_id":ident,"league":"NHL","home":gap["home"],
            "away":gap["away"],"side":side,"kickoff_utc":gap["kickoff_utc"],
            "published_probability":target,"recomputed_revue_probability":round(side_p(base),3),
            "source_5v5_xg_inputs_equal":True,
            "elo_proxy":{"home":round(eh,2),"away":round(ea,2)},
            "historical_goalie_proxy_not_confirmed_starter":{
                "home_save_pct":hsv,"away_save_pct":asv},
            "counterfactuals":details,
            "not_identified_as_causal_explanation":True
        })
    comparisons.sort(key=lambda r:(-r["counterfactuals"]["observed_revue_inputs"]["absolute_gap_to_published_pp"],r["event_id"]))
    average=lambda key:round(sum(x["counterfactuals"][key]["absolute_gap_to_published_pp"] for x in comparisons)/len(comparisons),2) if comparisons else None
    return {
        "version":VERSION,"status":"same_real_observed_nhl_features_hypothetical_scenarios",
        "generated_at_utc":forensic["generated_at_utc"],
        "source_forensics":"docs/clairvoyance-nhl-forensics.json",
        "scenarios":{"observed_revue_inputs":"Recalculated from observed Revue Elo + source-confirmed 5v5 xG + Revue historical goalie proxies",
         "equal_elo_1500":"Hypothetical: replace both Revue Elo ratings with 1500; original hidden Elo NOT known",
         "equal_goalies_091":"Hypothetical: equalize both historical goalie proxies to 0.91; real starters NOT known",
         "neutral_xg_50_50":"Hypothetical: neutralize observed xG to 50/50",
         "equal_elo_equal_goalies":"Hypothetical combined neutral Elo and goalie"},
        "matched_scenarios":len(comparisons),
        "mean_abs_gap_published_vs_observed_revue_pp":average("observed_revue_inputs"),
        "mean_abs_gap_with_equal_elo_pp":average("equal_elo_1500"),
        "mean_abs_gap_with_equal_goalies_pp":average("equal_goalies_091"),
        "mean_abs_gap_with_neutral_xg_pp":average("neutral_xg_50_50"),
        "games_where_equal_elo_reduces_gap":sum(
            x["counterfactuals"]["equal_elo_1500"]["absolute_gap_to_published_pp"]<
            x["counterfactuals"]["observed_revue_inputs"]["absolute_gap_to_published_pp"]
            for x in comparisons),
        "games_where_equal_goalies_reduces_gap":sum(
            x["counterfactuals"]["equal_goalies_091"]["absolute_gap_to_published_pp"]<
            x["counterfactuals"]["observed_revue_inputs"]["absolute_gap_to_published_pp"]
            for x in comparisons),
        "games":comparisons,
        "real_bets_enabled":False,"calibration_or_betting_recommendations":False,
        "actual_original_hidden_elo_or_starters_verified":False,
        "original_published_model_family_verified":False,
        "note":"Never interpret lower hypothetical gap as evidence that the original used neutral Elo/goalies. Published bestBets can run a distinct frontend ensemble. This only diagnoses sensitivity with same Revue formula and real observed feature values."}

def main():
    p=argparse.ArgumentParser();p.add_argument("--docs",default="docs")
    p.add_argument("--output",default="docs/clairvoyance-nhl-scenarios.json")
    args=p.parse_args()
    root=Path(args.docs)
    def read(name):return json.loads((root/name).read_text(encoding="utf8"))
    data=investigate(read("clairvoyance-nhl-forensics.json"),
        read("nhl-clairvoyance-shadow-latest.json"))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(data["status"],data["matched_scenarios"],"games / 0 real bets")

if __name__=="__main__":main()
