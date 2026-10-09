"""Tests du calculateur indépendant de sensibilité au de-vig."""
import math
import unittest

from outils.sensibilite_devig import additive, comparer_methodes, multiplicative, puissance


class TestSensibiliteDevig(unittest.TestCase):
    def test_egalite_sur_deux_issues_symetriques(self):
        for methode in (multiplicative, additive, puissance):
            self.assertEqual(len(methode([1.9, 1.9])), 2)
            for p in methode([1.9, 1.9]):
                self.assertAlmostEqual(p, .5, places=10)

    def test_somme_probabilites_1x2(self):
        result = comparer_methodes([1.25, 6.5, 13.0])
        self.assertEqual(result["nombre_issues"], 3)
        for probabilities in result["probabilites"].values():
            self.assertAlmostEqual(sum(probabilities), 1.0, places=10)
            self.assertTrue(all(0 < p < 1 for p in probabilities))

    def test_sensibilite_longshot(self):
        data = comparer_methodes([1.25, 6.5, 13.0])
        self.assertGreater(data["dispersion_pp"][2], 0.01)

    def test_additive_refuse_probabilite_negative(self):
        self.assertIsNone(additive([1.1, 1.1, 100.0]))
        result = comparer_methodes([1.1, 1.1, 100.0])
        self.assertNotIn("additive", result["probabilites"])

    def test_marche_equilibre_faible_marge(self):
        data = comparer_methodes([2.0, 2.0])
        self.assertAlmostEqual(data["marge_brute_pp"], 0.0)
        self.assertAlmostEqual(data["dispersion_pp"][0], 0.0, places=10)

    def test_rejette_cotes_invalides(self):
        for odds in ([], [1.6], [1.2, 4.5, 8, 12], [1, 2.0],
                     [0.8, 2.0], [float("nan"), 2.0],
                     [float("inf"), 2.0], ["a", 2]):
            with self.subTest(odds=odds), self.assertRaises(ValueError):
                comparer_methodes(odds)

    def test_cotes_numeriques_finies(self):
        for proba in puissance([1.6, 2.6]):
            self.assertTrue(math.isfinite(proba))

    def test_underround_possible(self):
        data = comparer_methodes([2.2, 2.2])
        self.assertLess(data["marge_brute_pp"], 0)
        self.assertAlmostEqual(sum(data["probabilites"]["puissance"]), 1.0)


if __name__ == "__main__":
    unittest.main()
