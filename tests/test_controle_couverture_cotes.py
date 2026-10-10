"""Synthetic multi-book soccer math tests + real read-only PulseScore snapshot tests."""
import unittest
import json
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path

from outils.controle_couverture_cotes import (
    analyze,source_rows,MIN_THEORETICAL_EDGE,VERSION
)
NOW=datetime(2026,10,10,19,tzinfo=timezone.utc)
UTC=lambda x:x.isoformat()
KICKOFF=NOW+timedelta(hours=3)


def market(book):
    h={"betclic_fr":(2.4,3.2,3.1),
       "winamax_fr":(2.,4.1,3.3),
       "pmu_fr":(2.,3.2,4.2)}[book]
    return {"market":"h2h","period_rule":"90min","quote_at":UTC(NOW),
            "outcomes":[dict(selection=side,price=price)
                for side,price in zip(("home","draw","away"),h)]}


def totals(book,line=2.5):
    p={"betclic_fr":(2.12,1.82),"winamax_fr":(1.82,2.10),
       "pmu_fr":(1.90,1.90)}[book]
    return {"market":"totals","period_rule":"90min","quote_at":UTC(NOW),
            "outcomes":[{"selection":"over","line":line,"price":p[0]},
                        {"selection":"under","line":line,"price":p[1]}]}


def event():
    return {
        "league":"PL","event_id":"401333333","home":"Arsenal","away":"Leeds",
        "start_utc":UTC(KICKOFF),
        "bookmakers":[{"bookmaker":book,"markets":[market(book),totals(book)]}
          for book in ("betclic_fr","winamax_fr","pmu_fr")],
    }


def radar(*events):
    return {
        "version":"revue_pulsescore_six_hour_radar_v1",
        "status":"observed","provider":"PulseScore",
        "market_prices_are_live":False,"positive_ev_verified":False,
        "real_bets_enabled":False,"existing_paper_ledger_modified":False,
        "horizon_hours":6,"request_cap":8,"requests_used":3,
        "generated_at_utc":UTC(NOW),"observations":list(events),
    }


class CrossBookTests(unittest.TestCase):
    def test_three_way_complete_and_two_way_totals_are_math_not_bookable(self):
        raw=radar(event());untouched=deepcopy(raw)
        output=analyze({"radar_6h":raw},NOW)
        self.assertEqual(raw,untouched)
        self.assertEqual(output["version"],VERSION)
        self.assertEqual(output["source_event_snapshots_audited"],1)
        self.assertEqual(output["complete_cross_book_markets_checked"],2)
        self.assertEqual(output["potential_snapshot_cover_count"],2)
        self.assertEqual({x["market"] for x in output["potential_snapshot_covers"]},
                         {"h2h","totals"})
        first=next(x for x in output["potential_snapshot_covers"] if x["market"]=="h2h")
        self.assertEqual(first["period_rule"],"90min")
        self.assertLess(first["inverse_odds_sum"],1-MIN_THEORETICAL_EDGE)
        self.assertGreater(first["mathematical_snapshot_excess_pct"],0)
        self.assertEqual(first["bookmaker_count"],3)
        self.assertFalse(first["claim_executable_arbitrage"])
        self.assertFalse(first["all_prices_confirmed_bookable"])
        self.assertFalse(output["risk_flags"]["claim_guaranteed_profit"])
        self.assertFalse(output["risk_flags"]["claim_positive_expected_value"])
        self.assertEqual(output["risk_flags"]["paid_api_calls_for_this_audit"],0)

    def test_never_assume_soccer_match_winner_equals_two_way_game_winner(self):
        game=event()
        for b in game["bookmakers"]:
            b["markets"][0]["period_rule"]="game_result"
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["complete_cross_book_markets_checked"],1)
        self.assertTrue(all(x["market"]=="totals" for x in out["potential_snapshot_covers"]))
        self.assertGreaterEqual(out["diagnostics"]["period_unverified"],3)

    def test_skip_nhl_unverified_overtime_even_when_odds_cover(self):
        game=event();game["league"]="NHL"
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)
        self.assertEqual(out["source_event_snapshots_audited"],0)
        self.assertGreater(out["diagnostics"]["unsupported_or_ambiguous_settlement"],0)

    def test_require_same_totals_line_and_half_or_whole(self):
        game=event()
        for b in game["bookmakers"]:
            b["markets"]=[totals(b,2.5 if b["bookmaker"]!="winamax_fr" else 3.5)]
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)
        game=event()
        for b in game["bookmakers"]:
            b["markets"]=[totals(b,2.25)]
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)

    def test_no_duplicate_bookmakers_or_market_rows(self):
        game=event()
        game["bookmakers"].append(deepcopy(game["bookmakers"][0]))
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)
        self.assertGreater(out["diagnostics"]["duplicate_bookmaker"],0)
        game=event()
        game["bookmakers"][0]["markets"].append(deepcopy(game["bookmakers"][0]["markets"][0]))
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)
        self.assertGreater(out["diagnostics"]["duplicate_book_market"],0)

    def test_stale_or_time_divergent_prices_cannot_be_combined(self):
        game=event()
        game["bookmakers"][0]["markets"][0]["quote_at"]=UTC(NOW-timedelta(minutes=27))
        out=analyze({"radar_6h":radar(game)},NOW)
        self.assertEqual(
            [x for x in out["potential_snapshot_covers"] if x["market"]=="h2h"],[])
        game=event()
        for bk in game["bookmakers"]:
            for m in bk["markets"]:m["quote_at"]=UTC(NOW-timedelta(minutes=90))
        self.assertEqual(analyze({"radar_6h":radar(game)},NOW)["potential_snapshot_cover_count"],0)

    def test_source_snapshot_freshness_and_provenance_fail_closed(self):
        old=radar(event())
        old["generated_at_utc"]=UTC(NOW-timedelta(hours=2))
        self.assertEqual(source_rows(old,NOW)[1],"missing_or_stale")
        fake=radar(event());fake["real_bets_enabled"]=True
        self.assertEqual(source_rows(fake,NOW)[1],"invalid_provenance")
        future=radar(event());future["generated_at_utc"]=UTC(NOW+timedelta(hours=4))
        self.assertEqual(source_rows(future,NOW)[1],"missing_or_stale")
        out=analyze({"radar_6h":fake},NOW)
        self.assertEqual(out["potential_snapshot_cover_count"],0)

    def test_mixing_stale_full_scan_with_new_radar_is_not_allowed(self):
        game=event()
        original=radar(game)
        b=radar(deepcopy(game))
        b["generated_at_utc"]=UTC(NOW-timedelta(hours=2))
        out=analyze({"radar_6h":original,"full_scan":b},NOW)
        self.assertEqual(out["source_event_snapshots_audited"],1)
        self.assertEqual(out["source_snapshots"]["full_scan"]["status"],
                         "missing_or_stale")

    def test_real_repo_observations_do_not_invent_covers(self):
        root=Path(__file__).resolve().parents[1]/"docs"
        full=json.loads((root/"engine-v2-latest.json").read_text("utf8"))
        short=json.loads((root/"pulsescore-radar-latest.json").read_text("utf8"))
        now=datetime.fromisoformat(short["generated_at_utc"].replace("Z","+00:00"))+timedelta(minutes=2)
        out=analyze({"radar_6h":short,"full_scan":full},now)
        self.assertIn("source_event_snapshots_audited",out)
        self.assertEqual(out["status"],"math_only_quotes_observed_no_bookable_confirmation")
        self.assertEqual(out["source_snapshots"]["radar_6h"]["status"],
                         "validated_snapshot_radar")
        for candidate in out["potential_snapshot_covers"]:
            self.assertIn(candidate["league"],{"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS"})
            self.assertEqual(candidate["period_rule"],"90min")
            self.assertLess(candidate["inverse_odds_sum"],1)
            self.assertFalse(candidate["claim_executable_arbitrage"])

    def test_no_naive_clock(self):
        with self.assertRaises(ValueError):
            analyze({"radar_6h":radar(event())},datetime(2026,10,10,19))


if __name__=="__main__":unittest.main()
