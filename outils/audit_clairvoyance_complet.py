#!/usr/bin/env python3
"""Static-only codebase inventory of public Clairvoyance source.

Does not execute, package, redistribute, or copy proprietary source content.
A separate GitHub Actions checkout is inspected locally then discarded.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess

AREAS={
    "football_opta":{
        "globs":["scripts/scrape_opta_stats.py","scripts/scrape_soccer*.py"],
        "our":["modeles/simulations/football_avance_independant.py","modeles/simulations/football_espn_statistiques.py"],
        "status":"partial_alternative_not_opta",
        "next":"Licensed xG/xGA/Power Rankings with validated temporal provenance"},
    "nhl_game_goalie":{
        "globs":["scripts/fetch_nhl.py","scripts/_nhl*.py","scripts/backtest_hockey_models.py","scripts/backtest_goalie_starter.py","app/scrapers/moneypuck.py"],
        "our":["modeles/simulations/nhl_independant.py","modeles/simulations/nhl_joueurs_independant.py"],
        "status":"partial_no_confirmed_goalies",
        "next":"Confirmed starters, verified data model and multi-season walk-forward"},
    "nba":{
        "globs":["scripts/fetch_nba.py","scripts/_nba*.py","scripts/test_nba*.py"],
        "our":["modeles/simulations/multisports_independant.py"],
        "status":"elo_only",
        "next":"Team pace, efficiencies and official player rotations"},
    "nfl_cfb":{
        "globs":["scripts/fetch_nfl.py","scripts/fetch_cfb.py","scripts/test_cfb*.py"],
        "our":["modeles/simulations/multisports_independant.py"],
        "status":"elo_only",
        "next":"Team schedules, opponents, injuries, QB confirmation, spreads"},
    "mlb":{
        "globs":["app/models/mlb_game.py","scripts/clairvoyance_update.py"],
        "our":["modeles/simulations/multisports_independant.py"],
        "status":"elo_only",
        "next":"Pitchers confirmed, bullpen, park adjusted runs"},
    "eu_hockey":{
        "globs":["scripts/fetch_liiga.py","scripts/fetch_shl.py","scripts/fetch_nla.py","scripts/fetch_extraliga.py","scripts/fetch_quanthockey.py"],
        "our":["modeles/simulations/sports_individuels_et_liiga.py"],
        "status":"liiga_only",
        "next":"Verified SHL, NL and Czech Extraliga official feed"},
    "odds_and_markets":{
        "globs":["scripts/_flashscore_odds.py","scripts/backtest_alt_lines.py","scripts/alt_line_scorecard.py"],
        "our":["outils/pulsescore_v2.py","outils/revue_engine_v2.py"],
        "status":"partial_fr_live",
        "next":"More supported market settlement semantics, consensus and price history"},
    "lock_settle":{
        "globs":["scripts/auto_lock_settle.py","scripts/lock_timing.py","scripts/settle_gate.py","scripts/live_tracker.py"],
        "our":["outils/revue_engine_v2.py","outils/suivi_football_avance.py"],
        "status":"paper_only_temporal",
        "next":"Verify all scoreboards, chronology and corrections for each market"},
    "historical_validation":{
        "globs":["scripts/backtest_*.py","scripts/audit_*.py","scripts/test_*.py"],
        "our":["outils/backtest_multisports.py","docs/backtests-multisports.json"],
        "status":"partial_small_samples",
        "next":"Prospective CLV, sport/market specific calibration, extended seasons"},
    "service_and_ops":{
        "globs":["scripts/daily_health_check.py","scripts/weekly_health_digest.py","scripts/_scraper_health.py",".github/workflows/*.yml"],
        "our":[".github/workflows/multisports-independent.yml",".github/workflows/revue-engine-v2.yml"],
        "status":"partial",
        "next":"Data freshness alerts, retry policies and monitoring"},
}
TECH={
    "league_sources":["espn","nhl","moneypuck","flashscore","theanalyst","opta",
                      "quanthockey","pulsescore","score","injur"],
    "model_methods":["elo","poisson","xg","xga","ppda","home","prior","blend",
                     "goalie","skater","pitcher","spread","moneyline"],
    "research":["backtest","calibrat","brier","logloss","simulate",
                "walk_forward","settle","lock","roi","clv"],
}

def inspect_frontend_model_symbols(root: Path) -> dict:
    """Inspect large inline frontend model without embedding any source code.

    We keep only declared JS function names and line positions. The public
    model actually runs in docs/app.html; Python-only audits miss it.
    """
    page=root/"docs/app.html"
    if not page.is_file():
        return {"status":"missing","named_function_count":0,"model_symbols":[]}
    source=page.read_text(encoding="utf-8",errors="replace")
    if not source:
        return {"status":"empty","named_function_count":0,"model_symbols":[]}
    names={}
    patterns=(
        r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?function\s*\(",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^\n]{0,160}?\)\s*=>",
    )
    flags=("nhl","nba","mlb","nfl","cfb","soccer","foot","hockey","goalie",
           "elo","poisson","bayes","ensemble","xg","predict","simulat",
           "backtest","calibr","injur","spread","market","margin",
           "model","prob","odds","prior","rate","line")
    for pattern in patterns:
        for hit in re.finditer(pattern,source):
            name=hit.group(1)
            names.setdefault(name,source.count("\n",0,hit.start())+1)
    found=[{"name":name,"line":line} for name,line in sorted(names.items(),
             key=lambda x:x[1])
             if any(k in name.lower() for k in flags)]
    return {
        "status":"read_only_symbol_index",
        "source":"docs/app.html",
        "source_bytes":len(source.encode("utf-8")),
        "named_function_count":len(names),
        "model_related_count":len(found),
        "model_symbols":found[:300],
        "symbols_truncated":len(found)>300,
        "note":"Function names only, no original JS source or model weights exported.",
    }


def root_relative(directory:Path,filepath:Path)->str:
    return filepath.relative_to(directory).as_posix()

def inventory(root:Path,project:Path|None=None,now:datetime|None=None)->dict:
    if not root.is_dir():raise ValueError("Source directory missing")
    files=sorted(x for x in root.rglob("*")
                 if x.is_file() and ".git" not in x.relative_to(root).parts)
    paths=[root_relative(root,p) for p in files]
    extensions=Counter(p.suffix.lower() or "[none]" for p in files)
    py=[p for p in files if p.suffix==".py"]
    parse_errors={}
    functions=[]
    imports=Counter()
    for f in py:
        path=root_relative(root,f)
        try:
            data=ast.parse(f.read_text(encoding="utf-8",errors="replace"),filename=path)
            funcs=[n for n in ast.walk(data)
                   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            functions.append({"path":path,"function_count":len(funcs),
                              "public_functions":[n.name for n in funcs
                                                  if not n.name.startswith("_")][:30]})
            for n in ast.walk(data):
                if isinstance(n,ast.Import):
                    for item in n.names:imports[item.name.split(".")[0]]+=1
                elif isinstance(n,ast.ImportFrom) and n.module:
                    imports[n.module.split(".")[0]]+=1
        except (SyntaxError,UnicodeError,OSError) as err:
            parse_errors[path]=type(err).__name__
    areas={}
    for key,config in AREAS.items():
        matched=sorted({p for pat in config["globs"]
                        for p in paths if __import__("fnmatch").fnmatch(p,pat)})
        checked={p:bool(project and (project/p).is_file())
                 for p in config["our"]}
        areas[key]={
            "original_files":matched[:120],
            "original_file_count":len(matched),
            "corresponding_revue_modules":checked,
            "current_status":config["status"],
            "remaining":config["next"],
        }
    try:
        sha=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],
                            capture_output=True,text=True,check=True,
                            timeout=3).stdout.strip()
    except Exception:
        sha=None
    now=now or datetime.now(timezone.utc)
    result={
        "generated_at_utc":now.isoformat(),
        "source":"Purple-Wraith/clairvoyance-backend",
        "source_commit_sha":sha,
        "policy":"Static inspection only. Source code not copied or executed.",
        "copyright":{"license_file_present":any(
            p.upper().split("/")[-1] in ("LICENSE","LICENSE.MD","COPYING","LICENSE.TXT")
            and "/" not in p for p in paths),
            "permission_to_redistribute_source":False},
        "counts":{
            "files":len(paths),"python_files":len(py),
            "html_js_files":sum(p.suffix.lower() in (".js",".html",".ts") for p in files),
            "workflows":sum(path.startswith(".github/workflows/") and path.endswith(".yml")
                            for path in paths),
            "python_functions":sum(x["function_count"] for x in functions),
            "python_parse_errors":len(parse_errors),
        },
        "frontend_model_symbols":inspect_frontend_model_symbols(root),
        "extensions":dict(extensions.most_common()),
        "source_areas":areas,
        "parsed_python_functions":functions,
        "python_parse_errors":parse_errors,
        "main_python_dependencies":[{"name":k,"import_sites":v}
                                    for k,v in imports.most_common(35)],
        "next_priority":[
            "Regulatory/market correctness and verification of outcome semantics",
            "NHL confirmed starters / rest / current-vs-prior without leakage",
            "Sports-specific efficiency models, shot data and lineups",
            "Odds history plus prospective closing line and calibration",
            "EU hockey feeds from official permitted sources",
            "Licensed xG source (Opta/The Analyst not copied)",
        ],
    }
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True)
    a.add_argument("--project",default=".")
    a.add_argument("--output",default="docs/clairvoyance-code-audit.json")
    args=a.parse_args()
    report=inventory(Path(args.source),Path(args.project))
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Audit static: source",report["source_commit_sha"],
          "files",report["counts"]["files"],
          "py",report["counts"]["python_files"],
          "functions",report["counts"]["python_functions"],
          "license",report["copyright"]["license_file_present"])
    print("Frontend model functions:",
          report["frontend_model_symbols"]["named_function_count"],
          "model-related:",report["frontend_model_symbols"].get("model_related_count",0))
    for k,v in report["source_areas"].items():
        print(f"  {k}: {v['original_file_count']} files; status={v['current_status']}")

if __name__=="__main__":
    main()
