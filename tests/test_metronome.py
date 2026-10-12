"""Métronome : rythme des relances et workflows réellement relançables."""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "metronome.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "metronome.yml"


class MetronomeTests(unittest.TestCase):
    def run_script(self, minutes):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "calls.log"
            gh = Path(tmp) / "gh"
            gh.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{log}"\n')
            gh.chmod(0o755)
            env = {**os.environ, "PATH": f"{tmp}:{os.environ['PATH']}", "METRONOME_SLEEP_SECONDS": "0"}
            subprocess.run(["bash", str(SCRIPT), str(minutes)], check=True, env=env,
                           capture_output=True, text=True)
            return log.read_text().splitlines() if log.exists() else []

    def test_rhythm_over_six_hours(self):
        calls = self.run_script(360)
        count = lambda name: sum(name in c for c in calls)
        self.assertEqual(count("pulsescore-radar-6h.yml"), 6)   # toutes les heures
        self.assertEqual(count("revue-engine-v2.yml"), 3)       # toutes les 2 h
        self.assertEqual(count("multisports-independent.yml"), 2)  # toutes les 3 h
        self.assertTrue(all(c.startswith("workflow run ") and c.endswith("--ref main") for c in calls))

    def test_dispatched_workflows_exist_and_accept_dispatch(self):
        targets = set(re.findall(r"workflow run (\S+\.yml)", SCRIPT.read_text()))
        targets |= set(re.findall(r"workflow run (\S+\.yml)", WORKFLOW.read_text()))
        self.assertEqual(len(targets), 4)
        for name in targets:
            text = (ROOT / ".github" / "workflows" / name).read_text()
            self.assertIn("workflow_dispatch:", text, name)

    def test_cancel_stops_the_chain(self):
        text = WORKFLOW.read_text()
        self.assertIn("if: success()", text)
        self.assertIn("actions: write", text)
        self.assertIn("cancel-in-progress: false", text)


if __name__ == "__main__":
    unittest.main()
