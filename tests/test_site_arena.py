"""Static Revue ARENA pages: working navigation, shared CSS and no active CFB."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
PAGES=(
    "index.html","command-center.html","match-center.html","predictions-revue.html","nhl-source-input-gap.html","performance-comparateur.html","engine-v2.html","multisports.html",
    "nhl-joueurs.html","nhl-model.html","moneypuck.html","nhl-clairvoyance.html","football-avance.html",
    "qualite-modeles.html","ensemble-mc-bayes.html","parite-clairvoyance.html","reproduction-exacte.html",
)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.scripts=[]
        self.nav=[]
        self.title=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="a" and "href" in attrs:
            self.links.append(attrs["href"])
            if attrs.get("class")=="rv-brand":
                self.nav.append(attrs["href"])
        if tag=="link" and attrs.get("rel")=="stylesheet":
            self.links.append(attrs["href"])
        if tag=="script" and "src" in attrs:
            self.scripts.append(attrs["src"])
        if tag=="title":
            self.title=True

class ArenaTests(unittest.TestCase):
    def test_every_page_uses_shared_theme_and_navigation(self):
        for name in PAGES:
            with self.subTest(page=name):
                text=(DOCS/name).read_text(encoding="utf-8")
                dom=Page();dom.feed(text)
                self.assertTrue(dom.title)
                self.assertIn("./theme.css?v=2",dom.links)
                self.assertIn("./index.html",dom.links)
                self.assertIn("rv-topbar",text)
                self.assertIn("rv-nav",text)

    def test_all_inline_javascript_parses(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node.js unavailable in local environment")
        class Scripts(HTMLParser):
            def __init__(self):
                super().__init__();self.parts=[];self.reading=False
            def handle_starttag(self,tag,attrs):
                if tag=="script" and not dict(attrs).get("src"):self.reading=True;self.parts.append("")
            def handle_endtag(self,tag):
                if tag=="script":self.reading=False
            def handle_data(self,data):
                if self.reading:self.parts[-1]+=data
        for name in PAGES:
            p=Scripts();p.feed((DOCS/name).read_text(encoding="utf-8"))
            for i,js in enumerate(p.parts):
                if not js.strip():continue
                with self.subTest(page=name,script=i):
                    with tempfile.TemporaryDirectory() as tmp:
                        script=Path(tmp)/"check.js"
                        script.write_text(js,encoding="utf-8")
                        check=subprocess.run([node,"--check",str(script)],
                            capture_output=True,text=True,timeout=12)
                        self.assertEqual(check.returncode,0,check.stderr)

    def test_exact_replication_report_never_uses_functional_coverage_as_exactness(self):
        import json
        audit=json.loads((DOCS/"reproduction-exacte-audit.json").read_text(encoding="utf-8"))
        progress=json.loads((DOCS/"progression-revue.json").read_text(encoding="utf-8"))
        self.assertIsNone(audit["exact_reproduction_percent"])
        self.assertEqual(audit["exact_end_to_end_parity"],"NOT_VERIFIED")
        self.assertTrue(audit["functional_coverage_percent_is_not_reproduction"])
        self.assertEqual(progress["exact_end_to_end_parity"],"NOT_VERIFIED")
        self.assertIsNone(progress["exact_reproduction_percent"])
        self.assertGreater(audit["backend"]["source_route_count"],0)
        self.assertIn("reproduction-exacte-audit.json",
                      (DOCS/"reproduction-exacte.html").read_text(encoding="utf-8"))

    def test_main_page_uses_strict_reproduction_not_35_percent(self):
        front=(DOCS/"index.html").read_text(encoding="utf-8")
        self.assertIn("parite-modeles-clairvoyance.json",front)
        self.assertIn("parite-clairvoyance.html",front)
        self.assertNotIn('jsonFile("progression-revue.json")',front)

    def test_progress_is_exact_source_model_parity(self):
        import json
        d=json.loads((DOCS/"parite-modeles-clairvoyance.json").read_text(encoding="utf-8"))
        self.assertEqual(d["total_target_models"],44)
        self.assertGreaterEqual(d["verified_formula_parity_models"],2)
        self.assertEqual(d["formula_parity_percent"],round(100*d["verified_formula_parity_models"]/d["total_target_models"]))
        self.assertEqual(sum(m["status"]=="exact_formula_parity_verified" for m in d["models"]),
                         d["verified_formula_parity_models"])
        self.assertIn("CFB",d["excluded"])
        self.assertIsNone(d["overall_repository_reproduction_percent"])
        self.assertIn("parite-modeles-clairvoyance.json",
                      (DOCS/"index.html").read_text(encoding="utf-8"))

    def test_all_internal_links_exist(self):
        for name in PAGES:
            doc=Page();doc.feed((DOCS/name).read_text(encoding="utf-8"))
            for href in doc.links+doc.scripts:
                url=urlsplit(href)
                if url.scheme or url.netloc or href.startswith("#") or href.startswith("mailto:"):
                    continue
                with self.subTest(page=name,link=href):
                    file=(DOCS/url.path).resolve()
                    self.assertTrue(file.is_relative_to(DOCS.resolve()))
                    self.assertTrue(file.is_file(),href)

    def test_all_in_one_command_center_is_connected_and_honest(self):
        page=(DOCS/"command-center.html").read_text(encoding="utf-8")
        home=(DOCS/"index.html").read_text(encoding="utf-8")
        self.assertIn("command-center.html",home)
        self.assertIn("CENTRE DE CONTRÔLE",home)
        for key in ("match-center-latest.json","engine-v2-latest.json",
                    "health-latest.json","engine-v2-ledger.json",
                    "revue-control-ledger-latest.json","revue-control-state-latest.json",
                    "/revue/control","/revue/ledger","EXPORT CSV",
                    "timeZone:\"Europe/Paris\"",
                    "real_bets_enabled","paper_only","AUCUNE value démontrée",
                    "API de validation indisponible"):
            with self.subTest(fragment=key):self.assertIn(key,page)
        import json
        journal=json.loads((DOCS/"revue-control-ledger-latest.json").read_text(encoding="utf-8"))
        state=json.loads((DOCS/"revue-control-state-latest.json").read_text(encoding="utf-8"))
        self.assertTrue(journal["paper_only"])
        self.assertTrue(journal["static_snapshot"])
        self.assertFalse(journal["real_bets_enabled"])
        self.assertTrue(state["not_live_provider_health"])
        self.assertTrue(state["static_snapshot"])
        self.assertNotIn("localStorage",page)
        self.assertNotIn("document.write",page)

    def test_research_forecast_page_displays_no_unproven_original_picks(self):
        frontend=(DOCS/"index.html").read_text(encoding="utf-8")
        page=(DOCS/"predictions-revue.html").read_text(encoding="utf-8")
        self.assertIn("predictions-revue.html",frontend)
        self.assertIn("/revue/predictions",page)
        self.assertIn("source_input_parity_with_original",page)
        self.assertIn("pick_recommendation_verified",page)
        self.assertIn("real_bets_enabled",page)
        self.assertIn("Aucun pari recommandé",page)

    def test_performance_dashboard_has_genuine_report_sources(self):
        ui=(DOCS/"performance-comparateur.html").read_text(encoding="utf-8")
        front=(DOCS/"index.html").read_text(encoding="utf-8")
        self.assertIn("performance-comparateur.html",front)
        for data in ("football-shadow-performance.json",
                     "ensemble-mc-bayes-performance.json",
                     "nhl-shadow-performance.json",
                     "multisport-prospective-performance.json"):
            with self.subTest(source=data):
                self.assertIn(data,ui)
                self.assertTrue((DOCS/data).is_file())
        self.assertIn("Aucune mise réelle",ui)

    def test_nhl_source_input_gap_is_diagnostic_only(self):
        import json
        report=json.loads((DOCS/"nhl-source-input-delta.json").read_text(encoding="utf-8"))
        front=(DOCS/"index.html").read_text(encoding="utf-8")
        page=(DOCS/"nhl-source-input-gap.html").read_text(encoding="utf-8")
        exact=(DOCS/"reproduction-exacte.html").read_text(encoding="utf-8")
        self.assertIn("nhl-source-input-gap.html",front)
        self.assertIn("nhl-source-input-gap.html",exact)
        self.assertIn("nhl-source-input-delta.json",page)
        self.assertIn("original_inputs_identical",page)
        self.assertFalse(report["real_bets_enabled"])
        self.assertFalse(report["original_inputs_identical"])
        self.assertFalse(report["end_to_end_parity_verified"])
        self.assertEqual(report["games_comparable"],len(report["games"]))

    def test_match_center_is_discoverable_and_reports_only_source_observations(self):
        import json
        landing=(DOCS/"index.html").read_text(encoding="utf-8")
        center=(DOCS/"match-center.html").read_text(encoding="utf-8")
        report=json.loads((DOCS/"match-center-latest.json").read_text(encoding="utf-8"))
        self.assertIn("match-center.html",landing)
        self.assertIn("match-center-latest.json",landing)
        self.assertIn("match-center-latest.json",center)
        self.assertIn("bookmaker_prices_are_live",center)
        self.assertIn("Ni prix en direct",center)
        self.assertFalse(report["real_bets_enabled"])
        self.assertFalse(report["bookmaker_prices_are_live"])
        self.assertEqual(report["validated_value_bets"],0)
        self.assertNotIn("CFB",report["leagues"])
        self.assertEqual(report["metrics"]["upcoming_matches"],len(report["events"]))
        for e in report["events"]:
            self.assertIsNone(e["recommendation"])
            self.assertIsNone(e["ev"])
            for quote in e["quotes"]:
                self.assertTrue(quote["bookmaker"].endswith("_fr"))

    def test_front_page_gaming_visuals_and_real_telemetry(self):
        text=(DOCS/"index.html").read_text(encoding="utf-8")
        for fragment in ("EVERY","SIGNAL MONITOR","holo","module",
                         "multisports-latest.json","engine-v2-latest.json",
                         "no-store","aria-label"):
            self.assertIn(fragment,text)

    def test_cfb_not_in_live_model_feeds(self):
        model=(ROOT/"modeles/simulations/multisports_independant.py").read_text(encoding="utf-8")
        sports=(ROOT/"modeles/simulations/equipes_avance_multisports.py").read_text(encoding="utf-8")
        engine=(ROOT/"outils/revue_engine_v2.py").read_text(encoding="utf-8")
        pulse=(ROOT/"outils/pulsescore_v2.py").read_text(encoding="utf-8")
        self.assertNotIn('League("CFB"',model)
        self.assertNotIn('"CFB":(',sports)
        self.assertNotIn('"CFB":"americanfootball',engine)
        self.assertNotIn('"CFB":"american-football"',pulse)
        for path in ("multisports-latest.json","equipes-avance-shadow.json","backtests-multisports.json"):
            with self.subTest(file=path):
                import json
                data=json.loads((DOCS/path).read_text(encoding="utf-8"))
                self.assertNotIn("CFB",data.get("leagues",{}))
                self.assertNotIn("CFB",data.get("competitions",{}))

if __name__=="__main__":
    unittest.main()
