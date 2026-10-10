"""Regression tests for the single-screen, source-gated Revue Arcade V3."""
import json
import re
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
HTML=(DOCS/"index.html").read_text(encoding="utf8")
CSS=(DOCS/"arcade-v3.css").read_text(encoding="utf8")
JS=(DOCS/"arcade-v3-app.js").read_text(encoding="utf8")
CORE=(DOCS/"arcade-v3-data.js").read_text(encoding="utf8")
RADAR=(DOCS/"radar-6h.html").read_text(encoding="utf8")

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors=set()
        self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.anchors.add(a["id"])
        for key in ("href","src"):
            if a.get(key):self.refs.append(a[key])

class ArcadeV3Tests(unittest.TestCase):
    def test_public_home_has_three_clear_tasks(self):
        page=Links();page.feed(HTML)
        for key in ("home-jouer","home-pourquoi","home-bilan",
                    "home-picks","home-recent","home-profit","home-roi",
                    "home-settled","home-active","v3-explain",
                    "v3-sports","v3-search"):
            self.assertIn(key,page.anchors)
        for anchor in ("#home-jouer","#home-pourquoi","#home-bilan"):
            self.assertIn(anchor,page.refs)
        for script in ("./arcade-v3-data.js?v=3","./arcade-v3-app.js?v=4"):
            self.assertIn(script,page.refs)
        for link in ("./play.html","./bilan.html","./historique.html","./lab.html"):
            self.assertIn(link,page.refs)
        self.assertNotIn("parite-clairvoyance.html",HTML)
        self.assertNotIn("reproduction-exacte.html",HTML)
        self.assertNotIn("localStorage",HTML)

    def test_mobile_accessibility_and_historic_disclosure(self):
        self.assertIn("aria-pressed",HTML)
        self.assertIn("aria-live",HTML)
        self.assertIn("aria-label",HTML)
        self.assertIn("prefers-reduced-motion",CSS)
        self.assertIn("grid-template-columns:repeat(3",CSS)
        self.assertIn("data-page=\"arcade-v3\"",HTML)
        self.assertIn("cotes actuellement jouables",HTML)
        self.assertIn("simulations fictives",HTML)
        self.assertIn("paper_profit_units",CORE)
        self.assertIn("validated_value_bets===0",CORE)
        self.assertIn("available_as_real_market!==false",CORE)
        self.assertIn("model_is_calibrated!==false",CORE)
        self.assertIn("source_equivalent_predictions===false",CORE)
        self.assertIn("document.createElement",JS)
        self.assertNotIn("innerHTML",JS)
        self.assertNotIn("Math.random",JS)

    def test_six_hour_radar_has_readable_verified_real_snapshots_only(self):
        page=Links();page.feed(RADAR)
        for key in ("match-count","market-count","call-count","status","lookup","games"):
            self.assertIn(key,page.anchors)
        for link in ("./index.html","./pulsescore-radar-latest.json",
                     "./etat-donnees.html"):
            self.assertIn(link,page.refs)
        self.assertIn("market_prices_are_live!==false",RADAR)
        self.assertIn("positive_ev_verified!==false",RADAR)
        self.assertIn("Règlement des prolongations non vérifié",RADAR)
        self.assertIn("new_paper_bets_created!==false",RADAR)
        self.assertNotIn("innerHTML",RADAR)
        self.assertIn("COTES PULSESCORE 6H",HTML)
        with (DOCS/"pulsescore-radar-latest.json").open(encoding="utf8") as f:
            data=json.load(f)
        self.assertEqual(data["version"],"revue_pulsescore_six_hour_radar_v1")
        self.assertLessEqual(data["requests_used"],8)
        self.assertFalse(data["real_bets_enabled"])
        self.assertFalse(data["positive_ev_verified"])
        self.assertFalse(data["existing_paper_ledger_modified"])
        self.assertEqual(data["matches_observed"],len(data["observations"]))

    def test_model_precision_and_price_cover_pages_are_research_only(self):
        bilan=(DOCS/"bilan.html").read_text(encoding="utf8")
        quality_js=(DOCS/"revue-model-quality.js").read_text(encoding="utf8")
        cover_html=(DOCS/"couvertures-mathematiques.html").read_text(encoding="utf8")
        lab=(DOCS/"lab.html").read_text(encoding="utf8")
        self.assertIn('id="revue-model-quality"',bilan)
        self.assertIn("./revue-model-quality.js?v=1",bilan)
        self.assertIn("bookmaker_baseline_includes_vig",quality_js)
        self.assertIn("min_independent_fixtures_for_preliminary_evaluation",quality_js)
        self.assertIn("revue-crossbook-latest.json",cover_html)
        self.assertIn("claim_guaranteed_profit",cover_html)
        self.assertIn("claim_positive_expected_value",cover_html)
        self.assertIn("actual_prices_bookable_verified",cover_html)
        self.assertIn("couvertures-mathematiques.html",lab)
        self.assertNotIn("innerHTML",quality_js)
        self.assertNotIn("innerHTML",cover_html)
        for filename in ("revue-model-quality-latest.json","revue-crossbook-latest.json"):
            data=json.loads((DOCS/filename).read_text(encoding="utf8"))
            self.assertFalse(data.get("real_bets_enabled",data.get("risk_flags",{}).get("real_bets_enabled")))
        p=json.loads((DOCS/"revue-model-quality-latest.json").read_text(encoding="utf8"))
        self.assertFalse(p["claim_model_profitable"])
        self.assertFalse(p["verified_positive_ev"])
        r=json.loads((DOCS/"revue-crossbook-latest.json").read_text(encoding="utf8"))
        self.assertFalse(r["risk_flags"]["claim_guaranteed_profit"])
        self.assertEqual(r["risk_flags"]["paid_api_calls_for_this_audit"],0)

    def test_phase3_bilan_keeps_frozen_model_evidence_separate_from_paper_money(self):
        bilan=(DOCS/"bilan.html").read_text(encoding="utf8")
        app=(DOCS/"arcade-v3-app.js").read_text(encoding="utf8")
        view=(DOCS/"phase3-bilan.js").read_text(encoding="utf8")
        core=(DOCS/"arcade-v3-data.js").read_text(encoding="utf8")
        page=Links();page.feed(HTML)
        for anchor in ("v3-owned-locked","v3-owned-settled",
                       "v3-owned-elo","v3-owned-status"):
            self.assertIn(anchor,page.anchors)
        self.assertIn("./historique-phase2.html",page.refs)
        self.assertIn('id="phase3-owned-models"',bilan)
        self.assertIn("./phase3-bilan.js?v=1",bilan)
        self.assertIn("./arcade-v3-data.js?v=3",bilan)
        self.assertIn("window.RevueArcadeV3.ownedSnapshot",view)
        self.assertIn("report.models_calibrated!==false",core)
        self.assertIn("roi_computed",core)
        self.assertIn("phase2-owned-ledger.json",app)
        self.assertIn("phase2-owned-performance.json",app)
        self.assertIn('if(e.owned){',app)
        self.assertNotIn("innerHTML",view)
        self.assertNotIn("innerHTML",app)
        for f in ("arcade-v3-data.js","arcade-v3-app.js","phase3-bilan.js"):
            p=subprocess.run(["node","--check",str(DOCS/f)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,f+":"+p.stderr)

    def test_node_scripts_parse_and_static_data_available(self):
        for file in ("arcade-v3-data.js","arcade-v3-app.js"):
            proc=subprocess.run(["node","--check",str(DOCS/file)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
        m=json.loads((DOCS/"match-center-latest.json").read_text(encoding="utf8"))
        p=json.loads((DOCS/"picks-center-latest.json").read_text(encoding="utf8"))
        self.assertEqual(m["validated_value_bets"],0)
        self.assertFalse(m["bookmaker_prices_are_live"])
        self.assertFalse(p["real_bets_enabled"])
        self.assertFalse(p["verified_real_ev"])
        self.assertEqual(p["paper_summary"]["total"],len(p["paper_records"]))

if __name__=="__main__":unittest.main()
