"""Phase12 audits historical pregame forecasts separately from wager settlement."""
import copy,json,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from outils.phase12_audit import evaluate,VERSION
from outils.phase10_validation_prospective import lock,settle
from test_phase10_validation_prospective import observed,scores,NOW,KICK

D=Path(__file__).resolve().parents[1]/"docs"
def fixtures(settled=True):
 prospective=lock(None,observed(),NOW)
 when=NOW+timedelta(hours=12)
 if settled:prospective=settle(prospective,scores(when),when)
 nhl=json.loads((D/"nhl-shadow-ledger.json").read_text())
 picks=json.loads((D/"picks-center-latest.json").read_text())
 retro={"version":"revue_phase12_settlement_reconciliation_v1",
   "total_locks_after":len(prospective["records"]),
   "settled_after":sum(v["status"]=="settled" for v in prospective["records"].values()),
   "cross_source_conflicts":[]}
 return prospective,nhl,picks,retro,when
class Phase12QualityTests(unittest.TestCase):
 def test_actual_ledger_and_formula_pass(self):
  inp=fixtures()
  q=evaluate(*inp[:4],inp[4])
  self.assertEqual(q["version"],VERSION)
  self.assertEqual(q["multisport"]["settled"],3)
  self.assertEqual(q["multisport"]["pending"],0)
  # Live ledger grows as NHL games settle: compare to the ledger itself.
  expected=sum(e.get("status")=="settled" for e in inp[1]["events"])
  self.assertGreaterEqual(expected,1)
  self.assertEqual(q["NHL"]["settled"],expected)
  self.assertFalse(q["real_bets_enabled"])
  self.assertIsNone(q["ROI"])
  self.assertEqual(q["audit_errors"],[])
 def test_mutated_result_brier_reported(self):
  inp=list(fixtures())
  r=next(iter(inp[0]["records"].values()))
  r["brier"]+=.1
  q=evaluate(*inp[:4],inp[4])
  self.assertEqual(q["status"],"audit_error")
  self.assertGreater(len(q["audit_errors"]),0)
 def test_no_result_before_95_minutes(self):
  inp=list(fixtures())
  r=next(iter(inp[0]["records"].values()))
  r["resolved_at_utc"]=(KICK+timedelta(minutes=10)).isoformat()
  self.assertEqual(evaluate(*inp[:4],inp[4])["status"],"audit_error")
 def test_bad_status_cannot_look_settled(self):
  inp=list(fixtures(False))
  r=next(iter(inp[0]["records"].values()))
  r["result"]=1
  self.assertEqual(evaluate(*inp[:4],inp[4])["status"],"audit_error")
 def test_model_overdue_pending_is_visible(self):
  inp=fixtures(False)
  q=evaluate(*inp[:4],inp[4])
  self.assertEqual(q["multisport"]["overdue_pending"],3)
  self.assertEqual(q["multisport"]["settled"],0)
 def test_nhl_goals_mismatch_cannot_pass(self):
  inp=list(fixtures())
  r=next(x for x in inp[1]["events"] if x["status"]=="settled")
  r["home_goals"],r["away_goals"]=r["away_goals"],r["home_goals"]
  self.assertEqual(evaluate(*inp[:4],inp[4])["status"],"audit_error")
 def test_no_clairvoyance_profit_claims(self):
  inp=fixtures()
  q=evaluate(*inp[:4],inp[4])
  self.assertEqual(q["unverified_historical_NHL_bookmaker_markets_excluded"],
                   inp[2]["paper_summary"]["excluded"])
  self.assertFalse(q["original_predictions_modified"])
  self.assertFalse(q["calibrated"])
 def test_live_git_repo_snapshot_keeps_audit_green(self):
  files=("phase10-modeles-prospectif-ledger.json","nhl-shadow-ledger.json",
         "picks-center-latest.json","phase12-reconciliation-latest.json")
  source=[json.loads((D/f).read_text()) for f in files]
  report=evaluate(*source,datetime.now(timezone.utc))
  self.assertEqual(report["audit_errors"],[])
  self.assertEqual(report["multisport"]["locked"],len(source[0]["records"]))
  self.assertEqual(report["NHL"]["locked"],len(source[1]["events"]))
if __name__=="__main__":unittest.main()
