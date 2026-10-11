"""Vercel ne redéploie l'API que si son code ou ses données changent."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "vercel-ignore.sh"


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin"})


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "git/bash requis")
class VercelIgnoreTests(unittest.TestCase):
    def run_after(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            for name in ("docs/autre.json", "docs/match-center-latest.json", "api_revue/app.py", "outils/x.py"):
                (Path(tmp) / name).parent.mkdir(parents=True, exist_ok=True)
                (Path(tmp) / name).write_text("0")
            git(tmp, "add", "-A"); git(tmp, "commit", "-qm", "init")
            if files is None:
                return subprocess.run(["bash", str(SCRIPT)], cwd=tmp, capture_output=True).returncode
            for name in files:
                (Path(tmp) / name).write_text("1")
            git(tmp, "add", "-A"); git(tmp, "commit", "-qm", "change")
            return subprocess.run(["bash", str(SCRIPT)], cwd=tmp, capture_output=True).returncode

    def test_skip_unrelated_data_and_tools(self):
        self.assertEqual(self.run_after(["docs/autre.json", "outils/x.py"]), 0)

    def test_deploy_on_api_code_or_api_data(self):
        self.assertEqual(self.run_after(["api_revue/app.py"]), 1)
        self.assertEqual(self.run_after(["docs/match-center-latest.json"]), 1)

    def test_deploy_when_no_parent_commit(self):
        self.assertEqual(self.run_after(None), 1)


class VercelConfigTests(unittest.TestCase):
    def test_config_and_every_api_data_file_listed(self):
        cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["ignoreCommand"], "bash .github/scripts/vercel-ignore.sh")
        self.assertLessEqual(len(cfg["ignoreCommand"]), 256)
        script = SCRIPT.read_text(encoding="utf-8")
        used = set()
        for p in list((ROOT / "api_revue").glob("*.py")) + [ROOT / "api" / "index.py"]:
            used |= set(re.findall(r'"([a-z0-9-]+\.json)"', p.read_text(encoding="utf-8")))
        missing = sorted(f for f in used if "docs/" + f not in script)
        self.assertEqual(missing, [], "Fichiers lus par l'API absents de vercel-ignore.sh")


if __name__ == "__main__":
    unittest.main()
