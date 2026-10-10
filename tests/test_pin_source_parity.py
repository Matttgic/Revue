"""Source model fingerprint evidence cannot survive changed predictor/UI source code."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from outils.pin_source_parity import pin,FILES


class PinSourceParityTests(unittest.TestCase):
    def test_all_three_reference_artifacts_hashed_with_original_commit(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            for name in FILES:
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(("test file "+name).encode())
            doc=pin(root,{
                "original_source_commit":"same",
                "verified_formula_parity_models":44,
                "total_target_models":44,
            },"same")
            self.assertEqual(set(doc["reference_model_source_sha256"]),set(FILES))
            self.assertTrue(all(len(x)==64 for x in
                doc["reference_model_source_sha256"].values()))
            self.assertTrue(doc["unrelated_repository_commits_may_change"])

    def test_commit_mismatch_or_incomplete_formula_tests_fails(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            for name in FILES:
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(name)
            with self.assertRaises(ValueError):
                pin(root,{"original_source_commit":"old",
                          "verified_formula_parity_models":44,
                          "total_target_models":44},"new")
            with self.assertRaises(ValueError):
                pin(root,{"original_source_commit":"new",
                          "verified_formula_parity_models":43,
                          "total_target_models":44},"new")

    def test_missing_reference_file_never_pinned(self):
        with TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError):
                pin(Path(t),{"original_source_commit":"same",
                             "verified_formula_parity_models":44,
                             "total_target_models":44},"same")


if __name__=="__main__":
    unittest.main()
