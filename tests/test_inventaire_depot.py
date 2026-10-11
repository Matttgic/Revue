"""Structure du dépôt : outils rangés par groupe, index des outils à jour."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from outils.controles.inventaire_depot import (  # noqa: E402
    GROUPS, first_sentence, render_data, render_tools, stray_tools, theme,
)


class StructureTests(unittest.TestCase):
    def test_every_tool_lives_in_a_known_group(self):
        self.assertEqual(stray_tools(ROOT), [])

    def test_tools_index_is_current(self):
        current = (ROOT / "outils" / "README.md").read_text(encoding="utf-8")
        self.assertEqual(current, render_tools(ROOT),
                         "Regénérer : python -m outils.controles.inventaire_depot")

    def test_every_tool_has_a_description(self):
        text = render_tools(ROOT)
        self.assertNotIn("| — |", text)

    def test_data_inventory_lists_every_published_json(self):
        text = render_data(ROOT)
        for f in (ROOT / "docs").glob("*.json"):
            self.assertIn(f"](../docs/{f.name})", text)


class HelperTests(unittest.TestCase):
    def test_first_sentence(self):
        self.assertEqual(first_sentence("Un.  Deux."), "Un.")
        self.assertEqual(first_sentence("sans point"), "sans point")
        self.assertTrue(first_sentence("x" * 300).endswith("…"))

    def test_themes(self):
        self.assertEqual(theme("parite-clairvoyance-frontend.json"), "Reproduction Clairvoyance (parité, audits)")
        self.assertEqual(theme("nhl-shadow-ledger.json"), "NHL")
        self.assertEqual(theme("health-latest.json"), "État du dépôt et recette")

    def test_stray_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outils" / "collecte").mkdir(parents=True)
            (root / "outils" / "collecte" / "ok.py").write_text('"""Ok."""')
            (root / "outils" / "perdu.py").write_text("")
            (root / "outils" / "inconnu").mkdir()
            (root / "outils" / "inconnu" / "x.js").write_text("")
            self.assertEqual(stray_tools(root), ["outils/inconnu/x.js", "outils/perdu.py"])
        self.assertEqual(set(GROUPS), {"clairvoyance", "collecte", "suivi", "controles", "publication"})


if __name__ == "__main__":
    unittest.main()


class WorkflowSafetyTests(unittest.TestCase):
    def test_push_triggers_only_run_on_main(self):
        """Un workflow lancé sur une branche de travail ne doit jamais publier sur main."""
        import yaml
        for wf in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            on = yaml.safe_load(wf.read_text(encoding="utf-8")).get(True) or {}
            if isinstance(on, dict) and "push" in on:
                self.assertEqual((on["push"] or {}).get("branches"), ["main"], wf.name)
