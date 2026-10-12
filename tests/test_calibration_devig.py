"""Tests de la calibration des méthodes de retrait de marge."""
import json
import math
import tempfile
import unittest
from pathlib import Path

from outils.controles.calibration_devig import (
    METHODES, additive, americaine_vers_decimale, evaluer, lignes_sbr, rapport_de_cotes, shin,
)


class TestMethodes(unittest.TestCase):
    def test_somme_egale_un(self):
        for cotes in ([4.20, 3.70, 1.95], [1.19, 7.0, 14.0], [1.25, 4.0], [1.9, 1.9]):
            for nom, methode in METHODES.items():
                with self.subTest(nom=nom, cotes=cotes):
                    self.assertAlmostEqual(sum(methode(cotes)), 1.0, places=9)

    def test_shin_deux_issues_egale_additive(self):
        # Identité connue : sur deux issues, Shin et la méthode additive coïncident.
        for cotes in ([1.25, 4.0], [1.5, 2.6], [1.08, 8.5]):
            for a, b in zip(shin(cotes), additive(cotes)):
                self.assertAlmostEqual(a, b, places=8)

    def test_shin_trois_issues_reference(self):
        # Valeur de référence : racine exacte (contrôle R du paquet implied, shin_method='uniroot').
        p = shin([4.20, 3.70, 1.95])
        for obtenu, attendu in zip(p, [0.231572, 0.263574, 0.504854]):
            self.assertAlmostEqual(obtenu, attendu, places=5)

    def test_favori_corrige_plus_que_multiplicatif(self):
        # Les méthodes non proportionnelles attribuent plus au favori (biais favori-outsider).
        mult = METHODES["multiplicative"]([1.25, 4.0])[0]
        for nom in ("additive", "puissance", "shin", "rapport_de_cotes"):
            self.assertGreater(METHODES[nom]([1.25, 4.0])[0], mult, nom)

    def test_rapport_de_cotes_sans_marge(self):
        self.assertEqual(rapport_de_cotes([2.0, 2.0]), [0.5, 0.5])


class TestEvaluation(unittest.TestCase):
    def test_diff_appariee(self):
        lignes = [([1.25, 4.0], 0), ([1.25, 4.0], 1), ([2.0, 1.8], 1)]
        r = evaluer(lignes)
        self.assertEqual(r["n"], 3)
        self.assertEqual(r["methodes"]["multiplicative"]["diff_vs_multiplicative"], 0.0)
        attendu = -sum(math.log(METHODES["shin"](c)[g]) for c, g in lignes) / 3
        self.assertAlmostEqual(r["methodes"]["shin"]["logloss"], round(attendu, 6), places=6)

    def test_exclut_ligne_si_une_methode_echoue(self):
        r = evaluer([([1.1, 1.1, 100.0], 0), ([2.0, 3.5, 3.6], 0), ([1.5, 4.0, 6.5], 2)])
        self.assertEqual(r["lignes_exclues"], 1)
        self.assertEqual(r["n"], 2)

    def test_lecture_sbr(self):
        self.assertAlmostEqual(americaine_vers_decimale(-150), 1 + 100 / 150)
        self.assertAlmostEqual(americaine_vers_decimale(130), 2.3)
        donnees = [
            {"home_close_ml": -150, "away_close_ml": 130, "home_final": "3", "away_final": "2"},
            {"home_close_ml": -110, "away_close_ml": -110, "home_final": "1", "away_final": "1"},  # nul exclu
            {"home_close_ml": 150, "away_close_ml": 150, "home_final": "1", "away_final": "4"},  # somme < 1 exclue
        ]
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "nhl.json"
            chemin.write_text(json.dumps(donnees), encoding="utf-8")
            lignes = list(lignes_sbr(chemin))
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0][1], 0)


if __name__ == "__main__":
    unittest.main()
