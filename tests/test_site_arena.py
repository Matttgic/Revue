"""Static Revue ARENA pages: working navigation, shared CSS and no active CFB."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
PAGES=(
    "index.html","engine-v2.html","multisports.html",
    "nhl-joueurs.html","nhl-model.html","football-avance.html",
    "qualite-modeles.html",
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
                self.assertIn("theme.css?v=2",dom.links)
                self.assertIn("./index.html",dom.links)
                self.assertIn("rv-topbar",text)
                self.assertIn("rv-nav",text)

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
