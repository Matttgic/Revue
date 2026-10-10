"""Tests locaux pour les nouveaux flux individus + Liiga (aucun HTTP)."""
import unittest
from datetime import datetime,timedelta,timezone
from modeles.simulations.sports_individuels_et_liiga import (
    MIN_MATCHES,Match,dt_utc,parse_espn_scoreboard,individual_elo,parse_liiga,predict_liiga
)


class SportsIndividuelsLiigaTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,9,12,tzinfo=timezone.utc)

    def tennis_comp(self,mid,when,complete=False,winner=None):
        return {"id":mid,"date":when.isoformat(),"status":{"type":{"completed":complete}},
                "competitors":[
                    {"athlete":{"id":"a","displayName":"Alice A."},"winner":winner=="a"},
                    {"athlete":{"id":"b","displayName":"Bob B."},"winner":winner=="b"},
                ]}

    def test_grouped_tennis_matches(self):
        e={"id":"tournament","date":self.now.isoformat(),
           "groupings":[{"competitions":[self.tennis_comp("m1",self.now,True,"a")]}]}
        out=parse_espn_scoreboard({"events":[e]},"ATP")
        self.assertEqual(len(out),1)
        self.assertEqual(out[0].id,"ATP:m1")
        self.assertEqual(out[0].winner_id,"a")

    def test_unknown_match_winner_not_invented(self):
        e={"id":"t","competitions":[self.tennis_comp("m2",self.now,True,None)]}
        m=parse_espn_scoreboard({"events":[e]},"WTA")[0]
        self.assertIsNone(m.winner_id)

    def test_bye_or_doubles_rejected(self):
        x=self.tennis_comp("one",self.now)
        x["competitors"][0]["athlete"]["displayName"]="A / B"
        e={"id":"t","competitions":[x]}
        self.assertEqual(parse_espn_scoreboard({"events":[e]},"ATP"),[])

    def test_tennis_unresolved_bracket_seats_are_never_real_players(self):
        for name in ("TBD","TBA","BYE","Winner of semifinal 1","Qualifier"):
            with self.subTest(name=name):
                raw=self.tennis_comp("placeholder",self.now+timedelta(days=1))
                raw["competitors"][0]["athlete"]["displayName"]=name
                self.assertEqual(parse_espn_scoreboard(
                    {"events":[{"id":"bracket","competitions":[raw]}]},"WTA"),[])
        from modeles.simulations.sports_individuels_et_liiga import Match,individual_elo
        stale=Match("WTA:900","WTA",self.now+timedelta(days=1),
                    "x","y","TBD","TBD",False,None)
        self.assertEqual(individual_elo([stale],self.now,3),[])

    def test_ufc_fight_card_competitions(self):
        e={"id":"event","date":self.now.isoformat(),"competitions":[self.tennis_comp("fight",self.now)]}
        res=parse_espn_scoreboard({"events":[e]},"UFC")
        self.assertEqual(len(res),1)
        self.assertEqual(res[0].player1,"Alice A.")

    def test_timestamp_timezone_required(self):
        self.assertIsNone(dt_utc("2026-10-09T13:00:00"))
        self.assertIsNone(dt_utc(None))
        self.assertIsNotNone(dt_utc("2026-10-09T13:00:00Z"))

    def test_elo_needs_history(self):
        new=Match("n","ATP",self.now+timedelta(days=1),"a","b","A","B",False,None)
        out=individual_elo([new],self.now,days=3)
        self.assertEqual(len(out),1)
        self.assertIsNone(out[0]["probabilities"])

    def test_elo_with_valid_history(self):
        hist=[
            Match(str(i),"ATP",self.now-timedelta(days=12-i),
                  "a","b","A","B",True,"a" if i%2==0 else "b")
            for i in range(9)]
        future=Match("n","ATP",self.now+timedelta(days=1),"a","b","A","B",False,None)
        res=individual_elo(hist+[future],self.now,3)
        self.assertEqual(len(res),1)
        p=res[0]["probabilities"]
        self.assertAlmostEqual(p["home_win"]+p["away_win"],1)
        self.assertEqual(res[0]["training_games"]["home"],9)

    def test_future_results_not_training(self):
        past=[
            Match(str(i),"ATP",self.now-timedelta(days=i+1),
                  "a","b","A","B",True,"a") for i in range(8)]
        future=Match("n","ATP",self.now+timedelta(days=1),"a","b","A","B",False,None)
        oracle=Match("other","ATP",self.now+timedelta(days=5),"a","b","A","B",True,"b")
        x=individual_elo(past+[future],self.now,3)
        y=individual_elo(past+[oracle,future],self.now,3)
        self.assertEqual(x,y)

    def test_liiga_parse_fixture(self):
        raw=[{"id":555,"start":"2026-10-10T16:30Z","ended":False,
              "homeTeam":{"id":1,"teamName":"Tappara"},
              "awayTeam":{"id":2,"teamName":"Ilves"}}]
        g=parse_liiga(raw,self.now)
        self.assertEqual(len(g),1)
        self.assertEqual(g[0]["home"],"Tappara")
        self.assertFalse(g[0]["finished"])

    def test_liiga_score_requires_ended(self):
        raw=[{"id":555,"start":"2026-10-08T16:30Z","ended":False,
              "homeTeam":{"id":1,"teamName":"Tappara","goals":4},
              "awayTeam":{"id":2,"teamName":"Ilves","goals":0}}]
        g=parse_liiga(raw,self.now)
        self.assertIsNone(g[0]["hgoals"])
        self.assertFalse(g[0]["finished"])

    def test_liiga_model_needs_history(self):
        g=parse_liiga([{"id":555,"start":"2026-10-10T16:30Z","ended":False,
                "homeTeam":{"id":1,"teamName":"Tappara"},
                "awayTeam":{"id":2,"teamName":"Ilves"}}],self.now)
        x=predict_liiga(g,self.now,days=3)
        self.assertEqual(len(x),1)
        self.assertIsNone(x[0]["probabilities"])

    def test_liiga_so_extra_goal_not_always_scores(self):
        games=[]
        for i in range(12):
            when=self.now-timedelta(days=i+1)
            games.append({"id":i+1,"start":when.isoformat(),
                          "ended":True,"finishedType":"REGULAR",
                          "homeTeam":{"id":1,"teamName":"Tappara","goals":3+i%2},
                          "awayTeam":{"id":2,"teamName":"Ilves","goals":1+i%2}})
        games.append({"id":77,"start":(self.now+timedelta(days=1)).isoformat(),
                    "ended":False,"homeTeam":{"id":1,"teamName":"Tappara"},
                    "awayTeam":{"id":2,"teamName":"Ilves"}})
        result=predict_liiga(parse_liiga(games,self.now),self.now,3)
        self.assertEqual(len(result),1)
        p=result[0]["probabilities"]
        self.assertAlmostEqual(p["home_win"]+p["away_win"],1)
        self.assertTrue(0<p["over_5_5"]<1)


if __name__=="__main__":
    unittest.main()
