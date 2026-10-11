"""Offline tests: strictly observational paper settlement; no price API calls."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.suivi.reglement_multisport_officiel import grade_existing,official_index

NOW=datetime(2026,10,12,1,tzinfo=timezone.utc)
START=datetime(2026,10,11,19,tzinfo=timezone.utc)
ISO=lambda x:x.isoformat()
LOCK=START-timedelta(hours=1)
QUOTE=LOCK-timedelta(minutes=5)
MODEL=LOCK-timedelta(minutes=30)
OBS=START+timedelta(hours=3)
SNAP=OBS+timedelta(minutes=1)


def paper_bet(league="PL",event="401111",market="h2h",side="home",line=None):
    return {
        "id":"paper-00001","league":league,"event_id":event,
        "home":"Arsenal","away":"Chelsea","start_utc":ISO(START),
        "status":"pending","market":market,"side":side,"line":line,
        "quote_at":ISO(QUOTE),"model_at":ISO(MODEL),
        "locked_at":ISO(LOCK),"chronology":"pre_valide",
        "market_rule_verified":True,"paper_stake_units":1.0,
        "bookmaker_price":2.5,"outcome":"Arsenal",
    }


def final(league="PL",event="401111",home="Arsenal",away="Chelsea",hs=2,aw=1):
    return {"league":league,"event_id":event,"home":home,"away":away,
            "kickoff_utc":ISO(START),"state":"final",
            "home_score":hs,"away_score":aw,
            "observed_at_utc":ISO(OBS),
            "source":"ESPN scoreboard","prospective_bet_result":False}


def snapshot(*events):
    return {"status":"observed_scoreboard_not_streaming",
            "generated_at_utc":ISO(SNAP),"scores_are_live_stream":False,
            "pricing_used":False,"events":list(events)}


class VerifiedScores(unittest.TestCase):
    def test_observed_football_win_and_idempotence(self):
        bet=paper_bet()
        ledger={"version":1,"bets":[bet]}
        original=deepcopy(ledger)
        updated,report=grade_existing(ledger,snapshot(final()),NOW)
        self.assertEqual(ledger,original)
        self.assertEqual(updated["bets"][0]["status"],"won")
        self.assertEqual(updated["bets"][0]["score"],{"home":2,"away":1})
        self.assertEqual(updated["bets"][0]["paper_units_returned"],2.5)
        self.assertEqual(report["paper_profit_units"],1.5)
        self.assertEqual(report["settled_total"],1)
        self.assertEqual(report["newly_settled"],1)
        self.assertEqual(report["no_bets_created"],True)
        again,rep=grade_existing(updated,snapshot(final()),NOW)
        self.assertEqual(again,updated)
        self.assertEqual(rep["newly_settled"],0)

    def test_scoreboard_must_be_recent_and_explicitly_final(self):
        stale=snapshot(final())
        stale["generated_at_utc"]=ISO(NOW-timedelta(hours=12))
        with self.assertRaises(ValueError):
            grade_existing({"version":1,"bets":[]},stale,NOW)
        fake=snapshot(final())
        fake["scores_are_live_stream"]=True
        with self.assertRaises(ValueError):
            grade_existing({"version":1,"bets":[]},fake,NOW)
        wrong=snapshot(final())
        wrong["events"][0]["source"]="anonymous"
        self.assertEqual(grade_existing({"version":1,"bets":[paper_bet()]},wrong,NOW)[1]["newly_settled"],0)
        unfinished=snapshot(final())
        unfinished["events"][0]["state"]="in_progress"
        self.assertEqual(grade_existing({"version":1,"bets":[paper_bet()]},unfinished,NOW)[1]["newly_settled"],0)

    def test_id_team_kickoff_are_all_required(self):
        for change in ({"event_id":"wrong"},
                       {"home":"Liverpool"},
                       {"away":"Liverpool"},
                       {"kickoff_utc":ISO(START+timedelta(hours=1))}):
            rec=final()
            rec.update(change)
            result,report=grade_existing({"version":1,"bets":[paper_bet()]},snapshot(rec),NOW)
            self.assertEqual(report["newly_settled"],0)
            self.assertEqual(result["bets"][0]["status"],"pending")

    def test_unverified_market_rules_and_missing_timing(self):
        p=paper_bet()
        p["market_rule_verified"]=False
        out,r=grade_existing({"version":1,"bets":[p]},snapshot(final()),NOW)
        self.assertEqual(r["newly_settled"],0)
        bad=paper_bet()
        bad["quote_at"]=ISO(LOCK-timedelta(hours=3))
        out,r=grade_existing({"version":1,"bets":[bad]},snapshot(final()),NOW)
        self.assertEqual(r["newly_settled"],0)

    def test_unsupported_nhl_and_ucl_never_assume_ot_or_90min_rules(self):
        for league in ("NHL","UCL","CFB"):
            bet=paper_bet(league=league)
            row=final(league=league)
            out,report=grade_existing({"version":1,"bets":[bet]},snapshot(row),NOW)
            self.assertEqual(report["newly_settled"],0)
            self.assertEqual(out["bets"][0]["status"],"pending")

    def test_final_not_observed_after_start_is_rejected(self):
        rec=final()
        rec["observed_at_utc"]=ISO(START+timedelta(minutes=30))
        self.assertEqual(grade_existing({"version":1,"bets":[paper_bet()]},snapshot(rec),NOW)[1]["newly_settled"],0)
        rec=final()
        rec["observed_at_utc"]=ISO(SNAP+timedelta(minutes=10))
        self.assertEqual(grade_existing({"version":1,"bets":[paper_bet()]},snapshot(rec),NOW)[1]["newly_settled"],0)

    def test_duplicate_conflicting_result_quarantined(self):
        out,r=grade_existing({"version":1,"bets":[paper_bet()]},
                            snapshot(final(),final(hs=3)),NOW)
        self.assertEqual(r["newly_settled"],0)
        self.assertEqual(out["bets"][0]["status"],"pending")

    def test_settle_totals_and_draw_deterministically(self):
        bet=paper_bet(market="totals",side="over",line=2.5)
        out,r=grade_existing({"version":1,"bets":[bet]},snapshot(final()),NOW)
        self.assertEqual(out["bets"][0]["status"],"won")
        self.assertEqual(out["bets"][0]["paper_units_returned"],2.5)
        bet=paper_bet(market="totals",side="under",line=3)
        out,r=grade_existing({"version":1,"bets":[bet]},snapshot(final()),NOW)
        self.assertEqual(out["bets"][0]["status"],"push")
        self.assertEqual(out["bets"][0]["paper_units_returned"],1.0)
        bet=paper_bet(side="draw")
        out,r=grade_existing({"version":1,"bets":[bet]},snapshot(final(hs=1,aw=1)),NOW)
        self.assertEqual(out["bets"][0]["status"],"won")

    def test_never_touch_previously_graduated_or_unknown_records(self):
        won=paper_bet()
        won.update(status="won",paper_units_returned=2.5)
        pending=paper_bet(event="401112")
        untouched=deepcopy(won)
        out,r=grade_existing({"version":1,"bets":[won,pending]},snapshot(final()),NOW)
        self.assertEqual(out["bets"][0],untouched)
        self.assertEqual(out["bets"][1]["status"],"pending")
        self.assertEqual(r["newly_settled"],0)

if __name__=="__main__":unittest.main()
