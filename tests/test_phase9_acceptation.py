import unittest,json
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.controles.phase9_acceptation_production import build,FILES,V
ROOT=Path(__file__).resolve().parents[1]/"docs"
class GateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.docs={x:json.loads((ROOT/x).read_text()) for x in FILES}
 def test_repo_safe(self):
  r=build(ROOT,self.docs,datetime.now(timezone.utc))
  self.assertEqual(r["version"],V)
  self.assertTrue(r["static_gate_passed"],r["blockers"])
  self.assertFalse(r["public_http_verified_in_report"])
  self.assertFalse(r["real_bets_enabled"])
 def test_forged_value_is_blocked(self):
  d=deepcopy(self.docs)
  d["phase7-prices-performance-latest.json"]["verified_positive_EV_opportunities"]=3
  self.assertIn("unsafe_odd_claim",build(ROOT,d,datetime.now(timezone.utc))["blockers"])
 def test_backfill_is_blocked(self):
  d=deepcopy(self.docs);d["phase2-owned-performance.json"]["replayed_old_results"]=True
  self.assertIn("backfilled_history_claim",build(ROOT,d,datetime.now(timezone.utc))["blockers"])
 def test_stale_is_warning(self):
  d=deepcopy(self.docs)
  d["match-center-latest.json"]["generated_at_utc"]=(datetime.now(timezone.utc)-timedelta(days=9)).isoformat()
  r=build(ROOT,d,datetime.now(timezone.utc))
  self.assertIn("match-center-latest.json:stale",r["warnings"])
if __name__=="__main__":unittest.main()
