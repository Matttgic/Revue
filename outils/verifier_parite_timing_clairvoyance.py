"""Différentiel automatique avec le classificateur du dépôt original.

GitHub Actions récupère Clairvoyance en lecture seule. Aucun code ni ticket
original n'est redistribué. Les entrées synthétiques et le hash restent auditables.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess

from modeles.reproduction import clairvoyance_lock_timing as ours


def load_reference(root: Path):
    location = root / "scripts" / "lock_timing.py"
    if not location.is_file():
        raise FileNotFoundError("Original lock_timing.py unavailable")
    spec = importlib.util.spec_from_file_location("clairvoyance_timing_reference", location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, location


def validate(reference, source_path):
    # The historical publication convention is intentionally separate from
    # Revue's conservative (pre-only) eligibility rule.
    if reference.BASIS != ours.BASIS:
        raise AssertionError("Source publication basis changed; review required")
    for key, minutes in ours.LENGTHS.items():
        if reference.DUR_MIN.get(key) != minutes:
            raise AssertionError(f"Source league duration changed: {key}")
    league_values = ["NHL", "NBA", "NFL", "SHL", "LIIGA", "NLA",
                     "EXTRALIGA", "PL", "LIGA", "SERIEA", "CL",
                     "BUND", "MLS", "MLB", "WNBA", "KHL",
                     "Premier League", "La Liga", "Basketball", "Hockey"]
    rng = random.Random(20261010)
    start = 1791652800000  # 2026-10-10T20:00Z
    fixtures = [
        {"date": "2026-10-11T01:00:00Z", "home": "BOS", "away": "PHI"},
        {"date": "2026-11-01T08:30:00Z", "home": "TOR", "away": "MTL"},
        {"date": "2026-03-08T10:00:00Z", "home": "SEA", "away": "VAN"},
    ]
    ours_idx = ours.schedule_index(fixtures)
    their_idx = {}
    for fixture in fixtures:
        reference.add_game(their_idx, fixture, "home", "away")
    if ours_idx != their_idx:
        raise AssertionError("Schedule matching / Denver time drift")

    checked = 0
    cases = []
    for i in range(1800):
        sport = league_values[i % len(league_values)]
        shift = rng.choice([-250, -196, -151, -150, -121, -120, -1,
                            0, 1, 30, 119, 149, 150, 195, 210, 250])
        record = {
            "id": f"synthetic-{i}",
            "sport": sport,
            "league": rng.choice([sport, "NHL", "PL"]),
            "date": "2026-10-10",
            "hA": "BOS",
            "awA": "PHI",
            "startMs": start,
            "lockedAt": start + shift * 60000,
            "outcome": rng.choice(["win", "loss", "pending"]),
            "betType": rng.choice(["ML", "SPREAD", "PARLAY", "OU"]),
        }
        if i % 7 == 0:
            record["startMs"] = None
        if i % 11 == 0:
            record["lockedAt"] = None
        if i % 17 == 0:
            record["lockTiming"] = "late-manual"
        if i % 19 == 0:
            record["startMs"] = "invalid"
        if i % 29 == 0:
            record["sport"] = "HOCKEY"
            record["league"] = "NHL"
        if i % 31 == 0:
            record["hA"], record["awA"] = "PHI", "BOS"
        if i % 37 == 0:
            record["startMs"] = None
            record["lockedAt"] = ours.iso_millis("2026-10-11T00:00:00Z")
            record["date"] = "2026-10-10"

        for label, received, expected in (
            ("sport", ours.sport_code(record), reference.norm_sport(record)),
            ("parlay", ours.is_parlay(record), reference.is_parlay(record)),
            ("classification", ours.classify(record, ours_idx),
             reference.classify(record, their_idx)),
            ("late", ours.is_known_late(record, ours_idx),
             reference.is_known_late(record, their_idx)),
        ):
            if received != expected:
                raise AssertionError(f"{label} diverged, case {i}: {received} != {expected}")
            checked += 1
        cases.append(record)

    if ours.summarize(cases, ours_idx) != reference.summarize(cases, their_idx):
        raise AssertionError("Aggregate original settled-timing figures diverged")
    checked += 1
    late_original = reference.late_ids(cases, their_idx)
    late_ours = {p["id"] for p in cases if ours.is_known_late(p, ours_idx)}
    if late_original != late_ours:
        raise AssertionError("Known late ID set diverged")
    checked += len(cases)

    # Independent stricter Revue rule: only verified pre-start entries,
    # without CFB, parlays or retired leagues. Not a source-equality claim.
    safety_cases = [
        {"sport": "CFB", "league": "CFB", "startMs": start,
         "lockedAt": start - 60000},
        {"sport": "NHL", "league": "NHL", "startMs": None,
         "lockedAt": start - 60000},
        {"sport": "NHL", "league": "NHL", "startMs": start,
         "lockedAt": start - 60000},
    ]
    if [ours.revue_public_eligibility(p) for p in safety_cases] != [False, False, True]:
        raise AssertionError("CFB / unknown / pre-start safeguards regressed")
    reference_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(source_path.parent.parent), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=4).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        commit = None
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "verified_on_synthetic_inputs",
        "original_repository": "Purple-Wraith/clairvoyance-backend",
        "original_path": "scripts/lock_timing.py",
        "original_commit": commit,
        "original_sha256": reference_sha,
        "checked_operations": checked,
        "synthetic_cases": len(cases),
        "compared": ["sport normalization", "parlay exclusion",
                     "pre/during/after/unknown classifications",
                     "known-late detection", "settled summary",
                     "late pick identities", "schedule local-date keys"],
        "all_exact_on_test_inputs": True,
        "cfb_integration": "excluded",
        "revue_unknowns_accepted_as_confirmed_pre_match": False,
        "live_source_snapshots_equal": False,
        "full_application_reproduction_verified": False,
        "redistributed_original_source_code": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, source_path = load_reference(args.reference)
    report = validate(source, source_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Verified {report['checked_operations']} operations on "
          f"{report['synthetic_cases']} synthetic cases")


if __name__ == "__main__":
    main()
