"""Phase13: paired-only honest model evaluation and chronology-frozen holdout."""
import copy,json,math,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.suivi.phase13_comparaison_modeles import (
 evaluate,compare,score_summary,loss,soften,valid_vector,bins,
 calibrate,verify,nhl_comparison,VERSION,TRAIN_N,HOLDOUT_N,PAIRED_MIN,
)

ROOT=Path(__file__).resolve().parents[1]/"docs"
BASE=datetime(2026,10,1,0,tzinfo=timezone.utc)
VERSIONS=("revue_nba_espn_previous_standings_prior_v1",
          "revue_nba_prior_elo_regressed_v1",
          "revue_nba_prior_consensus_v1")

def fixture(i,mid,p=.6,y=0,lg="NBA",settled=True):
 kick=BASE+timedelta(days=i*2,hours=9)
 source=kick-timedelta(hours=2);locked=kick-timedelta(hours=1)
 resolution=kick+timedelta(hours=4)
 game=str(8000+i)
 n=3 if lg in {"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL"} else 2
 probs=[p,1-p] if n==2 else [p,.22,.78-p]
 result=0 if y==0 else 1 if n==2 else y
 scores={"home":3 if y==0 else 1,"away":1 if y==0 else 3}
 if n==3 and y==1:scores={"home":1,"away":1}
 brier,log=loss(probs,result)
 return {"id":lg+":"+game+":"+mid,"league":lg,"event_id":game,
  "home":"Home","away":"Away","kickoff_utc":kick.isoformat(),
  "locked_at_utc":locked.isoformat(),"source_model_at_utc":source.isoformat(),
  "input_observed_at_utc":{"ESPN":(source-timedelta(minutes=15)).isoformat()},
  "model_id":mid,"market":"90min_1x2" if n==3 else "full_game_2way",
  "probabilities":probs,"status":"settled" if settled else "pending",
  "result":result if settled else None,"scores":scores if settled else None,
  "resolved_at_utc":resolution.isoformat() if settled else None,
  "brier":round(brier,6) if settled else None,
  "logloss":round(log,6) if settled else None,
  "real_bet":False,"stake_units":0,"outcome_price":None}

def led(*rows):
 return {"version":"revue_phase10_forward_ledger_v1","records":{x["id"]:x for x in rows},"since_utc":BASE.isoformat()}

def integrity():
 return {"version":"revue_phase12_settlement_audit_v1",
  "status":"official_results_active_sample_accumulating",
  "real_bets_enabled":False,"original_predictions_modified":False,"audit_errors":[]}

def nhl():
 return json.loads((ROOT/"nhl-shadow-ledger.json").read_text(encoding="utf8"))

class QualityTests(unittest.TestCase):
 def test_numerical_multiclass_scores(self):
  self.assertEqual(round(loss([.6,.2,.2],0)[0],6),.24)
  self.assertAlmostEqual(loss([.6,.2,.2],0)[1],-math.log(.6))
  self.assertAlmostEqual(sum(soften([.5,.3,.2],1.5)),1)
  self.assertFalse(valid_vector([.6,float("nan")],2))
  self.assertFalse(valid_vector([True,False],2))
 def test_no_outcomes_means_no_model_champion(self):
  real=led(fixture(0,VERSIONS[0],settled=False),
           fixture(0,VERSIONS[1],settled=False))
  out=evaluate(real,nhl(),integrity(),BASE+timedelta(days=150))
  self.assertEqual(out["metrics"]["settled"],0)
  self.assertEqual(out["calibrated_models_approved"],0)
  self.assertEqual(out["verified_profitable_models"],0)
  self.assertFalse(out["real_bets_enabled"])
  self.assertIsNone(out["ROI"])
 def test_identical_game_cohort_only(self):
  rows=[fixture(0,VERSIONS[0],p=.6),fixture(1,VERSIONS[0],p=.7),
        fixture(1,VERSIONS[1],p=.55),fixture(2,VERSIONS[1],p=.45)]
  now=BASE+timedelta(days=9)
  m=verify(led(*rows),now)
  r=compare(("NBA",VERSIONS[0]),("NBA",VERSIONS[1]),m)
  self.assertEqual(r["paired_games"],1)
  self.assertEqual(r["reference_scores"]["n"],1)
  self.assertEqual(r["candidate_scores"]["n"],1)
  self.assertIsNone(r["bootstrap_95_brier_delta"])
  self.assertEqual(r["research_status"],"insufficient_pairs")
 def test_same_event_conflicting_official_scores_rejected(self):
  a=fixture(0,VERSIONS[0],y=0)
  b=fixture(0,VERSIONS[1],y=1)
  with self.assertRaisesRegex(ValueError,"disagree"):
   verify(led(a,b),BASE+timedelta(days=3))
 def test_leaked_lock_and_false_settlement_rejected(self):
  a=fixture(0,VERSIONS[0])
  a["locked_at_utc"]=(BASE+timedelta(days=1)).isoformat()
  with self.assertRaisesRegex(ValueError,"Leaked"):verify(led(a),BASE+timedelta(days=3))
  a=fixture(0,VERSIONS[0]);a["brier"]=0.0
  with self.assertRaisesRegex(ValueError,"Brier"):verify(led(a),BASE+timedelta(days=3))
 def test_bookmaker_lookalike_data_not_allowed(self):
  a=fixture(0,VERSIONS[0]);a["outcome_price"]=1.9
  with self.assertRaisesRegex(ValueError,"Real money"):verify(led(a),BASE+timedelta(days=3))
 def test_100_train_and_new_40_kickoffs_gate(self):
  rows=[{"p":[.6,.4],"y":i%2,"resolved":BASE+timedelta(days=2*i,hours=12),
         "kickoff":BASE+timedelta(days=2*i,hours=9),
         "fixture":("NBA",str(i))} for i in range(140)]
  fit=calibrate(rows)
  self.assertEqual(fit["training_n"],TRAIN_N)
  self.assertEqual(fit["holdout_n"],HOLDOUT_N)
  self.assertEqual(fit["holdout"]["raw"]["n"],40)
  self.assertEqual(fit["holdout"]["temperature_scaled"]["n"],40)
  self.assertIn(fit["frozen_temperature"],fit["temperature_candidates"])
 def test_simultaneous_kickoffs_not_leaked_into_holdout(self):
  rows=[{"p":[.55,.45],"y":i%2,"resolved":BASE+timedelta(days=i+1),
         "kickoff":BASE+timedelta(days=i),
         "fixture":("NBA",str(i))} for i in range(145)]
  for i in range(100,145):rows[i]["kickoff"]=rows[99]["resolved"]
  fit=calibrate(rows)
  self.assertEqual(fit["training_n"],100)
  self.assertEqual(fit["holdout_n"],0)
  self.assertIsNone(fit["holdout"])
 def test_fixed_bootstrap_needs_30_paired_games(self):
  rows=[]
  for i in range(31):
   rows.extend([fixture(i,VERSIONS[0],p=.6,y=i%2),
                fixture(i,VERSIONS[1],p=.55,y=i%2)])
  m=verify(led(*rows),BASE+timedelta(days=64))
  result=compare(("NBA",VERSIONS[0]),("NBA",VERSIONS[1]),m)
  self.assertEqual(result["paired_games"],31)
  self.assertEqual(len(result["bootstrap_95_brier_delta"]),2)
  self.assertFalse(result["auto_promote"])
  self.assertEqual(result["research_status"],"paired_exploratory_only_no_model_selection")
 def test_reliability_bins_separate_outcome_classes(self):
  rows=[{"p":[.6,.2,.2],"y":0},{"p":[.4,.4,.2],"y":1}]
  b=bins(rows)
  self.assertEqual([v["outcome"] for v in b],["home","draw","away"])
  self.assertEqual(sum(q["n"] for q in b[0]["bins"]),2)
 def test_real_ledger_keeps_roi_and_winner_unknown(self):
  ledger=json.loads((ROOT/"phase10-modeles-prospectif-ledger.json").read_text())
  now=datetime.now(timezone.utc)
  report=evaluate(ledger,nhl(),integrity(),now)
  self.assertEqual(report["calibrated_models_approved"],0)
  self.assertEqual(report["verified_profitable_models"],0)
  self.assertIsNone(report["ROI"])
  self.assertTrue(all(x["approved_for_betting"] is False for x in report["models"].values()))
 def test_football_versions_remain_separate_by_league(self):
  code="revue_football_espn_shots_log_pool_v1"
  a=fixture(1,code,p=.41,y=0,lg="PL")
  b=fixture(2,code,p=.42,y=1,lg="SERIEA")
  out=evaluate(led(a,b),nhl(),integrity(),BASE+timedelta(days=150))
  self.assertIn("PL::"+code,out["models"])
  self.assertIn("SERIEA::"+code,out["models"])
  self.assertEqual(out["models"]["PL::"+code]["settled"],1)
  self.assertEqual(out["models"]["SERIEA::"+code]["settled"],1)
  self.assertEqual(out["metrics"]["distinct_settled_fixtures"],2)
 def test_nhl_native_scalar_brier_not_confused_with_two_class_brier(self):
  ledger=nhl()
  out=nhl_comparison(ledger,datetime.now(timezone.utc))
  # Live ledger grows as NHL games settle: never hard-code its size.
  self.assertGreaterEqual(out["settled"],1)
  self.assertLessEqual(out["settled"],sum(e.get("status")=="settled" for e in ledger["events"]))
  self.assertAlmostEqual(out["reference_score"]["brier"],
                         2*out["native_binary_scalar_brier"],places=5)

 def test_bad_settlement_audit_stops_all_analysis(self):
  a=integrity();a["audit_errors"]=[{"bad":"scores"}]
  with self.assertRaisesRegex(ValueError,"Phase 12"):
   evaluate(led(fixture(0,VERSIONS[0])),nhl(),a,BASE+timedelta(days=3))

if __name__=="__main__":unittest.main()
