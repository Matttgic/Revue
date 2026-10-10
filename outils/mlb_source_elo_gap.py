"""MLB original predictor sensitivity to unavailable original SQL Elo ratings.

Reference publicly uses 1500 for a team absent from source SQL,
and +35 home-field Elo on MLB games. Revue computes its own ESPN-history
Elo; this report compares both inputs without pretending that the
original source SQL database is missing or equal to Revue history.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,json
from api_revue.fixtures import timestamp,SourceUnavailable
from api_revue.mlb_elo import replay_mlb_elo
from modeles.reproduction.clairvoyance_predictor import Game,mlb

MIN_LEAD=timedelta(minutes=20)

def analyze(fixtures:dict,history:dict,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("UTC-aware clock required")
    now=now.astimezone(timezone.utc)
    if fixtures.get("status")!="prototype_non_calibre":
        raise ValueError("Unverified source model status")
    observed=timestamp(fixtures.get("generated_at_utc"))
    if observed>now or now-observed>timedelta(hours=8):
        raise ValueError("Stale or future snapshot")
    season=(fixtures.get("competitions") or {}).get("MLB")
    if not isinstance(season,dict) or not isinstance(season.get("games"),list):
        raise ValueError("No MLB verified fixture collection")
    ratings=replay_mlb_elo(history,now)
    lookup={row["team"]:row for row in ratings["rows"]}
    report=[];seen=set();skipped={}
    def skip(reason):skipped[reason]=skipped.get(reason,0)+1
    for fixture in season["games"]:
        ident=str(fixture.get("event_id"))
        if not ident.isdecimal() or ident in seen:
            raise ValueError("Duplicate or invalid ESPN fixture")
        seen.add(ident)
        kickoff=timestamp(fixture["start_utc"])
        if kickoff<now+MIN_LEAD:
            skip("not_upcoming_20_minutes");continue
        if observed>kickoff-MIN_LEAD:
            skip("snapshot_observed_after_cutoff");continue
        home,away=fixture["home"],fixture["away"]
        if not isinstance(home,str) or not isinstance(away,str) or not home or home==away:
            raise ValueError("Bad MLB team identity")
        if home not in lookup or away not in lookup:
            skip("missing_revue_elo_coverage");continue
        h,a=lookup[home]["rating"],lookup[away]["rating"]
        g=Game(ident,home,away,game_date=kickoff.date().isoformat(),
               game_time_utc=kickoff.isoformat())
        replay=mlb(g,h,a)["model_home_win_prob"]
        neutral=mlb(g,1500.,1500.)["model_home_win_prob"]
        missing_home=mlb(g,1500.,a)["model_home_win_prob"]
        missing_away=mlb(g,h,1500.)["model_home_win_prob"]
        report.append({
            "event_id":ident,"home":home,"away":away,
            "start_utc":kickoff.isoformat(),
            "revue_elo_home":h,"revue_elo_away":a,
            "revue_historical_games_home":lookup[home]["games_played"],
            "revue_historical_games_away":lookup[away]["games_played"],
            "replayed_revue_home_probability":replay,
            "original_default_both_missing_home_probability":neutral,
            "original_default_home_missing_home_probability":missing_home,
            "original_default_away_missing_home_probability":missing_away,
            "replay_vs_both_default_pp":round((replay-neutral)*100,2),
            "original_sql_elo_inputs_verified_equal":False,
            "original_sql_missing_team_status_known":False,
            "market_moneylines_available":False,
            "betting_recommendation":None,
        })
    shifts=[abs(x["replay_vs_both_default_pp"]) for x in report]
    return {
        "generated_at_utc":now.isoformat(),
        "status":"conditional_source_elo_fallback_sensitivity_not_original_reproduction",
        "reference_behavior":"Original MLB predictor uses Elo team row or 1500 default, plus 35 home Elo, no pitcher adjustment",
        "diagnostic_revue_completed_espn_games":ratings["completed_espn_games"],
        "diagnostic_fixture_observed_at_utc":observed.isoformat(),
        "diagnostic_elo_cutoff_utc":ratings["cutoff_utc"],
        "reference_default_rating":1500.0,
        "source_formula":"independent behavioral reproduction",
        "original_sql_ratings_verified_equal":False,
        "original_sql_missing_team_status_known":False,
        "historical_sql_coverage_proven_identical":False,
        "historical_statuses_are_not_point_in_time_observations":True,
        "real_bets_enabled":False,
        "market_moneylines_available":False,
        "games_comparable":len(report),
        "mean_abs_delta_revue_vs_both_fallback_pp":round(sum(shifts)/len(shifts),2) if shifts else None,
        "skipped":skipped,
        "disclaimer":"Conditional Elo input sensitivity only; neither SQL ratings nor missing-team state or market odds in original Clairvoyance are known. Not backtested against original predictions or bookmaker market.",
        "games":report
    }

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--docs",default="docs")
    arg.add_argument("--output",default="docs/mlb-source-elo-gap.json")
    cli=arg.parse_args()
    root=Path(cli.docs)
    def read(name):return json.loads((root/name).read_text(encoding="utf-8"))
    result=analyze(read("multisports-latest.json"),read("multisports-history.json"),
                   datetime.now(timezone.utc))
    dest=Path(cli.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("MLB conditional source fallback scenarios:",result["games_comparable"],
          "out of",len(result["games"])+sum(result["skipped"].values()),
          "fixtures; no source SQL comparison and no bets.")

if __name__=="__main__":main()
