"""Offline quality checks for the official MoneyPuck-derived NHL snapshot."""
from __future__ import annotations
from datetime import datetime, timezone
import unittest

from outils.moneypuck_feed import (
    Download, create_snapshot, derive_rows, season_year, source_url, _clean_fraction
)

UTC = timezone.utc

def sample(team="NYR", value="0.55", games="3", situation="5on5"):
    return ("team,situation,games_played,iceTime,goalsFor,goalsAgainst,"
            "shotsOnGoalFor,shotsOnGoalAgainst,xGoalsFor,xGoalsAgainst,"
            "xGoalsPercentage,corsiPercentage,fenwickPercentage\n"
            f"{team},{situation},{games},10800,11,7,101,89,9.8,7.9,{value},0.52,0.50\n")


class OfficialMoneyPuckFeedTests(unittest.TestCase):
    def test_nhl_season_boundary(self):
        self.assertEqual(season_year(datetime(2026, 7, 1, tzinfo=UTC)), 2025)
        self.assertEqual(season_year(datetime(2026, 10, 10, tzinfo=UTC)), 2026)

    def test_only_official_regular_season_csv_url(self):
        self.assertEqual(source_url(2026),
            "https://moneypuck.com/moneypuck/playerData/seasonSummary/2026/regular/teams.csv")
        with self.assertRaises(ValueError):
            source_url(1900)

    def test_parity_parser_used_and_values_normalized(self):
        rows = derive_rows(sample(), 2026)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["team"], row["season"]), ("NYR", "2026-2027"))
        self.assertEqual(row["xg_share"], 0.55)
        self.assertAlmostEqual(row["xg_for_60"], 3.2667)
        self.assertAlmostEqual(row["shots_for_60"], 33.6667)
        self.assertEqual(row["games_played"], 3)
        self.assertAlmostEqual(row["save_pct"], round(1 - 7/89, 4))

    def test_fraction_or_percentage(self):
        self.assertEqual(_clean_fraction(53.5), 0.535)
        self.assertEqual(_clean_fraction(.535), .535)
        self.assertIsNone(_clean_fraction(float("nan")))
        self.assertIsNone(_clean_fraction(-2))
        self.assertIsNone(_clean_fraction(121))

    def test_no_ghost_teams_or_unplayed_or_bad_schema(self):
        self.assertEqual(derive_rows(sample(team="INVALIDTEAM"), 2026), [])
        self.assertEqual(derive_rows(sample(games="0"), 2026), [])
        self.assertEqual(derive_rows(sample(situation="other"), 2026), [])
        with self.assertRaises(ValueError):
            derive_rows("team,situation\nNYR,5on5\n", 2026)

    def test_historical_season_never_claimed_current(self):
        now = datetime(2026, 10, 10, 1, 0, tzinfo=UTC)
        def fetch(year):
            if year == 2026:
                raise TimeoutError("offline")
            return Download(sample(team="BOS", value="51.5"),
                            "Fri, 09 Oct 2026 02:00:00 GMT")
        doc = create_snapshot(now, fetch)
        self.assertEqual(doc["current_season"], "2026-2027")
        self.assertIn("seconds", doc["unit_note"])
        self.assertFalse(doc["seasons"]["2026-2027"])
        self.assertEqual(doc["status"]["2026-2027"]["status"], "unavailable")
        self.assertEqual(doc["seasons"]["2025-2026"][0]["season"], "2025-2026")
        self.assertFalse(doc["is_live"])

    def test_provenance_present_for_both_seasons(self):
        now = datetime(2026, 10, 10, 1, 0, tzinfo=UTC)
        def fetch(year):
            return Download(sample(team="BOS" if year == 2025 else "NYR"))
        doc = create_snapshot(now, fetch)
        self.assertEqual(sum(len(v) for v in doc["seasons"].values()), 2)
        self.assertIn("moneypuck.com/data.htm", doc["source_page"])
        self.assertIn("non-commercial", doc["licence_scope"].lower())
        self.assertIsNone(doc["status"]["2026-2027"]["source_updated_utc"])

    def test_fails_closed_when_all_sources_unavailable(self):
        def fail(year):
            raise ConnectionError("No internet")
        # ConnectionError is OSError; never publish an apparently fresh empty file.
        with self.assertRaises(RuntimeError):
            create_snapshot(datetime(2026, 10, 10, tzinfo=UTC), fail)


if __name__ == "__main__":
    unittest.main()
