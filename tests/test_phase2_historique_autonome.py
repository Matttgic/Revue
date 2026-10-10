"""Prospective Revue-owned predictions and Elo: network-free source-proof regression."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json

from outils.phase2_historique_autonome import (
    VERSION, REPORT_VERSION, utc, normalize, step, summarize, SUPPORTED,
)

NOW=datetime(2026,10,10,20,0,tzinfo=timezone.utc)
ISO=lambda t:t.isoformat()
KICK=NOW+timedelta(hours=4)

def game(lg="NFL",ident="401700001",home="Bears",away="Giants",start=KICK):
    soccer=lg in ("PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1")
    probs=({"home_win_90":.45,"draw_90":.30,"away_win_90":.25}
           if soccer else {"home_win":.6,"away_win":.4})
    return {
        "league":lg,"event_id":ident,"home":home,"away":away,
        "start_utc":ISO(start),"status":"prototype_non_calibre",
        "odds":None,"probabilities":probs,"training_games":{"home":7,"away":8},
    }

def docs(games,created=None):
    return {"generated_at_utc":ISO(created or NOW-timedelta(minutes=10)),
            "status":"prototype_non_calibre",
            "competitions":{
             lg:{"games":[g for g in games if g["league"]==lg]}
             for lg in set(g["league"] for g in games),
            }}

def challenger(league,event,kind="ensemble",when=None):
    assert kind in ("ensemble","team","football")
    base=dict(event)
    base.update({"model":"shadow_v1","status":"shadow_non_calibre",
                 "odds":None,"probabilities":deepcopy(event["probabilities"])})
    if kind=="football":
        base["espn_features_published_at"]={
            "home":ISO(NOW-timedelta(hours=2)),
            "away":ISO(NOW-timedelta(hours=2)),
        }
    d={"generated_at_utc":ISO(when or NOW-timedelta(minutes=5)),
       ("competitions" if kind=="football" else "leagues"):{
          league:{"games":[base]}
       }}
    return d

def results(rows=None,time=None):
    return {
      "status":"observed_scoreboard_not_streaming",
      "scores_are_live_stream":False,"pricing_used":False,
      "generated_at_utc":ISO(time or NOW),"events":rows or [],
    }

def score(g,at,home=20,away=10):
    return {
      "league":g["league"],"event_id":g["event_id"],
      "home":g["home"],"away":g["away"],"kickoff_utc":g["start_utc"],
      "state":"final","home_score":home,"away_score":away,
      "observed_at_utc":ISO(at),"source":"ESPN scoreboard",
      "prospective_bet_result":False,
    }

EMPTY={}
def tick(prev,models,time,official=None,team=None,ensemble=None,football=None):
    return step(prev,models,team or {},ensemble or {},football or {},
                official or results(time=time),time)

class Phase2Provenance(unittest.TestCase):
    def test_new_locked_predictions_only_and_competing_models_immutable(self):
        nfl=game()
        pl=game("PL","401700002","Arsenal","Chelsea")
        base=docs([nfl,pl])
        team=challenger("NFL",nfl,"team")
        ensemble=challenger("NFL",nfl)
        football=challenger("PL",pl,"football")
        original=deepcopy((base,team,ensemble,football))
        ledger,changes=tick(None,base,NOW,team=team,ensemble=ensemble,football=football)
        self.assertEqual((base,team,ensemble,football),original)
        self.assertEqual(ledger["version"],VERSION)
        self.assertEqual(changes["new_prediction_locks"],2)
        self.assertEqual(len(ledger["events"]),2)
        n=ledger["events"]["NFL:401700001"]
        s=ledger["events"]["PL:401700002"]
        self.assertEqual(n["market"],"full_game_two_way")
        self.assertEqual(s["market"],"1X2_90min")
        self.assertEqual(set(n["probabilities"]),
                         {"baseline","advanced_team","montecarlo_bayes"})
        self.assertEqual(set(s["probabilities"]),{"baseline","football_advanced"})
        self.assertEqual(len(n["probabilities"]["baseline"]["probabilities"]),2)
        self.assertEqual(len(s["probabilities"]["baseline"]["probabilities"]),3)
        self.assertFalse(n["real_bet"])
        self.assertEqual(n["stake_units"],0)
        later=deepcopy(base)
        later["competitions"]["NFL"]["games"][0]["probabilities"]["home_win"]=.88
        newer,update=tick(ledger,later,NOW+timedelta(minutes=12))
        self.assertEqual(update["new_prediction_locks"],0)
        self.assertEqual(newer["events"]["NFL:401700001"],n)

    def test_real_final_grades_once_and_independent_elo(self):
        nfl=game();base=docs([nfl])
        history,init=tick(None,base,NOW)
        later=NOW+timedelta(hours=7)
        public=results([score(nfl,later,27,14)],later)
        next_state,delta=tick(history,base,later,public)
        self.assertEqual(delta["new_graded_forecasts"],1)
        self.assertEqual(delta["new_independent_elo_results"],1)
        b=next_state["events"]["NFL:401700001"]
        self.assertEqual(b["status"],"settled")
        self.assertEqual(b["model_scores"]["baseline"]["brier"],.32)
        self.assertAlmostEqual(b["model_scores"]["baseline"]["log_loss"],.51082562)
        self.assertEqual(next_state["elo_ratings"]["NFL"],{"Bears":1512.0,"Giants":1488.0})
        self.assertFalse(next_state["elo_events"]["NFL:401700001"].get("real_bet",False))
        again,change=tick(next_state,base,later+timedelta(hours=1),results([score(nfl,later,27,14)],later))
        self.assertEqual(change["new_graded_forecasts"],0)
        self.assertEqual(change["new_independent_elo_results"],0)
        self.assertEqual(again["events"]["NFL:401700001"],b)

    def test_old_completed_games_never_create_fake_pregame_model_or_elo(self):
        old=game(start=NOW-timedelta(days=1))
        base=docs([old])
        initial,delta=tick(None,base,NOW,results([score(old,NOW,20,17)],NOW))
        self.assertEqual(delta["new_prediction_locks"],0)
        self.assertEqual(delta["new_independent_elo_results"],0)
        self.assertEqual(initial["events"],{})
        self.assertEqual(initial["elo_events"],{})

    def test_independent_elo_counts_post_start_finals_without_fabricating_model_predictions(self):
        match=game("NBA",ident="401700003",home="Heat",away="Celtics",
                   start=NOW+timedelta(hours=2))
        prev,_=tick(None,docs([]),NOW)
        later=NOW+timedelta(hours=5)
        newer,change=tick(prev,docs([]),later,results([score(match,later,100,101)],later))
        self.assertEqual(change["new_prediction_locks"],0)
        self.assertEqual(change["new_graded_forecasts"],0)
        self.assertEqual(change["new_independent_elo_results"],1)
        self.assertEqual(newer["elo_ratings"]["NBA"],{"Heat":1488.0,"Celtics":1512.0})
        self.assertEqual(newer["events"],{})

    def test_soccer_three_way_draw_brier(self):
        soccer=game("LIGUE1","401700004","PSG","Monaco")
        base=docs([soccer])
        prev,_=tick(None,base,NOW)
        later=NOW+timedelta(hours=7)
        after,_=tick(prev,base,later,results([score(soccer,later,1,1)],later))
        item=after["events"]["LIGUE1:401700004"]
        self.assertEqual(item["result"],"draw")
        self.assertAlmostEqual(item["model_scores"]["baseline"]["brier"],(.45**2+(.30-1)**2+.25**2),places=7)
        self.assertEqual(after["elo_ratings"]["LIGUE1"],{"PSG":1500.0,"Monaco":1500.0})

    def test_invalid_results_do_not_grade_but_source_names_must_match(self):
        match=game();base=docs([match])
        locked,_=tick(None,base,NOW)
        later=NOW+timedelta(hours=7)
        wrong=score(match,later)
        wrong["home"]="Rams"
        after,delta=tick(locked,base,later,results([wrong],later))
        self.assertEqual(delta["new_graded_forecasts"],0)
        self.assertEqual(after["events"]["NFL:401700001"]["status"],"pending")
        self.assertEqual(delta["new_independent_elo_results"],1)
        self.assertIn("Rams",after["elo_ratings"]["NFL"])
        bad=score(match,later);bad["source"]="random feed"
        after,_=tick(locked,base,later,results([bad],later))
        self.assertEqual(after["elo_events"],{})
        bad=score(match,later);bad["observed_at_utc"]=ISO(KICK+timedelta(minutes=5))
        after,_=tick(locked,base,later,results([bad],later))
        self.assertEqual(after["elo_events"],{})
        bad=score(match,later);bad["home_score"]="27"
        after,_=tick(locked,base,later,results([bad],later))
        self.assertEqual(after["elo_events"],{})

    def test_duplicate_conflicting_scoreboards_rejected(self):
        match=game();base=docs([match]);locked,_=tick(None,base,NOW)
        later=NOW+timedelta(hours=6)
        x=score(match,later,27,14);y=score(match,later,17,14)
        after,meta=tick(locked,base,later,results([x,y],later))
        self.assertEqual(meta["scoreboard_conflicts_excluded"],1)
        self.assertEqual(after["elo_events"],{})
        self.assertEqual(after["events"]["NFL:401700001"]["status"],"pending")

    def test_stale_future_publish_and_after_kickoff_block_new_locks(self):
        match=game();now=NOW
        old=docs([match],NOW-timedelta(hours=16))
        future=docs([match],NOW+timedelta(minutes=1))
        self.assertEqual(tick(None,old,now)[1]["new_prediction_locks"],0)
        self.assertEqual(tick(None,future,now)[1]["new_prediction_locks"],0)
        late=game(start=NOW+timedelta(minutes=9))
        self.assertEqual(tick(None,docs([late]),now)[1]["new_prediction_locks"],0)
        bad=game();bad["probabilities"]={"home_win":1.4,"away_win":-.4}
        self.assertEqual(tick(None,docs([bad]),now)[1]["new_prediction_locks"],0)
        changed=game();changed["odds"]=1.7
        self.assertEqual(tick(None,docs([changed]),now)[1]["new_prediction_locks"],0)

    def test_ban_incompatible_market_leagues_and_overlong_samples(self):
        for lg in ("NHL","MLS","UCL","ATP","WTA","UFC","LIIGA"):
            self.assertNotIn(lg,SUPPORTED)
        self.assertIsNone(normalize({"home_win":.5,"away_win":.3},"NFL"))
        self.assertIsNone(normalize({"home_win_90":.6,"draw_90":.5,"away_win_90":.1},"PL"))
        self.assertIsNone(normalize({"home_win":True,"away_win":0},"NBA"))

    def test_forecast_versions_and_source_features_cannot_be_backfilled(self):
        x=game("PL")
        base=docs([x])
        future=challenger("PL",x,"football",NOW+timedelta(minutes=3))
        led,_=tick(None,base,NOW,football=future)
        self.assertNotIn("football_advanced",led["events"]["PL:401700001"]["probabilities"])
        leaked=challenger("PL",x,"football")
        leaked["competitions"]["PL"]["games"][0]["espn_features_published_at"]["home"]=ISO(NOW+timedelta(hours=2))
        led,_=tick(None,base,NOW,football=leaked)
        self.assertNotIn("football_advanced",led["events"]["PL:401700001"]["probabilities"])

    def test_report_does_not_claim_original_sql_or_roi(self):
        nfl=game()
        led,_=tick(None,docs([nfl]),NOW)
        r=summarize(led,NOW)
        self.assertEqual(r["version"],REPORT_VERSION)
        self.assertFalse(r["identical_original_clairvoyance_sql_history"])
        self.assertFalse(r["replayed_old_results"])
        self.assertFalse(r["models_calibrated"])
        self.assertFalse(r["roi_computed"])
        self.assertEqual(r["total_unique_matches_locked"],1)
        self.assertEqual(r["per_league"]["NFL"]["models"]["baseline"]["settled"],0)
        self.assertIsNone(r["per_league"]["NFL"]["models"]["baseline"]["brier"])

    def test_existing_revue_snapshots_have_valid_schema_and_no_lock_backfill(self):
        root=Path(__file__).resolve().parents[1]/"docs"
        base=json.loads((root/"multisports-latest.json").read_text("utf8"))
        advanced=json.loads((root/"equipes-avance-shadow.json").read_text("utf8"))
        ens=json.loads((root/"ensemble-mc-bayes-latest.json").read_text("utf8"))
        foot=json.loads((root/"football-advanced-shadow.json").read_text("utf8"))
        scores=json.loads((root/"scoreboard-revue-latest.json").read_text("utf8"))
        now=utc(base["generated_at_utc"])+timedelta(hours=1)
        out,meta=step(None,base,advanced,ens,foot,scores,now)
        self.assertGreater(meta["new_prediction_locks"],0)
        self.assertEqual(out["version"],VERSION)
        self.assertTrue(all(utc(e["locked_at_utc"])<utc(e["start_utc"])-timedelta(minutes=20)
                            for e in out["events"].values()))
        self.assertTrue(all(k.split(":")[0] in SUPPORTED for k in out["events"]))
        self.assertEqual(meta["new_independent_elo_results"],0)

if __name__=="__main__":unittest.main()
