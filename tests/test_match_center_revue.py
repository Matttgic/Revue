"""First-party match center: no phantom odds, no source mismatch, no past picks."""
import copy
from datetime import datetime,timedelta,timezone
import unittest
from outils.match_center_revue import collect_center, instant

NOW=datetime(2026,10,10,9,tzinfo=timezone.utc)
KICK=(NOW+timedelta(hours=6)).isoformat()
GENERATED=(NOW-timedelta(hours=2)).isoformat()
QUOTE=(NOW-timedelta(minutes=15)).isoformat()


def fixture():
    game={"event_id":"X-101","home":"Arsenal","away":"Leeds","start_utc":KICK,
          "status":"prototype_non_calibre",
          "probabilities":{"home_win_90":.48,"draw_90":.27,"away_win_90":.25,"over_2_5":.52}}
    ms={"generated_at_utc":GENERATED,"competitions":{"PL":{"sport":"Football","games":[game]}}}
    advanced={"generated_at_utc":GENERATED,"competitions":{"PL":{"games":[{
        **{k:game[k] for k in ("event_id","home","away","start_utc")},
        "probabilities":{"home_win_90":.5,"draw_90":.25,"away_win_90":.25}}]}}}
    scanner={"mode":"PAPER_ONLY","odds_board":{"events":[{
        **{k:game[k] for k in ("event_id","home","away","start_utc")},
        "league":"PL","bookmakers":[
          {"bookmaker":"betclic_fr","markets":[{
            "market":"h2h","period_rule":"90min","quote_at":QUOTE,
            "outcomes":[{"selection":"home","price":1.88},{"selection":"draw","price":3.6},
                        {"selection":"away","price":4.6}]
          }]},
        ],
    }]}}
    nhl={"generated_at_utc":GENERATED,"games":[]}
    ensemble={"generated_at_utc":GENERATED,"leagues":{}}
    return {"multisports":ms,"scanner":scanner,"advanced":advanced,"nhl":nhl,"ensemble":ensemble}


def build(payload=None,now=NOW):
    return collect_center(**(payload or fixture()),now=now)


class MatchCenterTests(unittest.TestCase):
    def test_strict_fixture_join_real_quotes_and_separate_models(self):
        doc=build();self.assertEqual(doc["status"],"experimental_revue_match_center")
        self.assertEqual(doc["metrics"]["upcoming_matches"],1)
        self.assertEqual(doc["metrics"]["with_observed_bookmaker_quotes"],1)
        ev=doc["events"][0]
        self.assertEqual(len(ev["research"]),2)
        self.assertEqual(ev["quotes"][0]["bookmaker"],"betclic_fr")
        self.assertEqual(ev["quotes"][0]["outcomes"]["draw"],3.6)
        self.assertTrue(ev["quotes"][0]["rule_verified"])
        self.assertIsNone(ev["ev"])
        self.assertIsNone(ev["recommendation"])
        self.assertFalse(ev["qualified_for_real_betting"])
        self.assertEqual(doc["validated_value_bets"],0)
        self.assertFalse(doc["real_bets_enabled"])

    def test_different_kickoff_or_teams_never_join(self):
        for field,new_value in [("away","Chelsea"),("start_utc",(NOW+timedelta(hours=7)).isoformat())]:
            payload=fixture()
            payload["scanner"]["odds_board"]["events"][0][field]=new_value
            payload["advanced"]["competitions"]["PL"]["games"][0][field]=new_value
            doc=build(payload)
            self.assertEqual(doc["events"][0]["quotes"],[])
            self.assertEqual(len(doc["events"][0]["research"]),1)
            self.assertGreaterEqual(doc["rejections"]["fixture_mismatch"],2)

    def test_no_future_stale_or_postkickoff_quotes(self):
        for quote in [
            (NOW+timedelta(minutes=1)).isoformat(),
            (NOW-timedelta(hours=25)).isoformat(),
            (NOW+timedelta(hours=7)).isoformat(),
        ]:
            payload=fixture()
            payload["scanner"]["odds_board"]["events"][0]["bookmakers"][0]["markets"][0]["quote_at"]=quote
            self.assertEqual(build(payload)["events"][0]["quotes"],[])

    def test_wrong_market_rules_or_incomplete_selection_hidden(self):
        for rule,outcomes in [
            ("overtime_rule_unverified",None),
            ("90min",[{"selection":"home","price":2.0}]),
            ("90min",[{"selection":"home","price":1.0},{"selection":"draw","price":3.0},{"selection":"away","price":4.0}]),
        ]:
            payload=fixture()
            market=payload["scanner"]["odds_board"]["events"][0]["bookmakers"][0]["markets"][0]
            market["period_rule"]=rule
            if outcomes is not None:market["outcomes"]=outcomes
            self.assertEqual(build(payload)["events"][0]["quotes"],[])

    def test_cfb_never_displayed_and_only_future_events(self):
        payload=fixture()
        copygame=copy.deepcopy(payload["multisports"]["competitions"]["PL"]["games"][0])
        copygame["event_id"]="CFB-001"
        payload["multisports"]["competitions"]["CFB"]={"sport":"CFB","games":[copygame]}
        self.assertEqual(len(build(payload)["events"]),1)
        payload["multisports"]["competitions"]["PL"]["games"][0]["start_utc"]=NOW.isoformat()
        self.assertEqual(len(build(payload)["events"]),0)

    def test_missing_invalid_probabilities_never_implied(self):
        for p in (None, {"home_win_90":.99,"draw_90":.9,"away_win_90":.1},
                  {"home_win_90":float("nan"),"draw_90":.2,"away_win_90":.4}):
            payload=fixture()
            payload["multisports"]["competitions"]["PL"]["games"][0]["probabilities"]=p
            payload["advanced"]["competitions"]["PL"]["games"]=[]
            ev=build(payload)["events"][0]
            self.assertEqual(ev["research"],[])
            self.assertEqual(len(ev["quotes"]),1)

    def test_duplicated_event_ids_raise(self):
        payload=fixture()
        row=payload["multisports"]["competitions"]["PL"]["games"][0]
        payload["multisports"]["competitions"]["PL"]["games"].append(copy.deepcopy(row))
        with self.assertRaisesRegex(ValueError,"Duplicate event"):
            build(payload)

    def test_main_fixture_feed_future_or_stale_rejected(self):
        payload=fixture()
        payload["multisports"]["generated_at_utc"]=(NOW+timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(ValueError,"out of date"):
            build(payload)
        payload=fixture()
        payload["multisports"]["generated_at_utc"]=(NOW-timedelta(days=5)).isoformat()
        with self.assertRaisesRegex(ValueError,"out of date"):
            build(payload)

    def test_nhl_two_clairvoyance_models_are_different_and_never_called_parity_predictions(self):
        payload=fixture()
        nhlfixture={"event_id":"2026020070","home":"BOS","away":"PHI",
                    "start_utc":KICK}
        payload["multisports"]["competitions"]["NHL"]={"sport":"Hockey","games":[{
            **nhlfixture,"probabilities":{"home_win":.53,"away_win":.47}}]}
        payload["nhl"]={
            "generated_at_utc":GENERATED,
            "point_in_time_audit":{"status":"verified_temporal_bounds"},
            "games":[{**nhlfixture,"home_win":.64,"away_win":.36,
                      "research_low_sample_shrink":{"model_id":"revue_nhl_low_sample_shrink_v1",
                                                   "home_win":.58,"away_win":.42}}]
        }
        models=build(payload)["events"][1 if build(payload)["events"][0]["league"]=="PL" else 0]["research"]
        self.assertEqual(len(models),3)
        self.assertEqual({m["id"] for m in models},{
            "revue_multisports_score_model","clairvoyance_nhl_formula_revue_inputs",
            "revue_nhl_low_sample_shrink_v1"})
        payload["nhl"]["point_in_time_audit"]["status"]="failed"
        self.assertEqual(len([e for e in build(payload)["events"] if e["league"]=="NHL"][0]["research"]),1)

    def test_unauthorized_bookmaker_not_published(self):
        payload=fixture()
        payload["scanner"]["odds_board"]["events"][0]["bookmakers"][0]["bookmaker"]="pinnacle"
        self.assertEqual(build(payload)["events"][0]["quotes"],[])

    def test_reject_timezone_naive(self):
        with self.assertRaises(ValueError):
            instant("2026-10-10T12:00:00")


if __name__=="__main__":unittest.main()
