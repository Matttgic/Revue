"""Phase 8: navigation, source-gated explanations, technical-access tests."""
import re,subprocess,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/"docs"
PAGES=("index.html","play.html","pourquoi.html","bilan.html","historique.html","lab.html")
PRIMARY=("play.html","pourquoi.html","bilan.html")
class Phase8Tests(unittest.TestCase):
    def test_exactly_three_navigation_links_on_every_public_page(self):
        for page in PAGES:
            with self.subTest(page=page):
                text=(D/page).read_text(encoding="utf8")
                for name in ("rv-nav","arc-bottom-nav"):
                    nav=re.search(r'<nav class="'+name+r'"[^>]*>(.*?)</nav>',text,re.S)
                    self.assertIsNotNone(nav)
                    self.assertEqual(tuple(re.findall(r'href="./([^"]+)"',nav.group(1))),PRIMARY)
                self.assertIn("phase8-ui.css?v=2",text)
                self.assertIn('href="./lab.html"',text)
                self.assertIn('href="./index.html"',text)
    def test_why_page_uses_same_source_gates_as_home(self):
        why=(D/"pourquoi.html").read_text()
        for token in ('id="home-pourquoi"','id="v3-explain"','id="home-picks"',
                      'id="v3-search"','id="v3-sports"','data-page="pourquoi"',
                      "arcade-v3-data.js?v=3","arcade-v3-app.js?v=4"):
            self.assertIn(token,why)
        js=(D/"arcade-v3-app.js").read_text()
        self.assertIn("new URLSearchParams(window.location.search)",js)
        self.assertIn('selected=league+":"+id',js)
        self.assertIn('if($("home-recent"))drawPaper();',js)
        self.assertNotIn("innerHTML",js)
    def test_from_play_to_exact_match_explanation(self):
        js=(D/"retro-app.js").read_text()
        self.assertGreaterEqual(js.count("./pourquoi.html?league="),2)
        self.assertIn("encodeURIComponent(g.event_id)",js)
        self.assertIn('route==="pourquoi"',js)
        self.assertIn('href="./pourquoi.html"',(D/"play.html").read_text())
    def test_simple_bilan_preserves_advanced_quality(self):
        text=(D/"bilan.html").read_text()
        for token in ('<details class="phase8-details">','id="bilan-profit"',
                      'id="bilan-roi"','id="phase3-owned-models"',
                      'id="revue-model-quality"','data-nhl-performance'):
            self.assertIn(token,text)
    def test_lab_search_keeps_existing_tools(self):
        html=(D/"lab.html").read_text();js=(D/"phase8-lab.js").read_text()
        for token in ('id="lab-filter"','id="lab-filter-count"',
                      'phase7-cotes-bilan.html','reproduction-exacte.html'):
            self.assertIn(token,html)
        self.assertIn("link.hidden=!visible",js)
    def test_javascript_syntax_and_local_asset_paths(self):
        for js in ("retro-app.js","arcade-v3-app.js","phase8-lab.js"):
            check=subprocess.run(["node","--check",str(D/js)],capture_output=True,text=True)
            self.assertEqual(check.returncode,0,js+": "+check.stderr)
        for page in PAGES:
            html=(D/page).read_text()
            for path in re.findall(r'(?:href|src)="(\./[^"#?]+)',html):
                self.assertTrue((D/path[2:]).is_file(),page+": "+path)
    def test_accessible_mobile_3d_reduced_motion(self):
        css=(D/"phase8-ui.css").read_text()
        for word in ("grid-template-columns:repeat(3","prefers-reduced-motion:reduce",
                     "focus-visible","phase8-orb"):
            self.assertIn(word,css)
if __name__=="__main__":unittest.main()
