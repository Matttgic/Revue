"""Tests hors ligne du moteur temporel indépendant. Pas de réseau ni de pari réel."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from modeles.reproduction.clairvoyance_lock_timing import (
    BASIS, classify, excluded_sport, game_start, iso_millis,
    is_parlay, match_key, revue_public_eligibility, revue_timing_report,
    schedule_index, source_scope, sport_code, summarize,
)

START = datetime(2026, 10, 10, 20, tzinfo=timezone.utc).timestamp() * 1000


def pick(**overrides):
    record = {
        "id": "paper-1", "sport": "NHL", "league": "NHL",
        "startMs": START, "lockedAt": START - 25 * 60000,
        "date": "2026-10-10", "hA": "BOS", "awA": "PHI",
        "outcome": "win", "betType": "ML",
    }
    record.update(overrides)
    return record


class OriginalTimingReconstruction(unittest.TestCase):
    def test_lead_boundaries(self):
        self.assertEqual(classify(pick()), "pre")
        self.assertEqual(classify(pick(lockedAt=START)), "during")
        self.assertEqual(classify(pick(lockedAt=START + 149 * 60000)), "during")
        self.assertEqual(classify(pick(lockedAt=START + 150 * 60000)), "after")
        self.assertEqual(classify(pick(sport="NFL", league="NFL", lockedAt=START + 150 * 60000)), "during")
        self.assertEqual(classify(pick(sport="PL", league="PL", lockedAt=START + 120 * 60000)), "after")

    def test_unknown_and_manual_late(self):
        self.assertEqual(classify(pick(startMs=None)), "unknown")
        self.assertEqual(classify(pick(startMs=None, lockTiming="late-manual")), "during")
        self.assertEqual(classify(pick(lockedAt=None)), "unknown")
        self.assertFalse(revue_public_eligibility(pick(startMs=None)))
        self.assertFalse(revue_public_eligibility(pick(startMs=None, lockTiming="late-manual")))

    def test_schedule_index_uses_denver_local_date_and_no_orientation(self):
        fixtures = [{"home": "BOS", "away": "PHI", "date": "2026-10-11T01:00:00Z"}]
        idx = schedule_index(fixtures)
        self.assertIn(match_key("2026-10-10", "PHI", "BOS"), idx)
        item = pick(startMs=None, hA="PHI", awA="BOS", date="2026-10-10",
                    lockedAt=iso_millis("2026-10-11T00:30:00Z"))
        self.assertEqual(game_start(item, idx), iso_millis("2026-10-11T01:00:00Z"))
        self.assertEqual(classify(item, idx), "pre")
        self.assertEqual(classify(item), "unknown")

    def test_invalid_dates_are_unknown_not_future_guesses(self):
        for invalid in (None, "", "2026-?", "1998-01-01T00:00:00Z", 1750000000000):
            self.assertIsNone(iso_millis(invalid))

    def test_alias_and_scope_without_cfb(self):
        self.assertEqual(sport_code(pick(sport="Football", league="NFL")), "NFL")
        self.assertEqual(sport_code(pick(sport="Hockey", league="NHL")), "NHL")
        self.assertEqual(sport_code(pick(sport="Premier League")), "PL")
        self.assertTrue(excluded_sport(pick(sport="CFB", league="CFB")))
        self.assertFalse(source_scope(pick(sport="CFB", league="CFB")))
        self.assertFalse(source_scope(pick(sport="MLS", league="MLS")))
        self.assertFalse(source_scope(pick(sport="BUND", league="BUND")))
        self.assertFalse(revue_public_eligibility(pick(sport="CFB", league="CFB")))

    def test_parlays_out_of_source_figures(self):
        for attrs in ({"betType": "PARLAY"}, {"betType": "PL_PARLAY"},
                      {"hA": "PARLAY"}, {"hA": "NBA-PARLAY"}):
            self.assertTrue(is_parlay(pick(**attrs)))
            self.assertFalse(source_scope(pick(**attrs)))

    def test_counting_source_includes_unknown_but_revue_does_not_certify(self):
        entries = [
            pick(id="a"), pick(id="b", startMs=None),
            pick(id="c", lockedAt=START + 30 * 60000, outcome="loss"),
            pick(id="d", lockedAt=START + 200 * 60000, outcome="loss"),
            pick(id="e", outcome="pending"), pick(id="f", sport="CFB", league="CFB"),
            pick(id="g", betType="PARLAY"),
        ]
        original_style = summarize(entries[:5])
        self.assertEqual(original_style["basis"], BASIS)
        self.assertEqual(original_style["settled_pre_start"], 1)
        self.assertEqual(original_style["settled_excluded_in_progress"], 1)
        self.assertEqual(original_style["settled_excluded_after_end"], 1)
        self.assertEqual(original_style["settled_unknown_timing_included"], 1)
        report = revue_timing_report(entries)
        self.assertEqual(report["revue_verified_pre_start_count"], 2) # pending is classified pre, not a settled gain
        self.assertEqual(report["source_compatible_timing"]["settled_pre_start"], 1)
        self.assertEqual(report["revue_unknown_not_verified"], 1)
        self.assertFalse(report["original_sql_parity_verified"])
        self.assertFalse(report["real_bets_enabled"])
        self.assertEqual(entries[0]["outcome"], "win")

    def test_empty_and_immutable(self):
        self.assertEqual(revue_timing_report([])["revue_verified_pre_start_count"], 0)
        inputs = [pick(id="p")]
        old = copy.deepcopy(inputs)
        revue_timing_report(inputs)
        self.assertEqual(inputs, old)


if __name__ == "__main__":
    unittest.main()
