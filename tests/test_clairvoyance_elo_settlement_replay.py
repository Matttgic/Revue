"""Faithful Clairvoyance Elo mathematics, honest private SQL provenance."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
import unittest

from outils.clairvoyance.clairvoyance_elo_settlement_replay import (
    VERSION,SOURCE_K,SOURCE_DEFAULT,update_pair,eligible,reconstruct,
)

NOW=datetime(2026,10,10,23,0,tzinfo=timezone.utc)
START=NOW-timedelta(hours=6)


def pick(ident="paper-e01",event="2026029001",home="BOS",away="PHI",
         league="NHL",market="h2h",side="home",status="won"):
    return {
        "id":ident,"league":league,"event_id":event,"market":market,
        "side":side,"status":status,"home":home,"away":away,
        "start_utc":START.isoformat(),
        "locked_at":(START-timedelta(hours=2)).isoformat(),
        "quote_at":(START-timedelta(hours=2,minutes=1)).isoformat(),
        "model_at":(START-timedelta(hours=3)).isoformat(),
        "chronology":"pre_valide","market_rule_verified":True,
        "score":{"home":3,"away":2},
        "settled_at":(START+timedelta(hours=3)).isoformat(),
        "settlement_source":"ESPN observed final, league and fixture identity verified",
    }


class EloFaithful(unittest.TestCase):
    def test_original_elo_equation_k32_no_home_advantage(self):
        self.assertEqual((SOURCE_DEFAULT,SOURCE_K),(1500.0,32.0))
        self.assertEqual(update_pair(1500,1500),(1516.0,1484.0))
        self.assertEqual(update_pair(1516,1484),(1530.53,1469.47))
        self.assertAlmostEqual(sum(update_pair(1400,1600)),3000.0)

    def test_one_strict_moneyline_settlement_one_update(self):
        ledger={"version":1,"bets":[pick()]}
        orig=deepcopy(ledger)
        result=reconstruct(ledger,NOW)
        self.assertEqual(orig,ledger)
        self.assertEqual(result["version"],VERSION)
        self.assertEqual(result["eligible_revue_settled_moneyline_updates"],1)
        self.assertEqual(result["by_sport"]["NHL"]["ratings"]["BOS"]["rating"],1516)
        self.assertEqual(result["by_sport"]["NHL"]["ratings"]["PHI"]["rating"],1484)
        self.assertTrue(result["updates_only_on_settled_moneyline_picks"])
        self.assertFalse(result["updates_every_completed_nhl_game"])
        self.assertFalse(result["original_sql_elo_values_available"])
        self.assertFalse(result["identical_original_settled_pick_history_verified"])
        self.assertFalse(result["real_bets_enabled"])

    def test_source_updates_per_pick_not_per_distinct_game(self):
        a=pick()
        b=pick(ident="paper-e02",side="away",status="lost")
        b["settled_at"]=(START+timedelta(hours=4)).isoformat()
        res=reconstruct({"version":1,"bets":[a,b]},NOW)
        self.assertEqual(res["eligible_revue_settled_moneyline_updates"],2)
        self.assertEqual(res["duplicate_event_updates"],["NHL:2026029001"])
        self.assertEqual(res["by_sport"]["NHL"]["ratings"]["BOS"]["rating"],1530.53)
        self.assertEqual(res["by_sport"]["NHL"]["ratings"]["PHI"]["rating"],1469.47)
        self.assertFalse(res["original_sql_ordering_verified"])

    def test_unsettled_totals_invalid_chronology_and_ambiguous_rules_skipped(self):
        candidates=[]
        for id_,change in enumerate([
            {"market":"totals","side":"over"},
            {"market_rule_verified":False},
            {"status":"pending"},
            {"league":"NBA"},
            {"settlement_source":"unverified"},
            {"locked_at":(START+timedelta(minutes=3)).isoformat()},
            {"quote_at":(START+timedelta(minutes=2)).isoformat()},
            {"side":"draw"},
        ]):
            b=pick(ident=f"paper-skip-{id_}")
            b.update(change)
            candidates.append(b)
        result=reconstruct({"version":1,"bets":candidates},NOW)
        self.assertEqual(result["eligible_revue_settled_moneyline_updates"],0)
        self.assertEqual(result["by_sport"]["NHL"]["ratings"],{})
        self.assertEqual(result["by_sport"]["MLB"]["ratings"],{})
        self.assertEqual(len(candidates),sum(result["rejected_entries"].values()))

    def test_conflicting_winner_final_no_elo(self):
        b=pick(status="lost")
        good,why=eligible(b,NOW)
        self.assertFalse(good)
        self.assertEqual(why,"recorded_result_conflicts_score")
        b=pick()
        b["score"]={"home":1,"away":1}
        self.assertEqual(eligible(b,NOW)[1],"invalid_score")

    def test_source_must_be_official_final_after_match(self):
        b=pick()
        b["settled_at"]=(START+timedelta(minutes=10)).isoformat()
        self.assertEqual(eligible(b,NOW)[1],"invalid_score_chronology")
        b=pick()
        b["settled_at"]=(NOW+timedelta(hours=2)).isoformat()
        self.assertEqual(eligible(b,NOW)[1],"invalid_score_chronology")
        b=pick()
        b["score"]["away"]=None
        self.assertEqual(eligible(b,NOW)[1],"invalid_score")

    def test_duplicate_id_refused_not_double_counted(self):
        p=pick()
        with self.assertRaises(ValueError):
            reconstruct({"version":1,"bets":[p,deepcopy(p)]},NOW)

    def test_real_revue_paper_ledger_does_not_fabricate_sql_elo(self):
        root=Path(__file__).resolve().parents[1]/"docs"
        ledger=json.loads((root/"engine-v2-ledger.json").read_text("utf8"))
        initial=deepcopy(ledger)
        clock=max(NOW,datetime.now(timezone.utc))
        result=reconstruct(ledger,clock)
        self.assertEqual(ledger,initial)
        self.assertEqual(result["status"],
            "source_elo_update_math_verified_private_state_unknown")
        self.assertFalse(result["original_sql_elo_values_available"])
        for update in result["update_audit"]:
            self.assertTrue(update["verified_official_score"])
            self.assertFalse(update["identical_original_sql_rating"])

    def test_naive_clock_and_unknown_ledger_fail_closed(self):
        with self.assertRaises(ValueError):
            reconstruct({"version":1,"bets":[]},datetime(2026,10,10))
        with self.assertRaises(ValueError):
            reconstruct({"version":3,"bets":[]},NOW)


if __name__=="__main__":
    unittest.main()
