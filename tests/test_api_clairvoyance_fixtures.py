"""API source-route contract tests on real-shaped, time-stamped Revue snapshots."""
from datetime import date,datetime,timedelta,timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from api_revue.fixtures import fixture_rows,SourceUnavailable,snapshot


NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
START=NOW+timedelta(hours=3)
GAME={
    "event_id":"2026020070","home":"BOS","away":"PHI",
    "start_utc":START.isoformat(),"status":"prototype_non_calibre",
    "probabilities":{"home_win":.60,"away_win":.4},
}
MLB={**GAME,"event_id":"401907994","home":"Guardians","away":"White Sox"}


def dataset():
    return {
        "generated_at_utc":(NOW-timedelta(minutes=5)).isoformat(),
        "status":"prototype_non_calibre",
        "competitions":{"NHL":{"games":[GAME]},"MLB":{"games":[MLB]}},
    }


def scores(state="final",home=3,away=1,started=True):
    kickoff=(NOW-timedelta(hours=3) if started else START).isoformat()
    return {
        "generated_at_utc":NOW.isoformat(),
        "status":"observed_scoreboard_not_streaming",
        "events":[{
            "league":"NHL","event_id":"2026020070","home":"BOS","away":"PHI",
            "kickoff_utc":kickoff,"state":state,"home_score":home,"away_score":away,
            "observed_at_utc":NOW.isoformat(),
        }],
    }


class FixtureContractTests(unittest.TestCase):
    def test_scheduled_nhl_and_mlb_have_same_original_fields(self):
        nhl=fixture_rows(dataset(),None,"NHL",START.date(),NOW)
        mlb=fixture_rows(dataset(),None,"MLB",START.date(),NOW)
        self.assertEqual(len(nhl),1)
        self.assertEqual(len(mlb),1)
        self.assertEqual(nhl[0]["espn_id"],"2026020070")
        self.assertEqual(mlb[0]["espn_id"],"401907994")
        self.assertEqual(nhl[0]["status"],"STATUS_SCHEDULED")
        self.assertIsNone(nhl[0]["home_moneyline"])
        self.assertIsNone(mlb[0]["home_pitcher"])
        self.assertEqual(mlb[0]["id"],401907994)
        self.assertNotIn("home_pitcher",nhl[0])

    def test_scores_only_join_on_id_teams_and_kickoff(self):
        data=dataset()
        data["competitions"]["NHL"]["games"][0]["start_utc"]=(NOW-timedelta(hours=3)).isoformat()
        rows=fixture_rows(data,scores(),"NHL",(NOW-timedelta(hours=3)).date(),NOW)
        self.assertEqual(rows[0]["status"],"STATUS_FINAL")
        self.assertEqual((rows[0]["home_score"],rows[0]["away_score"]),(3,1))
        for mod,value in (
            ("home","COL"),("kickoff_utc",(NOW-timedelta(hours=2)).isoformat()),
            ("event_id","different"),("home_score",-1),
        ):
            snap=scores()
            snap["events"][0][mod]=value
            again=fixture_rows(data,snap,"NHL",(NOW-timedelta(hours=3)).date(),NOW)
            self.assertEqual(again[0]["status"],"STATUS_SCHEDULED")
            self.assertIsNone(again[0]["home_score"])

    def test_prices_and_pitchers_never_inferred_from_model_odds(self):
        doc=dataset()
        doc["competitions"]["MLB"]["games"][0]["odds"]={"home":2.4,"away":1.55}
        row=fixture_rows(doc,None,"MLB",START.date(),NOW)[0]
        self.assertIsNone(row["home_moneyline"])
        self.assertIsNone(row["away_moneyline"])
        self.assertIsNone(row["over_under"])
        self.assertIsNone(row["home_pitcher"])

    def test_duplicate_ids_do_not_generate_ambiguous_results(self):
        doc=dataset()
        doc["competitions"]["NHL"]["games"].append(dict(doc["competitions"]["NHL"]["games"][0]))
        with self.assertRaises(SourceUnavailable):
            fixture_rows(doc,None,"NHL",START.date(),NOW)

    def test_stale_snapshot_rejected_instead_of_stale_fake_live_response(self):
        with TemporaryDirectory() as root:
            path=Path(root)/"multisports-latest.json"
            data=dataset()
            data["generated_at_utc"]=(NOW-timedelta(days=5)).isoformat()
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(SourceUnavailable):
                snapshot(path,NOW)
            data["generated_at_utc"]=(NOW+timedelta(minutes=5)).isoformat()
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(SourceUnavailable):
                snapshot(path,NOW)

    def test_utc_date_scope_is_explicit(self):
        self.assertEqual(fixture_rows(dataset(),None,"NHL",(START+timedelta(days=1)).date(),NOW),[])
        with self.assertRaises(ValueError):
            fixture_rows(dataset(),None,"CFB",START.date(),NOW)


if __name__=="__main__":unittest.main()
