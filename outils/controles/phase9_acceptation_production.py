"""Phase9: independent offline static and data-provenance release gate."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

V="revue_phase9_release_gate_v1"
PAGES=("index.html","play.html","pourquoi.html","bilan.html","lab.html","historique.html")
FILES=("match-center-latest.json","picks-center-latest.json","phase2-owned-performance.json","phase6-predictions-latest.json","phase7-prices-performance-latest.json","health-latest.json")
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.refs=[];self.nav=[];self.active=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ("src","href"):
   if a.get(k):self.refs.append(a[k])
  if tag=="nav" and a.get("class") in ("rv-nav","arc-bottom-nav"):self.active=[]
  elif tag=="a" and self.active is not None:self.active.append(a.get("href"))
 def handle_endtag(self,tag):
  if tag=="nav" and self.active is not None:self.nav.append(self.active);self.active=None

def build(root,data,now):
 if now.tzinfo is None:raise ValueError("Clock must be timezone-aware")
 errors=[];warnings=[]
 for page in PAGES:
  try:s=Parser();s.feed((root/page).read_text(encoding="utf8"))
  except OSError:errors.append("missing_page:"+page);continue
  if s.nav!=[["./play.html","./pourquoi.html","./bilan.html"]]*2:errors.append("navigation:"+page)
  if "./phase8-ui.css?v=2" not in s.refs:errors.append("style:"+page)
  for ref in s.refs:
   if ref.startswith("./"):
    name=ref[2:].split("?")[0].split("#")[0]
    if name and ".." not in Path(name).parts and not (root/name).is_file():
     errors.append("missing_asset:"+page+":"+name)
 picks=data["picks-center-latest.json"];games=data["match-center-latest.json"]
 own=data["phase2-owned-performance.json"];original=data["phase6-predictions-latest.json"]
 odds=data["phase7-prices-performance-latest.json"];health=data["health-latest.json"]
 def check(v,label):
  if not v:errors.append(label)
 check(picks.get("real_bets_enabled") is False and picks.get("verified_real_ev") is False
       and picks.get("live_bookmaker_prices") is False
       and picks.get("research_model_calibrated") is False,"unsafe_paper_claims")
 check(games.get("real_bets_enabled") is False and games.get("bookmaker_prices_are_live") is False
       and games.get("validated_value_bets")==0,"unsafe_match_center")
 check(own.get("real_bets_enabled") is False and own.get("replayed_old_results") is False
       and own.get("identical_original_clairvoyance_sql_history") is False,"backfilled_history_claim")
 check(original.get("strict_original_prediction_parity_verified") is False,"false_parity_claim")
 check(odds.get("verified_positive_EV_opportunities")==0 and odds.get("verified_live_quotes") is False
       and odds.get("real_bets_enabled") is False,"unsafe_odd_claim")
 check(health.get("facts",{}).get("fully_calibrated") is False,"false_calibration")
 age={}
 for file,limit in (("match-center-latest.json",12),("picks-center-latest.json",12),
                    ("phase7-prices-performance-latest.json",15),("health-latest.json",12)):
  try:
   t=datetime.fromisoformat(data[file]["generated_at_utc"].replace("Z","+00:00"))
   if t.tzinfo is None:raise ValueError("No timezone")
   hours=round((now-t.astimezone(timezone.utc)).total_seconds()/3600,1)
   state="future" if hours<-.05 else "stale" if hours>limit else "recent"
  except (ValueError,KeyError,TypeError):hours=None;state="unknown"
  age[file]={"hours":hours,"state":state}
  if state!="recent":warnings.append(file+":"+state)
 if health.get("status")!="components_fresh":warnings.extend(str(x) for x in health.get("warnings",[]))
 summary=picks.get("paper_summary") or {};audited=odds.get("paper_performance") or {}
 if summary.get("settled")!=audited.get("settled"):warnings.append("paper_audit_requires_refresh")
 errors=sorted(set(errors));warnings=sorted(set(warnings))
 return {"version":V,"generated_at_utc":now.isoformat(),
  "status":"blocked" if errors else "static_site_verified_with_data_warnings" if warnings else "static_site_verified",
  "static_gate_passed":not errors,"blockers":errors,"warnings":warnings,"source_ages":age,
  "pages_checked":list(PAGES),"paper_settled":summary.get("settled"),
  "paper_virtual_profit_units":summary.get("paper_profit_units"),
  "source_output_comparisons":original.get("observed_output_comparisons"),
  "bookable_odds_proven":False,"calibrated_models_proven":False,
  "positive_ev_verified":False,"real_bets_enabled":False,"paid_api_calls":0,
  "public_http_verified_in_report":False,"pages_smoke_test_separate":True,
  "CFB_excluded":True,
  "note":"Static local release evidence only. GitHub Pages HTTP smoke verified independently by deployment workflow. All profit figures are paper-only."}

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",default="docs")
 p.add_argument("--output",default="docs/phase9-readiness-latest.json")
 a=p.parse_args();root=Path(a.root)
 docs={x:json.loads((root/x).read_text()) for x in FILES}
 report=build(root,docs,datetime.now(timezone.utc))
 Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
 print(report["status"],"blockers=",len(report["blockers"]),"warnings=",len(report["warnings"]))
 if report["blockers"]:raise SystemExit(1)
if __name__=="__main__":main()
