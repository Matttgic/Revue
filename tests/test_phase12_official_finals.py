"""Phase12: overdue ESPN finals recovery + fail-closed prospective settlement."""
import copy
import json
import unittest
from datetime import datetime,timedelta,timezone
from outils.suivi.phase12_official_finals import (
    recover,eligible_targets,schedule_dates,parse_final,MAX_FETCH,
)
from outils.suivi.phase10_validation_prospective import lock,reconcile_and_settle,score_index
from test_phase10_validation_prospective import observed,scores,NOW,KICK

AFTER=NOW+timedelta(hours=12)

def espn_game(league,id,home,away,h=2,a=1,when=KICK,complete=True):
 return {"id":str(id),"date":when.isoformat(),
  "status":{"type":{"completed":complete,"state":"post" if complete else "in"}},
  "competitions":[{"competitors":[
   {"homeAway":"home","team":{"id":"123","shortDisplayName":home},"score":str(h)},
   {"homeAway":"away","team":{"id":"456","shortDisplayName":away},"score":str(a)}]}]}

def source(*rows):
 return lambda url:{"events":list(rows)}

class OfficialRecoveryTests(unittest.TestCase):
 def test_only_pending_previously_locked_games_can_be_queried(self):
  ledger=lock(None,observed(),NOW)
  targets=eligible_targets(ledger,AFTER)
  self.assertEqual(len(targets),3)
  self.assertIn("NBA:101",targets)
  self.assertIn("MLB:102",targets)
  self.assertIn("PL:103",targets)
  ledger["records"]["NBA:101:revue_nba_prior_consensus_v1"]["status"]="settled"
  self.assertEqual(len(eligible_targets(ledger,AFTER)),2)
 def test_will_not_forge_future_or_expired_matches(self):
  ledger=lock(None,observed(),NOW)
  self.assertEqual(eligible_targets(ledger,NOW),{})
  self.assertEqual(eligible_targets(ledger,AFTER+timedelta(days=22)),{})
 def test_official_final_is_recovered_after_normal_window(self):
  ledger=lock(None,observed(),NOW)
  requested=[]
  def fetch(url):
   requested.append(url)
   if "/nba/" in url:return {"events":[espn_game("NBA","101","Hawks","Bulls",113,107)]}
   if "/mlb/" in url:return {"events":[espn_game("MLB","102","Dodgers","Padres",5,2)]}
   if "/eng.1/" in url:return {"events":[espn_game("PL","103","Arsenal","Chelsea",1,1)]}
   return {"events":[]}
  late=NOW+timedelta(days=6)
  # Previously locked fixtures are reused six days later: never insert a prediction.
  data=recover(ledger,late,fetch)
  self.assertEqual(data["verified_finals"],3,data["diagnostics"])
  self.assertEqual(len(data["events"]),3)
  self.assertLessEqual(len(requested),MAX_FETCH)
  self.assertEqual(data["no_forecasts_created"],True)
  self.assertEqual(data["paid_api_calls"],0)
  self.assertTrue(all(x["source"]=="ESPN scoreboard" for x in data["events"]))
  self.assertEqual(score_index(data,late).__len__(),3)
 def test_wrong_team_or_time_cannot_settle(self):
  ledger=lock(None,observed(),NOW)
  after=AFTER
  data=recover(ledger,after,source(
   espn_game("NBA","101","Nets","Bulls",88,70),
   espn_game("MLB","102","Dodgers","Padres",4,3,when=KICK+timedelta(hours=1))))
  self.assertEqual(data["verified_finals"],0)
  self.assertGreater(data["diagnostics"].get("team_or_kickoff_mismatch",0),0)
 def test_duplicate_final_with_changed_score_is_quarantined(self):
  ledger=lock(None,observed(),NOW)
  def fetch(url):
   if "/nba/" in url:
    return {"events":[espn_game("NBA","101","Hawks","Bulls",112,104),
                      espn_game("NBA","101","Hawks","Bulls",98,121)]}
   return {"events":[]}
  data=recover(ledger,AFTER,fetch)
  self.assertEqual(data["verified_finals"],0)
  self.assertIn("NBA:101",data["conflicting_final_ids"])
 def test_nonfinal_or_early_or_tied_NBA_is_ineligible(self):
  e=espn_game("NBA","101","Hawks","Bulls",75,75)
  self.assertIsNone(parse_final(e,"NBA",AFTER))
  e=espn_game("NBA","101","Hawks","Bulls",75,70,complete=False)
  self.assertIsNone(parse_final(e,"NBA",AFTER))
  e=espn_game("NBA","101","Hawks","Bulls",75,70)
  self.assertIsNone(parse_final(e,"NBA",KICK+timedelta(minutes=80)))
 def test_cross_source_disagreement_quarantines_match(self):
  ledger=lock(None,observed(),NOW)
  current=scores(AFTER)
  archive=scores(AFTER)
  archive["events"][0]["home_score"]=80
  archive["events"][0]["away_score"]=120
  joined,conflicts=reconcile_and_settle(ledger,current,archive,AFTER)
  self.assertIn("NBA:101",conflicts)
  self.assertEqual(joined["records"]["NBA:101:revue_nba_prior_consensus_v1"]["status"],"pending")
  self.assertEqual(sum(r["status"]=="settled" for r in joined["records"].values()),2)
 def test_matching_recent_and_archive_grades_exactly_once(self):
  ledger=lock(None,observed(),NOW)
  current=scores(AFTER)
  accepted,conflicts=reconcile_and_settle(ledger,current,copy.deepcopy(current),AFTER)
  self.assertEqual(conflicts,[])
  self.assertEqual(sum(r["status"]=="settled" for r in accepted["records"].values()),3)
  repeated,_=reconcile_and_settle(accepted,current,copy.deepcopy(current),AFTER)
  self.assertEqual(repeated["records"],accepted["records"])
 def test_corrupt_virtual_wager_frozen_lock_is_never_graduated(self):
  ledger=lock(None,observed(),NOW)
  row=ledger["records"]["NBA:101:revue_nba_prior_consensus_v1"]
  row["real_bet"]=True
  result,_=reconcile_and_settle(ledger,scores(AFTER),{},AFTER)
  self.assertEqual(result["records"][row["id"]]["status"],"pending")
 def test_lock_cannot_come_after_inputs(self):
  ledger=lock(None,observed(),NOW)
  ledger["records"]["NBA:101:revue_nba_prior_consensus_v1"]["source_model_at_utc"]=(NOW+timedelta(minutes=2)).isoformat()
  result,_=reconcile_and_settle(ledger,scores(AFTER),{},AFTER)
  self.assertEqual(result["records"]["NBA:101:revue_nba_prior_consensus_v1"]["status"],"pending")
 def test_no_extra_requests_when_only_MLS_left(self):
  ledger=lock(None,observed(),NOW)
  for row in ledger["records"].values():row["league"]="MLS"
  data=recover(ledger,AFTER,lambda url: (_ for _ in ()).throw(RuntimeError("No calls")))
  self.assertEqual(data["requests"]["attempted"],0)
  self.assertEqual(data["verified_finals"],0)
 def test_missing_ESPN_day_is_reported_not_a_winner(self):
  ledger=lock(None,observed(),NOW)
  data=recover(ledger,AFTER,lambda url: (_ for _ in ()).throw(RuntimeError("Offline")))
  self.assertEqual(data["verified_finals"],0)
  self.assertEqual(data["requests"]["failures"],data["requests"]["attempted"])
  self.assertEqual(data["unresolved_eligible"],3)
 def test_calendar_is_per_league_and_bounded(self):
  ledger=lock(None,observed(),NOW)
  keys=eligible_targets(ledger,AFTER)
  plan=schedule_dates(keys,AFTER,max_fetch=4)
  self.assertLessEqual(len(plan),4)
  self.assertTrue(all(league in {"NBA","MLB","PL"} for league,_ in plan))
if __name__=="__main__":unittest.main()
