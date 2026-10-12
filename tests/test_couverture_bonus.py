"""Tests de la couverture de bonus et des surebets."""
import unittest
from datetime import datetime, timezone

from outils.suivi.couverture_bonus import freebet, marches, pari_rembourse, rapport, surebet

T = "2026-10-12T10:00:00+00:00"
MAINTENANT = datetime(2026, 10, 12, 10, 5, tzinfo=timezone.utc)


def tableau(cotes_par_operateur, instant=T, marche="h2h", ligue="LIGUE1", debut="2026-10-12T19:00:00+00:00"):
    bks = []
    for op, cotes in cotes_par_operateur.items():
        bks.append({"bookmaker": op, "markets": [{"market": marche, "period_rule": "90min", "quote_at": instant,
                    "outcomes": [{"selection": s, "price": p} for s, p in cotes.items()]}]})
    return {"generated_at_utc": T, "odds_board": {"events": [
        {"league": ligue, "home": "A", "away": "B", "start_utc": debut, "bookmakers": bks}]}}


def marches_(t):
    return marches(t, MAINTENANT)


class TestCouverture(unittest.TestCase):
    def test_surebet_detecte_et_benefice_egal(self):
        m = marches_(tableau({"x": {"home": 2.2, "draw": 3.6, "away": 3.9}, "y": {"home": 2.0, "draw": 3.9, "away": 4.4}}))[0]
        s = surebet(m)
        self.assertGreater(s["rendement"], 0)
        self.assertGreater(s["benefice_garanti"], 0)
        nets = s["benefice_par_issue"].values()
        self.assertLess(max(nets) - min(nets), 0.6)  # écart dû aux arrondis seulement

    def test_pas_de_surebet_avec_marge(self):
        m = marches_(tableau({"x": {"home": 1.9, "draw": 3.4, "away": 4.0}}))[0]
        self.assertIsNone(surebet(m))

    def test_freebet_formule(self):
        m = marches_(tableau({"fb": {"home": 2.0, "draw": 3.5, "away": 4.0}, "y": {"home": 2.1, "draw": 3.4, "away": 4.2}}))[0]
        p = freebet(m, "fb", 10)
        o = p["mises"]
        i = next(k for k, v in o.items() if v["nature"] == "freebet")
        autres = [v["cote"] for k, v in o.items() if k != i]
        attendu = (o[i]["cote"] - 1) * (1 - sum(1 / c for c in autres))
        self.assertAlmostEqual(p["taux_conversion"], round(attendu, 4))
        self.assertEqual(o[i]["operateur"], "fb")
        self.assertGreater(p["benefice_garanti"], 0)
        self.assertAlmostEqual(p["benefice_garanti"], 10 * attendu, delta=0.5)

    def test_cote_min_respectee(self):
        m = marches_(tableau({"fb": {"over": 1.3, "under": 3.6}, "y": {"over": 1.32, "under": 3.5}}, marche="totals"))[0]
        p = freebet(m, "fb", 10, cote_min=2.0)
        self.assertEqual(p["mises"]["under"]["nature"], "freebet")
        self.assertIsNone(freebet(m, "fb", 10, cote_min=5.0))

    def test_pari_rembourse_couverture_ailleurs(self):
        m = marches_(tableau({"pr": {"home": 2.0, "draw": 3.5, "away": 4.0}, "y": {"home": 2.0, "draw": 3.4, "away": 4.1}}))[0]
        p = pari_rembourse(m, "pr", 100, conversion=0.6)
        i = next(k for k, v in p["mises"].items() if v["operateur"] == "pr")
        self.assertTrue(all(v["operateur"] == "y" for k, v in p["mises"].items() if k != i))
        self.assertGreater(p["benefice_si_freebet_converti"], 0)
        self.assertLess(p["perte_maximale_avant_conversion_du_freebet"], p["benefice_si_freebet_converti"])

    def test_cotes_d_instants_differents_refusees(self):
        t = tableau({"fb": {"over": 2.0, "under": 2.0}}, marche="totals")
        t["odds_board"]["events"][0]["bookmakers"].append(
            {"bookmaker": "y", "markets": [{"market": "totals", "period_rule": "90min", "quote_at": "2026-10-12T11:00:00+00:00",
                                           "outcomes": [{"selection": "over", "price": 2.1}, {"selection": "under", "price": 2.1}]}]})
        m = marches_(t)[0]
        p = freebet(m, "fb", 10)
        # la cote de « y », plus haute mais prise une heure plus tard, n'est pas utilisée
        self.assertTrue(all(v["operateur"] == "fb" for v in p["mises"].values()))

    def test_marche_incomplet_ignore(self):
        self.assertEqual(marches_(tableau({"x": {"home": 2.0, "draw": 3.0}})), [])

    def test_rapport(self):
        r = rapport(tableau({"x": {"home": 2.0, "draw": 3.5, "away": 4.0}, "y": {"home": 2.1, "draw": 3.4, "away": 4.2}}),
                    maintenant=MAINTENANT)
        self.assertEqual(r["operateurs"], ["x", "y"])
        self.assertEqual(r["marches_complets"], 1)
        self.assertTrue(r["source_cotes"]["utilisable"])

    def test_perimetre_securise(self):
        cotes = {"x": {"home": 2.0, "away": 2.0}}
        self.assertEqual(marches_(tableau(cotes, ligue="NHL")), [])                                   # hors football
        self.assertEqual(marches_(tableau({"x": {"home": 2.0, "draw": 3.4, "away": 4.0}},
                                          debut="2026-10-12T10:15:00+00:00")), [])                    # trop proche
        self.assertEqual(marches_(tableau(cotes)), [])                                                 # 1N2 incomplet

    def test_cotes_perimees(self):
        r = rapport(tableau({"x": {"home": 2.0, "draw": 3.5, "away": 4.0}}),
                    maintenant=datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc))
        self.assertFalse(r["source_cotes"]["utilisable"])
        self.assertEqual(r["marches_complets"], 0)


if __name__ == "__main__":
    unittest.main()
