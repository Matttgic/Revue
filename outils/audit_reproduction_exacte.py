#!/usr/bin/env python3
"""Strict, reproducible audit of Clairvoyance full-stack reproduction.

Source is a temporary, read-only checkout. Report summaries and hashes only:
no third-party source code or proprietary dataset is redistributed.
Function-level equality and first-party features never count as a 100%
end-to-end clone. Outputs JSON with null for unmeasured exact parity.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess

EXPECTED_SOURCE = "Purple-Wraith/clairvoyance-backend"
TARGET = "Matttgic/Revue"
FRONTEND_SOURCE = "docs/app.html"
ROUTE_SOURCES = (
    "app/main.py", "app/routers/admin.py", "app/routers/mlb.py",
    "app/routers/nhl.py", "app/routers/picks.py",
    "app/routers/predictions.py",
)
# This is an explicitly declared subset of published JSON products, not all
# hundreds of source files. Neither keys nor outputs are fabricated.
STATIC_PRODUCTS = (
    "docs/data.json", "docs/picks.json", "docs/live_data.json",
    "docs/automation_status.json", "docs/engine_performance.json",
    "docs/sport_performance.json", "docs/player_stats.json",
    "docs/team_logos.json", "docs/soccer_fbref.json",
)
EVIDENCE_REPORTS = (
    "docs/parite-modeles-clairvoyance.json",
    "docs/parite-clairvoyance-frontend.json",
    "docs/parite-clairvoyance-predictor.json",
    "docs/parite-clairvoyance-nhl-observe.json",
    "docs/parite-donnees-clairvoyance.json",
)


def source_commit(folder: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(folder), "rev-parse", "HEAD"],
            text=True, timeout=8, stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 512), b""):
            h.update(chunk)
    return h.hexdigest()


class StaticIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.page_links: set[str] = set()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(str(attrs["id"]))
        if tag == "a" and attrs.get("href"):
            self.page_links.add(str(attrs["href"]))


def static_dom(root: Path, pages: tuple[str, ...]) -> StaticIds:
    parser = StaticIds()
    for relative in pages:
        page = root / relative
        if not page.is_file():
            continue
        # Static HTML only. Original dynamic JS templates, CSS, animations,
        # and pixel-accurate rendering are NOT captured by this method.
        parser.feed(page.read_text(encoding="utf-8"))
    return parser


def own_http_route_signatures(root: Path) -> list[str]:
    """Inspect declared FastAPI routes in Revue without executing code."""
    path=root/"api_revue/app.py"
    if not path.is_file():
        return []
    source=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    result=set()
    for node in ast.walk(source):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        for d in node.decorator_list:
            if (isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and
                isinstance(d.func.value,ast.Name) and d.func.value.id=="app" and
                d.func.attr.lower() in ("get","post","patch","put","delete") and
                d.args and isinstance(d.args[0],ast.Constant) and
                isinstance(d.args[0].value,str)):
                result.add(d.func.attr.upper()+" "+d.args[0].value)
    return sorted(result)


def current_nhl_schedule_pairs(reference: Path, mapping: dict) -> bool:
    """Recheck factual IDs against current original NHL calendar, not just commit."""
    path=reference/"docs/nhl_schedule.json"
    if mapping.get("status")!="verified_fixture_identity_pairs" or not path.is_file():
        return False
    try:
        source=_json(path)
        originals={}
        for item in source.get("games") or []:
            try:
                when=datetime.fromisoformat(item["date"].replace("Z","+00:00")).astimezone(timezone.utc)
                key=(item["home"],item["away"],when.isoformat())
                originals.setdefault(key,[]).append(str(item["id"]))
            except (KeyError,TypeError,ValueError):
                continue
        observed=mapping.get("mappings") or []
        if (not observed or mapping.get("matched")!=len(observed) or
            mapping.get("unmatched") != 0):
            return False
        provider_ids=set()
        official_ids=set()
        for row in observed:
            key=(row["home"],row["away"],datetime.fromisoformat(
                row["start_utc"].replace("Z","+00:00")).astimezone(timezone.utc).isoformat())
            espn=str(row["original_espn_id"])
            official=str(row["nhl_game_id"])
            if (originals.get(key)!=[espn] or
                espn in provider_ids or official in official_ids):
                return False
            provider_ids.add(espn)
            official_ids.add(official)
        return True
    except (OSError,KeyError,TypeError,ValueError,UnicodeDecodeError):
        return False


SCHEMAS = {
    "MLBGameOut": "app/schemas/mlb.py",
    "NHLGameOut": "app/schemas/nhl.py",
    "NHLTeamStatOut": "app/schemas/nhl.py",
    "NHLGoalieStatOut": "app/schemas/nhl.py",
    "NHLSkaterStatOut": "app/schemas/nhl.py",
}


def _annotation_shape(node: ast.AST) -> str:
    """Normalize Optional[T] vs T | None without erasing requiredness."""
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and
            node.value.id == "Optional"):
        return _annotation_shape(node.slice) + "?"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = _annotation_shape(node.left), _annotation_shape(node.right)
        if right == "None": return left + "?"
        if left == "None": return right + "?"
    return ast.unparse(node)


def _schema_class_fields(classes: dict[str, ast.ClassDef],name:str,
                         ancestry:tuple[str,...]=()) -> dict:
    if name in ancestry:
        raise ValueError("Cycle in Pydantic model inheritance")
    node=classes.get(name)
    if node is None:
        raise ValueError(f"Pydantic class not found: {name}")
    values={}
    for parent in node.bases:
        if isinstance(parent,ast.Name) and parent.id in classes:
            values.update(_schema_class_fields(classes,parent.id,ancestry+(name,)))
    for entry in node.body:
        if isinstance(entry,ast.AnnAssign) and isinstance(entry.target,ast.Name):
            values[entry.target.id]={
                "type":_annotation_shape(entry.annotation),
                "required":entry.value is None,
            }
    return values


def _classes_from_files(root:Path,paths:tuple[str,...]) -> dict:
    classes={}
    for relative in paths:
        source=root/relative
        if not source.is_file():
            return {}
        tree=ast.parse(source.read_text(encoding="utf-8"),filename=relative)
        for node in tree.body:
            if isinstance(node,ast.ClassDef):
                classes[node.name]=node
    return classes


def compare_api_schemas(reference:Path,target:Path) -> dict:
    """Field- and nullability-shape evidence, NOT verified matching values."""
    source=_classes_from_files(reference,tuple(sorted(set(SCHEMAS.values()))))
    implementation=_classes_from_files(target,("api_revue/app.py",))
    result={}
    for name in SCHEMAS:
        try:
            origin=_schema_class_fields(source,name)
            own=_schema_class_fields(implementation,name)
            missing=sorted(set(origin)-set(own))
            extra=sorted(set(own)-set(origin))
            mismatched=sorted(k for k in set(origin)&set(own) if origin[k]!=own[k])
            exact=bool(origin and own and not (missing or extra or mismatched))
            result[name]={
                "field_shapes_equal":exact,
                "reference_field_count":len(origin),
                "implemented_field_count":len(own),
                "missing_fields":missing,
                "extra_fields":extra,
                "type_or_requiredness_mismatches":mismatched,
            }
        except ValueError:
            result[name]={
                "field_shapes_equal":False,
                "reference_field_count":None,
                "implemented_field_count":None,
                "missing_fields":[],
                "extra_fields":[],
                "type_or_requiredness_mismatches":[],
                "status":"source_or_target_schema_unavailable",
            }
    matching=sum(bool(x["field_shapes_equal"]) for x in result.values())
    return {
        "reference_schemas_compared":len(SCHEMAS),
        "field_shapes_identical":matching,
        "all_targeted_field_shapes_identical":matching==len(SCHEMAS),
        "original_database_identity_equal":False,
        "live_response_values_equal":"NOT_VERIFIED",
        "nullable_and_required_field_shapes_only":True,
        "models":result,
    }


def route_inventory(root: Path) -> list[dict]:
    found = []
    for relative in ROUTE_SOURCES:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Original route source unavailable: {relative}")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        router_prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "router" for t in node.targets
            ) and isinstance(node.value, ast.Call):
                for arg in node.value.keywords:
                    if arg.arg == "prefix" and isinstance(arg.value, ast.Constant):
                        router_prefix = str(arg.value.value)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                    continue
                owner = dec.func.value
                if not isinstance(owner, ast.Name) or owner.id not in ("app", "router"):
                    continue
                method = dec.func.attr.upper()
                if method not in ("GET", "POST", "PATCH", "DELETE", "PUT"):
                    continue
                if not dec.args or not isinstance(dec.args[0], ast.Constant):
                    continue
                pathpart = str(dec.args[0].value)
                route = (router_prefix if owner.id == "router" else "") + pathpart
                found.append({
                    "method": method, "path": route,
                    "source_file": relative,
                    "original_function": node.name,
                    "target_parity": "unverified",
                })
    return sorted(found, key=lambda r: (r["path"], r["method"]))


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def strict_report(reference: Path, target: Path, generated: datetime) -> dict:
    if generated.tzinfo is None:
        raise ValueError("Audit timestamp must be timezone aware")
    if not (reference / FRONTEND_SOURCE).is_file():
        raise FileNotFoundError("Original frontend missing")
    if not (target / "docs/index.html").is_file():
        raise FileNotFoundError("Revue frontend missing")
    routes = route_inventory(reference)
    response_schemas = compare_api_schemas(reference,target)
    source_route_keys={r["method"]+" "+r["path"] for r in routes}
    own_declared=own_http_route_signatures(target)
    matching_routes=sorted(source_route_keys.intersection(own_declared))
    current_sha = source_commit(reference)
    if not current_sha:
        # A source snapshot without its commit is useful for inspection only,
        # NOT for proof of an exact reproduction of any particular revision.
        revision_status = "unverified_source_commit"
    else:
        revision_status = "source_revision_recorded"

    evidence = {}
    for relative in EVIDENCE_REPORTS:
        path = target / relative
        if not path.is_file():
            evidence[relative] = {"status": "missing"}
            continue
        obj = _json(path)
        pinned = obj.get("original_source_commit") or obj.get("reference_commit")
        supported = bool(current_sha and pinned == current_sha)
        evidence[relative] = {
            "status": "verified_at_current_commit" if supported else
                      "historical_or_unpinned_evidence",
            "source_commit_of_test": pinned,
            "matches_current_source_commit": supported,
            "targeted_formula_tests": obj.get("exact_equality_tests_passed"),
        }
    model = _json(target / "docs/parite-modeles-clairvoyance.json")
    real_path = target / "docs/parite-clairvoyance-nhl-observe.json"
    real = _json(real_path) if real_path.is_file() else {}
    validated_real = bool(
        current_sha and real.get("reference_commit") == current_sha and
        type(real.get("real_nhl_fixtures_compared")) is int and
        real["real_nhl_fixtures_compared"] > 0 and
        real.get("reference_vs_revue_entire_output_dict_equal") ==
          real["real_nhl_fixtures_compared"] and
        real.get("original_data_sources_identical") is False and
        real.get("identical_original_clairvoyance_predictions_proven") is False
    )
    id_path=target/"docs/parite-nhl-espn-id-map.json"
    id_map=_json(id_path) if id_path.is_file() else {}
    id_pairs_current=current_nhl_schedule_pairs(reference,id_map)
    elo_path=target/"docs/parite-elo-mlb-source.json"
    elo_audit=_json(elo_path) if elo_path.is_file() else {}
    current_elo_sha=sha256(reference/"app/services/elo.py")
    elo_verified=bool(
        current_elo_sha and
        elo_audit.get("reference_elo_source_sha256")==current_elo_sha and
        elo_audit.get("status")=="verified_elo_rule_on_revue_espn_history" and
        type(elo_audit.get("historical_mlb_final_games_checked")) is int and
        elo_audit["historical_mlb_final_games_checked"]>=20 and
        elo_audit.get("exact_update_equal_to_original")==elo_audit["historical_mlb_final_games_checked"] and
        elo_audit.get("original_clairvoyance_sql_rating_parity")=="NOT_VERIFIED"
    )
    original_predictor_hash=sha256(reference/"app/services/predictor.py")
    mlb_full_predictor_verified=bool(
        elo_verified and original_predictor_hash and
        elo_audit.get("mlb_original_predictor_sha256")==original_predictor_hash and
        elo_audit.get("same_input_full_prediction_objects_equal") ==
          elo_audit.get("historical_mlb_final_games_checked") and
        elo_audit.get("predictions_are_historical_equality_tests_not_pregame_bets") is True
    )
    checked = model.get("verified_formula_parity_models")
    target_count = model.get("total_target_models")
    if not (type(checked) is int and type(target_count) is int and
            0 <= checked <= target_count):
        raise ValueError("Unreliable formula equality test counts")
    source_front = reference / FRONTEND_SOURCE
    target_front = target / "docs/index.html"
    src_hash, dst_hash = sha256(source_front), sha256(target_front)
    source_dom = static_dom(reference, (FRONTEND_SOURCE,))
    target_htmls = tuple(sorted(str(p.relative_to(target)) for p in
                                (target / 'docs').glob('*.html')))
    target_dom = static_dom(target, target_htmls)
    source_missing = sorted(source_dom.ids - target_dom.ids)
    source_web = (reference / "docs/index.html")
    products = [{
        "original": relative,
        "reference_file_exists": (reference / relative).is_file(),
        "reference_size_bytes": (reference / relative).stat().st_size
            if (reference / relative).is_file() else None,
        "identical_path_in_revue": (target / relative).is_file(),
        "identical_bytes_confirmed": (
            sha256(reference / relative) == sha256(target / relative))
            if (reference / relative).is_file() and (target / relative).is_file()
            else False,
        "equivalent_semantic_content": "unverified",
    } for relative in STATIC_PRODUCTS]
    license_candidates = (
        "LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.md",
    )
    license_found = next(
        (rel for rel in license_candidates if (reference / rel).is_file()),
        None,
    )
    # A static GitHub Pages site is not an HTTP JSON backend. Revue may have
    # working export files but this is not equivalent to the FastAPI route.
    all_routes = [
        {**route, "target_parity": "not_implemented_as_equivalent_http_api"}
        for route in routes
    ]
    return {
        "generated_at_utc": generated.astimezone(timezone.utc).isoformat(),
        "source_repository": EXPECTED_SOURCE,
        "target_repository": TARGET,
        "source_commit": current_sha,
        "source_revision_status": revision_status,
        "scope": "exact end-to-end application behaviour (CFB intentionally excluded)",
        "goal": "100% verified equality of interface, backend, data features, calculations, and outputs on identical time-stamped inputs",
        "exact_reproduction_percent": None,
        "exact_end_to_end_parity": "NOT_VERIFIED",
        "functional_coverage_percent_is_not_reproduction": True,
        "original_license_file": license_found,
        "wholesale_source_redistribution_authorized": False,
        "copyright_note": "No license located is not permission. Reimplement independently or obtain explicit authorization.",
        "frontend": {
            "reference_path": FRONTEND_SOURCE,
            "reference_size_bytes": source_front.stat().st_size,
            "reference_sha256": src_hash,
            "reference_index_and_app_same_bytes":
                sha256(source_web) == src_hash,
            "target_path": "docs/index.html",
            "target_size_bytes": target_front.stat().st_size,
            "target_sha256": dst_hash,
            "identical_html": src_hash == dst_hash,
            "pixel_accurate_visual_comparison": "NOT_PERFORMED",
            "interactive_behaviour_parity": "NOT_VERIFIED",
            "static_dom_inventory": {
                "source_static_ids": len(source_dom.ids),
                "target_static_ids_all_pages": len(target_dom.ids),
                "same_static_ids": len(source_dom.ids & target_dom.ids),
                "original_static_ids_not_present_in_revue": len(source_missing),
                "first_unmatched_source_ids": source_missing[:45],
                "measurement_limits": "Only static HTML IDs, across all Revue HTML pages. Dynamic JS content, page design, layout, and behavior are NOT verified.",
            },
        },
        "backend": {
            "source_routes": all_routes,
            "source_route_count": len(all_routes),
            "source_signatures_declared_in_revue": len(matching_routes),
            "declared_matching_signatures": matching_routes,
            "declared_but_unverified_not_full_parity": True,
            "serving_api_host": "https://revue-api-tawny.vercel.app",
            "end_to_end_verified_equivalent_routes": 0,
            "status": "FastAPI + database behaviour not replicated as equivalent server API",
        },
        "model_formulas": {
            "verified_in_declared_subset": checked,
            "declared_subset_total": target_count,
            "reference_commit_of_verification":
                model.get("original_source_commit"),
            "verification_is_on_current_source_commit":
                bool(current_sha and
                     model.get("original_source_commit") == current_sha),
            "current_real_game_same_input_outputs_equal":
                "VERIFIED_ON_REVUE_INPUTS_ONLY" if validated_real else "NOT_VERIFIED",
            "current_nhl_real_fixtures_tested": real["real_nhl_fixtures_compared"] if validated_real else 0,
            "current_nhl_full_output_dicts_equal": real["reference_vs_revue_entire_output_dict_equal"] if validated_real else 0,
            "original_proprietary_input_identity_verified": False,
            "all_original_models_catalogued": False,
        },
        "mlb_elo_source_replay": {
            "source_formula_unchanged_since_test":elo_verified,
            "replayed_espn_final_games":elo_audit["historical_mlb_final_games_checked"] if elo_verified else 0,
            "exact_update_results":elo_audit["exact_update_equal_to_original"] if elo_verified else 0,
            "historical_same_input_full_predictor_outputs_equal":elo_audit["same_input_full_prediction_objects_equal"] if mlb_full_predictor_verified else 0,
            "historical_full_predictor_evidence_current":mlb_full_predictor_verified,
            "these_were_not_prospective_locked_predictions":True,
            "mlb_teams_in_history":elo_audit.get("teams",0) if elo_verified else 0,
            "original_database_elo_ratings_equal":False,
            "original_complete_training_history_equal":False,
            "evidence_file":"docs/parite-elo-mlb-source.json",
            "note":"Exact original Elo arithmetic on Revue history, not original SQL values, source data, or betting model parity.",
        },
        "nhl_fixture_identity": {
            "verified_source_revision": bool(id_map.get("source_commit")==current_sha and id_pairs_current),
            "verified_against_current_source_schedule": id_pairs_current,
            "source_espn_id_matches": id_map.get("matched",0) if id_pairs_current else 0,
            "mapping_created_from_source_commit": id_map.get("source_commit"),
            "revue_id_pairs_exact_team_and_utc": id_pairs_current,
            "all_source_data_equal": False,
            "original_goalie_odds_or_roster_equal": False,
            "description": "NHL vs ESPN factual match identifiers only; not whole model or provider input parity.",
        },
        "http_response_schema_field_parity": response_schemas,
        "static_data_contracts": {
            "declared_subset_count": len(products),
            "byte_identical_products": sum(x["identical_bytes_confirmed"] for x in products),
            "same_real_input_semantic_parity": "NOT_VERIFIED",
            "items": products,
        },
        "prior_test_evidence": evidence,
        "critical_blockers": [
            "No matching original frontend interaction/pixel rendering evidence",
            "Source FastAPI routes, database writes and security behaviour not reproduced as exact API",
            "Original data and injury/lineup provider snapshots not proven identical and temporally matched",
            "Real matches have not been tested with same model inputs, market rules and output probabilities",
            "Third-party datasets such as Opta may be subject to separate redistribution restrictions",
        ],
        "note": "Function-level exact checks are valuable but cannot be added to functional estimates or used as a full-app reproduction percentage.",
    }


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--source", type=Path, required=True)
    cli.add_argument("--target", type=Path, default=Path("."))
    cli.add_argument("--output", type=Path, default=Path("docs/reproduction-exacte-audit.json"))
    args = cli.parse_args()
    report = strict_report(
        args.source.resolve(), args.target.resolve(), datetime.now(timezone.utc)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.is_file():
        try:
            previous = json.loads(args.output.read_text(encoding="utf-8"))
            check_new = {k: v for k, v in report.items() if k != "generated_at_utc"}
            check_old = {k: v for k, v in previous.items() if k != "generated_at_utc"}
            if check_new == check_old:
                # No meaningful changes: avoid a daily commit for the clock.
                report["generated_at_utc"] = previous["generated_at_utc"]
        except (ValueError, KeyError, TypeError):
            pass
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Reproduction exacte:", report["exact_end_to_end_parity"],
          "source API", report["backend"]["source_route_count"],
          "routes, Revue equivalent", report["backend"]["end_to_end_verified_equivalent_routes"],
          "historical formula", report["model_formulas"]["verified_in_declared_subset"],
          "of", report["model_formulas"]["declared_subset_total"])


if __name__ == "__main__":
    main()
