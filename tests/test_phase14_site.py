"""Phase14: public source gate must never make an operational site look profitable."""
import json,re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"docs"
PAGES=("index.html","play.html","pourquoi.html","bilan.html")
class Phase14UITests(unittest.TestCase):
 def test_three_main_screens_clean_mobile_status(self):
  for page in PAGES:
   html=(ROOT/page).read_text(encoding="utf8")
   with self.subTest(page=page):
    self.assertIn('id="phase14-brief"',html)
    self.assertIn('aria-label="Statut vérifié de Revue"',html)
    self.assertIn("phase14-ui.css?v=1",html)
    self.assertIn("phase14-ui.js?v=1",html)
    self.assertIn('name="viewport"',html)
    self.assertIn('href="./lab.html"',html)
    self.assertEqual(len(re.findall('id="phase14-brief"',html)),1)
    self.assertIn('href="./play.html"',html)
    self.assertIn('href="./pourquoi.html"',html)
    self.assertIn('href="./bilan.html"',html)
  self.assertIn('<summary>NOTRE HISTORIQUE DE MODÈLES',(ROOT/"index.html").read_text())
  self.assertIn('<summary>AUTRES HOCKEYS',(ROOT/"play.html").read_text())
 def test_zero_betting_or_parity_claim_and_no_DOM_injection(self):
  js=(ROOT/"phase14-ui.js").read_text(encoding="utf8")
  self.assertIn("certified_bet_recommendations!==0",js)
  self.assertIn("independently_approved_models!==0",js)
  self.assertIn("source_parity_100_percent!==false",js)
  self.assertIn("Date.now()-published",js)
  self.assertIn("document.createElement",js)
  self.assertNotIn("innerHTML",js)
  self.assertNotIn("Math.random",js)
  p=subprocess.run(["node","--check",str(ROOT/"phase14-ui.js")],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr)
 def test_last_published_json_reconciles_sources(self):
  report=json.loads((ROOT/"phase14-readiness-latest.json").read_text(encoding="utf8"))
  picks=json.loads((ROOT/"picks-center-latest.json").read_text(encoding="utf8"))
  models=json.loads((ROOT/"phase13-modeles-evaluation-latest.json").read_text(encoding="utf8"))
  audit=json.loads((ROOT/"phase12-result-integrity-latest.json").read_text(encoding="utf8"))
  self.assertEqual(report["version"],"revue_phase14_public_contract_v1")
  self.assertTrue(report["technical_gate_passed"],report["blockers"])
  self.assertEqual(report["today"]["certified_bet_recommendations"],0)
  self.assertEqual(report["simulation_paper"]["settled"],picks["paper_summary"]["settled"])
  self.assertEqual(report["models"]["locked_forecasts"],models["metrics"]["locked"])
  self.assertEqual(report["models"]["officially_settled_forecasts"],audit["multisport"]["settled"])
  self.assertFalse(report["real_bets_enabled"])
  self.assertFalse(report["source_parity_100_percent"])
if __name__=="__main__":unittest.main()
