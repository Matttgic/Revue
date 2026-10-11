"""Phase 14: user-facing release truth gate for the three-screen Revue Arcade.

Read saved source-verified sports records. Publish a small, machine-checkable
summary with no real-money claim, no fabricated rankings, and no new API calls.
A passing technical gate is NOT proof of 100% Clairvoyance replication or EV.
"""
from __future__ import annotations
import argparse,json,math
from collections import Counter
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION="revue_phase14_public_contract_v1"
PAGES=("index.html","play.html","pourquoi.html","bilan.html")
REQUIRED={
 "center":"match-center-latest.json",
 "picks":"picks-center-latest.json",
 "models":"phase13-modeles-evaluation-latest.json",
 "performance":"phase10-modeles-performance.json",
 "settlement":"phase12-result-integrity-latest.json",
 "readiness":"phase9-readiness-latest.json",
 "sources":"phase11-source-quality-latest.json",
}
JOURNEY=("./play.html","./pourquoi.html","./bilan.html")

class Page(HTMLParser):
 def __init__(self):
  super().__init__()
  self.links=[];self.refs=[];self.ids=[];self.nav=[];self.open_nav=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if "id" in a:self.ids.append(a["id"])
  for key in ("src","href"):
   v=a.get(key)
   if v:self.refs.append(v)
  if tag=="nav" and a.get("class") in ("rv-nav","arc-bottom-nav"):
   self.open_nav=[]
  if tag=="a" and self.open_nav is not None:
   self.open_nav.append(a.get("href"))
 def handle_endtag(self,tag):
  if tag=="nav" and self.open_nav is not None:
   self.nav.append(self.open_nav);self.open_nav=None

def source_age(doc,now,hours):
 try:
  t=datetime.fromisoformat(doc["generated_at_utc"].replace("Z","+00:00"))
  if t.tzinfo is None:raise ValueError("missing timezone")
  age=(now-t.astimezone(timezone.utc)).total_seconds()/3600
  return {"hours":round(age,2),"state":"future" if age<-.034 else "stale" if age>hours else "recent"}
 except (KeyError,ValueError,TypeError):
  return {"hours":None,"state":"unknown"}

def build(root:Path,data:dict,now:datetime):
 if now.tzinfo is None:raise ValueError("UTC-aware clock required")
 now=now.astimezone(timezone.utc)
 failures=[];warnings=[];routes=[]
 def bad(code):failures.append(code)
 for page in PAGES:
  try:
   html=(root/page).read_text(encoding="utf8")
   p=Page();p.feed(html)
  except OSError:
   bad("missing_primary_screen:"+page);continue
  if p.nav != [list(JOURNEY),list(JOURNEY)]:bad("three_screen_navigation:"+page)
  if "phase14-brief" not in p.ids:bad("missing_source_status:"+page)
  if len(p.ids)!=len(set(p.ids)):bad("duplicate_html_id:"+page)
  if 'name="viewport"' not in html:bad("missing_mobile_viewport:"+page)
  if "phase14-ui.css?v=1" not in html or "phase14-ui.js?v=1" not in html:
   bad("missing_phase14_shell:"+page)
  if "./lab.html" not in p.refs:bad("technical_lab_link_missing:"+page)
  for ref in p.refs:
   if not ref.startswith("./"):continue
   rel=ref[2:].split("#",1)[0].split("?",1)[0]
   if rel and (".." in Path(rel).parts or not (root/rel).is_file()):
    bad("missing_internal_asset:"+page+":"+rel)
  routes.append(page)
 center=data["center"];picks=data["picks"];models=data["models"]
 performance=data["performance"];settlement=data["settlement"]
 readiness=data["readiness"];sources=data["sources"]
 if (center.get("status")!="experimental_revue_match_center" or
     center.get("real_bets_enabled") is not False or
     center.get("bookmaker_prices_are_live") is not False or
     center.get("validated_value_bets")!=0 or
     not isinstance(center.get("events"),list) or
     (center.get("metrics") or {}).get("upcoming_matches")!=len(center["events"])):
  bad("invalid_match_inventory")
 if (picks.get("status")!="revue_independent_picks_hub_static_research_paper_only" or
     picks.get("real_bets_enabled") is not False or
     picks.get("verified_real_ev") is not False or
     picks.get("live_bookmaker_prices") is not False or
     picks.get("research_model_calibrated") is not False or
     not isinstance(picks.get("paper_records"),list)):
  bad("invalid_paper_provenance")
 if (models.get("version")!="revue_phase13_model_evaluation_v1" or
     models.get("real_bets_enabled") is not False or
     models.get("verified_profitable_models")!=0 or
     models.get("calibrated_models_approved")!=0 or
     models.get("ROI") is not None or
     (models.get("protocol") or {}).get("no_auto_model_selection") is not True):
  bad("invalid_model_calibration_claim")
 if (settlement.get("version")!="revue_phase12_settlement_audit_v1" or
     settlement.get("real_bets_enabled") is not False or
     settlement.get("original_predictions_modified") is not False or
     settlement.get("audit_errors") or settlement.get("status")=="audit_error"):
  bad("invalid_official_result_audit")
 if (readiness.get("version")!="revue_phase9_release_gate_v1" or
     readiness.get("static_gate_passed") is not True or
     readiness.get("real_bets_enabled") is not False or
     readiness.get("positive_ev_verified") is not False):
  bad("underlying_release_gate_blocked")
 if (sources.get("version")!="revue_phase11_source_quality_v1" or
     sources.get("real_bets_enabled") is not False or
     sources.get("model_probabilities_modified") is not False or
     sources.get("paper_ledger_modified") is not False):
  bad("source_provenance_unverified")
 records=picks.get("paper_records") or []
 summary=picks.get("paper_summary") or {}
 total=len(records)
 statuses=Counter(x.get("status") for x in records if isinstance(x,dict))
 graded=[x for x in records if isinstance(x,dict) and x.get("status") in ("won","lost","push")]
 stake=sum(x.get("paper_stake_units",0) for x in graded)
 profit=sum(x.get("paper_profit_units",0) for x in graded)
 if (total!=summary.get("total") or statuses["won"]!=summary.get("wins") or
     statuses["lost"]!=summary.get("losses") or
     statuses["push"]!=summary.get("pushes") or
     len(graded)!=summary.get("settled") or
     statuses["pending"]!=summary.get("pending") or
     statuses["unverified"]!=summary.get("excluded") or
     any(x.get("real_bet") is not False for x in records) or
     any(x.get("verified_pregame") is not True for x in graded) or
     any(x.get("paper_profit_units") is not None for x in records if x not in graded) or
     not math.isfinite(stake) or not math.isfinite(profit) or
     abs(stake-summary.get("settled_stake_units",float("nan")))>0.02 or
     abs(profit-summary.get("paper_profit_units",float("nan")))>0.02):
  bad("paper_reconciliation_failed")
 if isinstance(summary.get("paper_roi_percent"),(int,float)) and stake>0:
  if abs(summary["paper_roi_percent"]-100*profit/stake)>0.03:
   bad("paper_ROI_miscalculated")
 metrics=models.get("metrics") or {}
 model_perf=performance
 multi=settlement.get("multisport") or {}
 nhl=settlement.get("NHL") or {}
 if (metrics.get("locked")!=model_perf.get("total_locked") or
     metrics.get("settled")!=model_perf.get("settled") or
     metrics.get("locked")!=multi.get("locked") or
     metrics.get("settled")!=multi.get("settled") or
     multi.get("pending")!=multi.get("locked",0)-multi.get("settled",0) or
     (sources.get("paper_market_quarantine") or {}).get("total")!=statuses["unverified"] or
     settlement.get("unverified_historical_NHL_bookmaker_markets_excluded")!=statuses["unverified"]):
  bad("model_settlement_or_exclusions_disagree")
 ages={}
 for label,limit in (("center",12),("picks",24),("models",24),("settlement",24),("sources",24)):
  ages[label]=source_age(data[label],now,limit)
  if ages[label]["state"]!="recent":warnings.append(label+"_snapshot_"+ages[label]["state"])
 if metrics.get("settled",0)<100:
  warnings.append("multisport_calibration_not_proven")
 if nhl.get("settled",0)<100:
  warnings.append("NHL_calibration_not_proven")
 warnings.append("original_Clairvoyance_models_not_identical")
 # A research fixture exists only if it has a valid future date and research model.
 upcoming=0;with_model=0
 for e in center.get("events") or []:
  if not isinstance(e,dict) or e.get("league")=="CFB":continue
  try:
   t=datetime.fromisoformat(e["start_utc"].replace("Z","+00:00"))
   if t.tzinfo is None or t.astimezone(timezone.utc)<=now:continue
  except (KeyError,ValueError,TypeError):continue
  upcoming+=1
  if e.get("research"):with_model+=1
 warnings=sorted(set(warnings));failures=sorted(set(failures))
 status=("blocked" if failures else
  "research_only_data_stale" if any(x["state"]!="recent" for x in ages.values())
  else "research_site_operational_models_unvalidated")
 return {
  "version":VERSION,"generated_at_utc":now.isoformat(),
  "status":status,"technical_gate_passed":not failures,
  "blockers":failures,"warnings":warnings,
  "navigation":["À JOUER","POURQUOI","BILAN"],"pages_checked":routes,
  "today":{"upcoming_fixtures":upcoming,"upcoming_with_research_models":with_model,
   "certified_bet_recommendations":0,"bookable_French_odds_verified":False,
   "model_probability_calibration_verified":False,"recommendation":"AUCUN PARI VALIDÉ"},
  "simulation_paper":{"total":total,"settled":len(graded),"won":statuses["won"],
   "lost":statuses["lost"],"push":statuses["push"],"pending":statuses["pending"],
   "excluded":statuses["unverified"],"net_units":round(profit,2),
   "paper_roi_percent":round(100*profit/stake,2) if stake>0 else None,
   "real_money":False,"profitability_proven":False},
  "models":{"locked_forecasts":metrics.get("locked",0),
    "officially_settled_forecasts":metrics.get("settled",0),
    "distinct_officially_settled_fixtures":metrics.get("distinct_settled_fixtures",0),
    "NHL_locked":nhl.get("locked",0),"NHL_settled":nhl.get("settled",0),
    "candidate_pairs":metrics.get("paired_comparisons",0),"independently_approved_models":0,
    "ROI":None,"validated_favorite":None},
  "sources":ages,"no_backfilled_predictions":True,
  "real_bets_enabled":False,"paid_api_calls":0,
  "static_gate_is_not_public_HTTP_test":True,"source_parity_100_percent":False,
  "note":"Product may pass navigation/deployment acceptance while all models still lack independent validation. Paper profits are not real betting returns. The Pages HTTP check runs separately."}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--root",default="docs")
 p.add_argument("--output",default="docs/phase14-readiness-latest.json")
 a=p.parse_args();root=Path(a.root)
 data={k:json.loads((root/path).read_text(encoding="utf8")) for k,path in REQUIRED.items()}
 result=build(root,data,datetime.now(timezone.utc))
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
 print("Phase14",result["status"],"blockers",len(result["blockers"]),
       "paper",result["simulation_paper"]["settled"],"multisport_models",result["models"]["officially_settled_forecasts"],
       "paid_API_calls",result["paid_api_calls"])
 if result["blockers"]:raise SystemExit(1)

if __name__=="__main__":main()
