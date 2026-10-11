"""Source-only NHL ESPN probable goalie join; missing statuses never promoted."""
import json
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
from outils.collecte.nhl_espn_goalies import combine,espn_candidate,team_code

SNAP=json.loads((Path(__file__).resolve().parents[1]/"docs"/"nhl-frontend-observed-latest.json").read_text("utf8"))
T=datetime.fromisoformat(SNAP["generated_at_utc"].replace("Z","+00:00"))+timedelta(minutes=2)
ONE={**deepcopy(SNAP),"games":[deepcopy(SNAP["games"][0])],"games_emitted":1}
ROW=ONE["games"][0]

def comp(side,team,name=None,status=None):
    row={"homeAway":side,"team":{"abbreviation":team},"probables":[]}
    if name:
        row["probables"]=[{"name":"probableStartingGoalie",
                            "athlete":{"fullName":name},
                            "status":{"type":status}}]
    return row

def event(home=None,away=None,start=None,home_status="confirmed",away_status="probable"):
    return {"id":"401999999","date":start or ROW["start_utc"],
      "competitions":[{"competitors":[
        comp("home",home or ROW["home"],"Goalie One",home_status),
        comp("away",away or ROW["away"],"Goalie Two",away_status)]}]}

class GoalieFeedTest(unittest.TestCase):
    def test_explicit_confirmed_and_projected_keep_separate(self):
        m=combine(ONE,[{"events":[event()]}],T)
        self.assertEqual(m["provider_rows_matched"],1)
        self.assertEqual(m["verified_current_starters"],1)
        self.assertEqual(m["projected_starters"],1)
        self.assertEqual(m["rows"][0]["home_goalie"]["status"],"confirmed")
        self.assertEqual(m["rows"][0]["away_goalie"]["status"],"projected")
        self.assertFalse(m["used_in_prediction_model"])
        self.assertFalse(m["injuries_verified"])
        self.assertFalse(m["real_bets_enabled"])
        self.assertFalse(m["rows"][0]["used_in_model_probabilities"])

    def test_missing_or_unknown_status_never_becomes_confirmed(self):
        a=event(home_status="maybe",away_status="maybe")
        m=combine(ONE,[{"events":[a]}],T)
        self.assertIsNone(m["rows"][0]["home_goalie"])
        self.assertIsNone(m["rows"][0]["away_goalie"])
        self.assertEqual(m["verified_current_starters"],0)
        self.assertEqual(m["diagnostics"]["matched_without_reported_starters"],1)
        b=event()
        b["competitions"][0]["competitors"][0]["probables"]=[]
        m=combine(ONE,[{"events":[b]}],T)
        self.assertEqual(m["verified_current_starters"],0)

    def test_no_match_on_opponent_or_kickoff_mismatch(self):
        wrong=event(home="XXX")
        m=combine(ONE,[{"events":[wrong]}],T)
        self.assertEqual(m["rows"],[])
        later=event(start=(datetime.fromisoformat(ROW["start_utc"].replace("Z","+00:00"))+
                            timedelta(minutes=50)).isoformat())
        m=combine(ONE,[{"events":[later]}],T)
        self.assertEqual(m["provider_rows_matched"],0)

    def test_duplicate_espn_match_never_selected_arbitrarily(self):
        a=event()
        b=deepcopy(a)
        b["id"]="402222222"
        b["competitions"][0]["competitors"][0]["probables"][0]["athlete"]["fullName"]="Other"
        m=combine(ONE,[{"events":[a,b]}],T)
        self.assertEqual(m["provider_rows_matched"],0)
        self.assertEqual(m["verified_current_starters"],0)
        self.assertEqual(m["diagnostics"]["no_unique_espn_match"],1)

    def test_already_started_match_and_invalid_model_are_excluded(self):
        m=combine(ONE,[{"events":[event()]}],T+timedelta(days=2))
        self.assertFalse(m["rows"])
        forged=deepcopy(ONE)
        forged["real_bets_enabled"]=True
        with self.assertRaises(ValueError):
            combine(forged,[],T)

    def test_nhl_abbreviation_aliases_and_reschedule_variation(self):
        self.assertEqual(team_code({"team":{"abbreviation":"TB"}}),"TBL")
        self.assertEqual(team_code({"team":{"abbreviation":"SJ"}}),"SJS")
        self.assertEqual(team_code({"team":{"abbreviation":"ARI"}}),"ARI")
        base=deepcopy(ONE)
        base["games"][0]["home"]="TBL"
        base["games"][0]["away"]="SJS"
        x=event(home="TB",away="SJ")
        m=combine(base,[{"events":[x]}],T)
        self.assertEqual(m["provider_rows_matched"],1)

    def test_corrupt_fixture_or_provider_returns_no_observation(self):
        self.assertIsNone(espn_candidate({"id":"0"}))
        self.assertIsNone(espn_candidate({"date":ROW["start_utc"],"competitions":[{"competitors":[]}]}))
        m=combine(ONE,[{"not":"events"}],T)
        self.assertEqual(m["diagnostics"]["invalid_espn_feed"],1)
        self.assertEqual(m["verified_current_starters"],0)

if __name__=="__main__":unittest.main()
