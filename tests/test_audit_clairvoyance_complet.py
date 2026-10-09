import unittest
import tempfile
from pathlib import Path
from datetime import datetime,timezone
from outils.audit_clairvoyance_complet import inventory, inspect_frontend_model_symbols

NOW=datetime(2026,10,9,20,tzinfo=timezone.utc)
class StaticInventoryTests(unittest.TestCase):
    def test_counts_without_executing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"src";root.mkdir()
            d=root/"scripts";d.mkdir()
            (d/"fetch_nhl.py").write_text("def fetch():\n    raise RuntimeError('MUST NOT RUN')\n")
            (d/"scrape_opta_stats.py").write_text("import json\ndef study():\n    return 2\n")
            a=root/".github/workflows";a.mkdir(parents=True)
            (a/"daily.yml").write_text("name: test\n")
            project=Path(tmp)/"revue";project.mkdir()
            pr=project/"modeles/simulations";pr.mkdir(parents=True)
            (pr/"nhl_independant.py").write_text("# shadow")
            out=inventory(root,project,NOW)
            self.assertEqual(out["counts"]["python_files"],2)
            self.assertEqual(out["counts"]["python_functions"],2)
            self.assertEqual(out["counts"]["workflows"],1)
            self.assertFalse(out["copyright"]["permission_to_redistribute_source"])
            self.assertTrue(out["source_areas"]["nhl_game_goalie"]["corresponding_revue_modules"]["modeles/simulations/nhl_independant.py"])
            self.assertEqual(out["generated_at_utc"],NOW.isoformat())

    def test_frontend_inline_js_models_indexed_without_copying_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            docs=root/"docs"
            docs.mkdir()
            docs.joinpath("app.html").write_text(
                '<script>function predictNHL(a){return a;} '
                'const nbAModel=(x)=>x; '
                'function unrelatedLogger(){} '
                'const eloRate = function(x){return x;};</script>',
                encoding="utf-8"
            )
            report=inspect_frontend_model_symbols(root)
            self.assertEqual(report["status"],"read_only_symbol_index")
            self.assertEqual(report["model_related_count"],3)
            self.assertEqual({x["name"] for x in report["model_symbols"]},
                             {"predictNHL","nbAModel","eloRate"})
            self.assertNotIn("function predictNHL",str(report))

    def test_license_and_syntax_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"LICENSE").write_text("Rights reserved")
            (root/"bad.py").write_text("def f(:\n")
            out=inventory(root)
            self.assertTrue(out["copyright"]["license_file_present"])
            self.assertEqual(out["counts"]["python_parse_errors"],1)
            self.assertEqual(out["counts"]["python_functions"],0)

    def test_source_directory_required(self):
        with self.assertRaises(ValueError):
            inventory(Path("/no/existing/location/clairvoyance"))
if __name__=="__main__":unittest.main()
