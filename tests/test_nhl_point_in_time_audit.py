"""Fail-closed NHL MoneyPuck feature freshness and sample chronology tests."""
import copy
from datetime import datetime, timedelta, timezone
import unittest

from modeles.simulations.nhl_independant import Game
from outils.nhl_point_in_time_audit import verify_point_in_time, as_utc

UTC=timezone.utc
NOW=datetime(2026,10,10,6,tzinfo=UTC)
SOURCE=NOW-timedelta(hours=2)
SNAPSHOT=NOW-timedelta(hours=1)
SEASON="2026-2027"


def fixture():
    row=lambda team,count:{"team":team,"season":SEASON,"situation":"5on5",
                            "games_played":count,"xg_share":.52}
    t={"source":"MoneyPuck.com","is_live":False,"current_season":SEASON,
       "generated_at_utc":SNAPSHOT.isoformat(),
       "status":{SEASON:{"status":"available","source_updated_utc":SOURCE.isoformat()}},
       "seasons":{SEASON:[row("BOS",2),row("NYR",2)]}}
    g={"source":"MoneyPuck.com","is_live":False,"current_season":SEASON,
       "generated_at_utc":SNAPSHOT.isoformat(),
       "statuses":{SEASON:{"status":"available","source_updated_utc":SOURCE.isoformat()}},
       "seasons":{SEASON:[{"name":"A","team":"BOS","games_played":2,"starter_status":"unknown"}]}}
    past=[Game(id=str(i),start_utc=SOURCE-timedelta(days=i),
               home="BOS",away="NYR",state="OFF",home_goals=3,away_goals=1)
          for i in (1,2)]
    upcoming=Game(id="future",start_utc=NOW+timedelta(hours=3),
                  home="BOS",away="NYR",state="FUT")
    return t,g,past+[upcoming]


class TemporalIntegrityTest(unittest.TestCase):
    def verify(self,t,g,s):
        return verify_point_in_time(t,g,s,NOW,"20262027")

    def test_regular_fixture_is_verified_without_future_games(self):
        t,g,s=fixture()
        report=self.verify(t,g,s)
        self.assertEqual(report["status"],"verified_temporal_bounds")
        self.assertEqual(report["official_games_before_team_source"],2)
        self.assertEqual(report["money_puck_team_games_observed"],2)
        self.assertEqual(report["team_5v5_rows_checked"],2)
        self.assertEqual(report["goalie_rows_checked"],1)

    def test_a_snapshot_cannot_claim_games_after_its_publication(self):
        t,g,s=fixture()
        t["seasons"][SEASON][0]["games_played"]=3
        with self.assertRaisesRegex(ValueError,"Look-ahead"):
            self.verify(t,g,s)

    def test_goalie_history_cannot_exceed_official_club_history(self):
        t,g,s=fixture()
        g["seasons"][SEASON][0]["games_played"]=3
        with self.assertRaisesRegex(ValueError,"Look-ahead"):
            self.verify(t,g,s)

    def test_a_future_game_does_not_increase_published_sample(self):
        t,g,s=fixture()
        s.append(Game(id="future-false-final",start_utc=NOW+timedelta(days=1),
                      home="BOS",away="NYR",state="OFF",home_goals=1,away_goals=0))
        report=self.verify(t,g,s)
        self.assertEqual(report["official_games_before_team_source"],2)

    def test_source_after_report_cannot_be_used(self):
        t,g,s=fixture()
        t["status"][SEASON]["source_updated_utc"]=(NOW+timedelta(hours=4)).isoformat()
        with self.assertRaisesRegex(ValueError,"source/snapshot"):
            self.verify(t,g,s)

    def test_future_report_is_rejected(self):
        t,g,s=fixture()
        g["generated_at_utc"]=(NOW+timedelta(minutes=5)).isoformat()
        with self.assertRaisesRegex(ValueError,"timestamps"):
            self.verify(t,g,s)

    def test_stale_inputs_fail_closed(self):
        t,g,s=fixture()
        old=NOW-timedelta(days=9)
        t["status"][SEASON]["source_updated_utc"]=old.isoformat()
        t["generated_at_utc"]=(NOW-timedelta(days=8)).isoformat()
        with self.assertRaisesRegex(ValueError,"too old"):
            self.verify(t,g,s)

    def test_no_current_season_or_source_rejected(self):
        t,g,s=fixture()
        t["current_season"]="2025-2026"
        with self.assertRaisesRegex(ValueError,"season identity"):
            self.verify(t,g,s)

    def test_duplicate_schedule_rejected(self):
        t,g,s=fixture()
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            self.verify(t,g,s+[copy.deepcopy(s[0])])

    def test_invalid_goaltender_confirmation_rejected(self):
        t,g,s=fixture()
        g["seasons"][SEASON][0]["starter_status"]="confirmed"
        with self.assertRaisesRegex(ValueError,"confirmed"):
            self.verify(t,g,s)

    def test_invalid_or_naive_source_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            as_utc("2026-10-09T10:00:00")
        t,g,s=fixture()
        t["status"][SEASON]["source_updated_utc"]="bad"
        with self.assertRaises(ValueError):
            self.verify(t,g,s)

    def test_current_source_undercount_is_allowed(self):
        t,g,s=fixture()
        t["seasons"][SEASON][0]["games_played"]=1
        self.assertEqual(self.verify(t,g,s)["status"],"verified_temporal_bounds")


if __name__=="__main__":
    unittest.main()
