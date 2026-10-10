"""Quantify NHL data-input gaps without changing historical frozen predictions.

Original predictor: MoneyPuck situation='all' and NHL Edge
goalie with most games. Revue shadow: situation='5on5' and MoneyPuck goalie.
All outcomes use the *same REVue proxy Elo*; no original SQL equivalence.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,json,math
from modeles.reproduction.clairvoyance_predictor import Game,nhl

MIN_LEAD=timedelta(minutes=20)
SOURCE_DEFAULTS={"NHL_SEASON":"20252026","NHL_GAME_TYPE":3}
DISCLAIMER=("Research sensitivity only. Revue Elo is NOT original SQL. "
    "The public source config defaults to 2025-26 playoffs; this run uses "
    "2026-27 regular season. Source default does not prove deployment config. "
    "MoneyPuck original scraper never rescales xGoalsPercentage; if input "
    "is 0..1, source formula divides xG difference by 100 again. Exact "
    "original stored values remain unverified. NHL official goalie stats "
    "can postdate the frozen forecast.")


def dt(v):
    if not isinstance(v,str): raise ValueError("Missing source timestamp")
    d=datetime.fromisoformat(v.replace("Z","+00:00"))
    if d.tzinfo is None: raise ValueError("Timestamp must be timezone-aware")
    return d.astimezone(timezone.utc)


def frac(v):
    if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1:
        raise ValueError("Invalid probability/rate")
    return float(v)


def team_index(doc,season,situation):
    out={}
    for row in doc["seasons"][season]:
        if row.get("situation")!=situation:continue
        team=row["team"]
        if team in out or not isinstance(team,str) or not team:
            raise ValueError("Duplicate/invalid team in MoneyPuck")
        out[team]=frac(row["xg_share"])
    return out


def goalie_index(doc):
    by_team={}
    for row in doc["goalies"]:
        if row.get("season")!=doc["season"] or row.get("game_type_id")!=doc["game_type_id"]:
            raise ValueError("Mixed NHL goalie season/game type")
        games=row.get("games_played")
        if type(games) is not int or games<0: raise ValueError("Bad goalie games")
        by_team.setdefault(row["team_abbrev"],[]).append(row)
    result={}
    for team,group in by_team.items():
        most=max(g["games_played"] for g in group)
        candidates=[g for g in group if g["games_played"]==most]
        if most==0 or len(candidates)!=1:
            result[team]={"status":"tie_or_zero_games","games":most}
            continue
        item=candidates[0]
        if item.get("overall_save_pct") is None:
            result[team]={"status":"missing_save_pct","games":most}
            continue
        result[team]={"status":"unique_most_games",
                      "save_pct":frac(item["overall_save_pct"]),
                      "name":item.get("player_name"),"games":most}
    return result


def analyze(teams,mp_goalies,official,shadow,now):
    now=dt(now.isoformat())
    season=teams.get("current_season")
    if (not isinstance(season,str) or len(season)!=9 or
        official.get("status")!="verified_nhl_official_stats_snapshot" or
        official.get("source")!="api.nhle.com/stats/rest/en" or
        official.get("season")!=season.replace("-","") or
        official.get("game_type_id")!=2 or
        teams.get("source")!="MoneyPuck.com" or
        mp_goalies.get("source")!="MoneyPuck.com" or
        mp_goalies.get("current_season")!=season or
        teams.get("status",{}).get(season,{}).get("status")!="available" or
        mp_goalies.get("statuses",{}).get(season,{}).get("status")!="available" or
        shadow.get("status")!="experimental_not_calibrated" or
        shadow.get("bookmaker_odds_available") is not False):
        raise ValueError("Source, season or research-state provenance invalid")
    stamps={
        "frozen_forecast":dt(shadow["generated_at_utc"]),
        "moneypuck_team_observed":dt(teams["generated_at_utc"]),
        "moneypuck_goalie_observed":dt(mp_goalies["generated_at_utc"]),
        "official_goalie_observed":dt(official["generated_at_utc"]),
        "moneypuck_team_provider":dt(teams["status"][season]["source_updated_utc"]),
        "moneypuck_goalie_provider":dt(mp_goalies["statuses"][season]["source_updated_utc"]),
    }
    if any(t>now for t in stamps.values()):raise ValueError("Future data leakage")
    all_stats=team_index(teams,season,"all")
    five=team_index(teams,season,"5on5")
    official_g=goalie_index(official)
    output=[]; skipped={}; seen=set()
    def skip(reason):
        skipped[reason]=skipped.get(reason,0)+1
    for entry in shadow["games"]:
        ident=str(entry["event_id"])
        if ident in seen: raise ValueError("Duplicate shadow fixture")
        seen.add(ident)
        start=dt(entry["start_utc"])
        if start<now+MIN_LEAD:
            skip("not_upcoming");continue
        if any(t>start-MIN_LEAD for t in stamps.values()):
            skip("source_observed_after_pregame_cutoff");continue
        home,away=entry["home"],entry["away"]
        if any(t not in source for t in (home,away) for source in (all_stats,five)):
            skip("missing_moneypuck_team");continue
        old_xg=entry["xg_5v5_share_pct"]
        if not all(abs(frac(old_xg[s]/100)-five[t])<1e-5
                   for s,t in (("home",home),("away",away))):
            skip("different_team_snapshot");continue
        frozen_g=entry["historical_goalie_proxy"]
        old_h=frac(frozen_g["home"]["save_pct"]) if frozen_g.get("home") else None
        old_a=frac(frozen_g["away"]["save_pct"]) if frozen_g.get("away") else None
        he,ae=entry["home_elo_proxy"],entry["away_elo_proxy"]
        if not all(type(x) in (int,float) and math.isfinite(x) and 500<x<2500 for x in (he,ae)):
            raise ValueError("Untrusted Elo")
        game=Game(ident,home,away,game_time_utc=start.isoformat())
        def p(x,y,g1,g2):
            return nhl(game,he,ae,x,y,g1,g2)["model_home_win_prob"]
        baseline=p(old_xg["home"],old_xg["away"],old_h,old_a)
        home_all,away_all=100*all_stats[home],100*all_stats[away]
        all_only=p(home_all,away_all,old_h,old_a)
        h=official_g.get(home,{"status":"missing"})
        a=official_g.get(away,{"status":"missing"})
        complete=h["status"]==a["status"]=="unique_most_games"
        g_only=p(old_xg["home"],old_xg["away"],h["save_pct"],a["save_pct"]) if complete else None
        both=p(home_all,away_all,h["save_pct"],a["save_pct"]) if complete else None
        # The public scraper stores the unscaled numeric CSV value; the public
        # predictor divides the xGoals% difference by 100. Revue's shadow
        # instead supplied 0..100 percentages. If CSV values were fractions,
        # the original formula's xG contribution would be 100 times smaller.
        # This is a counterfactual INPUT SCALE scenario: the exact raw CSV,
        # source SQL, source season and original Elo are not verified equal.
        fraction_only=p(all_stats[home],all_stats[away],old_h,old_a)
        fraction_both=(p(all_stats[home],all_stats[away],
                         h["save_pct"],a["save_pct"]) if complete else None)
        output.append({
            "event_id":ident,"home":home,"away":away,"start_utc":start.isoformat(),
            "frozen_published_home_probability":entry["home_win"],
            "recomputed_frozen_inputs_probability":baseline,
            "all_xg_only_home_probability":all_only,
            "all_xg_raw_fraction_only_home_probability":fraction_only,
            "official_goalie_only_home_probability":g_only,
            "all_xg_and_official_goalie_home_probability":both,
            "all_xg_raw_fraction_and_official_goalie_home_probability":fraction_both,
            "raw_fraction_vs_pct_points_scale_change_pp":
                round(100*(fraction_only-all_only),2),
            "raw_fraction_vs_pct_points_scale_change_with_official_goalie_pp":
                round(100*(fraction_both-both),2) if complete else None,
            "xg_only_change_pp":round(100*(all_only-baseline),2),
            "goalie_only_change_pp":round(100*(g_only-baseline),2) if complete else None,
            "combined_change_pp":round(100*(both-baseline),2) if complete else None,
            "official_goalie_selection":{"home":h,"away":a},
            "xg_all_share_pct":{"home":home_all,"away":away_all},
            "xg_5on5_share_pct":{"home":old_xg["home"],"away":old_xg["away"]},
            "new_comparison_uses_original_sql":False,"is_new_frozen_prediction":False
        })
    shifts=[abs(x["combined_change_pp"]) for x in output if x["combined_change_pp"] is not None]
    xs=[abs(x["xg_only_change_pp"]) for x in output]
    scales=[abs(x["raw_fraction_vs_pct_points_scale_change_pp"]) for x in output]
    scales_both=[abs(x["raw_fraction_vs_pct_points_scale_change_with_official_goalie_pp"])
                 for x in output
                 if x["raw_fraction_vs_pct_points_scale_change_with_official_goalie_pp"] is not None]
    return {
        "generated_at_utc":now.isoformat(),
        "status":"diagnostic_not_original_source_parity",
        "original_source_selector":{"money_puck_situation":"all",
                                    "goalie":"NHL Edge most games played",
                                    "observed_source_config_defaults":SOURCE_DEFAULTS},
        "diagnostic_source_season":season,"diagnostic_game_type_id":2,
        "source_default_differs_from_diagnostic":True,
        "same_team_csv_snapshot_for_both_situations":True,
        "nhl_goalies_observed_after_frozen_forecast":stamps["official_goalie_observed"]>stamps["frozen_forecast"],
        "source_observation_times_utc":{k:v.isoformat() for k,v in stamps.items()},
        "num_frozen_shadow_games":len(shadow["games"]),
        "games_comparable":len(output),
        "games_with_unique_nhl_official_goalie":len(shifts),
        "different_all_vs_5on5_team_rates":sum(all_stats[t]!=five[t] for t in all_stats.keys()&five.keys()),
        "mean_abs_delta_xg_only_pp":round(sum(xs)/len(xs),2) if xs else None,
        "mean_abs_delta_combined_pp":round(sum(shifts)/len(shifts),2) if shifts else None,
        "mean_abs_delta_source_xg_input_scale_pp":round(sum(scales)/len(scales),2) if scales else None,
        "mean_abs_delta_source_scale_with_official_goalie_pp":
            round(sum(scales_both)/len(scales_both),2) if scales_both else None,
        "raw_moneypuck_fraction_scenario":{
            "assumed_raw_input_unit":"fraction_0_to_1",
            "contrasted_input_unit":"percentage_points_0_to_100",
            "original_scraper_numeric_normalization":"none",
            "original_predictor_divisor":100,
            "original_database_raw_value_equality_verified":False,
            "original_deployment_config_verified":False,
            "not_source_parity_and_not_a_new_pick":True
        },
        "skipped":skipped,"real_bets_enabled":False,
        "original_inputs_identical":False,"end_to_end_parity_verified":False,
        "disclaimer":DISCLAIMER,"games":output
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--docs",default="docs")
    cli.add_argument("--output",default="docs/nhl-source-input-delta.json")
    args=cli.parse_args()
    root=Path(args.docs)
    def load(file):return json.loads((root/file).read_text(encoding="utf-8"))
    data=analyze(load("moneypuck-nhl-latest.json"),
                 load("moneypuck-goalies-latest.json"),
                 load("nhl-official-stats-latest.json"),
                 load("nhl-clairvoyance-shadow-latest.json"),
                 datetime.now(timezone.utc))
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Source-shape-only NHL study:",data["games_comparable"],
          "upcoming games;",data["games_with_unique_nhl_official_goalie"],
          "complete. No original predictions or bets.")


if __name__=="__main__":main()
