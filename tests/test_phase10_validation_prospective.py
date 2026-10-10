"""Phase 10: immutable model-specific forward locks and strict ESPN-only settlement."""
import json,unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.phase10_modeles_multisports import build
from outils.phase10_validation_prospective import lock,settle,summarize,empty

NOW=datetime(2026,10,10,20,tzinfo=timezone.utc)
KICK=NOW+timedelta(hours=8)
SOURCE=NOW-timedelta(minutes=10)
def observed():
 events=[]
 for league,ident,h,a,code,prob in (
  ("NBA","101","Hawks","Bulls","revue_nba_prior_consensus_v1",{"home_win":.55,"away_win":.45}),
  ("MLB","102","Dodgers","Padres","revue_mlb_espn_history_elo_v1",{"home_win":.60,"away_win":.40}),
  ("PL","103","Arsenal","Chelsea","revue_football_espn_shots_log_pool_v1",
   {"home_win_90":.45,"draw_90":.30,"away_win_90":.25})):
  events.append({"event_id":ident,"league":league,"home":h,"away":a,
    "start_utc":KICK.isoformat(),"model_id":code,
    "status":"shadow_research_only_unvalidated","calibrated":False,
    "source_sql_parity":False,"bookable_price_verified":False,
    "betting_recommendation":None,"EV":None,
    "probabilities":prob,"inputs_observed_utc":{"ESPN":SOURCE.isoformat()}})
 return {"version":"revue_phase10_multisport_model_candidates_v1",
  "generated_at_utc":SOURCE.isoformat(),"status":"shadow_research_only_unvalidated",
  "real_bets_enabled":False,"prices_are_currently_bookable":False,"calibrated":False,
  "verified_positive_EV":0,"no_historical_backfill":True,"models":events}
def scores(after=NOW+timedelta(hours=11)):
 matches=[("NBA","101","Hawks","Bulls",112,104),
          ("MLB","102","Dodgers","Padres",4,3),
          ("PL","103","Arsenal","Chelsea",1,1)]
 return {"status":"observed_scoreboard_not_streaming","generated_at_utc":after.isoformat(),
    "scores_are_live_stream":False,"pricing_used":False,
    "events":[{"event_id":id,"league":lg,"home":h,"away":a,
      "kickoff_utc":KICK.isoformat(),"state":"final","source":"ESPN scoreboard",
      "home_score":x,"away_score":y,"observed_at_utc":after.isoformat(),
      "prospective_bet_result":False}for lg,id,h,a,x,y in matches]}
class Phase10LedgerTests(unittest.TestCase):
 def test_lock_all_three_sports_once_then_no_mutation(self):
  report=observed()
  one=lock(None,report,NOW)
  self.assertEqual(len(one["records"]),3)
  before=json.dumps(one,sort_keys=True)
  report["models"][0]["probabilities"]={"home_win":.99,"away_win":.01}
  two=lock(one,report,NOW+timedelta(minutes=5))
  self.assertEqual(json.dumps(two,sort_keys=True),before)
 def test_lock_does_not_backfill_postkickoff(self):
  self.assertEqual(len(lock(None,observed(),KICK+timedelta(minutes=5))["records"]),0)
 def test_bogus_live_price_or_wager_rejected(self):
  for field,v in (("real_bets_enabled",True),
                  ("prices_are_currently_bookable",True),
                  ("verified_positive_EV",20)):
   inp=observed();inp[field]=v
   self.assertEqual(len(lock(None,inp,NOW)["records"]),0)
 def test_created_after_kickoff_rejected(self):
  inp=observed();inp["models"][0]["inputs_observed_utc"]["ESPN"]=(NOW+timedelta(days=1)).isoformat()
  self.assertEqual(len(lock(None,inp,NOW)["records"]),2)
 def test_no_settlement_for_live_or_early_or_mismatched(self):
  ledger=lock(None,observed(),NOW)
  s=scores()
  s["events"][0]["home"]="Nets"
  s["events"][1]["state"]="in_progress"
  s["events"][2]["observed_at_utc"]=(NOW-timedelta(hours=1)).isoformat()
  self.assertEqual(settle(ledger,s,NOW+timedelta(hours=11))["records"],
                   ledger["records"])
 def test_espn_finals_grade_and_brier(self):
  ledger=lock(None,observed(),NOW)
  s=settle(ledger,scores(),NOW+timedelta(hours=11))
  self.assertEqual(sum(v["status"]=="settled" for v in s["records"].values()),3)
  values={r["league"]:r for r in s["records"].values()}
  self.assertEqual(values["NBA"]["result"],0)
  self.assertEqual(values["MLB"]["result"],0)
  self.assertEqual(values["PL"]["result"],1)
  self.assertAlmostEqual(values["NBA"]["brier"],.405,places=3)
  self.assertAlmostEqual(values["PL"]["brier"],.815,places=3)
  self.assertTrue(values["PL"]["logloss"]>0)
  perf=summarize(s,NOW+timedelta(hours=11))
  self.assertEqual(perf["settled"],3)
  self.assertIsNone(perf["roi"])
  self.assertFalse(perf["calibration_achieved"])
 def test_duplicate_scoreboard_cannot_settle(self):
  inp=scores();inp["events"].append(deepcopy(inp["events"][0]))
  ledger=lock(None,observed(),NOW)
  result=settle(ledger,inp,NOW+timedelta(hours=11))
  nba=[r for r in result["records"].values() if r["league"]=="NBA"][0]
  self.assertEqual(nba["status"],"pending")
 def test_one_result_cannot_regrade_frozen_history(self):
  ledger=lock(None,observed(),NOW)
  scored=settle(ledger,scores(),NOW+timedelta(hours=11))
  changed=scores(NOW+timedelta(hours=13))
  changed["events"][0]["home_score"]=98;changed["events"][0]["away_score"]=111
  repeated=settle(scored,changed,NOW+timedelta(hours=13))
  self.assertEqual(repeated["records"],scored["records"])
 def test_mls_is_research_only_until_period_rules_known(self):
  inp=observed();r=deepcopy(inp["models"][2]);r["league"]="MLS";r["event_id"]="104"
  inp["models"].append(r)
  l=lock(None,inp,NOW)
  self.assertEqual(len(l["records"]),4)
  report=scores();report["events"].append({
    **deepcopy(report["events"][2]),"league":"MLS","event_id":"104"})
  settled=settle(l,report,NOW+timedelta(hours=11))
  self.assertEqual(settled["records"]["MLS:104:revue_football_espn_shots_log_pool_v1"]["status"],"pending")
 def test_cfb_and_unknown_sports_are_not_locked(self):
  inp=observed();r=deepcopy(inp["models"][0]);r["league"]="CFB";r["event_id"]="115"
  inp["models"].append(r)
  self.assertEqual(len(lock(None,inp,NOW)["records"]),3)
if __name__=="__main__":unittest.main()
