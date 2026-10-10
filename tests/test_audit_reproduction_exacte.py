"""Source-pinned reproduction audit tests; do not bundle third-party source."""
from datetime import datetime,timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from outils.audit_reproduction_exacte import route_inventory, strict_report

NOW=datetime(2026,10,10,9,tzinfo=timezone.utc)


def _write(root:Path,path:str,body:str) -> None:
    dest=root/path
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(body,encoding="utf-8")


class StrictReproductionTests(unittest.TestCase):
    def make(self,source:Path,target:Path):
        for path in ("app/main.py","app/routers/admin.py","app/routers/mlb.py",
                     "app/routers/nhl.py","app/routers/picks.py","app/routers/predictions.py"):
            _write(source,path,"# test fixture: not original source\n")
        _write(source,"app/main.py","""from fastapi import FastAPI
app=FastAPI()
@app.get("/health")
async def health(): pass
""")
        _write(source,"app/routers/nhl.py","""from fastapi import APIRouter
router=APIRouter(prefix="/nhl")
@router.get("/schedule")
async def get_schedule(): pass
@router.post("/goals/{id}")
async def get_goalie(id): pass
""")
        _write(source,"docs/app.html","<html><title>Reference fixture</title></html>")
        _write(source,"docs/index.html","<html><title>Reference fixture</title></html>")
        _write(target,"docs/index.html","<html><title>Revue original</title></html>")
        _write(target,"docs/parite-modeles-clairvoyance.json",json.dumps({
            "verified_formula_parity_models":44,"total_target_models":44,
            "original_source_commit":"test-reference-commit",
            "exact_equality_tests_passed":5232,
        }))
        for path in ("docs/parite-clairvoyance-frontend.json",
                     "docs/parite-clairvoyance-predictor.json",
                     "docs/parite-donnees-clairvoyance.json"):
            _write(target,path,json.dumps({"reference_commit":"a-different-revision"}))

    def test_routes_source_not_confused_with_target_static_pages(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            routes=route_inventory(source)
            self.assertEqual(len(routes),3)
            self.assertEqual({(x["method"],x["path"]) for x in routes},
                             {("GET","/health"),("GET","/nhl/schedule"),("POST","/nhl/goals/{id}")})
            result=strict_report(source,target,NOW)
            self.assertEqual(result["backend"]["source_route_count"],3)
            self.assertEqual(result["backend"]["end_to_end_verified_equivalent_routes"],0)
            self.assertIsNone(result["exact_reproduction_percent"])
            self.assertFalse(result["frontend"]["identical_html"])
            self.assertEqual(result["model_formulas"]["verified_in_declared_subset"],44)
            self.assertEqual(result["model_formulas"]["current_real_game_same_input_outputs_equal"],"NOT_VERIFIED")
            self.assertFalse(result["wholesale_source_redistribution_authorized"])

    def test_matching_frontend_bytes_do_not_imply_complete_application(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            _write(target,"docs/index.html",(source/"docs/app.html").read_text())
            result=strict_report(source,target,NOW)
            self.assertTrue(result["frontend"]["identical_html"])
            self.assertEqual(result["frontend"]["pixel_accurate_visual_comparison"],"NOT_PERFORMED")
            self.assertEqual(result["exact_end_to_end_parity"],"NOT_VERIFIED")

    def test_missing_source_file_raises_instead_of_reporting_false_success(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            (source/"app/routers/nhl.py").unlink()
            with self.assertRaises(FileNotFoundError):
                strict_report(source,target,NOW)

    def test_invalid_equality_count_fails_closed(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            _write(target,"docs/parite-modeles-clairvoyance.json",json.dumps({
                "verified_formula_parity_models":900,"total_target_models":44,
            }))
            with self.assertRaises(ValueError):
                strict_report(source,target,NOW)

    def test_data_products_distinguish_same_path_from_actual_equal_bytes(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            _write(source,"docs/data.json",'{"a":1}')
            _write(target,"docs/data.json",'{"a":2}')
            result=strict_report(source,target,NOW)
            item=next(x for x in result["static_data_contracts"]["items"]
                      if x["original"]=="docs/data.json")
            self.assertTrue(item["identical_path_in_revue"])
            self.assertFalse(item["identical_bytes_confirmed"])
            self.assertEqual(item["equivalent_semantic_content"],"unverified")
            self.assertIsNone(result["exact_reproduction_percent"])

    def test_scope_excludes_cfb(self):
        with TemporaryDirectory() as tmp:
            source,target=Path(tmp)/"original",Path(tmp)/"revue"
            self.make(source,target)
            result=strict_report(source,target,NOW)
            self.assertIn("CFB intentionally excluded",result["scope"])

if __name__=="__main__":
    unittest.main()
