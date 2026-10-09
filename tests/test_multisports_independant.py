"""Offline tests for Revue's independent multisport calculator."""
import unittest
from dataclasses import replace
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
import json
import tempfile

from modeles.simulations.multisports_independant import (
    Event, League, LEAGUES, UNSUPPORTED, _logistic, _over,
    _soccer_1x2, _windows, calculate, load_nhl_reference, parse_event,
    query_url, build_snapshot,
)


def make_event(eid, day, home="Arsenal", away="Chelsea", result=None, league="PL"):
    return Event(
        id=str(eid), league=league, start=day,
        home_id=home, away_id=away, home=home, away=away,
        complete=result is not None,
        home_score=result[0] if result else None,
        away_score=result[1] if result else None,
    )


class MultisportTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
        self.soccer = next(g for g in LEAGUES if g.key == "PL")

    def test_all_12_public_leagues_included(self):
        self.assertGreaterEqual(len(LEAGUES), 12)
        self.assertTrue({"NBA", "WNBA", "NFL", "MLB", "NCAAB", "PL", "LALIGA",
                         "SERIEA", "BUNDESLIGA", "LIGUE1", "MLS", "UCL"}
                        .issubset({x.key for x in LEAGUES}))

    def test_cfb_is_disabled(self):
        self.assertNotIn("CFB", {l.key for l in LEAGUES})
    def test_unsupplied_sources_are_explicit(self):
        keys = {x["key"] for x in UNSUPPORTED}
        self.assertTrue({"ATP", "WTA", "SHL", "LIIGA", "NL", "EXTRALIGA", "UFC"}.issubset(keys))

    def test_parse_espn_completed_soccer(self):
        sample = {
            "id": "abc", "date": "2026-10-08T19:00Z",
            "status": {"type": {"completed": True}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "team": {"id": "1", "shortDisplayName": "AAA"}, "score": "2"},
                {"homeAway": "away", "team": {"id": "2", "shortDisplayName": "BBB"}, "score": "0"},
            ]}],
        }
        g = parse_event(sample, "PL")
        self.assertEqual(g.id, "abc")
        self.assertEqual((g.home_score, g.away_score), (2, 0))
        self.assertTrue(g.scored)
        sample["status"]["type"]["completed"] = False
        self.assertIsNone(parse_event(sample, "PL").home_score)

    def test_parse_rejects_no_start_or_teams(self):
        self.assertIsNone(parse_event({"id": "x"}, "NBA"))
        self.assertIsNone(parse_event({"id": "x", "date": "2026-10-09T10:00Z",
                                        "competitions": [{"competitors": []}]}, "NBA"))

    def test_probability_components(self):
        p1, px, p2 = _soccer_1x2(1.5, 1.2)
        self.assertAlmostEqual(p1 + px + p2, 1.0)
        self.assertGreater(p1, 0)
        self.assertLess(_over(3, 3.5), _over(3, 2.5))
        with self.assertRaises(ValueError):
            _over(3, 3.0)

    def test_window_partition_no_gaps(self):
        periods = _windows(date(2026, 10, 1), date(2026, 10, 9), 4)
        self.assertEqual(periods, [
            (date(2026, 10, 1), date(2026, 10, 4)),
            (date(2026, 10, 5), date(2026, 10, 8)),
            (date(2026, 10, 9), date(2026, 10, 9)),
        ])

    def test_query_uses_sport_and_single_date(self):
        url = query_url(self.soccer, date(2026, 10, 8), date(2026, 10, 8))
        self.assertIn("soccer/eng.1/scoreboard", url)
        self.assertIn("dates=20261008", url)
        with self.assertRaises(ValueError):
            query_url(self.soccer, date(2026, 10, 8), date(2026, 10, 9))

    def test_insufficient_history_not_fake_prediction(self):
        games = [make_event(1, self.now + timedelta(hours=20))]
        output = calculate(self.soccer, games, self.now, 3)
        self.assertEqual(len(output), 1)
        self.assertIsNone(output[0]["probabilities"])
        self.assertEqual(output[0]["status"], "historique_insuffisant")

    def test_soccer_predictions_after_training(self):
        training = [make_event(i, self.now-timedelta(days=20-i),
                               result=(2+i%2, i%2)) for i in range(10)]
        future = make_event(999, self.now+timedelta(hours=24))
        output = calculate(self.soccer, training+[future], self.now, 3)
        self.assertEqual(len(output), 1)
        p = output[0]["probabilities"]
        self.assertAlmostEqual(p["home_win_90"]+p["draw_90"]+p["away_win_90"], 1, places=3)
        self.assertGreater(p["over_2_5"], 0)

    def test_other_sports_are_two_way(self):
        for key in ("NBA", "NFL", "MLB"):
            league = next(x for x in LEAGUES if x.key == key)
            training = [make_event(i, self.now - timedelta(days=20-i),
                        home="H",away="A",result=(100+i,90+i),league=key) for i in range(15)]
            out = calculate(league, training+[make_event("next",self.now+timedelta(days=1),
                             home="H",away="A",league=key)],self.now,3)
            self.assertEqual(len(out),1)
            probs=out[0]["probabilities"]
            self.assertAlmostEqual(probs["home_win"]+probs["away_win"],1)
            self.assertNotIn("home_win_90",probs)
            self.assertIsNone(out[0]["odds"])

    def test_games_already_started_excluded(self):
        old = make_event("live", self.now-timedelta(minutes=5))
        self.assertEqual(calculate(self.soccer,[old],self.now,2),[])

    def test_future_games_cannot_train_themselves(self):
        games = [make_event(i,self.now-timedelta(days=i),result=(2,1)) for i in range(1,11)]
        next_game=make_event("tomorrow",self.now+timedelta(days=1))
        third_future=make_event("future",self.now+timedelta(days=40),result=(70,0))
        a=calculate(self.soccer,games+[next_game],self.now,3)
        b=calculate(self.soccer,games+[next_game,third_future],self.now,3)
        self.assertEqual(a,b)

    def test_elo_behaviour(self):
        self.assertGreater(_logistic(1700,1500,0),0.5)

    def test_nhl_reference_age_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"nhl.json"
            path.write_text(json.dumps({
                "generated_at_utc":(self.now-timedelta(days=3)).isoformat(),
                "games":[]}),encoding="utf-8")
            games,meta=load_nhl_reference(path,self.now,2)
            self.assertEqual(games,[])
            self.assertEqual(meta["status"],"stale")

    def test_nhl_reference_ingested(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"nhl.json"
            path.write_text(json.dumps({
                "generated_at_utc":self.now.isoformat(),
                "games":[{
                    "event_id":"123",
                    "start_utc":(self.now+timedelta(hours=24)).isoformat(),
                    "home":"BOS","away":"MTL",
                    "probabilities":{"home_win":0.6,"away_win":0.4},
                    "expected_goals":{"home":3,"away":2.5},
                }]
            }),encoding="utf-8")
            games,meta=load_nhl_reference(path,self.now,3)
            self.assertEqual(len(games),1)
            self.assertEqual(games[0]["status"],"prototype_non_calibre")

    def test_invalid_sport_names_rejected(self):
        with self.assertRaises(ValueError):
            build_snapshot(self.now,3,{"NOT_A_SPORT"})

    def test_invalid_day_ranges_rejected(self):
        with self.assertRaises(ValueError):
            build_snapshot(self.now,0,set())


if __name__ == "__main__":
    unittest.main()
