"""Phase 12 settlement audit: verify scores, never reinterpret paper returns."""
from __future__ import annotations
import json,math
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.match_center_revue import instant
from outils.phase10_validation_prospective import SOCCER_REG,SOCCER_ALL

VERSION="revue_phase12_settlement_audit_v1"

def evaluate(prospective,nhl,picks,retro,now):
 if now.tzinfo is None:raise ValueError("UTC timestamp required")
 if prospective.get("version")!="revue_phase10_forward_ledger_v1" or not isinstance(prospective.get("records"),dict):raise ValueError("Invalid prospective records")
 if not isinstance(nhl.get("events"),list):raise ValueError("NHL official ledger missing")
 problems=[];overdue=[];stats={"settled":0,"pending":0}
 for key,r in prospective["records"].items():
  try:
   kick=instant(r["kickoff_utc"]);locked=instant(r["locked_at_utc"])
   model_at=instant(r["source_model_at_utc"]);p=r["probabilities"]
   if not model_at<=locked<=kick-timedelta(minutes=20):raise ValueError("postkickoff prediction")
   if r["id"]!=key or r["real_bet"] is not False or r["stake_units"]!=0 or r["outcome_price"] is not None:raise ValueError("non paper locked record")
   if not isinstance(p,list) or len(p)!=(3 if r["league"] in SOCCER_ALL else 2):raise ValueError("wrong market vector")
   if any(type(x) not in (int,float) or not math.isfinite(x) or x<=0 or x>=1 for x in p) or abs(sum(p)-1)>.005:raise ValueError("invalid probability")
   if r["status"]=="settled":
    if r["league"] in {"MLS","UCL"}:raise ValueError("unverified stage graded")
    h,a=r["scores"]["home"],r["scores"]["away"]
    if type(h) is not int or type(a) is not int or min(h,a)<0 or (len(p)==2 and h==a):raise ValueError("invalid final")
    outcome=(0 if h>a else 1 if h==a else 2) if len(p)==3 else (0 if h>a else 1)
    br=sum((x-(1 if i==outcome else 0))**2 for i,x in enumerate(p))
    if r["result"]!=outcome or abs(r["brier"]-br)>.00002 or abs(r["logloss"]+math.log(p[outcome]))>.00002:raise ValueError("stored score corrupted")
    if instant(r["resolved_at_utc"])<kick+timedelta(minutes=95):raise ValueError("premature final")
    stats["settled"]+=1
   elif r["status"]=="pending":
    if any(r.get(f) is not None for f in ("result","scores","brier","logloss","resolved_at_utc")):raise ValueError("pending has result")
    stats["pending"]+=1
    if now>kick+timedelta(minutes=95):overdue.append({"league":r["league"],"event_id":r["event_id"],"model_id":r["model_id"],"hours":round((now-kick).total_seconds()/3600,1)})
   else:raise ValueError("unknown state")
  except (ValueError,TypeError,KeyError,OverflowError) as exc:problems.append({"record":key,"error":str(exc)[:100]})
 nhl_settled=0;nhl_pending=0
 for r in nhl["events"]:
  if r.get("status")=="settled":
   nhl_settled+=1
   try:
    h,a=r["home_goals"],r["away_goals"];p=r["home_win_probability"]
    if type(h) is not int or type(a) is not int or h==a or r["result"]!=int(h>a) or abs((p-r["result"])**2-r["brier"])>.00002:raise ValueError("NHL mismatch")
   except (ValueError,TypeError,KeyError) as exc:problems.append({"NHL":r.get("event_id"),"error":str(exc)[:100]})
  elif r.get("status")=="pending":nhl_pending+=1
  else:problems.append({"NHL":r.get("event_id"),"error":"unknown NHL state"})
 excluded=(picks.get("paper_summary") or {}).get("excluded")
 if picks.get("real_bets_enabled") is not False or picks.get("verified_real_ev") is not False or type(excluded) is not int:raise ValueError("Paper source not verified")
 if retro.get("version")!="revue_phase12_settlement_reconciliation_v1" or retro.get("total_locks_after")!=len(prospective["records"]):raise ValueError("Reconciliation mismatch")
 if retro.get("settled_after")!=stats["settled"]:problems.append({"reconciliation":"settled count mismatch"})
 return {"version":VERSION,"generated_at_utc":now.isoformat(),
  "status":"audit_error" if problems else "official_results_active_sample_accumulating",
  "multisport":{"locked":len(prospective["records"]),**stats,"overdue_pending":len(overdue),"overdue_examples":overdue[:20]},
  "NHL":{"locked":len(nhl["events"]),"settled":nhl_settled,"pending":nhl_pending,"official_NHL_score_source":True},
  "unverified_historical_NHL_bookmaker_markets_excluded":excluded,
  "conflicting_ESPN_final_ids":retro.get("cross_source_conflicts",[]),
  "audit_errors":problems,"ROI":None,"real_bets_enabled":False,
  "original_predictions_modified":False,"calibrated":False,"CFB_excluded":True,
  "note":"NBA MLB soccer graded only from frozen ESPN official finals. NHL has independent official scoreboard. Bookmaker period-ambiguous observations remain outside the ROI."}
def main():
 d=Path("docs")
 def r(name):return json.loads((d/name).read_text(encoding="utf8"))
 report=evaluate(r("phase10-modeles-prospectif-ledger.json"),r("nhl-shadow-ledger.json"),
   r("picks-center-latest.json"),r("phase12-reconciliation-latest.json"),datetime.now(timezone.utc))
 (d/"phase12-result-integrity-latest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
 print("Official grading:",report["multisport"]["settled"],"multisport;",
   report["NHL"]["settled"],"NHL; audit errors",len(report["audit_errors"]))
 if report["audit_errors"]:raise SystemExit(1)
if __name__=="__main__":main()
