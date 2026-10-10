"""Test actual HTTP routes and explicit refusals, not merely function names."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

try:
    from fastapi.testclient import TestClient
    from api_revue.app import create_app
except ImportError:
    TestClient=None

NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
START=NOW+timedelta(hours=3)


@unittest.skipUnless(TestClient,"FastAPI / httpx not installed")
class SourceRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.write("multisports-latest.json",{
            "generated_at_utc":NOW.isoformat(),"status":"prototype_non_calibre",
            "competitions":{
                "NHL":{"games":[{"event_id":"2026020070","home":"BOS",
                       "away":"PHI","start_utc":START.isoformat()}]},
                "MLB":{"games":[{"event_id":"401907994","home":"Guardians",
                       "away":"White Sox","start_utc":START.isoformat()}]}
            },
        })
        self.write("parite-nhl-espn-id-map.json",{
            "generated_at_utc":NOW.isoformat(),
            "status":"verified_fixture_identity_pairs",
            "matched":1,"unmatched":0,
            "mappings":[{
                "nhl_game_id":"2026020070",
                "original_espn_id":"401892469",
                "home":"BOS","away":"PHI","start_utc":START.isoformat(),
            }],
        })
        self.write("scoreboard-revue-latest.json",{
            "generated_at_utc":NOW.isoformat(),
            "status":"observed_scoreboard_not_streaming","events":[],
        })
        self.write("reproduction-exacte-audit.json",{
            "source_commit":"reference-commit",
            "exact_end_to_end_parity":"NOT_VERIFIED",
            "exact_reproduction_percent":None,
            "backend":{"source_route_count":24,"end_to_end_verified_equivalent_routes":0},
        })
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))

    def write(self,name,data):
        (self.root/name).write_text(json.dumps(data),encoding="utf-8")

    def test_nhl_schedule_uses_original_output_field_set(self):
        response=self.client.get("/nhl/schedule",params={"game_date":START.date().isoformat()})
        self.assertEqual(response.status_code,200,response.text)
        result=response.json()
        self.assertEqual(len(result),1)
        self.assertEqual(set(result[0]),{
            "id","espn_id","game_date","game_time_utc","status",
            "home_team","away_team","home_score","away_score","home_moneyline",
            "away_moneyline","over_under",
        })
        self.assertEqual(result[0]["espn_id"],"401892469")
        self.assertEqual(result[0]["id"],401892469)
        self.assertIsNone(result[0]["home_score"])

    def test_missing_original_espn_mapping_is_503_not_a_fabricated_id(self):
        (self.root/"parite-nhl-espn-id-map.json").unlink()
        response=self.client.get("/nhl/schedule",params={"game_date":START.date().isoformat()})
        self.assertEqual(response.status_code,503)
        self.assertIn("parite-nhl-espn-id-map.json",response.json()["detail"])

    def test_mlb_schedule_and_exact_espn_id_lookup(self):
        game=self.client.get("/mlb/schedule",params={"game_date":START.date().isoformat()})
        self.assertEqual(game.status_code,200)
        rows=game.json()
        self.assertEqual(len(rows),1)
        self.assertEqual(len(rows[0]),15)
        detail=self.client.get("/mlb/games/401907994")
        self.assertEqual(detail.status_code,200,detail.text)
        self.assertEqual(detail.json(),rows[0])
        self.assertEqual(self.client.get("/mlb/games/00000001").status_code,404)
        self.assertEqual(self.client.get("/mlb/games/not-an-id").status_code,404)

    def test_predictions_do_not_fake_source_elo_or_profitability(self):
        response=self.client.get("/predictions/",params={"game_date":START.date().isoformat()})
        self.assertEqual(response.status_code,503)
        self.assertIn("not proven identical",response.json()["detail"])

    def test_missing_or_stale_sources_are_unavailable_not_empty_games(self):
        self.write("multisports-latest.json",{
            "generated_at_utc":(NOW-timedelta(days=4)).isoformat(),
            "status":"prototype_non_calibre","competitions":{"NHL":{"games":[]}},
        })
        response=self.client.get("/nhl/schedule",params={"game_date":START.date().isoformat()})
        self.assertEqual(response.status_code,503)

    def test_health_not_data_freshness_and_parity_remains_unknown(self):
        self.assertEqual(self.client.get("/health").json(),{"status":"ok"})
        parity=self.client.get("/revue/parity")
        self.assertEqual(parity.status_code,200)
        self.assertEqual(parity.json()["source_routes"],24)
        self.assertEqual(parity.json()["exact_end_to_end_parity"],"NOT_VERIFIED")
        self.assertIsNone(parity.json()["exact_reproduction_percent"])
        self.assertTrue(parity.json()["not_original_backend"])

    def test_input_validation(self):
        response=self.client.get("/nhl/schedule",params={"game_date":"not-a-date"})
        self.assertEqual(response.status_code,422)
        self.assertEqual(self.client.post("/admin/pipeline").status_code,404)

if __name__=="__main__":unittest.main()
