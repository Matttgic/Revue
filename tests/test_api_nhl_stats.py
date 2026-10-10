"""HTTP contract checks on self-contained test fixtures (not production data)."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from api_revue.app import create_app
from api_revue.nhl_stats import live_moneypuck_snapshot
from api_revue.fixtures import SourceUnavailable

NOW=datetime(2026,10,10,14,tzinfo=timezone.utc)


class NHLAdvancedRoutes(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))
        self.put("nhl-official-stats-latest.json",{
            "generated_at_utc":NOW.isoformat(),
            "status":"verified_nhl_official_stats_snapshot",
            "source":"api.nhle.com/stats/rest/en",
            "season":"20262027","game_type_id":2,
            "reports":{"goalie_summary":{"status":"available"},
                       "skater_summary":{"status":"available"}},
            "teams":[{
                "id":i,"team_id":i,"team_abbrev":f"T{i:02d}",
                "team_name":"Test", "season":"20262027","game_type_id":2,
                "games_played":3,"wins":2,"losses":1,"ot_losses":0,
                "goals_for":10,"goals_against":6,
                "goals_for_per_game":3.3333,"goals_against_per_game":2.0,
                "pp_pct":.24,"pk_pct":.81,
                "shots_for_per_game":30,"shots_against_per_game":27,
                "offensive_zone_time_pct":None,"defensive_zone_time_pct":None,
                "neutral_zone_time_pct":None,
            } for i in range(1,29)],
            "goalies":[{
                "id":8478024,"player_id":8478024,"player_name":"Goalie 1",
                "team_abbrev":"ANA","season":"20262027","game_type_id":2,
                "games_played":3,"overall_save_pct":.924,"goals_against_avg":2.1,
                "saves_even_strength":78,"save_pct_even_strength":.92,
                "saves_power_play":9,"save_pct_power_play":1.0,
                "saves_short_handed":3,"save_pct_short_handed":1.0,
            }],
            "skaters":[{
                "id":12345,"player_id":12345,"player_name":"Skater 1",
                "team_abbrev":"ANA","season":"20262027","game_type_id":2,
                "shots_wrist":None,"shots_snap":None,"shots_slap":None,
                "shots_backhand":None,"shots_tip":None,
                "shots_deflected":None,"shots_wrap_around":None,
                "avg_speed":None,"top_speed":None,
            }],
        })
        self.put("moneypuck-nhl-latest.json",{
            "generated_at_utc":NOW.isoformat(),"source":"MoneyPuck.com",
            "is_live":False,"current_season":"2026-2027",
            "status":{"2026-2027":{"status":"available","teams":28}},
            "seasons":{"2026-2027":[
                {"team":f"T{i:02d}","situation":situation,
                 "season":"2026-2027","games_played":3,"xg_share":.51,
                 "xg_for_60":2.8,"xg_against_60":2.6,
                 "shots_for_60":28,"shots_against_60":27,
                 "save_pct":.91,"pdo":1.02}
                 for i in range(1,29) for situation in ("all","5on5")
            ]},
        })

    def put(self,name,body):
        (self.root/name).write_text(json.dumps(body),encoding="utf-8")

    def test_team_schema_and_source(self):
        r=self.client.get("/nhl/teams")
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(len(r.json()),28)
        self.assertEqual(r.json()[0]["wins"],2)
        self.assertIn("partial",r.headers["X-Revue-Parity"])
        self.assertIsNone(r.json()[0]["offensive_zone_time_pct"])

    def test_goalie_and_skater_identity_not_lineup(self):
        r=self.client.get("/nhl/goalies",params={"min_games":2})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(len(r.json()),1)
        self.assertEqual(r.json()[0]["player_id"],8478024)
        self.assertNotIn("confirmed_starter",r.json()[0])
        self.assertEqual(self.client.get("/nhl/goalies",params={"min_games":4}).json(),[])
        self.assertEqual(self.client.get("/nhl/goalies",params={"min_games":0}).status_code,422)
        r=self.client.get("/nhl/skaters",params={"team":"ana"})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()[0]["player_id"],12345)
        self.assertIsNone(r.json()[0]["avg_speed"])
        self.assertEqual(self.client.get("/nhl/skaters",params={"team":"PHI"}).json(),[])
        self.assertEqual(self.client.get("/nhl/skaters",params={"team":"BADCODE"}).status_code,422)

    def test_moneypuck_shares_are_ratios_not_invented_percent(self):
        for name in ("all","5on5"):
            r=self.client.get("/nhl/moneypuck",params={"situation":name})
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(len(r.json()),28)
            self.assertEqual(r.json()[0]["x_goals_pct"],.51)
            self.assertEqual(r.json()[0]["x_goals_for_60"],2.8)
            self.assertIsNone(r.json()[0]["goals_for"])
            self.assertEqual(r.json()[0]["season"],"20262027")
        self.assertEqual(self.client.get("/nhl/moneypuck",params={"situation":"powerPlay"}).status_code,422)

    def test_fail_closed_on_stale_and_malformed_sources(self):
        official=json.loads((self.root/"nhl-official-stats-latest.json").read_text())
        official["generated_at_utc"]=(NOW-timedelta(hours=30)).isoformat()
        self.put("nhl-official-stats-latest.json",official)
        self.assertEqual(self.client.get("/nhl/teams").status_code,503)
        self.assertEqual(self.client.get("/nhl/goalies").status_code,503)
        mp=json.loads((self.root/"moneypuck-nhl-latest.json").read_text())
        mp["seasons"]["2026-2027"][0]["xg_share"]=400
        self.put("moneypuck-nhl-latest.json",mp)
        self.assertEqual(self.client.get("/nhl/moneypuck").status_code,503)

    def test_fresh_moneypuck_live_source_and_no_phantom_fields(self):
        header="team,situation,games_played,goalsFor,goalsAgainst,xGoalsPercentage,name,icetime,xGoals,goals"
        teamrows=[f"T{i:02d},all,3,9,8,, ,,, " for i in range(1,26)]
        teamrows += [f"T{i:02d},5on5,3,,,0.53, ,,, " for i in range(1,26)]
        goalie=[f"T{i:02d},all,3,,,,Goalie{i},3600,3.2,2" for i in range(1,26)]
        def fetch(url):
            return header+"\\n"+"\\n".join(goalie if url.endswith("goalies.csv") else teamrows)
        data=live_moneypuck_snapshot(NOW,fetcher=fetch)
        self.assertEqual(len(data["teams"]),25)
        self.assertEqual(len(data["goalies"]),25)
        self.assertEqual(data["teams"]["T01"]["goals_for_pg"],3)
        self.assertEqual(data["teams"]["T01"]["xgf_pct"],53)
        self.assertEqual(data["goalies"][0]["gsax"],1.2)
        self.assertFalse(data["confirmed_starting_goalies"])
        self.assertIn("partial",data["revue_reproduction_status"])

    def test_moneypuck_live_fails_closed_when_provider_down(self):
        def blocked(url):
            raise OSError("provider unavailable")
        with self.assertRaises(SourceUnavailable):
            live_moneypuck_snapshot(NOW,fetcher=blocked)
        self.assertEqual(self.client.post("/nhl/moneypuck/live").status_code,405)

    def test_cors_only_for_revue_frontend(self):
        yes=self.client.get("/nhl/teams",headers={"Origin":"https://matttgic.github.io"})
        self.assertEqual(yes.headers.get("access-control-allow-origin"),"https://matttgic.github.io")
        no=self.client.get("/nhl/teams",headers={"Origin":"https://evil.example"})
        self.assertIsNone(no.headers.get("access-control-allow-origin"))


if __name__=="__main__":unittest.main()
