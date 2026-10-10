"""Phase 10: true forward-only model-specific locks and ESPN final evaluations.

Independent of earlier immutable multisports ledgers: new NBA/MLB/football
models are locked independently before kickoff, never added to old locks.
Settlement requires unambiguous official final and identical teams/kickoff.
No actual bet, stake, prices, CLV, Opta xG, or profitability inference.
"""
from __future__ import annotations
import argparse,json,math
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.match_center_revue import instant,compatible,valid_predictions,game_key

VERSION="revue_phase10_forward_ledger_v1"
SOURCE_VERSION="revue_phase10_multisport_model_candidates_v1"
SOCCER_REG={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"}
SOCCER_ALL=SOCCER_REG|{"MLS","UCL"}
LEAD=timedelta(minutes=20)
LOCK_MAX_AGE=timedelta(hours=3)
SCORE_MAX_AGE=timedelta(hours=6)
EXPECTED_MODELS={
 "revue_nba_espn_previous_standings_prior_v1":"NBA",
 "revue_nba_prior_elo_regressed_v1":"NBA",
 "revue_nba_prior_consensus_v1":"NBA",
 "revue_mlb_espn_history_elo_v1":"MLB",
 "revue_football_espn_shots_log_pool_v1":"soccer",
}

def fresh_report(report,now):
 try:return (report.get("version")==SOURCE_VERSION and
   report.get("status")=="shadow_research_only_unvalidated" and
   report.get("real_bets_enabled") is False and
   report.get("prices_are_currently_bookable") is False and
   report.get("calibrated") is False and
   report.get("verified_positive_EV")==0 and
   report.get("no_historical_backfill") is True and
   now-LOCK_MAX_AGE<=instant(report["generated_at_utc"])<=now and
   isinstance(report.get("models"),list))
 except (ValueError,KeyError,TypeError):return False

def empty():return {"version":VERSION,"since_utc":None,"records":{}}

def vector(prob,league):
 fields=("home_win_90","draw_90","away_win_90") if league in SOCCER_ALL else ("home_win","away_win")
 if not isinstance(prob,dict) or not valid_predictions(prob):return None
 p=[prob.get(k) for k in fields]
 if any(type(x) not in (float,int) or not math.isfinite(x) or not 0<x<1 for x in p):
  return None
 if abs(sum(p)-1)>.005:return None
 return p

def lock(current,model_report,now):
 if now.tzinfo is None:raise ValueError("Aware clock required")
 if current is None:current=empty()
 if current.get("version")!=VERSION or not isinstance(current.get("records"),dict):
  raise ValueError("Unknown locked-record format")
 output=json.loads(json.dumps(current))
 if not fresh_report(model_report,now):return output
 generated=instant(model_report["generated_at_utc"])
 seen=set()
 for c in model_report["models"]:
  if not isinstance(c,dict):continue
  code=c.get("model_id");league=c.get("league")
  expected=EXPECTED_MODELS.get(code)
  if expected is None or (league!="NBA" if expected=="NBA" else
                           league!="MLB" if expected=="MLB" else league not in SOCCER_ALL):
   continue
  try:
   event_id=str(c["event_id"])
   if not event_id.isdecimal():continue
   key=game_key(league,event_id)+":"+code
   if key in seen:raise ValueError("Duplicate source model/event key")
   seen.add(key)
   if key in output["records"]:continue
   kick=instant(c["start_utc"])
   if (now>kick-LEAD or generated>kick-LEAD or
       not isinstance(c.get("home"),str) or not c["home"] or
       not isinstance(c.get("away"),str) or not c["away"] or c["home"]==c["away"] or
       c.get("status")!="shadow_research_only_unvalidated" or
       c.get("calibrated") is not False or c.get("source_sql_parity") is not False or
       c.get("bookable_price_verified") is not False or
       c.get("EV") is not None or c.get("betting_recommendation") is not None):
    continue
   prob=vector(c.get("probabilities"),league)
   if prob is None:continue
   times=c.get("inputs_observed_utc")
   if not isinstance(times,dict) or not times:continue
   if not all(instant(v)<=generated and instant(v)<=now for v in times.values()):
    continue
   output["records"][key]={
     "id":key,"event_id":event_id,"league":league,
     "home":c["home"],"away":c["away"],
     "kickoff_utc":kick.isoformat(),"locked_at_utc":now.astimezone(timezone.utc).isoformat(),
     "model_id":code,"market":"90min_1x2" if league in SOCCER_ALL else "full_game_2way",
     "probabilities":prob,"source_model_at_utc":generated.isoformat(),
     "input_observed_at_utc":times,
     "status":"pending","result":None,"scores":None,"resolved_at_utc":None,
     "brier":None,"logloss":None,
     "real_bet":False,"stake_units":0,"outcome_price":None}
  except (KeyError,ValueError,TypeError):
   continue
 if output["since_utc"] is None and output["records"]:
  output["since_utc"]=now.astimezone(timezone.utc).isoformat()
 return output

def score_index(scoreboard,now):
 try:
  observed=instant(scoreboard["generated_at_utc"])
  if (scoreboard.get("status")!="observed_scoreboard_not_streaming" or
      scoreboard.get("scores_are_live_stream") is not False or
      scoreboard.get("pricing_used") is not False or
      not now-SCORE_MAX_AGE<=observed<=now):
   return {}
 except (ValueError,TypeError,KeyError):return {}
 found={}
 for row in scoreboard.get("events") or []:
  if not isinstance(row,dict):continue
  league=row.get("league")
  if league not in (SOCCER_REG|{"NBA","MLB"}):continue
  try:
   if (row.get("state")!="final" or
       row.get("source")!="ESPN scoreboard" or
       row.get("prospective_bet_result") is not False or
       instant(row["observed_at_utc"])!=observed):continue
   kick=instant(row["kickoff_utc"])
   if observed<kick+timedelta(minutes=55):continue
   h,a=row.get("home_score"),row.get("away_score")
   if (type(h) is not int or type(a) is not int or
       not 0<=h<=300 or not 0<=a<=300 or
       (league in {"NBA","MLB"} and h==a)):continue
   key=game_key(league,row["event_id"])
   if key in found:found[key]=None
   else:found[key]=row
  except (ValueError,TypeError,KeyError):continue
 return found

def settle(ledger,scores,now):
 if now.tzinfo is None:raise ValueError("Aware clock required")
 if ledger.get("version")!=VERSION:raise ValueError("Invalid ledger")
 out=json.loads(json.dumps(ledger))
 finals=score_index(scores,now)
 for row in out["records"].values():
  if row.get("status")!="pending":continue
  if row["league"] not in SOCCER_REG|{"NBA","MLB"}:continue
  final=finals.get(game_key(row["league"],row["event_id"]))
  if not isinstance(final,dict) or not compatible(
     {"home":row["home"],"away":row["away"],"start_utc":row["kickoff_utc"]},
     {"home":final["home"],"away":final["away"],"start_utc":final["kickoff_utc"]}):
   continue
  locked=instant(row["locked_at_utc"]);kick=instant(row["kickoff_utc"])
  if not locked<=kick-LEAD:continue
  h,a=final["home_score"],final["away_score"]
  winner=0 if h>a else 2 if row["league"] in SOCCER_REG and h<a else 1 if row["league"] in SOCCER_REG else 1
  p=row["probabilities"]
  if len(p) not in (2,3) or (len(p)==2 and row["league"] in SOCCER_REG):continue
  # Outcome index is 0=home, 1=draw/away (2way), 2=away (3way).
  outcome=winner
  if len(p)==2:outcome=0 if h>a else 1
  brier=(p[0]-1)**2+sum(v*v for v in p[1:]) if outcome==0 else sum(
    (x-1)**2 if i==outcome else x*x for i,x in enumerate(p))
  ll=-math.log(p[outcome])
  row.update({"status":"settled","result":outcome,
              "scores":{"home":h,"away":a},
              "resolved_at_utc":instant(scores["generated_at_utc"]).isoformat(),
              "brier":round(brier,6),"logloss":round(ll,6)})
 return out

def summarize(ledger,now):
 rows=list(ledger["records"].values())
 bymodel=defaultdict(list)
 for row in rows:
  if row["status"]=="settled":bymodel[row["model_id"]].append(row)
 models={}
 for name in EXPECTED_MODELS:
  g=bymodel[name]
  models[name]={"locked":sum(r["model_id"]==name for r in rows),
   "settled":len(g),
   "mean_brier_multiclass_unscaled":round(sum(r["brier"] for r in g)/len(g),6) if g else None,
   "mean_logloss":round(sum(r["logloss"] for r in g)/len(g),6) if g else None,
   "minimum_100_settled_reached":len(g)>=100,
   "calibrated":False,"profitable":False}
 return {"version":VERSION,"generated_at_utc":now.isoformat(),
  "status":"forward_locked_only_no_retroactive_predictions",
  "started_at_utc":ledger["since_utc"],"total_locked":len(rows),
  "pending":sum(r["status"]=="pending" for r in rows),
  "settled":sum(r["status"]=="settled" for r in rows),
  "by_league":{lg:{"locked":sum(r["league"]==lg for r in rows),
                      "settled":sum(r["league"]==lg and r["status"]=="settled" for r in rows)}
               for lg in sorted({r["league"] for r in rows})},
  "models":models,"real_bets_enabled":False,"roi":None,
  "no_historical_backfill":True,"bookmaker_prices_verified":False,
  "original_source_sql_equivalence":False,"calibration_achieved":False,
  "settlement_restriction":"Only ESPN final in NBA, MLB and 90min domestic football; MLS/UCL intentionally not settled without stage/rules verification.",
  "note":"Brier and logloss on prospective locks only. Correlated NBA models are not independent; cross-model comparison requires SAME match cohort. No price profit or guarantee."}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--models",default="docs/phase10-modeles-multisports-latest.json")
 ap.add_argument("--scores",default="docs/scoreboard-revue-latest.json")
 ap.add_argument("--ledger",default="docs/phase10-modeles-prospectif-ledger.json")
 ap.add_argument("--report",default="docs/phase10-modeles-performance.json")
 a=ap.parse_args();now=datetime.now(timezone.utc)
 models=json.loads(Path(a.models).read_text(encoding="utf8"))
 previous=json.loads(Path(a.ledger).read_text(encoding="utf8")) if Path(a.ledger).exists() else None
 scores=json.loads(Path(a.scores).read_text(encoding="utf8")) if Path(a.scores).exists() else {}
 result=settle(lock(previous,models,now),scores,now)
 summary=summarize(result,now)
 for filename,doc in ((a.ledger,result),(a.report,summary)):
  path=Path(filename);path.parent.mkdir(parents=True,exist_ok=True)
  path.write_text(json.dumps(doc,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
 print("Phase10",summary["total_locked"],"forward locks",summary["settled"],"officially settled; no bets.")
if __name__=="__main__":main()
