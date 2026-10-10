"""Phase11 public source truth: model/data differences cannot be hidden."""
import json,re,subprocess,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"docs"
class SourceSiteTests(unittest.TestCase):
 def test_public_screen_is_mobile_and_has_source_gate(self):
  page=(D/"phase11-donnees.html").read_text(encoding="utf8")
  script=(D/"phase11-data.js").read_text(encoding="utf8")
  lab=(D/"lab.html").read_text(encoding="utf8")
  for name in ("p11-state","p11-sports","p11-goalies","p11-pitchers",
               "p11-quarantine","p11-quarantine-count"):
   self.assertIn('id="'+name+'"',page)
  self.assertIn('href="./phase11-donnees.html"',lab)
  self.assertIn('href="./lab.html"',page)
  self.assertIn('href="./play.html"',page)
  self.assertIn('href="./pourquoi.html"',page)
  self.assertIn('href="./bilan.html"',page)
  for name in ("phase11-source-quality-latest.json","mlb-official-probable-pitchers-latest.json"):
   self.assertIn(name,script)
  self.assertIn("verified_EV_opportunities!==0",script)
  self.assertIn("real_bets_enabled!==false",script)
  self.assertIn("paper_ledger_modified!==false",script)
  self.assertIn("document.createElement",script)
  self.assertNotIn("innerHTML",script)
  for name in ("phase11-data.js","retro-app.js"):
   result=subprocess.run(["node","--check",str(D/name)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
 def test_source_report_is_paper_only_and_no_fake_pitcher_confirmation(self):
  q=json.loads((D/"phase11-source-quality-latest.json").read_text(encoding="utf8"))
  p=json.loads((D/"picks-center-latest.json").read_text(encoding="utf8"))
  mlb=json.loads((D/"mlb-official-probable-pitchers-latest.json").read_text(encoding="utf8"))
  self.assertEqual(q["version"],"revue_phase11_source_quality_v1")
  self.assertFalse(q["paper_ledger_modified"])
  self.assertFalse(q["model_probabilities_modified"])
  self.assertFalse(q["real_bets_enabled"])
  self.assertFalse(q["source_parity_100_percent"])
  self.assertEqual(q["verified_EV_opportunities"],0)
  self.assertEqual(q["paper_market_quarantine"]["total"],p["paper_summary"]["excluded"])
  self.assertTrue(all(x["resolution"]=="quarantined_no_retroactive_settlement"
                      and x["included_in_settled_roi"] is False for x in
                      q["paper_market_quarantine"]["records"]))
  self.assertEqual(mlb["confirmed_starting_pitchers"],0)
  self.assertFalse(mlb["model_recomputed"])
  self.assertTrue(all(x["pitchers_are_probable_not_confirmed"] and
                      x["starting_pitchers_independently_confirmed"] is False
                      for x in mlb["rows"]))
 def test_espn_goalie_rows_are_statused_without_model_bias(self):
  q=json.loads((D/"phase11-source-quality-latest.json").read_text(encoding="utf8"))
  g=q["NHL_espn_observations"]
  self.assertFalse(g["used_in_prediction"])
  self.assertEqual(g["actual_game_starts_independently_verified"],0)
  self.assertTrue(all(f["probabilities_modified"] is False and
                      f["source_ready_for_lineup_dependent_models"] is False for f in g["fixtures"]))
if __name__=="__main__":unittest.main()
