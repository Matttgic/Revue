"""Tennis ATP/WTA, UFC and official Liiga frozen-probability tracker."""
import unittest
from datetime import datetime,timedelta,timezone
from outils.individual_prospective_revue import base,lock,settle,performance,source_results,VERSION
NOW=datetime(2026,10,10,12,tzinfo=timezone.utc)
def t(h):return (NOW+timedelta(hours=h)).isoformat()
def fixture():
    fixtures={"generated_at_utc":t(-1),"status":"prototype_non_calibre",
              "competitions":{
        "WTA":{"status":"ok","games":[{"event_id":"WTA:7","home":"Maya","away":"Nora",
                 "start_utc":t(6),"status":"prototype_non_calibre",
                 "probabilities":{"home_win":.65,"away_win":.35},
                 "training_games":{"home":7,"away":8}}]},
        "LIIGA":{"status":"ok","games":[{"event_id":"77","home":"Tappara","away":"Ilves",
                   "start_utc":t(8),"status":"prototype_non_calibre",
                   "probabilities":{"home_win":.55,"away_win":.45,"over_5_5":.5},
                   "training_games":{"home":12,"away":9}}]},
        "UFC":{"status":"ok","games":[{"event_id":"UFC:82","home":"A","away":"B",
                  "start_utc":t(9),"status":"historique_insuffisant",
                  "probabilities":None,"training_games":{"home":0,"away":0}}]}
    }}
    history={"WTA":{"events":[]},"LIIGA":{
        "source":"liiga.fi public API v2","observed_at_utc":t(-1),
        "events":[]}}
    return fixtures,history

class IndividualTrackingTests(unittest.TestCase):
    def test_lock_actual_known_players_and_preserve_immutable_probabilities(self):
        source,history=fixture()
        rows=lock(base(),source,NOW)["events"]
        self.assertEqual(len(rows),2)
        self.assertTrue(all(x["status"]=="pending" and x["stake_units"]==0 for x in rows))
        source["competitions"]["WTA"]["games"][0]["probabilities"]["home_win"]=.12
        next=lock({"version":VERSION,"events":rows},source,NOW)
        self.assertEqual(next["events"],rows)
        self.assertEqual([x for x in rows if x["league"]=="WTA"][0]["p_home"],.65)

    def test_placeholder_late_or_weak_history_never_locks(self):
        s,h=fixture()
        w=s["competitions"]["WTA"]["games"][0]
        w["home"]="TBD"
        l=s["competitions"]["LIIGA"]["games"][0]
        l["training_games"]["away"]=2
        self.assertEqual(lock(base(),s,NOW)["events"],[])
        w["home"]="Maya";w["training_games"]["home"]=7
        w["start_utc"]=t(.1)
        self.assertEqual(lock(base(),s,NOW)["events"],[])

    def test_espn_result_only_after_confirmed_flag_and_same_name(self):
        s,h=fixture()
        initial=lock(base(),s,NOW)
        now=NOW+timedelta(hours=10)
        s["generated_at_utc"]=t(10)
        h["WTA"]["events"]=[{"id":"WTA:7","league":"WTA","starts":t(6),
             "player1":"Maya","player2":"Nora","player1_id":"7","player2_id":"8",
             "finished":True,"winner_id":"8"}]
        settled=settle(initial,s,h,now)
        row=next(x for x in settled["events"] if x["league"]=="WTA")
        self.assertEqual(row["status"],"settled")
        self.assertEqual(row["result"],0)
        self.assertAlmostEqual(row["brier"],.65**2)
        self.assertFalse(row["real_bet"])
        self.assertIsNone(performance(settled,now)["leagues"]["WTA"]["roi"])
        h["WTA"]["events"][0]["player2"]="Other"
        self.assertEqual(settle(initial,s,h,now)["events"][1 if initial["events"][1]["league"]=="WTA" else 0]["status"],"pending")

    def test_liiga_final_requires_ended_and_exact_fixture(self):
        s,h=fixture()
        initial=lock(base(),s,NOW)
        now=NOW+timedelta(hours=11)
        s["generated_at_utc"]=t(11)
        h["LIIGA"]["observed_at_utc"]=t(11)
        match={"id":"77","starts":t(8),"home":"Tappara","away":"Ilves",
                "finished":False,"home_goals":3,"away_goals":2,"shootout":False}
        h["LIIGA"]["events"]=[match]
        self.assertEqual(settle(initial,s,h,now)["events"][0]["status"],"pending")
        match["finished"]=True
        result=settle(initial,s,h,now)
        row=next(x for x in result["events"] if x["league"]=="LIIGA")
        self.assertEqual(row["status"],"settled")
        self.assertEqual(row["result"],1)
        self.assertEqual(row["source_result"]["source"],"liiga.fi API v2 ended flag")

    def test_forged_late_original_forecast_cannot_be_settled(self):
        s,h=fixture()
        original=lock(base(),s,NOW)
        w=next(x for x in original["events"] if x["league"]=="WTA")
        w["locked_at_utc"]=t(7)
        new_time=NOW+timedelta(hours=10)
        s["generated_at_utc"]=t(10)
        h["WTA"]["events"]=[{"id":"WTA:7","league":"WTA","starts":t(6),
             "player1":"Maya","player2":"Nora","player1_id":"7","player2_id":"8",
             "finished":True,"winner_id":"7"}]
        result=settle(original,s,h,new_time)
        self.assertEqual(next(x for x in result["events"] if x["league"]=="WTA")["status"],"pending")

    def test_stale_source_cannot_create_picks_or_settle(self):
        s,h=fixture()
        s["generated_at_utc"]=t(-30)
        self.assertEqual(lock(base(),s,NOW)["events"],[])
        self.assertEqual(source_results(s,h,NOW),{})

if __name__=="__main__":unittest.main()
