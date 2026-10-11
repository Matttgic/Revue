"""Phase 11: source provenance, goalie evidence and bookmaker-rule quarantine.

Audit existing, verified source snapshots ONLY. Never convert ESPN probable
goalies to starting lineups, ESPN shots to Opta xG, or an unknown NHL
regulation/overtime price into a verified wager. No paid provider requests.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path

VERSION="revue_phase11_source_quality_v1"
MAX_AGE_H={"goalies":12,"nba":48,"mlb":48,"football":48,"center":12,"picks":24}
INPUT_FILES={
 "center":"match-center-latest.json","goalies":"nhl-espn-goalies-latest.json",
 "nba":"clairvoyance-nba-advanced-ratings.json","mlb":"mlb-source-elo-gap.json",
 "football":"football-advanced-shadow.json",
 "picks":"picks-center-latest.json","paper_ledger":"engine-v2-ledger.json",
 "phase5":"phase5-sources-latest.json","models":"phase10-modeles-performance.json",
}
SOCCER={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL"}

def utc(v):
 if not isinstance(v,str):raise ValueError("Missing datetime")
 t=datetime.fromisoformat(v.replace("Z","+00:00"))
 if t.tzinfo is None:raise ValueError("Datetime without timezone")
 return t.astimezone(timezone.utc)

def age(doc,now,hours):
 try:
  t=utc(doc["generated_at_utc"])
  n=(now-t).total_seconds()/3600
  return {"age_hours":round(n,2),
   "status":"future" if n<-.05 else "stale" if n>hours else "recent",
   "max_age_hours":hours}
 except (ValueError,TypeError,KeyError,OverflowError):
  return {"age_hours":None,"status":"unknown","max_age_hours":hours}

def goalie_evidence(center,goalies,now):
 issues=[];by_event={};provenance=goalies.get("status")=="espn_probable_goalies_observed_not_part_of_model"
 provenance=provenance and goalies.get("used_in_prediction_model") is False and goalies.get("real_bets_enabled") is False
 fresh=age(goalies,now,MAX_AGE_H["goalies"])["status"]=="recent"
 source_ok=bool(provenance and fresh and isinstance(goalies.get("rows"),list))
 seen=set()
 if source_ok:
  for row in goalies["rows"]:
   if not isinstance(row,dict):
    issues.append("invalid_goalie_row");continue
   ident=str(row.get("event_id") or "")
   if not ident.isdigit() or ident in seen:
    issues.append("duplicate_or_invalid_official_goalie_event_id");continue
   seen.add(ident);by_event[ident]=row
 matched,confirmed,projected,complete=0,0,0,0
 fixtures=[]
 for e in center.get("events",[]):
  if e.get("league")!="NHL":continue
  key=str(e.get("event_id") or "")
  obs=by_event.get(key)
  statuses={"home":None,"away":None}
  evidence=None
  if obs is not None:
   try:
    kick=utc(e["start_utc"])
    seen_at=utc(obs["observed_at_utc"])
    fixture_ok=(e["home"]==obs["home"] and e["away"]==obs["away"] and
      kick==utc(obs["start_utc"]) and
      seen_at<=now and seen_at<kick and
      age({"generated_at_utc":obs["observed_at_utc"]},now,12)["status"]=="recent" and
      obs.get("used_in_model_probabilities") is False and
      obs.get("injuries_verified") is False and
      obs.get("sportsbook_prices_verified") is False)
    if fixture_ok:
     names=set()
     for side in ("home","away"):
      g=obs.get(side+"_goalie")
      if g is None:continue
      if (not isinstance(g,dict) or not isinstance(g.get("name"),str) or
          not g["name"].strip() or g.get("status") not in ("confirmed","projected") or
          g.get("source")!="ESPN probableStartingGoalie"):
       fixture_ok=False;break
      if g["name"].strip() in names:fixture_ok=False;break
      names.add(g["name"].strip())
      statuses[side]={"name":g["name"].strip(),"status":g["status"]}
    if fixture_ok:
     matched+=1
     evidence=seen_at.isoformat()
     confirmed+=sum(g is not None and g["status"]=="confirmed" for g in statuses.values())
     projected+=sum(g is not None and g["status"]=="projected" for g in statuses.values())
     if all(g and g["status"]=="confirmed" for g in statuses.values()):complete+=1
    else:
     statuses={"home":None,"away":None}
     issues.append("goalie_fixture_mismatch_or_future_observation:"+key)
   except (KeyError,ValueError,TypeError):
    issues.append("goalie_malformed_or_missing_timestamp:"+key)
  fixtures.append({"league":"NHL","event_id":key,"home":e.get("home"),"away":e.get("away"),
    "source_observed_utc":evidence,"home_goalie":statuses["home"],"away_goalie":statuses["away"],
    "both_reported_confirmed":all(g and g["status"]=="confirmed" for g in statuses.values()),
    "source_ready_for_lineup_dependent_models":False,
    "probabilities_modified":False,
    "note":"ESPN status is observed provider wording, not a guarantee of actual starting lineup."})
 return {"source_report_valid":source_ok,"source_age":age(goalies,now,12),
    "future_nhl_fixtures":len(fixtures),"matched_upcoming_fixtures":matched,
    "goalie_sides_confirmed_by_espn":confirmed,"goalie_sides_projected_by_espn":projected,
    "fixtures_with_both_espn_confirmed":complete,"actual_game_starts_independently_verified":0,
    "used_in_prediction":False,"fixtures":fixtures,"issues":issues}

def quarantined(picks,ledger):
 bets=ledger.get("bets") if ledger.get("version")==1 else None
 if not isinstance(bets,list):raise ValueError("Unknown paper source ledger")
 index={}
 for item in bets:
  if not isinstance(item,dict):continue
  k=item.get("id")
  if k in index:raise ValueError("Duplicate paper id in original ledger")
  index[k]=item
 rec=picks.get("paper_records")
 if not isinstance(rec,list):raise ValueError("No auditable paper records")
 found=[];invalid=[]
 for r in rec:
  if not isinstance(r,dict) or r.get("status")!="unverified":continue
  base=index.get(r.get("id"))
  if (not base or base.get("status")!="market_rule_unverified" or
      base.get("league")!=r.get("league") or
      str(base.get("event_id"))!=str(r.get("event_id")) or
      base.get("market")!=r.get("market") or
      base.get("side")!=r.get("side")):
   invalid.append(r.get("id"));continue
  found.append({"id":r["id"],"league":r["league"],"event_id":str(r["event_id"]),
    "market":r["market"],"reason_code":"market_period_and_overtime_terms_unknown",
    "source_status":"market_rule_unverified","resolution":"quarantined_no_retroactive_settlement",
    "included_in_settled_roi":False,"can_auto_promote_to_win_loss":False})
 s=picks.get("paper_summary") or {}
 if len(found)+len(invalid)!=s.get("excluded"):
  raise ValueError("Excluded count differs from separate paper ledger")
 if invalid:raise ValueError("Unverified paper/source ledger disagreement")
 return found

def evaluate(data,now):
 if now.tzinfo is None:raise ValueError("Timezone aware audit clock required")
 now=now.astimezone(timezone.utc)
 center=data["center"];picks=data["picks"];goalies=data["goalies"]
 if (center.get("status")!="experimental_revue_match_center" or
     center.get("real_bets_enabled") is not False or
     center.get("bookmaker_prices_are_live") is not False or
     center.get("validated_value_bets")!=0):
  raise ValueError("Match center provenance invalid")
 if (picks.get("status")!="revue_independent_picks_hub_static_research_paper_only" or
     picks.get("real_bets_enabled") is not False or
     picks.get("verified_real_ev") is not False):
  raise ValueError("Paper picks provenance invalid")
 exclusions=quarantined(picks,data["paper_ledger"])
 hockey=goalie_evidence(center,goalies,now)
 nba=data["nba"];mlb=data["mlb"];football=data["football"]
 prior=(nba.get("status")=="source_formula_observed_regular_season_advanced" and
       nba.get("source_verified_espn_parser") is True and
       nba.get("teams_with_previous_advanced")==30)
 current=(prior and nba.get("teams_with_current_advanced")==30 and
          (nba.get("teamRatings") or {}).get("statsMode")=="current" and
          age(nba,now,48)["status"]=="recent")
 mlb_replay=mlb.get("status")=="conditional_source_elo_fallback_sensitivity_not_original_reproduction"
 mlb_replay=mlb_replay and mlb.get("original_sql_ratings_verified_equal") is False
 official_pitchers=data.get("mlb_pitchers") or {}
 pitcher_report_valid=(
  official_pitchers.get("status")=="official_MLB_probable_pitchers_observed_not_confirmed"
  and official_pitchers.get("model_recomputed") is False
  and official_pitchers.get("real_bets_enabled") is False
  and official_pitchers.get("confirmed_starting_pitchers")==0
  and age(official_pitchers,now,12)["status"]=="recent"
  and isinstance(official_pitchers.get("rows"),list))
 # An official probable pitcher NEVER becomes a confirmed starting pitcher.
 probable_count=official_pitchers.get("probable_pitcher_sides",0) if pitcher_report_valid else 0
 shots=(football.get("status")=="shadow_experimental_never_auto_bet" and
       (football.get("espn_observed_features") or {}).get("genuine_xg") is False)
 licensed_xg=(football.get("licensed_advanced_features") or {}).get("records",0)>0
 if licensed_xg and shots:raise ValueError("Inconsistent football xG provenance")
 categories={
  "NBA":{"previous_regular_season_teams":nba.get("teams_with_previous_advanced") if prior else 0,
     "current_regular_season_teams":nba.get("teams_with_current_advanced",0),
     "current_advanced_ready_for_models":bool(current),
     "forecast_mode":"current_verified" if current else "prior_only_or_unavailable",
     "missing":["actual_current_regular_season_advanced_data"] if not current else [],
     "original_sql_parity_proven":False},
  "NHL":{"goalie_observations":hockey["matched_upcoming_fixtures"],
     "both_sides_confirmed_by_ESPN":hockey["fixtures_with_both_espn_confirmed"],
     "actual_starters_verified":False,
     "missing":["actual_starting_goalies_independently_confirmed","private_original_elo_sql"],
     "original_sql_parity_proven":False},
  "MLB":{"ESPN_completed_games_used_for_diagnostic":mlb.get("diagnostic_revue_completed_espn_games") if mlb_replay else 0,
     "pitchers_verified_from_current_feed":False,
     "official_probable_pitcher_feed_available":pitcher_report_valid,
     "official_probable_pitcher_sides_observed":probable_count,
     "official_probable_pitcher_source_status":official_pitchers.get("status","not_requested"),
     "original_elo_sql_verified":False,
     "missing":["official_pregame_starting_pitcher_feed","private_original_elo_sql"],
     "original_sql_parity_proven":False},
  "FOOTBALL":{"ESPN_shots_available":bool(shots),
     "licensed_xg_available":bool(licensed_xg),
     "proprietary_Opta_xg_verified":False,
     "missing":["authorized_xg_xga_with_point_in_time_rights"] if not licensed_xg else [],
     "original_sql_parity_proven":False}
 }
 freshness={k:age(data[k],now,limit) for k,limit in MAX_AGE_H.items()}
 alerts=[f"{k}:source_{v['status']}" for k,v in freshness.items() if v["status"]!="recent"]
 alerts+=["paper_unverified_quarantined:"+str(len(exclusions))] if exclusions else []
 alerts+=hockey["issues"]
 perf=data["models"]
 return {"version":VERSION,"generated_at_utc":now.isoformat(),
  "status":"input_gates_verified_missing_original_model_sources",
  "sports":categories,"NHL_espn_observations":hockey,
  "paper_market_quarantine":{"total":len(exclusions),
    "all_nhl":all(x["league"]=="NHL" for x in exclusions),
    "original_ledger_unchanged":True,"historical_prices_are_not_bettable":True,
    "records":exclusions,"not_in_real_or_paper_settled_roi":True},
  "phase10_validation":{"locked_predictions":perf.get("total_locked"),
      "officially_settled":perf.get("settled"),
      "models_calibrated":False,
      "prospective_evidence_not_historical_backfill":True},
  "freshness":freshness,"warnings":sorted(set(alerts)),
  "real_bets_enabled":False,"verified_EV_opportunities":0,
  "model_probabilities_modified":False,"paper_ledger_modified":False,
  "paid_api_calls":0,"CFB_excluded":True,
  "source_parity_100_percent":False,
  "note":"Existing public source audit; a report of missing inputs is not equivalent to filling them. All uncertain NHL market rules remain excluded until original bookmaker market contract is verified before future selection."}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",default="docs")
 p.add_argument("--output",default="docs/phase11-source-quality-latest.json")
 a=p.parse_args();root=Path(a.root)
 data={key:json.loads((root/name).read_text(encoding="utf8")) for key,name in INPUT_FILES.items()}
 pitcher_path=root/"mlb-official-probable-pitchers-latest.json"
 if pitcher_path.exists():
  try:data["mlb_pitchers"]=json.loads(pitcher_path.read_text(encoding="utf8"))
  except (ValueError,OSError):data["mlb_pitchers"]={"status":"invalid_source"}
 result=evaluate(data,datetime.now(timezone.utc))
 dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
 print("Phase11",len(result["paper_market_quarantine"]["records"]),"NHL markets quarantined;",
       result["NHL_espn_observations"]["matched_upcoming_fixtures"],"goalie fixtures;",
       "NBA current",result["sports"]["NBA"]["current_advanced_ready_for_models"])
if __name__=="__main__":main()
