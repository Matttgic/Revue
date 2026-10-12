"""Tests du banc d'essai NHL contre la clôture : nettoyage, absence de fuite, calculs."""
import math
import random
import unittest
from dataclasses import replace
from datetime import date, timedelta

from outils.suivi.banc_nhl_cloture import (
    Match, ParamsFiltre, ajuster_logistique, appliquer_logistique, choisir_devig, nettoyer,
    predictions_filtre, predictions_revue, simuler_paris, verdict,
)

EQUIPES = ["Bruins", "Rangers", "Kings", "Sharks", "Jets", "Coyotes"]


def saison_synthetique(annee: int, graine: int = 1) -> list[Match]:
    rng = random.Random(graine + annee)
    debut, matchs = date(annee, 10, 5), []
    for jour in range(60):
        eq = EQUIPES[:]
        rng.shuffle(eq)
        for k in range(0, 6, 2):
            bd, be = rng.randint(0, 5), rng.randint(0, 5)
            if bd == be:
                bd += 1
            matchs.append(Match(debut + timedelta(days=jour), annee, eq[k], eq[k + 1], bd, be,
                                (1.9, 2.0), (1.85, 2.05)))
    return matchs


class TestNettoyage(unittest.TestCase):
    def test_normalise_et_exclut(self):
        base = {"season": 2013, "date": 20131010.0, "home_final": "3", "away_final": "2",
                "home_open_ml": -150, "away_open_ml": 130, "home_close_ml": -160, "away_close_ml": 140}
        lignes = [
            {**base, "home_team": "Phoenix", "away_team": "Tampa"},
            {**base, "home_team": "Phoenix", "away_team": "Tampa"},                     # doublon
            {**base, "home_team": 0, "away_team": "Kings"},                              # équipe absente
            {**base, "home_team": "Kings", "away_team": "Jets", "away_final": "3"},      # nul
            {**base, "home_team": "Kings", "away_team": "Wild", "home_close_ml": 150, "away_close_ml": 150},
        ]
        matchs, exclus = nettoyer(lignes)
        self.assertEqual(len(matchs), 1)
        self.assertEqual((matchs[0].dom, matchs[0].ext), ("Coyotes", "Lightning"))
        self.assertEqual(exclus, {"doublon": 1, "equipe_absente": 1, "nul": 1, "cotes_incoherentes": 1})


class TestAbsenceDeFuite(unittest.TestCase):
    """Changer les résultats du jour d ne doit modifier aucune prédiction des jours <= d (décalage 1)."""

    def setUp(self):
        self.matchs = saison_synthetique(2013) + saison_synthetique(2014)
        self.jour = self.matchs[len(self.matchs) // 4].jour  # milieu de la saison 2013
        self.modifies = [replace(m, buts_dom=m.buts_ext, buts_ext=m.buts_dom) if m.jour >= self.jour else m
                         for m in self.matchs]

    def _jusqua(self, preds):
        return {i: p for i, p in preds.items() if self.matchs[i].jour <= self.jour}

    def test_filtre(self):
        p = ParamsFiltre(0.001, 0.1, 0.75, 0.05)
        self.assertEqual(self._jusqua(predictions_filtre(self.matchs, p)),
                         self._jusqua(predictions_filtre(self.modifies, p)))

    def test_modele_revue(self):
        a, b = predictions_revue(self.matchs), predictions_revue(self.modifies)
        self.assertTrue(self._jusqua(a))
        self.assertEqual(self._jusqua(a), self._jusqua(b))
        self.assertNotEqual(a, b)  # les jours suivants, eux, changent bien

    def test_decalage_deux_ignore_la_veille(self):
        veille = self.jour - timedelta(days=1)
        modifies = [replace(m, buts_dom=m.buts_ext, buts_ext=m.buts_dom) if m.jour == veille else m
                    for m in self.matchs]
        p = ParamsFiltre(0.001, 0.1, 0.75, 0.05)
        jour_j = lambda preds: {i: v for i, v in preds.items() if self.matchs[i].jour == self.jour}
        self.assertEqual(jour_j(predictions_filtre(self.matchs, p, 2)), jour_j(predictions_filtre(modifies, p, 2)))
        self.assertNotEqual(jour_j(predictions_filtre(self.matchs, p, 1)), jour_j(predictions_filtre(modifies, p, 1)))


class TestCalculs(unittest.TestCase):
    def test_logistique_retrouve_les_coefficients(self):
        rng = random.Random(7)
        x = [[rng.gauss(0, 1), rng.gauss(0, 1)] for _ in range(4000)]
        vrai = [0.3, 1.2, -0.7]
        y = [1 if rng.random() < appliquer_logistique(vrai, xi) else 0 for xi in x]
        b = ajuster_logistique(x, y)
        for estime, attendu in zip(b, vrai):
            self.assertAlmostEqual(estime, attendu, delta=0.15)

    def test_paris_et_clv(self):
        m = Match(date(2016, 1, 1), 2016, "Bruins", "Kings", 3, 1, (2.2, 1.7), (2.0, 1.85))
        r = simuler_paris([m], [0.55], "multiplicative")  # EV domicile = 0,55 × 2,2 − 1 = 0,21
        self.assertEqual(r["paris"], 1)
        self.assertAlmostEqual(r["roi"]["mean"], 1.2)
        p_clo = (1 / 2.0) / (1 / 2.0 + 1 / 1.85)
        self.assertAlmostEqual(r["clv"]["mean"], round(2.2 * p_clo - 1, 4))
        self.assertEqual(r["part_cote_superieure_a_la_cloture"], 1.0)

    def test_verdict_abandon(self):
        paris = {"paris": 400, "roi": {"n": 400, "mean": -0.05, "ci95": [-0.09, -0.01]},
                 "clv": {"n": 400, "mean": -0.03, "ci95": [-0.04, -0.02]}}
        self.assertEqual(verdict(paris, None)["verdict"], "abandon")

    def test_devig_par_defaut_multiplicative(self):
        methode, _ = choisir_devig(saison_synthetique(2012) + saison_synthetique(2013))
        self.assertEqual(methode, "multiplicative")  # cotes constantes : aucune méthode ne gagne


if __name__ == "__main__":
    unittest.main()
