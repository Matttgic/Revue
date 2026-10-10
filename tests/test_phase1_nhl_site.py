"""Phase-1 public audit website must present source-backed evidence, never 100% bluff."""
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"docs"


class DOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set()
        self.links=set()
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get("id"):self.ids.add(d["id"])
        if d.get("href"):self.links.add(d["href"])


class Phase1Web(unittest.TestCase):
    def test_all_main_metrics_and_original_public_references_are_linked(self):
        html=(DOC/"phase1-nhl.html").read_text("utf8")
        d=DOM()
        d.feed(html)
        for key in ("gates","formulas","goalies","xg","gap","settled",
                    "checks","remaining","status"):
            self.assertIn(key,d.ids)
        for target in ("./index.html","./phase1-nhl-fidelity.json",
                        "./parite-nhl-gardiens-publics.json",
                        "./clairvoyance-elo-source-audit.json",
                        "./bilan.html"):
            self.assertIn(target,d.links)
        lab=(DOC/"lab.html").read_text("utf8")
        self.assertIn("./phase1-nhl.html",lab)
        self.assertIn('j.phase1_completed',html)
        self.assertIn('phase1_completion_is_not_functional_coverage_percent',html)
        self.assertIn('original_sql_goalie_rows_verified',str((DOC/"parite-nhl-gardiens-publics.json").read_text("utf8")))
        self.assertNotIn("innerHTML",html)

    def test_actual_evidence_refuses_to_claim_full_parity(self):
        phase=json.loads((DOC/"phase1-nhl-fidelity.json").read_text("utf8"))
        goalies=json.loads((DOC/"parite-nhl-gardiens-publics.json").read_text("utf8"))
        elo=json.loads((DOC/"clairvoyance-elo-source-audit.json").read_text("utf8"))
        self.assertFalse(phase["phase1_completed"])
        self.assertEqual(phase["version"],"revue_clairvoyance_nhl_phase1_acceptance_v1")
        self.assertEqual(phase["checkpoint"]["public_original_nhl_goalie_names_equal"],
                         goalies["matching_names"])
        self.assertEqual(phase["checkpoint"]["public_original_nhl_goalie_status_changes"],
                         goalies["different_statuses"])
        self.assertEqual(phase["checkpoint"]["eligible_revue_moneyline_source_elo_updates"],
                         elo["eligible_revue_settled_moneyline_updates"])
        self.assertTrue(phase["acceptance_gates"]["public_nhl_goalie_names_cross_source_identity"])
        self.assertFalse(phase["acceptance_gates"]["original_elo_sql_state_and_settlement_history"])
        self.assertFalse(phase["acceptance_gates"]["identical_published_probabilities"])
        self.assertFalse(elo["original_sql_elo_values_available"])
        self.assertFalse(goalies["original_prediction_parity_verified"])
        self.assertFalse(elo["real_bets_enabled"])
        self.assertTrue(all(x["gate"] in phase["acceptance_gates"]
                            for x in phase["remaining_requirements"]))


if __name__=="__main__":
    unittest.main()
