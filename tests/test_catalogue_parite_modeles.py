import unittest
from datetime import datetime,timezone
from outils.catalogue_parite_modeles import MODELS,generate
NOW=datetime(2026,10,9,tzinfo=timezone.utc)
def data():
    return {"status":"predictor_formula_parity_verified",
            "exact_equality_tests_passed":43,
            "reference_commit":"demo",
            "verified_modules":["backend_mlb_elo","backend_nhl_elo_moneypuck_goalie"]}
def audit():
    return {"frontend_model_symbols":{"model_symbols":[{"name":model[-1]} for model in MODELS if model[2]=="docs/app.html"]}}
class ReproductionOnlyProgressTests(unittest.TestCase):
    def test_two_of_13_are_exactly_verified(self):
        p=generate(data(),audit(),NOW)
        self.assertEqual(p["total_target_models"],13)
        self.assertEqual(p["verified_formula_parity_models"],2)
        self.assertEqual(p["formula_parity_percent"],15)
        self.assertIsNone(p["overall_repository_reproduction_percent"])
        self.assertEqual(p["remaining_unverified"],11)
        self.assertIn("CFB",p["excluded"])
    def test_original_models_never_count(self):
        p=generate({"status":"experimental_no_bets","verified_modules":["backend_mlb_elo"],"exact_equality_tests_passed":999},audit(),NOW)
        self.assertEqual(p["verified_formula_parity_models"],0)
        self.assertEqual(p["formula_parity_percent"],0)
    def test_missing_equality_never_count(self):
        q=data();q["exact_equality_tests_passed"]=0
        self.assertEqual(generate(q,audit(),NOW)["verified_formula_parity_models"],0)
    def test_all_frontend_pending_before_source_parity(self):
        p=generate(data(),audit(),NOW)
        self.assertTrue(all(m["status"]=="pending_implementation_or_parity"
                            for m in p["models"] if m["source_file"]=="docs/app.html"))
    def test_live_data_parity_not_claimed(self):
        p=generate(data(),audit(),NOW)
        self.assertTrue(all(m["reproduced_with_same_data"] is False for m in p["models"]))
        self.assertIsNone(p["prediction_parity_on_live_data_percent"])
if __name__=="__main__":
    unittest.main()
