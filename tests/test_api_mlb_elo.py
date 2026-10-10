"""End-to-end MLB Elo contract and historical integrity tests."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from fastapi.testclient import TestClient
from api_revue.app import create_app
from api_revue.fixtures import SourceUnavailable
from api_revue.mlb_elo import replay_mlb_elo,update_winner_loser,expected_score

NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)


def fixture(n=26):
    events=[]
    for i in range(n):
        events.append({
            "id":str(401000000+i),"league":"MLB",
            "start":(NOW-timedelta(days=35-i)).isoformat(),
            "home":"Dodgers" if i%2==0 else "Padres",
            "away":"Padres" if i%2==0 else "Dodgers",
            "complete":True,"home_score":3+(i%4),"away_score":1,
        })
    return {"version":1,"leagues":{"MLB":{"days_ok":[],"events":events}}}


class EloReconstructionTests(unittest.TestCase):
    def test_exact_original_elo_update_rule(self):
        self.assertEqual(update_winner_loser(1500.,1500.),(1516.,1484.))
        self.assertEqual(expected_score(1500,1500),0.5)
        a,b=update_winner_loser(1600,1450)
        self.assertAlmostEqual(a,round(1600+32*(1-expected_score(1600,1450)),2))
        self.assertAlmostEqual(b,round(1450-32*expected_score(1450,1600),2))

    def test_real_shaped_historical_finals_produce_auditable_rankings(self):
        data=fixture()
        result=replay_mlb_elo(data,NOW)
        self.assertEqual(result["completed_espn_games"],26)
        self.assertEqual(result["teams_count"],2)
        self.assertEqual(result["rows"][0]["games_played"],26)
        self.assertEqual(result["rows"][1]["games_played"],26)
        self.assertEqual(result["trace"][0]["before_home_elo"],1500.)
        self.assertEqual(result["trace"][0]["after_home_elo"],1516.)
        self.assertFalse(result["original_clairvoyance_sql_ratings_equal"])
        self.assertNotIn("recommendation",result["rows"][0])

    def test_future_or_unfinished_games_do_not_leak_into_elo(self):
        d=fixture()
        d["leagues"]["MLB"]["events"].append({
            "id":"401000089","league":"MLB","start":(NOW+timedelta(days=1)).isoformat(),
            "home":"Dodgers","away":"Padres","complete":True,"home_score":100,
            "away_score":0,
        })
        d["leagues"]["MLB"]["events"].append({
            "id":"401000090","league":"MLB","start":(NOW+timedelta(hours=3)).isoformat(),
            "home":"Dodgers","away":"Padres","complete":False,
            "home_score":None,"away_score":None,
        })
        result=replay_mlb_elo(d,NOW)
        self.assertEqual(result["completed_espn_games"],26)
        self.assertEqual(result["rows"],replay_mlb_elo(fixture(),NOW)["rows"])

    def test_bad_final_and_duplicate_id_fail_closed(self):
        d=fixture()
        d["leagues"]["MLB"]["events"][0]["home_score"]=None
        with self.assertRaises(SourceUnavailable):
            replay_mlb_elo(d,NOW)
        d=fixture()
        d["leagues"]["MLB"]["events"].append(dict(d["leagues"]["MLB"]["events"][0]))
        with self.assertRaises(SourceUnavailable):
            replay_mlb_elo(d,NOW)

    def test_unknown_schema_and_non_aware_clock_rejected(self):
        d=fixture()
        d["version"]=2
        with self.assertRaises(SourceUnavailable):
            replay_mlb_elo(d,NOW)
        with self.assertRaises(ValueError):
            replay_mlb_elo(fixture(),datetime(2026,10,10,12))

    def test_http_contract_partial_source_and_status(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"multisports-history.json").write_text(json.dumps(fixture()))
            client=TestClient(create_app(root=root,clock=lambda:NOW))
            resp=client.get("/mlb/elo")
            self.assertEqual(resp.status_code,200,resp.text)
            self.assertEqual(len(resp.json()),2)
            self.assertEqual(set(resp.json()[0]),{"team","rating","games_played","last_game_date"})
            self.assertIn("partial",resp.headers["X-Revue-Parity"])
            (root/"multisports-history.json").unlink()
            self.assertEqual(client.get("/mlb/elo").status_code,503)


if __name__=="__main__":
    unittest.main()
