"""Offline tests: official NHL scoreboard settlement of immutable research forecasts."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from outils.nhl_settlement_officiel import (
    MAX_DATES, SCORE_URL, download_results, due_scoreboard_dates,
    run, settle_existing,
)
from outils.nhl_shadow_tracker import VERSION, update_ledger

UTC = timezone.utc
LOCKED = datetime(2026, 10, 9, 18, tzinfo=UTC)
KICKOFF = datetime(2026, 10, 10, 1, tzinfo=UTC)  # New York: October 9
AFTER = datetime(2026, 10, 10, 6, tzinfo=UTC)


def report(with_variant=True):
    src = (LOCKED - timedelta(hours=1)).isoformat()
    row = {
        "event_id":"2026027001","home":"BOS","away":"NYR",
        "start_utc":KICKOFF.isoformat(),"home_win":.65,
        "shadow_only":True,"calibrated":False,
        "model_id":"clairvoyance_nhl_backend_formula_with_revue_elo_proxy",
    }
    if with_variant:
        row["research_low_sample_shrink"] = {
            "model_id":"revue_nhl_low_sample_shrink_v1",
            "home_win":.55,"shadow_only":True,"calibrated":False,
        }
    return {
        "generated_at_utc":LOCKED.isoformat(),
        "status":"experimental_not_calibrated",
        "sources":{
            "source_updated_utc":{"teams":src,"goalies":src},
            "source_snapshot_utc":{"teams":src,"goalies":src},
        },
        "point_in_time_audit":{
            "status":"verified_temporal_bounds",
            "as_of_utc":LOCKED.isoformat(),
            "source_updated_utc":{"teams":src,"goalies":src},
            "team_5v5_rows_checked":2,
        },
        "games":[row],
    }


def locked(with_variant=True):
    return update_ledger(None, report(with_variant), [], LOCKED)


def score(day="2026-10-09", state="OFF", home="BOS", away="NYR", goals=(3, 2),
          id=2026027001):
    return {
        "currentDate":day,
        "games":[{
            "id":id,"gameType":2,"gameState":state,
            "startTimeUTC":KICKOFF.isoformat().replace("+00:00","Z"),
            "homeTeam":{"abbrev":home,"score":goals[0]},
            "awayTeam":{"abbrev":away,"score":goals[1]},
        }],
    }


class OfficialSettlementTests(unittest.TestCase):
    def test_eastern_date_prevents_paris_utc_off_by_one(self):
        self.assertEqual(due_scoreboard_dates(locked(),AFTER),["2026-10-09"])
        self.assertEqual(due_scoreboard_dates(locked(),LOCKED),[])

    def test_only_requests_necessary_daily_scores_and_grades_paired(self):
        queries=[]
        def fetch(url):
            queries.append(url)
            return score()
        before=locked()
        baseline=deepcopy(before["events"][0])
        result,perf,days=run(before,AFTER,fetch)
        self.assertEqual(days,["2026-10-09"])
        self.assertEqual(queries,[SCORE_URL+"/2026-10-09"])
        self.assertEqual(before["events"][0],baseline)
        one=result["events"][0]
        self.assertEqual(one["status"],"settled")
        self.assertEqual(one["result"],1)
        self.assertEqual(one["home_goals"],3)
        self.assertAlmostEqual(one["brier"],.1225)
        self.assertAlmostEqual(one["research_brier"],.2025)
        self.assertEqual(one["locked_at_utc"],baseline["locked_at_utc"])
        self.assertEqual(one["research_home_win_probability"],.55)
        self.assertEqual(perf["research_paired_settled"],1)
        self.assertEqual(perf["research_paired_locked"],1)
        self.assertIsNone(perf["roi"])

    def test_no_guess_for_live_or_upcoming_scores(self):
        for state in ("FUT","PRE","LIVE","CRIT"):
            with self.subTest(state=state):
                result,perf,_=run(locked(),AFTER,lambda url:score(state=state))
                self.assertEqual(result["events"][0]["status"],"pending")
                self.assertEqual(perf["settled"],0)

    def test_missing_or_wrong_scoreboard_response_fails_closed(self):
        for payload in ({}, {"games":[]}, {"currentDate":"2026-10-10","games":[]}):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    run(locked(),AFTER,lambda url:payload)

    def test_wrong_fixture_mapping_does_not_settle(self):
        for changed in ({"home":"DET"},{"away":"MTL"},{"id":2026027002}):
            with self.subTest(changed=changed):
                result,perf,_=run(locked(),AFTER,
                    lambda url:score(**changed))
                self.assertEqual(result["events"][0]["status"],"pending")
                self.assertEqual(perf["settled"],0)

    def test_does_not_backfill_old_original_only_prediction(self):
        before=locked(False)
        after,perf,_=run(before,AFTER,lambda url:score())
        self.assertEqual(after["events"][0]["status"],"settled")
        self.assertIsNone(after["events"][0].get("research_brier"))
        self.assertEqual(perf["research_paired_locked"],0)
        self.assertEqual(perf["research_paired_settled"],0)

    def test_does_not_resettle_modified_score(self):
        final,perf,_=run(locked(),AFTER,lambda url:score())
        repeat,_,days=run(final,AFTER+timedelta(days=1),
            lambda url: (_ for _ in ()).throw(AssertionError("no more queries")))
        self.assertEqual(days,[])
        self.assertEqual(repeat["events"][0],final["events"][0])

    def test_never_creates_new_locks(self):
        original={"version":VERSION,"events":[]}
        after,perf,days=run(original,AFTER,
            lambda url: (_ for _ in ()).throw(AssertionError("unexpected HTTP")))
        self.assertEqual(after["events"],[])
        self.assertEqual(perf["locked_events"],0)
        self.assertEqual(days,[])

    def test_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            settle_existing({"version":"unknown","events":[]},[],AFTER)

    def test_maximum_query_days_prioritize_recent(self):
        original=locked()
        prototype=original["events"][0]
        original["events"]=[]
        for offset in range(MAX_DATES+4):
            row=deepcopy(prototype)
            row["event_id"]=str(offset)
            row["kickoff_utc"]=(KICKOFF-timedelta(days=offset)).isoformat()
            original["events"].append(row)
        days=due_scoreboard_dates(original,AFTER)
        self.assertEqual(len(days),MAX_DATES)
        self.assertEqual(days[0],"2026-10-09")
        self.assertEqual(days[-1],"2026-09-26")

if __name__=="__main__":
    unittest.main()
