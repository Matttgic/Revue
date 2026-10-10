"""No lookahead, fake moneylines, unverified NHL IDs or original-input claims."""
from datetime import date, datetime, timedelta, timezone
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from api_revue.app import create_app
from api_revue.fixtures import SourceUnavailable
from api_revue.research_predictions import predictions_from_files
from modeles.reproduction.clairvoyance_predictor import Game, nhl, mlb

NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
KICK=NOW+timedelta(hours=3)
TODAY=KICK.date()


class ResearchPredictionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.client=TestClient(create_app(root=self.root,clock=lambda:NOW))
        hist=[]
        for n in range(26):
            hist.append({
                "id":str(401000000+n),"league":"MLB",
                "start":(NOW-timedelta(days=35-n)).isoformat(),
                "home":"Dodgers" if n%2==0 else "Padres",
                "away":"Padres" if n%2==0 else "Dodgers",
                "complete":True,"home_score":4,"away_score":1,
            })
        self.save("multisports-history.json",{
            "version":1,"leagues":{"MLB":{"events":hist}}
        })
        self.save("multisports-latest.json",{
            "status":"prototype_non_calibre",
            "generated_at_utc":(NOW-timedelta(minutes=40)).isoformat(),
            "competitions":{"MLB":{"games":[{
                "event_id":"401907994","home":"Dodgers","away":"Padres",
                "start_utc":KICK.isoformat(),"odds":None
            }]}}
        })
        pre=(NOW-timedelta(hours=1)).isoformat()
        row={
            "event_id":"2026020070","home":"BOS","away":"PHI",
            "start_utc":KICK.isoformat(),
            "home_elo_proxy":1528.27,"away_elo_proxy":1493.44,
            "xg_5v5_share_pct":{"home":51,"away":32},
            "historical_goalie_proxy":{
                "home":{"save_pct":.9322},"away":{"save_pct":.9273}
            },
            "market_odds":None,"betting_recommendation":None
        }
        g=Game("401892469","BOS","PHI",
               game_date=TODAY.isoformat(),game_time_utc=KICK.isoformat())
        forecast=nhl(g,1528.27,1493.44,51,32,.9322,.9273)
        row["home_win"]=forecast["model_home_win_prob"]
        row["away_win"]=forecast["model_away_win_prob"]
        self.save("nhl-clairvoyance-shadow-latest.json",{
            "generated_at_utc":pre,
            "status":"experimental_not_calibrated",
            "bookmaker_odds_available":False,
            "point_in_time_audit":{
                "status":"verified_temporal_bounds","as_of_utc":pre
            },
            "games":[row],
        })
        self.save("parite-nhl-espn-id-map.json",{
            "generated_at_utc":NOW.isoformat(),
            "status":"verified_fixture_identity_pairs",
            "mappings":[{
                "nhl_game_id":"2026020070","original_espn_id":"401892469",
                "home":"BOS","away":"PHI","start_utc":KICK.isoformat()
            }]
        })

    def save(self,path,data):
        (self.root/path).write_text(json.dumps(data),encoding="utf-8")

    def data(self,path):
        return json.loads((self.root/path).read_text(encoding="utf-8"))

    def test_real_formula_outputs_on_both_sports_no_original_input_claim(self):
        doc=predictions_from_files(self.root,TODAY,NOW)
        self.assertEqual(doc["count"],2)
        self.assertFalse(doc["source_input_parity_with_original"])
        self.assertFalse(doc["real_bets_enabled"])
        self.assertFalse(doc["identical_original_clairvoyance_predictions_proven"])
        sports={row["sport"]:row for row in doc["predictions"]}
        self.assertEqual(set(sports),{"mlb","nhl"})
        self.assertEqual(sports["nhl"]["espn_game_id"],"401892469")
        self.assertEqual(sports["mlb"]["espn_game_id"],"401907994")
        for sport,row in sports.items():
            self.assertIsNone(row["formula_result"]["market_home_ml"])
            self.assertIsNone(row["formula_result"]["market_away_ml"])
            self.assertIsNone(row["formula_result"]["recommendation"])
            self.assertIsNone(row["formula_result"]["edge_pct"])
            self.assertFalse(row["pick_recommendation_verified"])
        self.assertEqual(sports["nhl"]["formula_result"]["model_home_win_prob"],
                         self.data("nhl-clairvoyance-shadow-latest.json")["games"][0]["home_win"])
        self.assertFalse(sports["nhl"]["features"]["goalies_are_confirmed_starters"])
        self.assertFalse(sports["mlb"]["features"]["same_original_sql_ratings"])

    def test_read_only_http_does_not_replace_original_endpoint(self):
        response=self.client.get("/revue/predictions",
            params={"game_date":TODAY.isoformat()})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()["count"],2)
        self.assertIn("research only",response.headers["X-Revue-Parity"])
        original=self.client.get("/predictions/",
            params={"game_date":TODAY.isoformat()})
        self.assertEqual(original.status_code,503)
        self.assertEqual(self.client.post("/revue/predictions").status_code,405)

    def test_no_retroactive_predictions(self):
        resp=self.client.get("/revue/predictions",
            params={"game_date":(NOW-timedelta(days=1)).date().isoformat()})
        self.assertEqual(resp.status_code,422)
        resp=self.client.get("/revue/predictions",
            params={"game_date":(NOW+timedelta(days=5)).date().isoformat()})
        self.assertEqual(resp.status_code,422)
        future=self.data("multisports-latest.json")
        future["competitions"]["MLB"]["games"][0]["start_utc"]=(NOW+timedelta(minutes=10)).isoformat()
        self.save("multisports-latest.json",future)
        nhl_doc=self.data("nhl-clairvoyance-shadow-latest.json")
        nhl_doc["games"][0]["start_utc"]=(NOW+timedelta(minutes=10)).isoformat()
        self.save("nhl-clairvoyance-shadow-latest.json",nhl_doc)
        self.assertEqual(self.client.get("/revue/predictions",
                         params={"game_date":TODAY.isoformat()}).status_code,503)

    def test_nhl_mapping_mismatch_drops_only_nhl(self):
        bad=self.data("parite-nhl-espn-id-map.json")
        bad["mappings"][0]["away"]="Wrong club"
        self.save("parite-nhl-espn-id-map.json",bad)
        doc=predictions_from_files(self.root,TODAY,NOW)
        self.assertEqual(doc["count"],1)
        self.assertEqual(doc["predictions"][0]["sport"],"mlb")

    def test_corrupt_nhl_prediction_does_not_pass_as_original_output(self):
        bad=self.data("nhl-clairvoyance-shadow-latest.json")
        bad["games"][0]["home_win"]=.999
        self.save("nhl-clairvoyance-shadow-latest.json",bad)
        doc=predictions_from_files(self.root,TODAY,NOW)
        self.assertEqual([r["sport"] for r in doc["predictions"]],["mlb"])
        self.assertIn("nhl",doc["unavailable_sports"])

    def test_future_or_stale_snapshots_cannot_create_models(self):
        self.save("nhl-clairvoyance-shadow-latest.json",{
            **self.data("nhl-clairvoyance-shadow-latest.json"),
            "generated_at_utc":(NOW-timedelta(days=4)).isoformat()
        })
        mlb_input=self.data("multisports-latest.json")
        mlb_input["generated_at_utc"]=(NOW+timedelta(hours=1)).isoformat()
        self.save("multisports-latest.json",mlb_input)
        with self.assertRaises(SourceUnavailable):
            predictions_from_files(self.root,TODAY,NOW)

    def test_unknown_mlb_team_never_uses_silent_1500_fallback(self):
        input_doc=self.data("multisports-latest.json")
        input_doc["competitions"]["MLB"]["games"][0]["home"]="Unknown Club"
        self.save("multisports-latest.json",input_doc)
        result=predictions_from_files(self.root,TODAY,NOW)
        self.assertEqual(result["count"],1)
        self.assertEqual(result["predictions"][0]["sport"],"nhl")

    def test_missing_markets_never_generate_picks_or_claim_real_odds(self):
        doc=predictions_from_files(self.root,TODAY,NOW)
        for row in doc["predictions"]:
            self.assertIsNone(row["formula_result"]["recommendation"])
            self.assertIsNone(row["formula_result"]["market_home_ml"])
            self.assertFalse(row["real_bets_enabled"])
        self.assertTrue(doc["not_live_odds"])
        self.assertTrue(doc["not_original_predictions_endpoint"])


if __name__=="__main__":
    unittest.main()
