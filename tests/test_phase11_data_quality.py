"""Phase 11 regression: missing stats remain missing; NHL market quarantine is immutable."""
from __future__ import annotations
import copy,json,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.controles.phase11_data_quality import evaluate,goalie_evidence,quarantined,INPUT_FILES
from outils.publication.match_center_revue import official_goalie_observation,collect_center
from test_match_center_revue import fixture,NOW,GENERATED,KICK

ROOT=Path(__file__).resolve().parents[1]/"docs"

class SourceQualityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data={k:json.loads((ROOT/f).read_text(encoding="utf8")) for k,f in INPUT_FILES.items()}
  cls.time=max(datetime.fromisoformat(cls.data[k]["generated_at_utc"].replace("Z","+00:00"))
               for k in ("center","goalies","picks"))+timedelta(minutes=1)
 def test_real_quarantine_matches_original_no_retrospective_repair(self):
  result=evaluate(self.data,self.time)
  summary=self.data["picks"]["paper_summary"]
  self.assertEqual(result["paper_market_quarantine"]["total"],summary["excluded"])
  self.assertTrue(result["paper_market_quarantine"]["all_nhl"])
  for r in result["paper_market_quarantine"]["records"]:
   self.assertEqual(r["source_status"],"market_rule_unverified")
   self.assertFalse(r["can_auto_promote_to_win_loss"])
   self.assertFalse(r["included_in_settled_roi"])
  self.assertFalse(result["paper_ledger_modified"])
  self.assertFalse(result["real_bets_enabled"])
  self.assertEqual(result["verified_EV_opportunities"],0)
 def test_wrong_paper_id_or_status_fails_closed(self):
  d=copy.deepcopy(self.data)
  row=next(r for r in d["picks"]["paper_records"] if r["status"]=="unverified")
  row["id"]="made-up-paper"
  with self.assertRaisesRegex(ValueError,"disagreement"):
   evaluate(d,self.time)
 def test_period_quarantine_has_not_changed_original(self):
  before=json.dumps(self.data["paper_ledger"],sort_keys=True)
  evaluate(self.data,self.time)
  self.assertEqual(json.dumps(self.data["paper_ledger"],sort_keys=True),before)
 def test_current_sources_explicitly_fail_if_missing(self):
  r=evaluate(self.data,self.time)
  self.assertEqual(r["sports"]["NBA"]["current_advanced_ready_for_models"],
                   r["sports"]["NBA"]["forecast_mode"]=="current_verified")
  self.assertFalse(r["sports"]["MLB"]["pitchers_verified_from_current_feed"])
  self.assertFalse(r["sports"]["NHL"]["actual_starters_verified"])
  self.assertEqual(r["sports"]["FOOTBALL"]["licensed_xg_available"],
                   bool((self.data["football"].get("licensed_advanced_features") or {}).get("records",0)))
  self.assertFalse(r["source_parity_100_percent"])
 def test_real_goalie_source_does_not_rewrite_probabilities(self):
  r=goalie_evidence(self.data["center"],self.data["goalies"],self.time)
  self.assertFalse(r["used_in_prediction"])
  self.assertEqual(r["actual_game_starts_independently_verified"],0)
  self.assertTrue(all(v["probabilities_modified"] is False for v in r["fixtures"]))
 def test_duplicated_source_goalies_can_never_be_assigned(self):
  d=copy.deepcopy(self.data["goalies"])
  original=next((r for r in d["rows"] if any(
    x["league"]=="NHL" and str(x["event_id"])==str(r["event_id"])
    for x in self.data["center"]["events"])),None)
  if not original:self.skipTest("Provider had no fixture matching center")
  center=next(x for x in self.data["center"]["events"] if x["league"]=="NHL"
              and str(x["event_id"])==str(original["event_id"]))
  d["rows"].append(copy.deepcopy(original))
  self.assertIsNone(official_goalie_observation(center,d,self.time))
 def test_wrong_teams_and_future_observation_rejected(self):
  d=copy.deepcopy(self.data["goalies"])
  eligible=next((r for r in d["rows"] if any(
    x["league"]=="NHL" and str(x["event_id"])==str(r["event_id"])
    for x in self.data["center"]["events"])),None)
  if eligible is None:self.skipTest("No source goalie fixtures")
  event=next(x for x in self.data["center"]["events"] if x["league"]=="NHL"
              and str(x["event_id"])==str(eligible["event_id"]))
  goalie=next(x for x in d["rows"] if str(x["event_id"])==str(event["event_id"]))
  original=goalie["home"];goalie["home"]="FAKE"
  self.assertIsNone(official_goalie_observation(event,d,self.time))
  goalie["home"]=original
  goalie["observed_at_utc"]=(self.time+timedelta(hours=1)).isoformat()
  self.assertIsNone(official_goalie_observation(event,d,self.time))
 def test_synthetic_NHL_espn_provenance_in_center(self):
  payload=fixture()
  nhl={"league":"NHL","event_id":"2026020999","home":"BOS","away":"PHI",
       "start_utc":KICK,"probabilities":{"home_win":.55,"away_win":.45}}
  payload["multisports"]["competitions"]["NHL"]={"sport":"Hockey","games":[nhl]}
  payload["goalie_observations"]={"status":"espn_probable_goalies_observed_not_part_of_model",
    "generated_at_utc":GENERATED,"used_in_prediction_model":False,
    "real_bets_enabled":False,"confirmed_is_not_a_guarantee_of_start":True,
    "rows":[{"event_id":"2026020999","home":"BOS","away":"PHI",
      "start_utc":KICK,"observed_at_utc":GENERATED,
      "home_goalie":{"name":"One Goalie","status":"confirmed","source":"ESPN probableStartingGoalie"},
      "away_goalie":{"name":"Other Goalie","status":"projected","source":"ESPN probableStartingGoalie"},
      "used_in_model_probabilities":False,"injuries_verified":False,
      "sportsbook_prices_verified":False}]}
  doc=collect_center(**payload,now=NOW)
  g=next(x for x in doc["events"] if x["league"]=="NHL")
  self.assertEqual(doc["metrics"]["with_verified_espn_goalie_observation"],1)
  self.assertEqual(g["observed_nhl_goalies"]["home"]["status"],"confirmed")
  self.assertEqual(g["observed_nhl_goalies"]["away"]["status"],"projected")
  self.assertFalse(g["observed_nhl_goalies"]["both_provider_confirmed"])
  self.assertFalse(g["observed_nhl_goalies"]["model_probabilities_recomputed"])
  self.assertFalse(g["qualified_for_real_betting"])
  self.assertIsNone(g["ev"])
 def test_synthetic_goalie_source_invalid_no_injection(self):
  payload=fixture()
  nhl={"league":"NHL","event_id":"2026020999","home":"BOS","away":"PHI",
       "start_utc":KICK,"probabilities":{"home_win":.55,"away_win":.45}}
  payload["multisports"]["competitions"]["NHL"]={"sport":"Hockey","games":[nhl]}
  payload["goalie_observations"]={"status":"espn_probable_goalies_observed_not_part_of_model",
    "generated_at_utc":GENERATED,"used_in_prediction_model":True,
    "real_bets_enabled":False,"confirmed_is_not_a_guarantee_of_start":True,
    "rows":[]}
  doc=collect_center(**payload,now=NOW)
  self.assertEqual(doc["metrics"]["with_verified_espn_goalie_observation"],0)
  self.assertIsNone(next(x for x in doc["events"] if x["league"]=="NHL")["observed_nhl_goalies"])

 def test_official_mlb_pitcher_attachment_fails_closed(self):
  from outils.publication.match_center_revue import official_mlb_probable_pitchers
  model={"league":"MLB","event_id":"401999992","home":"Dodgers","away":"Brewers",
         "start_utc":KICK}
  source={"status":"official_MLB_probable_pitchers_observed_not_confirmed",
          "generated_at_utc":GENERATED,"model_recomputed":False,
          "confirmed_starting_pitchers":0,"real_bets_enabled":False,
          "rows":[{"event_id":"401999992","home":"Dodgers","away":"Brewers",
            "start_utc":KICK,"observed_at_utc":GENERATED,
            "home_pitcher":{"name":"Pitcher A","mlb_person_id":123,
                "status":"probable_unconfirmed","source":"MLB Stats API probablePitcher"},
            "away_pitcher":None,"pitchers_are_probable_not_confirmed":True,
            "starting_pitchers_independently_confirmed":False,
            "used_in_model_probabilities":False,"sportsbook_prices_verified":False}]}
  p=official_mlb_probable_pitchers(model,source,NOW)
  self.assertEqual(p["home"]["name"],"Pitcher A")
  self.assertIsNone(p["away"])
  self.assertFalse(p["confirmed_actual_starters"])
  self.assertFalse(p["model_probabilities_recomputed"])
  corrupt=copy.deepcopy(source);corrupt["rows"][0]["home"]="Dodgers2"
  self.assertIsNone(official_mlb_probable_pitchers(model,corrupt,NOW))
  corrupt=copy.deepcopy(source);corrupt["rows"].append(copy.deepcopy(corrupt["rows"][0]))
  self.assertIsNone(official_mlb_probable_pitchers(model,corrupt,NOW))
  corrupt=copy.deepcopy(source);corrupt["rows"][0]["starting_pitchers_independently_confirmed"]=True
  self.assertIsNone(official_mlb_probable_pitchers(model,corrupt,NOW))

if __name__=="__main__":unittest.main()
