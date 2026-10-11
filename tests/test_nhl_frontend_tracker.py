"""Offline regression tests for immutable pre-match NHL frontend model comparison."""
import json
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path

from modeles.simulations.nhl_independant import Game
from outils.suivi.nhl_frontend_tracker import (
    VERSION,valid_report,lockable,update_ledger,summarize,process,due_scoreboard_days,
)

DOC=Path(__file__).resolve().parents[1]/"docs"/"nhl-frontend-observed-latest.json"
SAMPLE=json.loads(DOC.read_text(encoding="utf8"))
GENERATED=datetime.fromisoformat(SAMPLE["generated_at_utc"].replace("Z","+00:00"))
T=GENERATED+timedelta(minutes=2)


class NHLModels(unittest.TestCase):
    def test_real_source_forecast_lock_at_observation_time(self):
        self.assertTrue(valid_report(SAMPLE,T))
        result=update_ledger(None,SAMPLE,[],T)
        self.assertEqual(result["version"],VERSION)
        self.assertGreater(len(result["events"]),0)
        self.assertLessEqual(len(result["events"]),SAMPLE["games_emitted"])
        self.assertTrue(all(x["status"]=="pending" for x in result["events"]))
        self.assertTrue(all(x["model_monte_carlo"]>0 and x["model_ensemble"]>0 for x in result["events"]))
        self.assertTrue(all(x["calibrated"] is False and x["goalies_and_injuries_verified"] is False for x in result["events"]))
        self.assertTrue(all(x["locked_at_utc"]==T.isoformat() for x in result["events"]))
        perf=summarize(result,T)
        self.assertEqual(perf["settled_games"],0)
        self.assertIsNone(perf["models"]["ensemble"]["brier"])
        self.assertIsNone(perf["roi"])
        self.assertFalse(perf["statistically_valid_profitability_proven"])

    def test_immutable_existing_forecast_even_after_new_prediction_changes(self):
        first=update_ledger(None,SAMPLE,[],T)
        changed=deepcopy(SAMPLE)
        for x in changed["games"]:
            x["research"]["ensemble_home"]=0.9
            x["research"]["monte_carlo_home"]=0.8
        next_check=update_ledger(first,changed,[],T+timedelta(minutes=7))
        old={r["event_id"]:r for r in first["events"]}
        for r in next_check["events"]:
            self.assertEqual(r,old[r["event_id"]])
        self.assertEqual(SAMPLE["games_emitted"],len(SAMPLE["games"]))

    def test_official_game_score_settles_only_exact_id_kickoff_teams(self):
        ledger=update_ledger(None,SAMPLE,[],T)
        row=ledger["events"][0]
        kickoff=datetime.fromisoformat(row["kickoff_utc"])
        when=kickoff+timedelta(hours=4)
        original=deepcopy(ledger)
        final=Game(row["event_id"],kickoff,row["home"],row["away"],"OFF",3,2)
        graded=update_ledger(ledger,{},[final],when)
        self.assertEqual(ledger,original)
        found=next(r for r in graded["events"] if r["event_id"]==row["event_id"])
        self.assertEqual(found["status"],"settled")
        self.assertEqual(found["actual_home_win"],1)
        self.assertEqual(found["score_source"],"NHL official final")
        self.assertAlmostEqual(found["brier_ensemble"],(row["model_ensemble"]-1)**2,places=5)
        perf=summarize(graded,when)
        self.assertEqual(perf["settled_games"],1)
        self.assertIsNotNone(perf["models"]["ensemble"]["brier"])
        self.assertIsNotNone(perf["models"]["monte_carlo"]["log_loss"])
        self.assertFalse(perf["statistically_valid_profitability_proven"])
        again=update_ledger(graded,{},[final],when+timedelta(days=1))
        self.assertEqual(next(r for r in again["events"] if r["event_id"]==row["event_id"]),found)

    def test_wrong_result_identity_time_or_teams_never_graded(self):
        ledger=update_ledger(None,SAMPLE,[],T)
        row=ledger["events"][0]
        kickoff=datetime.fromisoformat(row["kickoff_utc"])
        when=kickoff+timedelta(hours=3)
        for bad in (
            Game("2026029999",kickoff,row["home"],row["away"],"OFF",3,1),
            Game(row["event_id"],kickoff+timedelta(minutes=3),row["home"],row["away"],"OFF",3,1),
            Game(row["event_id"],kickoff,"WPG",row["away"],"OFF",3,1),
            Game(row["event_id"],kickoff,row["home"],"WPG","OFF",3,1),
            Game(row["event_id"],kickoff,row["home"],row["away"],"FUT",None,None),
        ):
            after=update_ledger(ledger,{},[bad],when)
            self.assertEqual(sum(r["status"]=="settled" for r in after["events"]),0)
        self.assertTrue(due_scoreboard_days(ledger,when))

    def test_invalid_or_post_start_source_never_backfilled(self):
        fake=deepcopy(SAMPLE)
        fake["generated_at_utc"]=(T+timedelta(hours=1)).isoformat()
        self.assertFalse(valid_report(fake,T))
        forged=deepcopy(SAMPLE)
        forged["source_snapshot_utc"]["shadow"]=(T+timedelta(hours=2)).isoformat()
        self.assertFalse(valid_report(forged,T))
        finished=update_ledger(None,SAMPLE,[],T+timedelta(days=8))
        self.assertEqual(len(finished["events"]),0)
        tampered=deepcopy(SAMPLE)
        tampered["real_bets_enabled"]=True
        self.assertFalse(valid_report(tampered,T))
        now=GENERATED+timedelta(hours=12,minutes=1)
        self.assertFalse(valid_report(SAMPLE,now))

    def test_invalid_model_probabilities_and_starter_assertions(self):
        for mutate in (
            lambda x: x["research"].update(ensemble_home=0),
            lambda x: x["research"].update(simulation_draws=250),
            lambda x: x.update(injuries_verified=True),
            lambda x: x.update(bookmaker_quotes_available=True),
        ):
            bad=deepcopy(SAMPLE["games"][0]);mutate(bad)
            self.assertIsNone(lockable(bad,SAMPLE,T))
        dup=deepcopy(SAMPLE);dup["games"].append(dup["games"][0])
        dup["games_emitted"]+=1
        with self.assertRaises(ValueError):
            update_ledger(None,dup,[],T)

    def test_no_score_fabrication_without_official_results(self):
        ledger=update_ledger(None,SAMPLE,[],T)
        upcoming=update_ledger(ledger,{},[],T+timedelta(days=2))
        self.assertTrue(all(x["status"]=="pending" for x in upcoming["events"]))
        perf=summarize(upcoming,T+timedelta(days=2))
        self.assertEqual(perf["settled_games"],0)
        self.assertEqual(perf["pending_games"],len(upcoming["events"]))

    def test_process_with_mocked_valid_nhl_official_scoreboard(self):
        locked=update_ledger(None,SAMPLE,[],T)
        row=locked["events"][0]
        kickoff=datetime.fromisoformat(row["kickoff_utc"])
        when=kickoff+timedelta(hours=4)
        day=kickoff.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).date().isoformat()
        def fetch(url):
            queried=url.rsplit("/",1)[-1]
            if queried!=day:
                return {"currentDate":queried,"games":[]}
            return {"currentDate":day,"games":[{
                "id":int(row["event_id"]),"gameType":2,
                "startTimeUTC":kickoff.isoformat().replace("+00:00","Z"),
                "gameState":"OFF",
                "homeTeam":{"abbrev":row["home"],"score":2},
                "awayTeam":{"abbrev":row["away"],"score":1},
                "gameOutcome":{"lastPeriodType":"REG"},
            }]}
        update,perf=process(locked,{},when,fetcher=fetch)
        self.assertEqual(perf["settled_games"],1)
        self.assertEqual(update["events"][0]["event_id"],row["event_id"])

if __name__=="__main__":unittest.main()
