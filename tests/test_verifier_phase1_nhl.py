"""Phase 1 fidelity acceptance must not become green without private input/output parity."""
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json

from outils.clairvoyance.verifier_phase1_nhl import report, VERSION

DOCS=Path(__file__).resolve().parents[1]/"docs"
load=lambda name:json.loads((DOCS/name).read_text(encoding="utf8"))
P=load("parite-modeles-clairvoyance.json")
F=load("clairvoyance-nhl-forensics.json")
I=load("parite-donnees-clairvoyance.json")
PRO=load("nhl-frontend-prospective-performance.json")
WHEN=datetime(2026,10,10,20,tzinfo=timezone.utc)
ELO={
    "version":"revue_elo_settlement_only_source_semantics_v1",
    "status":"source_elo_update_math_verified_private_state_unknown",
    "reference_k_factor":32,
    "reference_initial_elo":1500.0,
    "updates_only_on_settled_moneyline_picks":True,
    "updates_every_completed_nhl_game":False,
    "paper_ledger_modified":False,
    "real_bets_enabled":False,
    "original_sql_elo_values_available":False,
    "identical_original_settled_pick_history_verified":False,
    "original_sql_ordering_verified":False,
    "eligible_revue_settled_moneyline_updates":0,
}


class FidelityGate(unittest.TestCase):
    def test_real_fixtures_show_formulas_and_xg_not_published_model_parity(self):
        a=report(P,F,ELO,I,PRO,WHEN)
        self.assertEqual(a["version"],VERSION)
        self.assertFalse(a["phase1_completed"])
        self.assertTrue(a["acceptance_gates"]["public_formula_subset_same_input_parity"])
        self.assertTrue(a["acceptance_gates"]["public_nhl_fixture_and_xg_alignment"])
        self.assertTrue(a["acceptance_gates"]["source_elo_update_algorithm"])
        self.assertFalse(a["acceptance_gates"]["original_elo_sql_state_and_settlement_history"])
        self.assertFalse(a["acceptance_gates"]["same_as_original_licensed_or_private_inputs"])
        self.assertFalse(a["acceptance_gates"]["identical_published_probabilities"])
        self.assertFalse(a["acceptance_gates"]["original_published_model_identity"])
        self.assertFalse(a["acceptance_gates"]["prospective_nhl_100_outcomes_for_initial_quality"])
        self.assertEqual(a["checkpoint"]["verified_target_formulas"],44)
        self.assertEqual(a["checkpoint"]["identical_public_5v5_xg_nhl_games"],F["input_summary"]["identical_5v5_xg_both_teams"])
        self.assertEqual(a["checkpoint"]["published_nhl_moneyline_comparisons"],F["model_summary"]["moneyline"]["comparisons"])
        self.assertEqual(a["checkpoint"]["published_nhl_moneyline_mean_gap_pp"],F["model_summary"]["moneyline"]["mean_absolute_gap_pp"])
        self.assertEqual(a["checkpoint"]["original_source_data_checks_done"],I["completed_data_checks"])
        self.assertFalse(a["real_bets_enabled"])

    def test_no_guessed_original_elo_state(self):
        modified=deepcopy(ELO)
        modified["original_sql_elo_values_available"]=True
        a=report(P,F,modified,I,PRO,WHEN)
        self.assertFalse(a["acceptance_gates"]["original_elo_sql_state_and_settlement_history"])
        modified["identical_original_settled_pick_history_verified"]=True
        a=report(P,F,modified,I,PRO,WHEN)
        self.assertFalse(a["acceptance_gates"]["original_elo_sql_state_and_settlement_history"])
        modified["original_sql_ordering_verified"]=True
        a=report(P,F,modified,I,PRO,WHEN)
        self.assertTrue(a["acceptance_gates"]["original_elo_sql_state_and_settlement_history"])
        self.assertFalse(a["phase1_completed"])

    def test_elo_updating_every_final_game_is_wrong_even_with_k32(self):
        fake=deepcopy(ELO)
        fake["updates_every_completed_nhl_game"]=True
        a=report(P,F,fake,I,PRO,WHEN)
        self.assertFalse(a["acceptance_gates"]["source_elo_update_algorithm"])
        self.assertFalse(a["phase1_completed"])

    def test_different_published_bestbet_model_cannot_be_called_exact(self):
        f=deepcopy(F)
        f["exact_prediction_replication_verified"]=True
        f["model_summary"]["moneyline"]["mean_absolute_gap_pp"]=0
        f["model_summary"]["moneyline"]["comparisons"]=40
        a=report(P,f,ELO,I,PRO,WHEN)
        self.assertFalse(a["acceptance_gates"]["original_published_model_identity"])
        self.assertFalse(a["phase1_completed"])

    def test_unverified_formula_catalogue_is_not_phase1_pass(self):
        p=deepcopy(P)
        p["verified_formula_parity_models"]=43
        a=report(p,F,ELO,I,PRO,WHEN)
        self.assertFalse(a["acceptance_gates"]["public_formula_subset_same_input_parity"])

    def test_naive_clock_rejected(self):
        with self.assertRaises(ValueError):
            report(P,F,ELO,I,PRO,datetime(2026,10,10,20))


if __name__=="__main__":
    unittest.main()
