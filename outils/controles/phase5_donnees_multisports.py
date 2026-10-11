"""Phase 5: validate independent NBA, NHL, MLB and football observations.

No paid calls, third-party redistribution, fictitious xG, historic bets or
claims that Clairvoyance's inaccessible deployed SQL inputs were reproduced.
"""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

VERSION="revue_phase5_source_gate_v1"
LEAGUES=("PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL")

def clock(v):
    if not isinstance(v,str):raise ValueError("Missing timestamp")
    try:d=datetime.fromisoformat(v.replace("Z","+00:00"))
    except ValueError as e:raise ValueError("Invalid timestamp") from e
    if d.tzinfo is None:raise ValueError("Missing source timezone")
    return d.astimezone(timezone.utc)

def number(v,lo,hi):
    return type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi

def stamped(x,now):
    t=clock(x["generated_at_utc"])
    if t>now+timedelta(minutes=2):raise ValueError("Future provider observation")
    return {"observed_at_utc":t.isoformat(),
            "fresh_36h":now-t<=timedelta(hours=36)}

def nba(x,now):
    if x.get("status")!="source_formula_observed_regular_season_advanced" or x.get("source_verified_espn_parser") is not True:
        raise ValueError("NBA advanced source unverified")
    obs=stamped(x,now)
    t=x["teamRatings"];teams=t["teams"]
    if not isinstance(teams,dict) or len(teams)>30:raise ValueError("NBA team coverage invalid")
    prior=sum(number((v.get("prior") or {}).get("ortg"),50,200) and
              number((v.get("prior") or {}).get("drtg"),50,200) for v in teams.values())
    current=sum(number((v.get("current") or {}).get("netRtg"),-80,80) for v in teams.values())
    if prior!=x["teams_with_previous_advanced"] or current!=x["teams_with_current_advanced"]:
        raise ValueError("NBA counts contradict actual team data")
    old,new=x["season_previous"],x["season_current"]
    if type(old) is not int or type(new) is not int or new!=old+1:
        raise ValueError("NBA season rollover invalid")
    if current==0 and t.get("statsSeasonUsed")!=old:
        raise ValueError("Preseason fabricated as current regular-season data")
    return {"source":"ESPN verified regular-season advanced by-team parser",**obs,
            "previous_season":old,"current_season":new,
            "prior_advanced_teams":prior,"current_advanced_teams":current,
            "mode":"current_regular" if current>=28 else "prior_only",
            "preseason_used_as_regular":False,
            "same_original_sql_or_injury_inputs_verified":False,
            "blockers":["Current regular-season advanced inputs missing or incomplete"] if current<28 else []}

def nhl(mp,official,shadow,now):
    a,b,c=stamped(mp,now),stamped(official,now),stamped(shadow,now)
    season=mp.get("current_season")
    if (mp.get("source")!="MoneyPuck.com" or mp.get("is_live") is not False or
        mp.get("status",{}).get(season,{}).get("status")!="available" or
        official.get("source")!="api.nhle.com/stats/rest/en" or
        official.get("status")!="verified_nhl_official_stats_snapshot" or
        official.get("season")!=season.replace("-","") or official.get("game_type_id")!=2 or
        shadow.get("status")!="backend_style_input_scenario_not_original_model_parity" or
        shadow.get("original_sql_ratings_available") is not False or
        shadow.get("has_verified_original_predictions") is not False or
        shadow.get("real_bets_enabled") is not False):
        raise ValueError("NHL wrong source, game type or original parity claim")
    shares={}
    for row in mp["seasons"][season]:
        sit=row.get("situation")
        if sit not in ("all","5on5"):continue
        team=row.get("team");key=(team,sit)
        if key in shares or not isinstance(team,str) or not number(row.get("xg_share"),0,1):
            raise ValueError("NHL duplicate team or bad xG rate")
        shares[key]=row["xg_share"]
    all_teams={t for t,s in shares if s=="all"}
    five={t for t,s in shares if s=="5on5"}
    by_team=defaultdict(list)
    for g in official["goalies"]:
        if g.get("season")!=official["season"] or g.get("game_type_id")!=2:
            raise ValueError("NHL mixed goalie season/type")
        n=g.get("games_played")
        if type(n) is not int or n<0:raise ValueError("NHL invalid goalie sample")
        by_team[g["team_abbrev"]].append(g)
    unique=set()
    for team,rows in by_team.items():
        played=max(r["games_played"] for r in rows)
        leaders=[r for r in rows if r["games_played"]==played]
        if played and len(leaders)==1 and number(leaders[0].get("overall_save_pct"),0,1):
            unique.add(team)
    supported=all_teams & five & unique
    pregame=sum(
        row.get("home") in supported and row.get("away") in supported and
        row.get("source_observed_by_frozen_model_time") is True and
        number(row.get("raw_fraction_home_probability"),0,1) and
        all(clock(doc["generated_at_utc"])<=clock(row["kickoff_utc"])-timedelta(minutes=20)
            for doc in (mp,official,shadow))
        for row in shadow.get("games") or [] if isinstance(row,dict))
    return {"source":"MoneyPuck observations + NHL official regular-season goalie summaries",**a,
            "official_goalies_observed_at_utc":b["observed_at_utc"],
            "source_style_observed_at_utc":c["observed_at_utc"],
            "season":season,"game_type_id":2,"all_situation_teams":len(all_teams),
            "five_on_five_teams":len(five),"unique_most_played_goalie_teams":len(unique),
            "teams_with_both_situations_and_goalie":len(supported),
            "historical_pregame_compatible_scenarios":pregame,
            "backend_xg_situation":"all",
            "frontend_shadow_xg_situation":"5on5",
            "original_source_public_default_game_type":3,
            "original_source_public_default_season":"20252026",
            "original_deployment_configuration_verified":False,
            "starting_goalies_confirmed":False,"sql_elo_verified":False,
            "money_puck_terms":"personal non-commercial with attribution; further use needs permission",
            "blockers":["Source deployed season/game type and SQL Elo inaccessible",
                        "Most-played goalie is not tonight's confirmed starter",
                        "MoneyPuck redistribution/commercial use not authorized by source snapshot"]}

def mlb(x,now):
    if (x.get("status")!="conditional_source_elo_fallback_sensitivity_not_original_reproduction" or
        x.get("original_sql_ratings_verified_equal") is not False or
        x.get("historical_sql_coverage_proven_identical") is not False or
        x.get("market_moneylines_available") is not False):
        raise ValueError("MLB falsely claims original Elo or odds")
    a=stamped(x,now)
    h=x.get("diagnostic_revue_completed_espn_games")
    n=x.get("games_comparable")
    if type(h) is not int or h<0 or type(n) is not int or n!=len(x.get("games") or []):
        raise ValueError("MLB historical count contradiction")
    for g in x.get("games") or []:
        if (g.get("original_sql_elo_inputs_verified_equal") is not False or
            not number(g.get("replayed_revue_home_probability"),0,1)):
            raise ValueError("MLB bad model input or false parity")
    return {"source":"ESPN independent historic Elo replay, original Elo=1500 fallback arithmetic",**a,
            "historical_espn_finals":h,"conditional_fixtures":n,
            "original_sql_ratings_verified":False,
            "history_is_pregame_locked_bets":False,
            "market_moneylines_verified":False,
            "blockers":["Original SQL ratings, settled-pick Elo update ordering and prices unavailable"]}

def football(features,shadow,now):
    a,b=stamped(features,now),stamped(shadow,now)
    if (features.get("status")!="real_boxscore_derived_not_opta" or
        features.get("xg_available") is not False or
        features.get("opta_available") is not False or
        shadow.get("status")!="shadow_experimental_never_auto_bet" or
        shadow.get("licensed_advanced_features",{}).get("status")!="no_authorized_source" or
        shadow.get("espn_observed_features",{}).get("genuine_xg") is not False):
        raise ValueError("Unlicensed xG was substituted for ESPN boxscores")
    teams=features["teams"]
    if not isinstance(teams,dict):raise ValueError("Missing teams")
    for row in teams.values():
        if (row.get("type")!="observed_shots_not_xg" or
            not number(row.get("shots_per_game"),0,100) or
            not number(row.get("sot_per_game"),0,row["shots_per_game"])):
            raise ValueError("Inconsistent football shots source")
    if shadow["espn_observed_features"]["teams"]!=len(teams):
        raise ValueError("Football counts contradict team inputs")
    byleague={}
    with_boxscores=0;total=0
    for league in LEAGUES:
        fixtures=(shadow.get("competitions",{}).get(league) or {}).get("games") or []
        usable=0
        for fixture in fixtures:
            if fixture.get("xg_used") is not False:
                raise ValueError("Football xG claimed without authorized source")
            if fixture.get("espn_stats_used") is True and fixture.get("status")=="shadow_non_calibre":
                usable+=1
        byleague[league]={"shadow_games":len(fixtures),"with_ESPN_boxscore_data":usable}
        total+=len(fixtures);with_boxscores+=usable
    return {"source":"ESPN soccer observed shot counts, NOT Opta xG",**a,
            "football_shadow_observed_at_utc":b["observed_at_utc"],
            "ESPN_observed_teams":len(teams),
            "shadow_fixtures":total,"with_ESPN_boxscores":with_boxscores,
            "authorized_Opta_xG_fixtures":0,"licensed_xG_source_available":False,
            "per_league":byleague,
            "blockers":["Authorized Opta xG/xGA source not connected",
                        "ESPN shots/possession cannot be relabelled xG"]}

def build(docs,now):
    if now.tzinfo is None:raise ValueError("Aware UTC clock required")
    now=now.astimezone(timezone.utc)
    values={"NBA":nba(docs["nba"],now),
            "NHL":nhl(docs["mp"],docs["goalies"],docs["nhl"],now),
            "MLB":mlb(docs["mlb"],now),
            "FOOTBALL":football(docs["football"],docs["football_shadow"],now)}
    observed=sum((values["NBA"]["prior_advanced_teams"]>0,
                  values["NHL"]["all_situation_teams"]>0,
                  values["MLB"]["historical_espn_finals"]>0,
                  values["FOOTBALL"]["ESPN_observed_teams"]>0))
    return {"version":VERSION,"generated_at_utc":now.isoformat(),
            "status":"independent_sports_inputs_observed_not_original_data_parity",
            "four_sports_with_observed_data":observed,
            "sports_with_identical_original_deployed_inputs_verified":0,
            "sports":values,"original_sql_access_verified":False,
            "same_clairvoyance_published_predictions_verified":False,
            "Opta_xG_authorized_and_ingested":False,
            "money_puck_data_sold_or_redistributed":False,
            "CFB_excluded":True,"real_bets_enabled":False,"paid_api_calls":0,
            "frozen_pregame_history_unchanged":True,
            "note":"Separate prior/current NBA, MoneyPuck all/5on5 and NHL goalie seasons, historical MLB Elo from source SQL, and football ESPN shots from licensed xG. No original deployed data parity claim."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--docs",default="docs")
    p.add_argument("--out",default="docs/phase5-sources-latest.json")
    opts=p.parse_args()
    root=Path(opts.docs)
    files={"nba":"clairvoyance-nba-advanced-ratings.json",
           "mp":"moneypuck-nhl-latest.json",
           "goalies":"nhl-official-stats-latest.json",
           "nhl":"nhl-backend-source-style-latest.json",
           "mlb":"mlb-source-elo-gap.json",
           "football":"football-espn-team-features.json",
           "football_shadow":"football-advanced-shadow.json"}
    docs={k:json.loads((root/v).read_text(encoding="utf-8")) for k,v in files.items()}
    result=build(docs,datetime.now(timezone.utc))
    target=Path(opts.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Phase 5: observations",result["four_sports_with_observed_data"],
          "/4; original deployed input parity 0/4 verified. No wagers.")

if __name__=="__main__":main()
