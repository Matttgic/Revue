"""Strictly bound real NHL matching-input parity validation."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import unittest

from outils.verifier_parite_predictor_nhl_observe import validate_rows

NOW=datetime(2026,10,10,9,tzinfo=timezone.utc)


def sample():
    return {
        "status":"experimental_not_calibrated",
        "generated_at_utc":NOW.isoformat(),
        "point_in_time_audit":{"status":"verified_temporal_bounds",
                               "as_of_utc":NOW.isoformat()},
        "bookmaker_odds_available":False,
        "games":[{
            "event_id":"2026020070","home":"BOS","away":"PHI",
            "start_utc":(NOW+timedelta(hours=3)).isoformat(),
            "home_elo_proxy":1527.3,"away_elo_proxy":1498.2,
            "xg_5v5_share_pct":{"home":53.2,"away":48.3},
            "historical_goalie_proxy":{"home":{"save_pct":.925},
                                      "away":{"save_pct":.901}},
            "market_odds":None,"betting_recommendation":None,
        }]
    }


class NHLLiveInputSourceTests(unittest.TestCase):
    def test_valid_real_fixture_shape_is_accepted(self):
        self.assertEqual(len(validate_rows(sample())),1)

    def test_no_unverified_or_future_sources(self):
        for changer in [
            lambda j:j["point_in_time_audit"].update(status="nope"),
            lambda j:j.update(generated_at_utc=(NOW+timedelta(minutes=2)).isoformat()),
            lambda j:j.update(bookmaker_odds_available=True),
            lambda j:j["games"][0].update(start_utc=(NOW-timedelta(hours=1)).isoformat()),
        ]:
            with self.subTest(changer=changer):
                j=sample()
                changer(j)
                with self.assertRaises(ValueError):
                    validate_rows(j)

    def test_no_false_goalie_or_xg_inputs(self):
        for change in [
            lambda g:g["historical_goalie_proxy"]["away"].update(save_pct=1.2),
            lambda g:g["xg_5v5_share_pct"].update(home=112),
            lambda g:g.update(home_elo_proxy=float("nan")),
            lambda g:g.update(market_odds={"fake":1.8}),
            lambda g:g.update(betting_recommendation="bet"),
        ]:
            j=sample()
            change(j["games"][0])
            with self.assertRaises(ValueError):
                validate_rows(j)

    def test_duplicate_fixture_is_not_double_counted(self):
        j=sample()
        j["games"].append(deepcopy(j["games"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicated"):
            validate_rows(j)

    def test_empty_report_cannot_report_perfect_parity(self):
        j=sample()
        j["games"]=[]
        with self.assertRaises(ValueError):
            validate_rows(j)

if __name__=="__main__":
    unittest.main()
