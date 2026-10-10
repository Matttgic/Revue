"""Phase 13: immutable out-of-sample multisport model comparison.

Only prospective ESPN/NHL official final scores, never paper bookmaker profits.
Compare paired model versions on identical fixture, kickoff, team identity,
market period and observed winner. Fit a *predeclared* temperature grid on
the first 100 genuinely resolved games, freeze its cutoff and evaluate only
new games kicking off after that cutoff. No auto model selection or bet signal.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.match_center_revue import instant
from outils.phase10_validation_prospective import (
    VERSION as LEDGER_VERSION, EXPECTED_MODELS, SOCCER_ALL, SOCCER_REG,
)

VERSION="revue_phase13_model_evaluation_v1"
TRAIN_N=100
HOLDOUT_N=40
PAIRED_MIN=30
RELIABILITY_BINS=5
TEMPERATURES=(0.65,0.8,1.0,1.25,1.5,2.0,2.5)
TOL=0.00003

def valid_vector(p,n):
 return (isinstance(p,list) and len(p)==n and
         all(type(x) in (int,float) and math.isfinite(x) and 0<x<1 for x in p)
         and abs(sum(p)-1)<=0.005)

def loss(p,y):
 return sum((x-(1 if i==y else 0))**2 for i,x in enumerate(p)),-math.log(p[y])

def score_summary(rows,temperature=None):
 if not rows:return {"n":0,"brier":None,"logloss":None}
 vals=[loss(soften(r["p"],temperature) if temperature is not None else r["p"],r["y"]) for r in rows]
 n=len(vals)
 return {"n":n,"brier":round(sum(s[0] for s in vals)/n,6),
         "logloss":round(sum(s[1] for s in vals)/n,6)}

def soften(p,t):
 if t is None or t==1.0:return list(p)
 z=[math.log(v)/t for v in p]
 m=max(z)
 x=[math.exp(v-m) for v in z]
 return [v/sum(x) for v in x]

def bins(rows):
 if not rows:return []
 out=[]
 outcomes=len(rows[0]["p"])
 for k in range(outcomes):
  buckets=[[] for _ in range(RELIABILITY_BINS)]
  for r in rows:
   p=r["p"][k];b=min(RELIABILITY_BINS-1,int(p*RELIABILITY_BINS))
   buckets[b].append(r)
  out.append({"outcome":("home","draw","away")[k] if outcomes==3 else ("home","away")[k],
   "bins":[{"lower":round(i/RELIABILITY_BINS,2),
            "upper":round((i+1)/RELIABILITY_BINS,2),"n":len(bucket),
            "mean_predicted":round(sum(x["p"][k] for x in bucket)/len(bucket),5) if bucket else None,
            "observed_rate":round(sum(x["y"]==k for x in bucket)/len(bucket),5) if bucket else None}
           for i,bucket in enumerate(buckets)]})
 return out

def verify(ledger,now):
 if now.tzinfo is None:raise ValueError("Clock must be timezone aware")
 if ledger.get("version")!=LEDGER_VERSION or not isinstance(ledger.get("records"),dict):
  raise ValueError("Frozen prospective model ledger invalid")
 models=defaultdict(list)
 game_results={}
 seen=set()
 for key,r in ledger["records"].items():
  if not isinstance(r,dict) or key!=r.get("id"):raise ValueError("Frozen model identity invalid")
  lg,mid=r.get("league"),r.get("model_id")
  if mid not in EXPECTED_MODELS:raise ValueError("Unknown model version in phase13")
  if (mid.startswith("revue_nba_") and lg!="NBA" or
      mid.startswith("revue_mlb_") and lg!="MLB" or
      mid.startswith("revue_football_") and lg not in SOCCER_ALL):
   raise ValueError("Cross-sport model mismatch")
  n=3 if lg in SOCCER_ALL else 2
  p=r.get("probabilities")
  if not valid_vector(p,n):raise ValueError("Invalid frozen probabilities")
  if (r.get("real_bet") is not False or r.get("stake_units")!=0 or
      r.get("outcome_price") is not None):
   raise ValueError("Real money/odds cannot inform phase13 model metrics")
  start=instant(r["kickoff_utc"]);locked=instant(r["locked_at_utc"])
  source=instant(r["source_model_at_utc"])
  if source>locked or locked>start-timedelta(minutes=20) or
     not isinstance(r.get("input_observed_at_utc"),dict) or
     not r["input_observed_at_utc"] or
     any(instant(v)>source for v in r["input_observed_at_utc"].values()):
   raise ValueError("Leaked pregame source timestamps")
  market=("90min_1x2" if n==3 else "full_game_2way")
  if r.get("market")!=market:raise ValueError("Market period identity mismatch")
  fixture=(lg,str(r["event_id"]),r["home"],r["away"],start.isoformat(),market)
  identity=fixture+(mid,)
  if identity in seen:raise ValueError("Duplicate candidate for one fixture")
  seen.add(identity)
  if r["status"]=="pending":
   if any(r.get(k) is not None for k in ("result","scores","resolved_at_utc","brier","logloss")):
    raise ValueError("Pending record has grades")
   continue
  if r["status"]!="settled":raise ValueError("Unrecognized model settlement")
  if lg in {"MLS","UCL"}:raise ValueError("Competition stage unverified for 90 minute result")
  observed=instant(r["resolved_at_utc"])
  if not start+timedelta(minutes=95)<=observed<=now:
   raise ValueError("Result observed before final or in future")
  score=r["scores"]
  h,a=score["home"],score["away"]
  if type(h) is not int or type(a) is not int or min(h,a)<0 or max(h,a)>300:
   raise ValueError("Final scores invalid")
  if n==2 and h==a:raise ValueError("Draw cannot settle 2way")
  y=(0 if h>a else 1 if h==a else 2) if n==3 else (0 if h>a else 1)
  brier,logloss=loss(p,y)
  if (r["result"]!=y or abs(brier-r["brier"])>TOL or
      abs(logloss-r["logloss"])>TOL):
   raise ValueError("Frozen Brier/LogLoss disagree with final")
  old=game_results.get(fixture)
  if old is not None and old!=((h,a),y):
   raise ValueError("Models for one event disagree about official final")
  game_results[fixture]=((h,a),y)
  models[(lg,mid)].append({"fixture":fixture,"kickoff":start,"resolved":observed,
                          "p":list(p),"y":y})
 return models

def calibrate(rows):
 rows=sorted(rows,key=lambda r:(r["resolved"],r["fixture"]))
 n=len(rows)
 result={"training_required":TRAIN_N,"holdout_required":HOLDOUT_N,
  "training_n":0,"holdout_n":0,"training_cutoff_utc":None,
  "frozen_temperature":None,"temperature_candidates":list(TEMPERATURES),
  "holdout":None,"status":"insufficient_training"}
 if n<TRAIN_N:return result
 train=rows[:TRAIN_N];cutoff=train[-1]["resolved"]
 scores=[(score_summary(train,t)["logloss"],abs(t-1),t) for t in TEMPERATURES]
 best=min(scores)[2]
 held=[r for r in rows[TRAIN_N:] if r["kickoff"]>cutoff]
 result.update({"training_n":TRAIN_N,"holdout_n":len(held),
  "training_cutoff_utc":cutoff.isoformat(),"frozen_temperature":best,
  "status":"awaiting_future_holdout"})
 if len(held)<HOLDOUT_N:return result
 raw=score_summary(held);adjusted=score_summary(held,best)
 m=len(held[0]["p"])
 uniform=score_summary([dict(r,p=[1/m]*m) for r in held])
 result["holdout"]={"raw":raw,"temperature_scaled":adjusted,"uniform_reference":uniform,
  "brier_delta_scaled_minus_raw":round(adjusted["brier"]-raw["brier"],6),
  "logloss_delta_scaled_minus_raw":round(adjusted["logloss"]-raw["logloss"],6)}
 result["status"]="holdout_exploratory_improved" if (adjusted["brier"]<raw["brier"] and
      adjusted["logloss"]<raw["logloss"] and adjusted["brier"]<uniform["brier"] and
      adjusted["logloss"]<uniform["logloss"]) else "holdout_exploratory_not_better"
 return result

def paired_interval(deltas,seed):
 if len(deltas)<PAIRED_MIN:return None
 rng=random.Random(seed)
 means=[]
 n=len(deltas)
 for _ in range(1000):
  means.append(sum(deltas[rng.randrange(n)] for _ in range(n))/n)
 means.sort()
 return [round(means[24],6),round(means[975],6)]

def compare(left,right,models,seed=13):
 cohort_left={r["fixture"]:r for r in models[left]}
 cohort_right={r["fixture"]:r for r in models[right]}
 common=sorted(set(cohort_left)&set(cohort_right))
 a=[cohort_left[key] for key in common];b=[cohort_right[key] for key in common]
 deltas_brier=[];deltas_log=[]
 for x,y in zip(a,b):
  if x["y"]!=y["y"]:raise ValueError("Inconsistent paired result")
  xb,xl=loss(x["p"],x["y"]);yb,yl=loss(y["p"],y["y"])
  deltas_brier.append(yb-xb);deltas_log.append(yl-xl)
 n=len(common)
 return {"league":left[0],"reference":left[1],"candidate":right[1],
  "paired_games":n,"reference_scores":score_summary(a),"candidate_scores":score_summary(b),
  "delta_brier_candidate_minus_reference":round(sum(deltas_brier)/n,6) if n else None,
  "delta_logloss_candidate_minus_reference":round(sum(deltas_log)/n,6) if n else None,
  "bootstrap_95_brier_delta":paired_interval(deltas_brier,seed),
  "bootstrap_95_logloss_delta":paired_interval(deltas_log,seed+1),
  "research_status":"insufficient_pairs" if n<PAIRED_MIN else
       "paired_exploratory_only_no_model_selection",
  "candidate_outperformed_on_games":sum(x<0 for x in deltas_brier),
  "paired_samples_are_distinct_fixtures":True,
  "auto_promote":False}

def nhl_comparison(ledger,now):
 if not isinstance(ledger.get("events"),list):
  raise ValueError("NHL official scoreboard ledger missing")
 pairs=[];single=[]
 seen=set()
 for e in ledger["events"]:
  eid=str(e.get("event_id"))
  if eid in seen:raise ValueError("Duplicate NHL fixture")
  seen.add(eid)
  if e.get("status")!="settled":continue
  locked=instant(e["locked_at_utc"]);kick=instant(e["kickoff_utc"]);resolved=instant(e["resolved_at_utc"])
  if not locked<=kick-timedelta(minutes=20) or not kick<resolved<=now:
   raise ValueError("Invalid official NHL chronology")
  h,a=e["home_goals"],e["away_goals"]
  if type(h) is not int or type(a) is not int or h==a or h<0 or a<0:
   raise ValueError("Invalid NHL final")
  y=0 if h>a else 1
  if e["result"]!=int(h>a):raise ValueError("NHL result inconsistent")
  p=e["home_win_probability"]
  if type(p) not in (int,float) or not 0<p<1:raise ValueError("Invalid NHL forecast")
  if abs((p-e["result"])**2-e["brier"])>TOL:raise ValueError("NHL Brier mismatched")
  row={"fixture":("NHL",eid),"p":[p,1-p],"y":y,"kickoff":kick,"resolved":resolved}
  single.append(row)
  q=e.get("research_home_win_probability")
  if q is not None:
   if type(q) not in (int,float) or not 0<q<1:raise ValueError("Invalid NHL research p")
   pairs.append((row,dict(row,p=[q,1-q])))
 report={"locked":len(ledger["events"]),"settled":len(single),
  "paired_settled":len(pairs),"reference_score":score_summary(single),
  "paired":{"games":len(pairs),"reference":score_summary([p[0] for p in pairs]),
            "candidate":score_summary([p[1] for p in pairs]),
            "comparison_validated":len(pairs)>=PAIRED_MIN},
  "separate_official_NHL_source":True,"original_sql_parity_proven":False,
  "automatically_deployed":False}
 if pairs:
  x=[loss(q["p"],q["y"])[0]-loss(p["p"],p["y"])[0] for p,q in pairs]
  report["paired"]["delta_brier_candidate_minus_reference"]=round(sum(x)/len(x),6)
 return report

def evaluate(ledger,nhl,integrity,now):
 if now.tzinfo is None:raise ValueError("Timezone-aware UTC timestamp required")
 if (integrity.get("version")!="revue_phase12_settlement_audit_v1" or
     integrity.get("status")=="audit_error" or
     integrity.get("real_bets_enabled") is not False or
     integrity.get("original_predictions_modified") is not False or
     integrity.get("audit_errors")):
  raise ValueError("Phase 12 verified settlement audit required")
 models=verify(ledger,now)
 nhl_report=nhl_comparison(nhl,now)
 versions={}
 for lg,mid in sorted(set((lg,mid) for lg,mid in
     [(row.get("league"),row.get("model_id")) for row in ledger["records"].values()]
     if mid in EXPECTED_MODELS)):
  rows=models[(lg,mid)]
  metrics=score_summary(rows)
  n=3 if lg in SOCCER_ALL else 2
  baseline=score_summary([dict(r,p=[1/n]*n) for r in rows])
  versions[mid]={"league":lg,"model_id":mid,"settled":len(rows),
   "frozen_locked":sum(x.get("model_id")==mid and x.get("league")==lg for x in ledger["records"].values()),
   "raw":metrics,"uniform_reference_same_matches":baseline,
   "reliability":bins(rows),"calibration":calibrate(rows),
   "preliminary_assessment_at_100":len(rows)>=TRAIN_N,
   "independent_holdout_complete":calibrate(rows)["holdout"] is not None,
   "approved_for_betting":False,"automatic_champion":False}
 # Only compare models from the SAME league, market and identified match.
 leagues={lg for lg,mid in models}
 pairs=[]
 for lg in sorted(leagues):
  mids=sorted({mid for l,mid in models if l==lg})
  for a in range(len(mids)):
   for b in range(a+1,len(mids)):
    pairs.append(compare((lg,mids[a]),(lg,mids[b]),models,seed=13+a*10+b))
 paired_count=sum(p["paired_games"] for p in pairs)
 true_games=len({r["fixture"] for rows in models.values() for r in rows})
 return {"version":VERSION,"generated_at_utc":now.astimezone(timezone.utc).isoformat(),
  "status":"research_only_awaiting_prospective_evidence",
  "protocol":{"prospective_only":True,"calibration_train_first_official_finals":TRAIN_N,
   "holdout_new_kickoffs_strictly_after_training_resolution":HOLDOUT_N,
   "temperature_grid_frozen":list(TEMPERATURES),"pairing":"identical ESPN event, league, teams, kickoff and market period",
   "preliminary_paired_sample":PAIRED_MIN,
   "bootstrap_ci_only_after_paired_count":PAIRED_MIN,
   "no_across_sport_aggregation":True,"no_auto_model_selection":True},
  "metrics":{"locked":len(ledger["records"]),"settled":sum(len(r) for r in models.values()),
    "distinct_settled_fixtures":true_games,"paired_comparisons":len(pairs),
    "paired_observation_overlap_not_independent":paired_count},
  "models":versions,"paired_comparisons":pairs,"NHL":nhl_report,
  "real_bets_enabled":False,"verified_profitable_models":0,
  "calibrated_models_approved":0,"original_clairvoyance_parity_proven":False,
  "source_sql_access":False,"ROI":None,
  "note":"A lower Brier/LogLoss is an observed research metric, not proof of an edge. Correlated NBA priors count as a single paired fixture, and all deployment requires independent later review."}

def main():
 cli=argparse.ArgumentParser()
 cli.add_argument("--root",default="docs")
 args=cli.parse_args();root=Path(args.root)
 def load(p):return json.loads((root/p).read_text(encoding="utf8"))
 now=datetime.now(timezone.utc)
 report=evaluate(load("phase10-modeles-prospectif-ledger.json"),
    load("nhl-shadow-ledger.json"),load("phase12-result-integrity-latest.json"),now)
 path=root/"phase13-modeles-evaluation-latest.json"
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
 print("Phase13",report["metrics"]["settled"],"multisport model outcomes,",
       report["metrics"]["distinct_settled_fixtures"],"unique fixtures,",
       report["NHL"]["settled"],"NHL finals,",
       report["metrics"]["paired_comparisons"],"pair comparisons")
if __name__=="__main__":main()
