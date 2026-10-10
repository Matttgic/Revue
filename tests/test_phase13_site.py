"""Phase13 public model quality view refuses fake ROI and unpaired league results."""
import json,subprocess,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"docs"
class Phase13Site(unittest.TestCase):
 def test_public_mobile_navigation_and_source_gates(self):
  html=(D/"phase13-modeles.html").read_text(encoding="utf8")
  js=(D/"phase13-modeles.js").read_text(encoding="utf8")
  lab=(D/"lab.html").read_text(encoding="utf8")
  self.assertIn('href="./phase13-modeles.html"',lab)
  for ident in ("p13-locked","p13-settled","p13-fixtures","p13-approved",
                "p13-status","p13-models","p13-pairs","p13-nhl","p13-calibration"):
   self.assertIn('id="'+ident+'"',html)
  for href in ('./play.html','./pourquoi.html','./bilan.html','./lab.html'):
   self.assertIn(href,html)
  self.assertIn("phase13-modeles-evaluation-latest.json",js)
  for gate in ("real_bets_enabled!==false","verified_profitable_models!==0",
               "calibrated_models_approved!==0","ROI!==null",
               "no_auto_model_selection!==true"):
   self.assertIn(gate,js)
  self.assertIn("document.createElement",js)
  self.assertNotIn("innerHTML",js)
  result=subprocess.run(["node","--check",str(D/"phase13-modeles.js")],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_saved_prospective_models_do_not_promote(self):
  o=json.loads((D/"phase13-modeles-evaluation-latest.json").read_text())
  ledger=json.loads((D/"phase10-modeles-prospectif-ledger.json").read_text())
  self.assertEqual(o["version"],"revue_phase13_model_evaluation_v1")
  self.assertEqual(o["metrics"]["locked"],len(ledger["records"]))
  self.assertEqual(o["metrics"]["settled"],
                   sum(r["status"]=="settled" for r in ledger["records"].values()))
  self.assertEqual(o["metrics"]["distinct_settled_fixtures"],
                   len({(r["league"],r["event_id"]) for r in ledger["records"].values()
                        if r["status"]=="settled"}))
  self.assertFalse(o["real_bets_enabled"])
  self.assertFalse(o["original_clairvoyance_parity_proven"])
  self.assertEqual(o["verified_profitable_models"],0)
  self.assertEqual(o["calibrated_models_approved"],0)
  self.assertIsNone(o["ROI"])
  self.assertTrue(o["protocol"]["no_auto_model_selection"])
  self.assertTrue(all(v["approved_for_betting"] is False and
                      v["automatic_champion"] is False for v in o["models"].values()))
 def test_leagues_and_paired_definitions_not_relabelled(self):
  o=json.loads((D/"phase13-modeles-evaluation-latest.json").read_text())
  for key,r in o["models"].items():
   self.assertTrue(key.startswith(r["league"]+"::"))
   self.assertEqual(r["frozen_locked"],
     sum(x["model_id"]==r["model_id"] and x["league"]==r["league"]
         for x in json.loads((D/"phase10-modeles-prospectif-ledger.json").read_text())["records"].values()))
  self.assertTrue(all(p["auto_promote"] is False and
                      p["paired_samples_are_distinct_fixtures"] is True
                      for p in o["paired_comparisons"]))
  self.assertTrue(o["NHL"]["separate_official_NHL_source"])
if __name__=="__main__":unittest.main()
