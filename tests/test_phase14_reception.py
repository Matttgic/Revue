"""Phase14 final-product acceptance: source truth, 3 tabs and research-only guard."""
from __future__ import annotations
import copy,json,unittest,subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.controles.phase14_reception import build,REQUIRED,VERSION,source_age

DOCS=Path(__file__).resolve().parents[1]/"docs"
NOW=datetime.now(timezone.utc)

class ReleaseContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.docs={name:json.loads((DOCS/path).read_text(encoding="utf8"))
            for name,path in REQUIRED.items()}

 def test_existing_sources_generate_truthful_product(self):
  r=build(DOCS,self.docs,NOW)
  self.assertEqual(r["version"],VERSION)
  self.assertEqual(r["status"]!="blocked",True,r["blockers"])
  self.assertTrue(r["technical_gate_passed"],r["blockers"])
  self.assertEqual(r["navigation"],["À JOUER","POURQUOI","BILAN"])
  self.assertEqual(r["pages_checked"],["index.html","play.html","pourquoi.html","bilan.html"])
  self.assertEqual(r["today"]["certified_bet_recommendations"],0)
  self.assertFalse(r["real_bets_enabled"])
  self.assertFalse(r["simulation_paper"]["real_money"])
  self.assertIsNone(r["models"]["ROI"])
  self.assertFalse(r["source_parity_100_percent"])
  self.assertEqual(r["paid_api_calls"],0)

 def test_real_paper_results_match_source(self):
  r=build(DOCS,self.docs,NOW)
  s=self.docs["picks"]["paper_summary"]
  p=r["simulation_paper"]
  self.assertEqual(p["total"],s["total"])
  self.assertEqual(p["settled"],s["settled"])
  self.assertEqual(p["excluded"],s["excluded"])
  self.assertAlmostEqual(p["net_units"],s["paper_profit_units"],places=2)
  self.assertAlmostEqual(p["paper_roi_percent"],s["paper_roi_percent"],places=2)

 def test_real_models_match_the_official_settlement(self):
  r=build(DOCS,self.docs,NOW)
  self.assertEqual(r["models"]["locked_forecasts"],self.docs["models"]["metrics"]["locked"])
  self.assertEqual(r["models"]["officially_settled_forecasts"],
                   self.docs["settlement"]["multisport"]["settled"])
  self.assertEqual(r["models"]["NHL_settled"],self.docs["settlement"]["NHL"]["settled"])
  self.assertEqual(r["models"]["independently_approved_models"],0)

 def test_source_calibration_pretence_is_blocked(self):
  data=copy.deepcopy(self.docs)
  data["models"]["calibrated_models_approved"]=3
  self.assertIn("invalid_model_calibration_claim",build(DOCS,data,NOW)["blockers"])

 def test_bookable_odds_pretence_is_blocked(self):
  data=copy.deepcopy(self.docs)
  data["center"]["bookmaker_prices_are_live"]=True
  self.assertIn("invalid_match_inventory",build(DOCS,data,NOW)["blockers"])

 def test_arbitrary_paper_win_or_roi_is_blocked(self):
  for field,value in [("wins",999),("paper_profit_units",1e6),
                      ("paper_roi_percent",35000),("excluded",0)]:
   data=copy.deepcopy(self.docs)
   data["picks"]["paper_summary"][field]=value
   self.assertIn("paper_reconciliation_failed" if field!="paper_roi_percent" else "paper_ROI_miscalculated",
                 build(DOCS,data,NOW)["blockers"],field)

 def test_nonverified_NHL_market_cannot_join_return(self):
  data=copy.deepcopy(self.docs)
  data["sources"]["paper_market_quarantine"]["total"]=0
  self.assertIn("model_settlement_or_exclusions_disagree",build(DOCS,data,NOW)["blockers"])

 def test_future_and_stale_data_never_appear_fresh(self):
  data=copy.deepcopy(self.docs)
  data["center"]["generated_at_utc"]=(NOW-timedelta(days=7)).isoformat()
  a=build(DOCS,data,NOW)
  self.assertTrue(a["technical_gate_passed"],a["blockers"])
  self.assertEqual(a["status"],"research_only_data_stale")
  self.assertEqual(a["sources"]["center"]["state"],"stale")
  self.assertTrue(any("center_snapshot_stale"==x for x in a["warnings"]))
  self.assertEqual(source_age({"generated_at_utc":(NOW+timedelta(days=3)).isoformat()},NOW,12)["state"],"future")

 def test_missing_firstparty_html_asset_is_blocker(self):
  source=(DOCS/"phase14-ui.js").read_text()
  self.assertIn('fetch("./phase14-readiness-latest.json"',source)
  self.assertIn("Date.now()-published",source)
  self.assertIn("bookable_French_odds_verified!==false",source)

 def test_js_parse_reduced_motion_and_single_source_status(self):
  for item in ("phase14-ui.js","retro-app.js","arcade-v3-app.js","phase13-modeles.js"):
   p=subprocess.run(["node","--check",str(DOCS/item)],capture_output=True,text=True)
   self.assertEqual(p.returncode,0,item+":"+p.stderr)
  self.assertIn("prefers-reduced-motion:reduce",(DOCS/"phase14-ui.css").read_text())

if __name__=="__main__":unittest.main()
