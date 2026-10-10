"""NHL source-style parity checks executed against the ORIGINAL predictor.

The original is loaded by existing read-only AST doubles in GitHub CI, not
copied into Revue. Inputs are already-observed NHL fixture, Revue Elo, MoneyPuck
all-situation xG and official most-used goalie stats. Identical outputs prove
math/field parity on these data ONLY, not original SQL or frontend bet picks.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from modeles.reproduction.clairvoyance_predictor import Game, nhl
from outils.verifier_parite_clairvoyance import reference_functions
from outils.nhl_backend_source_style import utc, VERSION


def compare(reference_root: Path, report: dict) -> dict:
    if (report.get("version") != VERSION
            or report.get("status") != "backend_style_input_scenario_not_original_model_parity"
            or report.get("has_verified_original_predictions") is not False
            or report.get("public_deployment_configuration_verified") is not False
            or report.get("real_bets_enabled") is not False
            or report.get("odds_collected") is not False
            or report.get("frozen_ledger_unchanged") is not True):
        raise ValueError("NHL research report parity flags invalid")
    seen = set()
    report_at = utc(report["generated_at_utc"])
    stamps = {key: utc(value) for key, value in report["input_observed_utc"].items()}
    if any(x > report_at for x in stamps.values()):
        raise ValueError("Reference inputs observed after report clock")
    src = reference_root / "app" / "services" / "predictor.py"
    functions = reference_functions(reference_root)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    commit = subprocess.run(
        ["git", "-C", str(reference_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    games_checked = 0
    operations = 0
    for row in report.get("games", []):
        eid = str(row.get("event_id", ""))
        if not eid.isdecimal() or eid in seen:
            raise ValueError("Invalid/duplicate NHL event")
        seen.add(eid)
        start = utc(row["kickoff_utc"])
        if start < report_at + timedelta(minutes=20):
            raise ValueError("Comparison includes already-starting fixture")
        if any(x > start - timedelta(minutes=20) for x in stamps.values()):
            raise ValueError("Source inputs observed past pre-match cutoff")
        if row.get("original_sql_elo_and_raw_xg_verified") is not False:
            raise ValueError("Original SQL availability flag false claim")
        h, a = row["home"], row["away"]
        eh, ea = row["home_elo_revue_proxy"], row["away_elo_revue_proxy"]
        goalies = row["official_goalies"]
        hg, ag = goalies["home"], goalies["away"]
        if (hg["status"] != "unique_most_games" or
                ag["status"] != "unique_most_games"):
            if (row["raw_fraction_home_probability"] is not None or
                    row["percentage_point_home_probability"] is not None):
                raise ValueError("Ambiguous goalie must suppress probabilities")
            continue
        for mode, scale, published_field in (
            ("raw_fraction", 1, "raw_fraction_home_probability"),
            ("percentage_point", 100, "percentage_point_home_probability"),
        ):
            xg = row["moneypuck_situation_all_raw_share"]
            hxg, axg = xg["home"] * scale, xg["away"] * scale
            game = Game(eid, h, a, game_time_utc=row["kickoff_utc"])
            db = SimpleNamespace(
                elos={("nhl", h): eh, ("nhl", a): ea},
                xg={h: hxg, a: axg},
                goalies={h: hg["save_pct"], a: ag["save_pct"]},
            )
            original = asyncio.run(functions["predict_nhl_game"](game, db))
            ours = nhl(game, eh, ea, hxg, axg,
                       hg["save_pct"], ag["save_pct"])
            if original != ours:
                raise AssertionError(f"NHL original-backend dict mismatch on {eid}: {mode}")
            if ours["model_home_win_prob"] != row[published_field]:
                raise AssertionError(f"NHL report probability changed on {eid}: {mode}")
            operations += 1
        games_checked += 1
    if operations == 0:
        raise ValueError("No NHL source-style real-case comparisons available")
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "source_style_backend_outputs_identical_on_tested_real_inputs",
        "original_repository": "Purple-Wraith/clairvoyance-backend",
        "original_predictor_path": "app/services/predictor.py",
        "original_commit": commit,
        "original_predictor_sha256": digest,
        "input_report": "docs/nhl-backend-source-style-latest.json",
        "input_report_generated_at_utc": report["generated_at_utc"],
        "source_style_real_nhl_games_checked": games_checked,
        "complete_result_dicts_identical": operations,
        "xg_modes_checked": ["raw_fraction", "percentage_point"],
        "source_sql_elo_or_input_parity_verified": False,
        "original_published_best_bets_parity_verified": False,
        "frozen_predictions_changed": False,
        "cfb_included": False,
        "note": "Read-only original predictor comparison on SAME independent Revue inputs, not on source SQL or current source bestBets.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=Path("docs/nhl-backend-source-style-latest.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/parite-nhl-source-style.json"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    report = compare(args.reference, data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report["source_style_real_nhl_games_checked"], "NHL fixtures,",
          report["complete_result_dicts_identical"], "backend original result dicts exactly matched")


if __name__ == "__main__":
    main()
