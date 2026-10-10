"""Model Arena: no future leaked result, no synthesized real EV in browser."""
import json,re,subprocess,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"docs"
class ModelSiteTests(unittest.TestCase):
 def test_model_arena_is_linked_and_script_is_valid(self):
  html=(D/"phase10-modeles.html").read_text(encoding="utf8")
  lab=(D/"lab.html").read_text(encoding="utf8")
  js=(D/"phase10-modeles.js").read_text(encoding="utf8")
  self.assertIn('href="./phase10-modeles.html"',lab)
  for anchor in ("m10-status","m10-matches","m10-performance","m10-locked","m10-settled"):
   self.assertIn('id="'+anchor+'"',html)
  for source in ("phase10-modeles-multisports-latest.json",
                 "match-center-latest.json","phase10-modeles-performance.json"):
   self.assertIn(source,js)
  for marker in ("real_bets_enabled!==false","verified_positive_EV!==0",
                 "bookmaker_prices_are_live!==false","roi!==null",
                 "document.createElement","replaceChildren","prefers"):
   if marker=="prefers":continue
   self.assertIn(marker,js)
  self.assertNotIn("innerHTML",js)
  self.assertNotIn("Math.random",js)
  result=subprocess.run(["node","--check",str(D/"phase10-modeles.js")],
       capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_prospective_no_bets_from_real_snapshots(self):
  cand=json.loads((D/"phase10-modeles-multisports-latest.json").read_text())
  perf=json.loads((D/"phase10-modeles-performance.json").read_text())
  ledger=json.loads((D/"phase10-modeles-prospectif-ledger.json").read_text())
  self.assertEqual(cand["version"],"revue_phase10_multisport_model_candidates_v1")
  self.assertEqual(perf["version"],"revue_phase10_forward_ledger_v1")
  self.assertEqual(perf["total_locked"],len(ledger["records"]))
  self.assertEqual(cand["metrics"]["candidates"],len(cand["models"]))
  self.assertEqual(len({(m["league"],m["event_id"]) for m in cand["models"]}),
                   cand["metrics"]["events_covered"])
  self.assertFalse(perf["real_bets_enabled"])
  self.assertFalse(cand["real_bets_enabled"])
  self.assertFalse(perf["calibration_achieved"])
  self.assertEqual(cand["verified_positive_EV"],0)
  self.assertIsNone(perf["roi"])
  self.assertTrue(all(x["real_bet"] is False and x["stake_units"]==0
                 for x in ledger["records"].values()))
 def test_all_matches_are_approved_sports(self):
  models=json.loads((D/"phase10-modeles-multisports-latest.json").read_text())["models"]
  self.assertFalse(any(x["league"]=="CFB" for x in models))
  self.assertTrue(all(x["calibrated"] is False and x["EV"] is None
                      and x["betting_recommendation"] is None for x in models))
if __name__=="__main__":unittest.main()
