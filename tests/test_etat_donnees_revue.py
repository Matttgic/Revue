"""Revue data-completeness report: independent source freshness and refusal gates."""
import json
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path

from outils.etat_donnees_revue import FILES,layer,report

ROOT=Path(__file__).resolve().parents[1]/"docs"
DATA={k:json.loads((ROOT/p).read_text(encoding="utf-8"))
      for k,p in FILES.items() if (ROOT/p).exists()}
NOW=max(datetime.fromisoformat(d['generated_at_utc'].replace('Z','+00:00')) for d in DATA.values() if d.get('generated_at_utc'))+timedelta(minutes=2)


class SourceReadinessTests(unittest.TestCase):
    def test_current_real_data_report_has_no_betting_claims(self):
        r=report(DATA,NOW)
        self.assertEqual(len(r["layers"]),len(FILES))
        self.assertFalse(r["realtime_bookmaker_availability_verified"])
        self.assertFalse(r["uncalibrated_models_are_not_betting_advice"] is False)
        self.assertFalse(r["original_clairvoyance_end_to_end_parity"])
        self.assertEqual(r["verified_positive_ev_opportunities"],0)
        self.assertFalse(r["real_bets_enabled"])
        self.assertEqual(r["paid_api_requests_for_this_audit"],0)
        self.assertGreater(r["facts"]["simulations"],0)
        self.assertGreaterEqual(r["facts"]["simulations_reglees"],0)
        self.assertGreater(r["facts"]["championnats_calendrier"],0)
        self.assertIn("Gardiens", " ".join(r["remaining_blockers"]))

    def test_stale_model_is_not_declared_fresh(self):
        stale=deepcopy(DATA)
        stale["calendrier"]["generated_at_utc"]=(NOW-timedelta(days=3)).isoformat()
        r=report(stale,NOW)
        self.assertEqual(r["layers"]["calendrier"]["status"],"stale")
        self.assertFalse(r["all_essential_snapshots_fresh"])
        self.assertIn("calendrier",r["remaining_blockers"][0])

    def test_future_snapshot_rejected(self):
        future=deepcopy(DATA)
        future["cotes"]["generated_at_utc"]=(NOW+timedelta(hours=7)).isoformat()
        r=report(future,NOW)
        self.assertEqual(r["layers"]["cotes"]["status"],"invalid_timestamp")
        self.assertEqual(r["facts"]["cotes_fournisseur"],"unknown")

    def test_missing_sources_and_wrong_provenance_fail_closed(self):
        r=report({},NOW)
        self.assertEqual(r["fresh_essential_layers"],0)
        self.assertFalse(r["all_essential_snapshots_fresh"])
        self.assertEqual(r["facts"]["simulations"],0)
        fake=deepcopy(DATA)
        fake["resultats"]["pricing_used"]=True
        self.assertEqual(report(fake,NOW)["layers"]["resultats"]["status"],
                         "invalid_provenance")
        fake=deepcopy(DATA)
        fake["journal"]["real_bets_enabled"]=True
        self.assertEqual(report(fake,NOW)["layers"]["journal"]["status"],
                         "invalid_provenance")

    def test_naive_clock_refused(self):
        with self.assertRaises(ValueError):
            report(DATA,datetime(2026,10,10,18,0,0))

    def test_report_does_not_mutate_inputs(self):
        before=deepcopy(DATA)
        report(DATA,NOW)
        self.assertEqual(before,DATA)

if __name__=="__main__":unittest.main()
