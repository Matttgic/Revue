"""Official NHL Stats REST adapter tests with mock, not fabricated production data."""
from datetime import datetime,timezone
import unittest
from outils.nhl_official_stats_revue import clean,positive_number,source_id

NOW=datetime(2026,10,10,tzinfo=timezone.utc)


def fixture():
    directory=[
        {"id":i,"triCode":f"T{i:02d}"} for i in range(1,29)
    ]
    teams=[
        {"teamId":i,"teamFullName":f"Test Team {i}",
         "gamesPlayed":i%4,"wins":1,"losses":0,"otLosses":0,
         "goalsFor":3,"goalsAgainst":1,"goalsForPerGame":3.0,
         "goalsAgainstPerGame":1.0}
        for i in range(1,29)
    ]
    return {
        "team_directory":directory,
        "team_summary":teams,
        "team_powerplay":[{"teamId":1,"powerPlayPct":.23}],
        "team_penaltykill":[{"teamId":1,"penaltyKillPct":.81}],
        "goalie_summary":[
            {"playerId":8945,"goalieFullName":"Sample Goalie",
             "teamAbbrevs":"T01","gamesPlayed":4,
             "savePct":.923,"goalsAgainstAverage":2.1},
            {"playerId":8946,"goalieFullName":"Moved Goalie",
             "teamAbbrevs":"T01,T02","gamesPlayed":6,
             "savePct":.9},
        ],
        "goalie_strength":[{"playerId":8945,"evSaves":71,"evSavePct":.922}],
        "skater_summary":[{"playerId":9876,"skaterFullName":"Sample Skater",
                           "teamAbbrevs":"T02","gamesPlayed":4}],
        "skater_shots":[{"playerId":9876,"wristShots":8,"slapShots":2}],
    }


class NHLStatsSnapshotTests(unittest.TestCase):
    def test_official_fields_and_own_ids_only(self):
        report=clean(fixture(),"20262027",NOW)
        self.assertEqual(len(report["teams"]),28)
        self.assertEqual(report["teams"][0]["team_abbrev"],"T01")
        self.assertEqual(report["teams"][0]["wins"],1)
        self.assertEqual(report["teams"][0]["pp_pct"],.23)
        self.assertEqual(report["teams"][0]["pk_pct"],.81)
        goalie=report["goalies"][0]
        self.assertEqual(goalie["player_id"],8945)
        self.assertEqual(goalie["overall_save_pct"],.923)
        self.assertEqual(goalie["saves_even_strength"],71)
        self.assertEqual(len(report["goalies"]),1)
        self.assertEqual(report["skaters"][0]["shots_wrist"],8)
        self.assertIsNone(report["skaters"][0]["avg_speed"])
        self.assertEqual(report["game_type_id"],2)
        self.assertEqual(report["status"],"verified_nhl_official_stats_snapshot")

    def test_reject_missing_team_roster_or_invalid_report(self):
        data=fixture()
        data["team_directory"]=data["team_directory"][:8]
        with self.assertRaisesRegex(ValueError,"enough current-season"):
            clean(data,"20262027",NOW)

    def test_unavailable_supplemental_reports_do_not_invent_stats(self):
        data=fixture()
        del data["skater_shots"]
        del data["goalie_strength"]
        del data["team_powerplay"]
        report=clean(data,"20262027",NOW)
        self.assertEqual(report["reports"]["skater_shots"]["status"],"unavailable")
        self.assertIsNone(report["skaters"][0]["shots_wrist"])
        self.assertIsNone(report["goalies"][0]["save_pct_even_strength"])
        self.assertIsNone(report["teams"][0]["pp_pct"])

    def test_nonnumeric_invalid_and_over100pct_rejected(self):
        self.assertIsNone(source_id(True))
        self.assertIsNone(positive_number(float("inf")))
        self.assertIsNone(positive_number(-1))
        self.assertIsNone(positive_number(1.4,fraction=True))
        data=fixture()
        data["goalie_summary"][0]["savePct"]=100.0
        report=clean(data,"20262027",NOW)
        self.assertIsNone(report["goalies"][0]["overall_save_pct"])

    def test_cross_team_goalies_not_assigned_arbitrarily(self):
        data=fixture()
        data["goalie_summary"][0]["teamAbbrevs"]="T01,T02"
        report=clean(data,"20262027",NOW)
        self.assertEqual(report["goalies"],[])


if __name__=="__main__":unittest.main()
