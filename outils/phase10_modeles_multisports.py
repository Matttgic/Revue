"""Phase 10: forward-only independent multisport research predictions.

NBA: prior-year ESPN standings and derived team Elo (no current regular season).
MLB: Revue's replayed ESPN-final Elo (NOT Clairvoyance private SQL).
Football: correlation-aware research pool of independent Revue score and
ESPN-shot-only advanced models (NOT licensed Opta xG).
NHL: already has independent models, do not manufacture duplicate signals.

No bookmaker EV, actual stakes, retrospective predictions or API calls.
"""
from __future__ import annotations
import argparse,json,math
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.match_center_revue import instant,compatible,valid_predictions,game_key

VERSION="revue_phase10_multisport_model_candidates_v1"
STATUS="shadow_research_only_unvalidated"
LEAD=timedelta(minutes=20)
MAX_AGE=timedelta(hours=72)
FOOTBALL={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL"}
NBA_ABBR={
 "Hawks":"ATL","Celtics":"BOS","Nets":"BKN","Hornets":"CHA",
 "Bulls":"CHI","Cavaliers":"CLE","Mavericks":"DAL","Nuggets":"DEN",
 "Pistons":"DET","Warriors":"GS","Rockets":"HOU","Pacers":"IND",
 "Clippers":"LAC","Lakers":"LAL","Grizzlies":"MEM","Heat":"MIA",
 "Bucks":"MIL","Timberwolves":"MIN","Pelicans":"NO","Knicks":"NY",
 "Thunder":"OKC","Magic":"ORL","76ers":"PHI","Suns":"PHX",
 "Trail Blazers":"POR","Kings":"SAC","Spurs":"SA","Raptors":"TOR",
 "Jazz":"UTAH","Wizards":"WSH"
}

def sane(n):
 return type(n) in (int,float) and math.isfinite(n)

def before(doc,now,kickoff,maximum=MAX_AGE):
 try:
  observed=instant(doc["generated_at_utc"])
  return now-maximum<=observed<=now and observed<=kickoff-LEAD
 except (KeyError,ValueError,TypeError):return False

def probability(n):
 return sane(n) and 0<n<1

def two_way(p):
 return (isinstance(p,dict) and probability(p.get("home_win"))
  and probability(p.get("away_win")) and
  abs(p["home_win"]+p["away_win"]-1)<.005)

def three_way(p):
 return (isinstance(p,dict) and all(probability(p.get(k)) for k in
  ("home_win_90","draw_90","away_win_90")) and
  abs(sum(p[k] for k in ("home_win_90","draw_90","away_win_90"))-1)<.005)

def exact_fixture(source,base):
 return (str(source.get("event_id"))==str(base.get("event_id")) and
         compatible(base,source))

def make_probability(ph):
 if not probability(ph):raise ValueError("Invalid home win")
 p=round(ph,6)
 return {"home_win":p,"away_win":round(1-p,6)}

def candidate(event,code,ph,ingredients,inputs,model_type="2way"):
 if model_type=="2way":
  outcomes=make_probability(ph)
 else:
  outcomes=ph
  if not three_way(outcomes):raise ValueError("Invalid 3way")
 return {"event_id":str(event["event_id"]),"league":event["league"],
  "home":event["home"],"away":event["away"],"start_utc":event["start_utc"],
  "model_id":code,"status":STATUS,"probabilities":outcomes,
  "calibrated":False,"source_sql_parity":False,"bookable_price_verified":False,
  "EV":None,"betting_recommendation":None,
  "inputs_observed_utc":dict(inputs),"method":ingredients}

def index_games(doc,rows,now):
 if not isinstance(doc,dict) or not isinstance(rows,list):return {}
 index={}
 for raw in rows:
  try:
   league=str(raw["league"]);key=game_key(league,raw["event_id"])
   if key in index:raise ValueError("Repeated source fixture: "+key)
   if not raw.get("home") or not raw.get("away") or raw["home"]==raw["away"]:
    raise ValueError("Missing team identity")
   kick=instant(raw["start_utc"])
   if not before(doc,now,kick):continue
   index[key]=raw
  except (KeyError,TypeError,ValueError) as exc:
   if "Repeated source fixture" in str(exc):raise
 return index

def nba_candidates(e,prior,advanced,now):
 if e["league"]!="NBA" or not before(prior,now,instant(e["start_utc"])):
  return [],"nba_prior_unavailable"
 prior_year=prior.get("previous_season_end_year")
 if (prior.get("status")!="shadow_nba_prior_only" or
     type(prior_year) is not int or not 2020<=prior_year<=2100):
  return [],"nba_prior_wrong_season"
 matches=[m for m in prior.get("matches") or [] if str(m.get("event_id"))==e["event_id"]]
 if len(matches)!=1 or not exact_fixture(matches[0],e):
  return [],"nba_no_matching_prior_fixture"
 m=matches[0]
 if not two_way(m.get("probabilities")) or m.get("status")!="shadow_prior_not_calibrated":
  return [],"nba_no_safe_prior_probability"
 p=m["probabilities"]["home_win"]
 inputs={"previous_standings":prior["generated_at_utc"]}
 candidates=[candidate(e,"revue_nba_espn_previous_standings_prior_v1",p,
   "ESPN prior-season standings with early-season regression; no confirmed lineups",inputs)]
 if not before(advanced,now,instant(e["start_utc"])):
  return candidates,"nba_advanced_prior_stale"
 ratings=advanced.get("teamRatings") or {}
 if (advanced.get("status")!="source_formula_observed_regular_season_advanced" or
     advanced.get("season_previous")!=prior_year or
     advanced.get("season_current")!=prior_year+1 or
     advanced.get("teams_with_current_advanced")!=0 or
     advanced.get("teams_with_previous_advanced")!=30 or
     ratings.get("statsMode")!="prior"):
  return candidates,"nba_advanced_prior_mode_unverified"
 hcode,acode=NBA_ABBR.get(e["home"]),NBA_ABBR.get(e["away"])
 elo=advanced.get("eloSeed") or {};teams=ratings.get("teams") or {}
 if (not hcode or not acode or hcode==acode or
     hcode not in teams or acode not in teams or
     not sane(elo.get(hcode)) or not sane(elo.get(acode)) or
     not 1000<=elo[hcode]<=2100 or not 1000<=elo[acode]<=2100):
  return candidates,"nba_no_qualified_roster_mapping"
 # Independent experimental home court +55 Elo, with aggressive
 # regression of preseason ratings; NOT asserted source prediction formula.
 strength=(elo[hcode]-elo[acode]+55)/400
 elo_p=1/(1+10**(-strength))
 regressed=0.58*elo_p+0.42*0.5
 inputs["advanced_previous_season"]=advanced["generated_at_utc"]
 candidates.append(candidate(e,"revue_nba_prior_elo_regressed_v1",regressed,
   "ESPN 2025-26 advanced net-rating-derived Elo; home +55 Elo; 42% neutral regression; no player availability",inputs))
 # Highly correlated models: the blend is NOT an additional independent vote.
 consensus=.55*p+.45*regressed
 candidates.append(candidate(e,"revue_nba_prior_consensus_v1",consensus,
   "Experimental correlated-prior average: standings 55%, regressed Elo 45%; NOT three independent models",inputs))
 return candidates,"nba_prior_both_available"

def mlb_candidate(e,mlb,now):
 if not before(mlb,now,instant(e["start_utc"])):return [],"mlb_source_stale"
 if (mlb.get("status")!="conditional_source_elo_fallback_sensitivity_not_original_reproduction" or
     mlb.get("original_sql_ratings_verified_equal") is not False or
     mlb.get("market_moneylines_available") is not False):
  return [],"mlb_sql_or_market_provenance_invalid"
 try:cutoff=instant(mlb["diagnostic_elo_cutoff_utc"])
 except (KeyError,ValueError,TypeError):return [],"mlb_history_cutoff_unknown"
 if cutoff>now or cutoff>instant(e["start_utc"])-LEAD:
  return [],"mlb_history_cutoff_after_lock"
 matches=[m for m in mlb.get("games") or [] if str(m.get("event_id"))==e["event_id"]]
 if len(matches)!=1 or not exact_fixture(matches[0],e):
  return [],"mlb_no_identical_history_fixture"
 row=matches[0]
 if (row.get("original_sql_elo_inputs_verified_equal") is not False or
     row.get("market_moneylines_available") is not False or
     not sane(row.get("revue_historical_games_home")) or
     not sane(row.get("revue_historical_games_away")) or
     min(row["revue_historical_games_home"],row["revue_historical_games_away"])<15 or
     not probability(row.get("replayed_revue_home_probability"))):
  return [],"mlb_inadequate_elo_history"
 return [candidate(e,"revue_mlb_espn_history_elo_v1",
   row["replayed_revue_home_probability"],
   "Revue Elo replay from verified ESPN finals; pitcher, injuries, private Clairvoyance SQL state absent",
   {"espn_elo_replay":mlb["generated_at_utc"],"last_eligible_history_cutoff_utc":cutoff.isoformat()})],"mlb_history_elo"

def football_candidate(e,base,advanced,now):
 key=game_key(e["league"],e["event_id"])
 if not before(base,now,instant(e["start_utc"])) or not before(advanced,now,instant(e["start_utc"])):
  return [],"football_base_or_shots_snapshot_stale"
 if (advanced.get("status")!="shadow_experimental_never_auto_bet" or
     (advanced.get("licensed_advanced_features") or {}).get("records")!=0 or
     (advanced.get("espn_observed_features") or {}).get("genuine_xg") is not False):
  return [],"football_shots_cannot_be_called_xg"
 base_comp=(base.get("competitions") or {}).get(e["league"]) or {}
 adv_comp=(advanced.get("competitions") or {}).get(e["league"]) or {}
 rb=[x for x in base_comp.get("games") or [] if str(x.get("event_id"))==e["event_id"]]
 ra=[x for x in adv_comp.get("games") or [] if str(x.get("event_id"))==e["event_id"]]
 if len(rb)!=1 or len(ra)!=1 or not exact_fixture(rb[0],e) or not exact_fixture(ra[0],e):
  return [],"football_fixture_mismatch"
 b,a=rb[0],ra[0]
 if (not three_way(b.get("probabilities")) or not three_way(a.get("probabilities")) or
     a.get("xg_used") is not False or a.get("espn_stats_used") is not True or
     a.get("status")!="shadow_non_calibre"):
  return [],"football_model_inputs_missing"
 train_b=b.get("training_games") or {};train_a=a.get("training_games") or {}
 if not all(sane(g.get(x)) and g[x]>=3 for g in (train_b,train_a) for x in ("home","away")):
  return [],"football_training_sample_too_small"
 # Refuse highly discordant models, then logarithmic opinion pool (not
 # independent weights: both may depend on ESPN observations).
 labels=("home_win_90","draw_90","away_win_90")
 pb=b["probabilities"];pa=a["probabilities"]
 distance=sum(abs(pb[k]-pa[k]) for k in labels)/2
 if distance>0.20:return [],"football_models_disagree_abstain"
 raw=[pb[k]**.45*pa[k]**.55 for k in labels]
 norm=sum(raw)
 p1=round(raw[0]/norm,6);p2=round(raw[1]/norm,6)
 pred={"home_win_90":p1,"draw_90":p2,"away_win_90":round(1-p1-p2,6)}
 if probability(pb.get("over_2_5")) and probability(pa.get("over_2_5")):
  pred["over_2_5"]=round(.45*pb["over_2_5"]+.55*pa["over_2_5"],6)
 result=candidate(e,"revue_football_espn_shots_log_pool_v1",pred,
   "Correlated ESPN score/shot feature models, geometric pool 45/55, requires >=3 team-history matches; not Opta xG",
   {"multisports":base["generated_at_utc"],"espn_shots_shadow":advanced["generated_at_utc"]},
   "3way")
 result["model_disagreement_tv"]=round(distance,5)
 return [result],"football_correlated_research_pool"

def build(center,base,nba,ratings,mlb,advanced,now):
 if now.tzinfo is None:raise ValueError("Timezone-aware UTC required")
 now=now.astimezone(timezone.utc)
 if (center.get("status")!="experimental_revue_match_center" or
     center.get("real_bets_enabled") is not False or
     center.get("bookmaker_prices_are_live") is not False or
     center.get("validated_value_bets")!=0):
  raise ValueError("Untrusted input market center")
 if not before(center,now,now+timedelta(days=3)):
  raise ValueError("Previous fixture inventory stale")
 results=[];states=Counter();sports=Counter();seen=set()
 for e in center.get("events") or []:
  league=e.get("league")
  if league not in {"NBA","MLB"} | FOOTBALL:continue
  key=game_key(league,e.get("event_id"))
  if key in seen:raise ValueError("Duplicate fixture: "+key)
  seen.add(key)
  try:
   kickoff=instant(e["start_utc"])
   if not now<=kickoff-LEAD:
    states["not_pregame_20m"]+=1;continue
   if league=="NBA":c,why=nba_candidates(e,nba,ratings,now)
   elif league=="MLB":c,why=mlb_candidate(e,mlb,now)
   else:c,why=football_candidate(e,base,advanced,now)
   states[why]+=1
   for pick in c:
    if not valid_predictions(pick["probabilities"]):
     raise ValueError("Invalid output probability vector")
    results.append(pick);sports[league]+=1
  except (KeyError,TypeError,ValueError):
   states["malformed_or_untrusted_event"]+=1
 return {"version":VERSION,"status":STATUS,"generated_at_utc":now.isoformat(),
  "fixture_inventory_source_at_utc":center["generated_at_utc"],
  "models":sorted(results,key=lambda x:(x["start_utc"],x["league"],x["event_id"],x["model_id"])),
  "metrics":{"candidates":len(results),"events_covered":len({(x["league"],x["event_id"]) for x in results}),
             "models_by_league":dict(sports),"decisions":dict(states)},
  "calibrated":False,"original_clairvoyance_sql_identical":False,
  "real_bets_enabled":False,"prices_are_currently_bookable":False,
  "verified_positive_EV":0,"requires_point_in_time_settlement":True,
  "no_historical_backfill":True,"paid_api_calls":0,"CFB_excluded":True,
  "notes":"Research only: previous-season NBA prior, independent MLB historical Elo, ESPN shots/score forecast pool. Never conflate correlated forecasts with independent evidence, pricing EV or exact Clairvoyance outputs."}

def main():
 cli=argparse.ArgumentParser()
 cli.add_argument("--root",default="docs")
 cli.add_argument("--output",default="docs/phase10-modeles-multisports-latest.json")
 args=cli.parse_args();root=Path(args.root)
 names=("match-center-latest.json","multisports-latest.json","nba-prior-shadow.json",
        "clairvoyance-nba-advanced-ratings.json","mlb-source-elo-gap.json",
        "football-advanced-shadow.json")
 docs=[json.loads((root/name).read_text(encoding="utf8")) for name in names]
 result=build(*docs,datetime.now(timezone.utc))
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
 print("Phase10 research models:",result["metrics"],"; no verified EV or wagers.")
if __name__=="__main__":main()
