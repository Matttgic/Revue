"""Règle de décision pré-enregistrée du journal papier."""
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from outils.suivi.regle_decision import RULE, eligible, evaluate, mean_ci  # noqa: E402

NOW = datetime(2026, 12, 1, tzinfo=timezone.utc)
START = datetime(2026, 11, 1, 19, tzinfo=timezone.utc)


def bet(i, status="won", price=2.0, p=0.55, **kw):
    b = {"id": f"paper-{i:06d}", "league": "PL", "market": "h2h", "status": status,
         "chronology": "pre_valide", "start_utc": (START + timedelta(hours=i)).isoformat(),
         "locked_at": (START + timedelta(hours=i - 3)).isoformat(),
         "quote_at": (START + timedelta(hours=i - 3)).isoformat(),
         "bookmaker": "betclic_fr", "bookmaker_price": price, "paper_stake_units": 1.0,
         "p_model": p, "market_rule_verified": True, "score": {"home": 1, "away": 0},
         "settled_at": (START + timedelta(hours=i + 2)).isoformat()}
    b.update(kw)
    return b


def ledger(bets):
    return {"version": 1, "started_at": START.isoformat(), "bets": bets}


class RuleFrozenTests(unittest.TestCase):
    def test_thresholds_cannot_change_silently(self):
        # Changer un seuil exige une nouvelle version de règle (et ce test).
        self.assertEqual(RULE, {"version": "revue_decision_rule_v1", "adopted_on": "2026-10-11",
                                "min_settled": 300, "min_for_stop": 100, "z": 1.96,
                                "min_clv_samples": 150})


class EligibilityTests(unittest.TestCase):
    def test_reasons(self):
        self.assertIsNone(eligible(bet(1)))
        self.assertEqual(eligible(bet(1, status="pending")), "non_regle")
        self.assertEqual(eligible(bet(1, chronology="post")), "chronologie_non_validee")
        late = bet(1); late["locked_at"] = late["start_utc"]
        self.assertEqual(eligible(late), "horodatage_invalide")
        quote_after = bet(1); quote_after["quote_at"] = (START + timedelta(hours=2)).isoformat()
        self.assertEqual(eligible(quote_after), "horodatage_invalide")
        self.assertEqual(eligible(bet(1, league="NHL", market_rule_verified=None)),
                         "regle_de_marche_non_verifiee")
        self.assertEqual(eligible(bet(1, bookmaker_price=1.0)), "cote_ou_mise_invalide")
        self.assertEqual(eligible(bet(1, bookmaker_price=True)), "cote_ou_mise_invalide")
        self.assertEqual(eligible(bet(1, score=None)), "resultat_sans_score")
        self.assertIsNone(eligible(bet(1, status="push", score=None)))


class VerdictTests(unittest.TestCase):
    def test_insufficient_below_volume(self):
        r = evaluate(ledger([bet(i) for i in range(20)]), NOW)
        self.assertEqual(r["verdict"], "insuffisant")
        self.assertEqual(r["criteria"][0]["progress"], "20/300")
        self.assertEqual(r["profit_units"], 20.0)
        self.assertFalse(r["real_bets_enabled"])

    def test_stop_when_roi_clearly_negative(self):
        bets = [bet(i, status="won" if i % 4 == 0 else "lost") for i in range(120)]
        self.assertEqual(evaluate(ledger(bets), NOW)["verdict"], "abandon")

    def test_promising_needs_all_four_criteria(self):
        bets = []
        for i in range(400):
            won = i % 5 < 3
            b = bet(i, status="won" if won else "lost", price=2.0,
                    p=0.75 if won else 0.35, p_peer_books_no_vig=0.5)
            start = datetime.fromisoformat(b["start_utc"])
            b["odds_history"] = [{"observed_at": (start - timedelta(minutes=30)).isoformat(),
                                  "price": 1.9, "bookmaker": "betclic_fr", "same_market_line": True}]
            bets.append(b)
        r = evaluate(ledger(bets), NOW)
        self.assertTrue(all(c["ok"] for c in r["criteria"]), r["criteria"])
        self.assertEqual(r["verdict"], "prometteur")
        # Sans cotes de clôture, le même journal n'est que « non concluant ».
        for b in bets:
            b.pop("odds_history")
        self.assertEqual(evaluate(ledger(bets), NOW)["verdict"], "non concluant")

    def test_excluded_rows_never_count(self):
        bets = [bet(i) for i in range(5)] + [bet(99, chronology="post")] * 3 + [bet(98, status="pending")]
        r = evaluate(ledger(bets), NOW)
        self.assertEqual(r["settled_eligible"], 5)
        self.assertEqual(r["excluded"], {"chronologie_non_validee": 3, "non_regle": 1})
        self.assertEqual(r["pending"], 1)

    def test_cumulative_and_segments(self):
        r = evaluate(ledger([bet(1), bet(2, status="lost"), bet(3, market="totals")]), NOW)
        self.assertEqual([x["units"] for x in r["cumulative_units"]], [1.0, 0.0, 1.0])
        self.assertEqual(r["exploratory_segments"]["by_market"]["totals"]["n"], 1)

    def test_mean_ci(self):
        self.assertIsNone(mean_ci([], 1.96))
        self.assertIsNone(mean_ci([1.0], 1.96)["ci95"])
        self.assertEqual(mean_ci([1.0, -1.0], 1.96)["mean"], 0.0)


class PublicationTests(unittest.TestCase):
    def test_published_report_matches_rule_and_page_is_linked(self):
        report = json.loads((ROOT / "docs" / "regle-decision-latest.json").read_text(encoding="utf-8"))
        self.assertEqual(report["version"], RULE["version"])
        self.assertIn(report["verdict"], {"insuffisant", "abandon", "prometteur", "non concluant"})
        self.assertIn("./regle-decision.html", (ROOT / "docs" / "lab.html").read_text(encoding="utf-8"))
        page = (ROOT / "docs" / "regle-decision.html").read_text(encoding="utf-8")
        self.assertIn("./regle-decision-latest.json", page)
        self.assertNotIn("innerHTML", page)


if __name__ == "__main__":
    unittest.main()
