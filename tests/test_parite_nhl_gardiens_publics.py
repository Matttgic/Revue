"""Read-only goalie identity parity; independent snapshots and no claims of starting XI."""
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from outils.clairvoyance.parite_nhl_gardiens_publics import compare,name_key,VERSION

NOW=datetime(2026,10,10,20,tzinfo=timezone.utc)
ORIG_AT=(NOW-timedelta(hours=1)).strftime("%Y-%m-%d %H:%M UTC")
REV_AT=(NOW-timedelta(minutes=30)).isoformat()
START=(NOW+timedelta(hours=4)).isoformat()

def reference():
    # 100 additional normal fixtures so reference completeness validation passes.
    games=[{"id":f"4018{x:05d}","home":"CAR","away":"SEA",
            "date":(NOW+timedelta(days=3+x)).isoformat()} for x in range(100)]
    games.append({
       "id":"401899999","home":"SJS","away":"EDM","date":START,
       "goalies":{"home":{"name":"Yaroslav Askarov","status":"projected"},
                  "away":{"name":"Tristan Jarry","status":"confirmed"},
                  "at":(NOW-timedelta(hours=2)).isoformat(),"src":"espn"}})
    return {"generated_at":ORIG_AT,"games":games}

def revue():
    return {
        "status":"espn_probable_goalies_observed_not_part_of_model",
        "source":"ESPN NHL scoreboard, separate from official NHL IDs",
        "generated_at_utc":REV_AT,
        "real_bets_enabled":False,"used_in_prediction_model":False,
        "rows":[{"event_id":"2026021234","home":"SJS","away":"EDM",
           "start_utc":START,"observed_at_utc":REV_AT,
           "home_goalie":{"name":"Yároslav Askarov","status":"confirmed"},
           "away_goalie":{"name":"Tristan Jarry","status":"confirmed"}}],
    }

class GoalieEvidence(unittest.TestCase):
    def test_real_names_match_but_change_in_status_is_not_prediction_mismatch(self):
        a=reference();b=revue()
        original=deepcopy((a,b))
        r=compare(a,b,NOW)
        self.assertEqual((a,b),original)
        self.assertEqual(r["version"],VERSION)
        self.assertEqual(r["matched_unique_games"],1)
        self.assertEqual(r["comparable_goalie_sides"],2)
        self.assertEqual(r["matching_names"],2)
        self.assertEqual(r["matching_statuses"],1)
        self.assertEqual(r["different_statuses"],1)
        self.assertEqual(r["unmatched_games"],0)
        self.assertTrue(r["not_a_verified_same_time_goalie_state"])
        self.assertFalse(r["original_sql_goalie_rows_verified"])
        self.assertFalse(r["original_prediction_parity_verified"])
        self.assertFalse(r["goalies_verified_to_have_played"])
        self.assertEqual(r["matches"][0]["reference_espn_event_id"],"401899999")
        self.assertFalse(r["matches"][0]["sides"]["home"]["status_equal"])
        self.assertTrue(r["matches"][0]["sides"]["home"]["name_equal"])

    def test_different_team_date_or_multiple_sources_not_falsely_mapped(self):
        r=revue();r["rows"][0]["home"]="NYR"
        self.assertEqual(compare(reference(),r,NOW)["matched_unique_games"],0)
        r=revue();r["rows"][0]["start_utc"]=(NOW+timedelta(hours=6)).isoformat()
        self.assertEqual(compare(reference(),r,NOW)["matched_unique_games"],0)
        a=reference()
        a["games"].append(deepcopy(a["games"][-1]))
        self.assertEqual(compare(a,revue(),NOW)["matched_unique_games"],0)

    def test_unverified_goalie_missing_not_guessed(self):
        a=reference()
        a["games"][-1]["goalies"]["home"]=None
        r=compare(a,revue(),NOW)
        self.assertEqual(r["comparable_goalie_sides"],1)
        self.assertEqual(r["matching_names"],1)
        self.assertEqual(r["diagnostics"]["side_missing_either_source"],1)
        b=revue();b["rows"][0]["away_goalie"]=None
        self.assertEqual(compare(reference(),b,NOW)["comparable_goalie_sides"],1)

    def test_stale_and_tampered_or_future_ref_rejected(self):
        a=reference();b=revue()
        a["generated_at"]=(NOW-timedelta(days=3)).strftime("%Y-%m-%d %H:%M UTC")
        with self.assertRaises(ValueError):compare(a,b,NOW)
        a=reference();b["real_bets_enabled"]=True
        with self.assertRaises(ValueError):compare(a,b,NOW)
        a["games"][-1]["goalies"]["at"]=(NOW+timedelta(days=2)).isoformat()
        b=revue()
        self.assertEqual(compare(a,b,NOW)["matched_unique_games"],0)
        self.assertEqual(compare(a,b,NOW)["diagnostics"]["reference_source_time_invalid"],1)

    def test_duplicate_revue_nhl_ids_fails(self):
        a=reference();b=revue()
        b["rows"].append(deepcopy(b["rows"][0]))
        with self.assertRaises(ValueError):compare(a,b,NOW)

    def test_normalization_does_not_require_same_accent_or_punctuation(self):
        self.assertEqual(name_key("Leevi Meriläinen"),name_key("Leevi Merilainen"))
        self.assertEqual(name_key("Yároslav Askarov"),name_key("Yaroslav Askarov"))

    def test_aware_clock_required(self):
        with self.assertRaises(ValueError):
            compare(reference(),revue(),datetime(2026,10,10))


if __name__=="__main__":
    unittest.main()
