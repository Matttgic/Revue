"""Tests indépendants du validateur original de Revue."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from outils.validateur_cotes import Cotation, esperance_de_gain


class TestCotes(unittest.TestCase):
    def setUp(self):
        self.quote = Cotation(
            bookmaker="Bookmaker autorisé (exemple)",
            marche="1N2",
            selection="Domicile",
            cote_decimale=1.80,
            observee_le=datetime(2026, 10, 9, 12, tzinfo=timezone.utc),
            debut_evenement=datetime(2026, 10, 9, 19, tzinfo=timezone.utc),
            provenance="agregateur_autorise",
            identifiant_source="exemple-ID-de-cotation",
        )

    def test_ev_avec_cote_observee(self):
        self.assertAlmostEqual(esperance_de_gain(0.60, self.quote), 0.08)

    def test_ev_negative_est_possible(self):
        self.assertAlmostEqual(esperance_de_gain(0.50, self.quote), -0.10)

    def test_rejet_cote_synthetique(self):
        with self.assertRaises(ValueError):
            esperance_de_gain(0.60, replace(self.quote, provenance="modele"))

    def test_rejet_cote_post_match(self):
        with self.assertRaises(ValueError):
            esperance_de_gain(
                0.60, replace(self.quote, observee_le=self.quote.debut_evenement)
            )

    def test_rejet_source_vide(self):
        with self.assertRaises(ValueError):
            esperance_de_gain(
                0.60, replace(self.quote, identifiant_source=" ")
            )

    def test_rejet_probabilite_invalide(self):
        for p in (-0.1, 1.1, float("nan"), float("inf"), None):
            with self.subTest(p=p), self.assertRaises(ValueError):
                esperance_de_gain(p, self.quote)

    def test_rejet_cote_ou_date_invalide(self):
        for quote in (
            replace(self.quote, cote_decimale=1.0),
            replace(self.quote, cote_decimale=float("nan")),
            replace(self.quote, observee_le=datetime(2026, 10, 9, 12)),
            replace(self.quote, bookmaker=""),
        ):
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                esperance_de_gain(0.60, quote)

    def test_identite_cote_avec_marge(self):
        p, marge = 0.60, 0.05
        self.assertAlmostEqual(p * ((1 - marge) / p) - 1, -marge)


if __name__ == "__main__":
    unittest.main()
