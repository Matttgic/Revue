"""Official NHL and ESPN scoreboard source and integrity tests."""
from datetime import datetime,timedelta,timezone,date
import unittest
from outils.scoreboard_revue import _parse_score_event,download_nhl,download_espn,collect

NOW=datetime(2026,10,10,13,tzinfo=timezone.utc)
KICK=NOW-timedelta(hours=2)


def raw_espn(state="in",completed=False,home="1",away="2"):
    return {
        "id":"101","date":KICK.isoformat(),"status":{"type":{"state":state,"completed":completed}},
        "competitions":[{"competitors":[
            {"homeAway":"home","team":{"id":"1","shortDisplayName":"Arsenal"},"score":home},
            {"homeAway":"away","team":{"id":"2","shortDisplayName":"Leeds"},"score":away}
        ]}],
    }


def raw_nhl(state="OFF"):
    return {
        "id":2026020070,
        "gameType":2,"gameState":state,
        "startTimeUTC":KICK.isoformat().replace("+00:00","Z"),
        "homeTeam":{"abbrev":"BOS","score":3},
        "awayTeam":{"abbrev":"PHI","score":1},
    }


class ScoreboardTests(unittest.TestCase):
    def test_espn_in_progress_is_observed_not_prospective(self):
        r=_parse_score_event(raw_espn(), "PL", NOW)
        self.assertEqual(r["state"],"in_progress")
        self.assertEqual(r["home_score"],1)
        self.assertEqual(r["away_score"],2)
        self.assertFalse(r["prospective_bet_result"])

    def test_espn_final_requires_final_marker_and_sane_scores(self):
        r=_parse_score_event(raw_espn("post",True),"PL",NOW)
        self.assertEqual(r["state"],"final")
        self.assertEqual(r["source"],"ESPN scoreboard")
        self.assertIsNone(_parse_score_event(raw_espn("post",True,"none",2),"PL",NOW))
        self.assertIsNone(_parse_score_event(raw_espn("post",True,1,-1),"PL",NOW))

    def test_non_started_game_does_not_report_live_score(self):
        r=_parse_score_event(raw_espn("pre",False),"PL",NOW)
        self.assertEqual(r["state"],"scheduled")
        self.assertIsNone(r["home_score"])

    def test_no_false_events_outside_40_hour_window(self):
        r=raw_espn()
        r["date"]=(NOW-timedelta(days=7)).isoformat()
        self.assertIsNone(_parse_score_event(r,"PL",NOW))

    def test_espn_fetch_rejects_malformed(self):
        with self.assertRaisesRegex(ValueError,"Malformed"):
            download_espn("PL",date(2026,10,10),NOW,lambda url:{"not_events":[]})
        with self.assertRaises(ValueError):
            download_espn("FOO",date(2026,10,10),NOW,lambda url:{"events":[]})

    def test_nhl_official_final_and_live(self):
        for state,expect in (("OFF","final"),("LIVE","in_progress"),("FUT","scheduled")):
            with self.subTest(state=state):
                day=date(2026,10,10)
                result=download_nhl(day,NOW,lambda url:{"currentDate":str(day),"games":[raw_nhl(state)]})
                self.assertEqual(result[0]["state"],expect)
                if expect=="scheduled":self.assertIsNone(result[0]["home_score"])
        with self.assertRaisesRegex(ValueError,"date mismatch"):
            download_nhl(date(2026,10,10),NOW,lambda url:{"currentDate":"2020-01-01","games":[]})

    def test_collect_gracefully_reports_partial_source_failures(self):
        def espn(url):
            if "/nba/" in url: raise RuntimeError("not available")
            return {"events":[raw_espn("post",True)]} if "/eng.1/" in url else {"events":[]}
        day=NOW.astimezone(timezone.utc).date().isoformat()
        result=collect(NOW,espn,lambda url:{"currentDate":url.split("/")[-1],"games":[raw_nhl()]})
        self.assertEqual(result["status"],"observed_scoreboard_not_streaming")
        self.assertFalse(result["scores_are_live_stream"])
        self.assertGreater(result["requests"]["failed"],0)
        self.assertGreater(result["final"],0)
        self.assertTrue(any(x["league"]=="NHL" for x in result["events"]))
        self.assertTrue(any(x["league"]=="PL" for x in result["events"]))
        self.assertTrue(all(x["prospective_bet_result"] is False for x in result["events"]))

if __name__=="__main__":unittest.main()
