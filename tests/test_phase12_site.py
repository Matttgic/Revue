"""Phase 12 output is read-only and distinct from historical bookmaker results."""
import json,subprocess,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"docs"
class Phase12Site(unittest.TestCase):
 def test_public_page_and_mobile_navigation(self):
  h=(P/"phase12-resultats.html").read_text(encoding="utf8")
  js=(P/"phase12-results.js").read_text(encoding="utf8")
  lab=(P/"lab.html").read_text(encoding="utf8")
  self.assertIn('href="./phase12-resultats.html"',lab)
  for target in ("s12-state","s12-all","s12-settled","s12-nhl",
                 "s12-quarantine","s12-recovery","s12-leagues","s12-overdue"):
   self.assertIn('id="'+target+'"',h)
  for target in ("./play.html","./pourquoi.html","./bilan.html","./lab.html"):
   self.assertIn(target,h)
  for src in ("phase12-result-integrity-latest.json","phase12-reconciliation-latest.json"):
   self.assertIn(src,js)
  self.assertIn("real_bets_enabled!==false",js)
  self.assertIn("original_predictions_modified!==false",js)
  self.assertIn("document.createElement",js)
  self.assertNotIn("innerHTML",js)
  result=subprocess.run(["node","--check",str(P/"phase12-results.js")],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_live_snapshot_never_claims_wagers(self):
  doc=json.loads((P/"phase12-result-integrity-latest.json").read_text())
  self.assertEqual(doc["version"],"revue_phase12_settlement_audit_v1")
  self.assertFalse(doc["real_bets_enabled"])
  self.assertFalse(doc["original_predictions_modified"])
  self.assertIsNone(doc["ROI"])
  self.assertEqual(doc["audit_errors"],[])
  self.assertGreaterEqual(doc["unverified_historical_NHL_bookmaker_markets_excluded"],0)
if __name__=="__main__":unittest.main()
