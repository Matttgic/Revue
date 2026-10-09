"""Tests du garde-fou original de chronologie Revue."""
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from outils.chronologie_pre_match import (
    Decision,
    PRE_VALIDE,
    TARDIF,
    INDETERMINE,
    COTE_NON_VERIFIABLE,
    FEATURE_NON_VERIFIABLE,
    admissible_backtest,
    bilan,
    classifier,
)


class TestChronologiePreMatch(unittest.TestCase):
    def setUp(self):
        utc = timezone.utc
        self.d = Decision(
            evenement_id="match-test",
            verrouille_le=datetime(2026, 10, 9, 18, 0, tzinfo=utc),
            debut_evenement=datetime(2026, 10, 9, 19, 0, tzinfo=utc),
            cote_observee_le=datetime(2026, 10, 9, 17, 59, tzinfo=utc),
            derniere_feature_publiee_le=datetime(2026, 10, 9, 16, 0, tzinfo=utc),
        )

    def test_pre_valide(self):
        self.assertEqual(classifier(self.d), PRE_VALIDE)
        self.assertTrue(admissible_backtest(self.d))

    def test_match_deja_commence(self):
        self.assertEqual(classifier(replace(self.d, verrouille_le=self.d.debut_evenement)), TARDIF)

    def test_verrouillage_apres_match(self):
        late = self.d.debut_evenement + timedelta(hours=4)
        self.assertEqual(classifier(replace(self.d, verrouille_le=late)), TARDIF)

    def test_lock_absent_exclu(self):
        d = replace(self.d, verrouille_le=None)
        self.assertEqual(classifier(d), INDETERMINE)
        self.assertFalse(admissible_backtest(d))

    def test_naive_dates_exclues(self):
        self.assertEqual(classifier(replace(self.d, debut_evenement=datetime(2026, 10, 9, 19))), INDETERMINE)

    def test_cote_inexistante_exclue(self):
        self.assertEqual(classifier(replace(self.d, cote_observee_le=None)), COTE_NON_VERIFIABLE)

    def test_cote_observee_apres_lock(self):
        q = replace(self.d, cote_observee_le=self.d.verrouille_le + timedelta(seconds=2))
        self.assertEqual(classifier(q), COTE_NON_VERIFIABLE)

    def test_feature_future_exclue(self):
        d = replace(self.d, derniere_feature_publiee_le=self.d.verrouille_le + timedelta(minutes=1))
        self.assertEqual(classifier(d), FEATURE_NON_VERIFIABLE)

    def test_timezone_offsets_comparables(self):
        plus_two = timezone(timedelta(hours=2))
        d = replace(self.d, verrouille_le=self.d.verrouille_le.astimezone(plus_two))
        self.assertEqual(classifier(d), PRE_VALIDE)

    def test_bilan_conserve_tous_les_exclus(self):
        items = [self.d, replace(self.d, verrouille_le=None),
                 replace(self.d, verrouille_le=self.d.debut_evenement)]
        self.assertEqual(bilan(items)[PRE_VALIDE], 1)
        self.assertEqual(bilan(items)[INDETERMINE], 1)
        self.assertEqual(bilan(items)[TARDIF], 1)


if __name__ == "__main__":
    unittest.main()
