"""Read-only match dossier HTTP with source truth and strict filtering."""
import json
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from api_revue.app import create_app
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
def when(hours):return (NOW+timedelta(hours=hours)).isoformat()

class GameDossierHttpTests(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.games=[
            {"key":"NHL:77","league":"NHL","event_id":"77","home":"BOS",
             "away":"PHI","start_utc":when(3),
             "historical_odds":{"observations":[{"bookmaker":"winamax_fr","price":2.0}],
                                "market_groups":[]},
             "research_models":[{"id":"nhl"}],
             "locked_forecast":{"status":"pending"},
             "home_history":{"games":2},"away_history":{"games":3},"no_real_betting":True},
            {"key":"UFC:UFC:88","league":"UFC","event_id":"UFC:88","home":"A",
             "away":"B","start_utc":when(4),
             "historical_odds":{"observations":[],"market_groups":[]},
             "research_models":[],"locked_forecast":None,
             "home_history":{"games":0},"away_history":{"games":0},"no_real_betting":True},
        ]
        self.save()
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))

    def save(self,date=None):
        self.root.joinpath("match-dossiers-latest.json").write_text(json.dumps({
            "status":"source_audited_static_match_dossiers_not_live",
            "generated_at_utc":date or when(-1),
            "source_match_center_at_utc":when(-2),
            "historical_data_not_point_in_time_forecasts":True,
            "real_bets_enabled":False,
            "original_clairvoyance_equivalence_verified":False,
            "bookmaker_prices_are_live":False,
            "validated_value_bets":0,
            "count":len(self.games),"games":self.games
        }),encoding="utf-8")

    def test_list_filter_and_detail_without_forged_bets(self):
        r=self.client.get("/revue/games",params={"league":"nhl","only_priced":True})
        self.assertEqual(r.status_code,200,r.text)
        d=r.json()
        self.assertEqual(d["total"],1)
        self.assertEqual(d["items"][0]["observed_price_count"],1)
        self.assertTrue(d["not_live"])
        self.assertFalse(d["original_parity_verified"])
        self.assertEqual(self.client.get("/revue/games",params={"query":"BOS"}).json()["total"],1)
        self.assertEqual(self.client.get("/revue/games",params={"offset":1,"limit":1}).json()["items"][0]["league"],"UFC")
        detail=self.client.get("/revue/games/UFC/UFC:88")
        self.assertEqual(detail.status_code,200,detail.text)
        self.assertEqual(detail.json()["event_id"],"UFC:88")
        self.assertTrue(detail.json()["no_real_betting"])
        self.assertEqual(self.client.get("/revue/games/NHL/999").status_code,404)

    def test_only_get_is_exposed_and_limit_validation(self):
        self.assertEqual(self.client.post("/revue/games",json={}).status_code,405)
        self.assertEqual(self.client.get("/revue/games?limit=0").status_code,422)
        self.assertEqual(self.client.get("/revue/games?limit=201").status_code,422)
        self.assertEqual(self.client.get("/revue/games?offset=-1").status_code,422)

    def test_stale_or_forged_snapshot_returns_503(self):
        self.save(when(-15))
        self.assertEqual(self.client.get("/revue/games").status_code,503)
        self.save()
        self.games[0]["no_real_betting"]=False
        self.save()
        self.assertEqual(self.client.get("/revue/games").status_code,503)

if __name__=="__main__":unittest.main()
