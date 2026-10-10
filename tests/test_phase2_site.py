"""Phase2 mobile site + permanent no-backfill history provenance regression."""
import unittest
import json
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from pathlib import Path

DOCS=Path(__file__).resolve().parents[1]/"docs"

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):self.ids.add(a["id"])
        for x in ("href","src"):
            if a.get(x):self.refs.append(a[x])

def as_utc(value):
    v=datetime.fromisoformat(value.replace("Z","+00:00"))
    if v.tzinfo is None:raise ValueError("Naive chronology")
    return v.astimezone(timezone.utc)

class Phase2Site(unittest.TestCase):
    def test_mobile_history_accessible_from_bilan_lab_and_official_readonly_files(self):
        page=(DOCS/"historique-phase2.html").read_text("utf8")
        dom=Links();dom.feed(page)
        for key in ("locks","settled","elo","leagues","status",
                    "models","matches","elo-table","league-filter","state-filter"):
            self.assertIn(key,dom.ids)
        for link in ("./index.html","./bilan.html",
                     "./phase2-owned-performance.json",
                     "./phase2-owned-ledger.json","./phase1-nhl.html"):
            self.assertIn(link,dom.refs)
        self.assertIn("real_bets_enabled!==false",page)
        self.assertIn("p.replayed_old_results!==false",page)
        self.assertIn("models_calibrated!==false",page)
        self.assertIn("new Date(x)",page)
        self.assertIn("own_elo",page)
        self.assertNotIn("innerHTML",page)
        self.assertIn("./historique-phase2.html",(DOCS/"bilan.html").read_text("utf8"))
        self.assertIn("./historique-phase2.html",(DOCS/"lab.html").read_text("utf8"))

    def test_only_truly_future_locks_and_actual_esport_final_scores(self):
        perf=json.loads((DOCS/"phase2-owned-performance.json").read_text("utf8"))
        ledger=json.loads((DOCS/"phase2-owned-ledger.json").read_text("utf8"))
        self.assertEqual(perf["version"],"revue_phase2_owned_performance_v1")
        self.assertEqual(ledger["version"],"revue_phase2_owned_history_v1")
        self.assertEqual(perf["since_utc"],ledger["since_utc"])
        self.assertFalse(perf["identical_original_clairvoyance_sql_history"])
        self.assertFalse(perf["replayed_old_results"])
        self.assertFalse(perf["roi_computed"])
        self.assertFalse(perf["models_calibrated"])
        self.assertFalse(perf["real_bets_enabled"])
        self.assertFalse(perf["odds_queried"])
        self.assertEqual(len(ledger["events"]),perf["total_unique_matches_locked"])
        self.assertEqual(
            sum(v["status"]=="settled" for v in ledger["events"].values()),
            perf["total_unique_matches_settled"])
        self.assertEqual(len(ledger["elo_events"]),perf["total_independent_elo_finals"])
        self.assertLessEqual(as_utc(ledger["since_utc"]),as_utc(perf["generated_at_utc"]))
        for k,evt in ledger["events"].items():
            with self.subTest(key=k):
                self.assertTrue(k.startswith(evt["league"]+":"))
                self.assertEqual(evt["event_id"],k.split(":",1)[1])
                self.assertFalse(evt["real_bet"])
                self.assertEqual(evt["stake_units"],0)
                self.assertIn(evt["market"],("1X2_90min","full_game_two_way"))
                self.assertGreaterEqual(as_utc(evt["locked_at_utc"]),
                    as_utc(ledger["since_utc"]))
                self.assertLessEqual(as_utc(evt["locked_at_utc"]),
                    as_utc(evt["start_utc"])-timedelta(minutes=20))
                self.assertTrue(evt["probabilities"])
                for model in evt["probabilities"].values():
                    probs=model["probabilities"]
                    self.assertEqual(len(probs),3 if evt["market"]=="1X2_90min" else 2)
                    self.assertAlmostEqual(sum(probs),1,places=5)
                    self.assertLessEqual(as_utc(model["published_at_utc"]),as_utc(evt["locked_at_utc"]))
                if evt["status"]=="settled":
                    self.assertEqual(evt["score_source"],"ESPN scoreboard")
                    self.assertGreaterEqual(as_utc(evt["resolved_at_utc"]),as_utc(evt["start_utc"]))
                    self.assertTrue(evt["model_scores"])
                else:
                    self.assertEqual(evt["status"],"pending")
                    self.assertIsNone(evt["model_scores"])
        for row in ledger["elo_events"].values():
            self.assertEqual(row["score_source"],"ESPN scoreboard")
            self.assertGreaterEqual(as_utc(row["start_utc"]),as_utc(ledger["since_utc"]))
            self.assertGreaterEqual(as_utc(row["observed_at_utc"]),as_utc(row["start_utc"]))
            self.assertIn(row["league"],perf["eligible_leagues"])

if __name__=="__main__":unittest.main()
