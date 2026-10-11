#!/usr/bin/env python3
"""Inventaires générés du dépôt Revue : jeux de données publiés et outils.

Écrit deux fichiers à partir de l'état réel du dépôt (aucun appel réseau) :
- catalogue/DONNEES.md : chaque docs/*.json, son thème, le workflow qui le
  publie, le script qui le produit et sa date de génération ;
- outils/README.md : chaque script de outils/<groupe>/ avec la première
  phrase de sa docstring.

Usage : python -m outils.controles.inventaire_depot
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

GROUPS = {
    "clairvoyance": ("Reproduction et audit de Clairvoyance",
                     "Comparaisons exactes avec le code source original (checkout temporaire en lecture "
                     "seule), audits de ses données, de ses sorties et de sa rentabilité affichée."),
    "collecte": ("Collecte de données",
                 "Acquisition des données externes : MoneyPuck, API NHL, ESPN, MLB Stats, PulseScore, "
                 "cotes FR. Sondes de structure des API."),
    "suivi": ("Suivi prospectif, règlement et évaluation",
              "Prévisions figées avant match, règlement sur scores officiels, journal papier, "
              "Brier / log-loss / CLV, backtests chronologiques."),
    "controles": ("Contrôles qualité",
                  "Validation des cotes, de la chronologie, du retrait de marge, de l'intégrité des "
                  "sources et portes d'acceptation."),
    "publication": ("Publication du site",
                    "Construction des écrans GitHub Pages (Match Center, Picks, dossiers, export)."),
}

# Thèmes des jeux de données, testés dans l'ordre (premier motif trouvé).
THEMES = (
    ("Reproduction Clairvoyance (parité, audits)", r"^(parite-|clairvoyance-|reproduction-|phase1-|phase4-|phase6-)"),
    ("NHL", r"^(nhl-|moneypuck)"),
    ("Football", r"^football-"),
    ("NBA / MLB", r"^(nba-|mlb-)"),
    ("Hockey européen", r"^euro-hockey"),
    ("Sports individuels", r"^individual-"),
    ("Cotes et journal papier", r"^(engine-v2|pulsescore|paper-|revue-crossbook|revue-control|picks-center|phase7-)"),
    ("Modèles multisports et évaluation", r"^(multisport|ensemble-|equipes-|backtests-|phase2-|phase10-|phase12-|phase13-|revue-model|scoreboard-)"),
    ("Écrans et dossiers de match", r"^(match-|arcade-)"),
    ("État du dépôt et recette", r"."),
)


def first_sentence(text: str) -> str:
    text = " ".join((text or "").split())
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    out = match.group(1) if match else text
    return out if len(out) <= 160 else out[:157].rstrip() + "…"


def docstring(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        try:
            return first_sentence(ast.get_docstring(ast.parse(source)) or "")
        except SyntaxError:
            return ""
    match = re.search(r"/\*\*?(.*?)\*/", source, re.S)
    if not match:
        return ""
    return first_sentence(re.sub(r"^\s*\*\s?", "", match.group(1), flags=re.M))


def tool_rows(root: Path) -> dict[str, list[tuple[str, str]]]:
    rows: dict[str, list[tuple[str, str]]] = {}
    for group in GROUPS:
        folder = root / "outils" / group
        rows[group] = [(p.name, docstring(p)) for p in sorted(folder.glob("*"))
                       if p.suffix in (".py", ".js")]
    return rows


def stray_tools(root: Path) -> list[str]:
    """Scripts posés à la racine de outils/ ou dans un groupe inconnu."""
    out = []
    for p in sorted((root / "outils").rglob("*")):
        if p.suffix not in (".py", ".js") or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(root / "outils").parts
        if len(rel) != 2 or rel[0] not in GROUPS:
            out.append(str(p.relative_to(root)))
    return out


def render_tools(root: Path) -> str:
    rows = tool_rows(root)
    lines = [
        "# Outils Revue",
        "",
        "<!-- Fichier généré par `python -m outils.controles.inventaire_depot` : ne pas éditer à la main. -->",
        "",
        "Scripts **écrits pour Revue** (aucun code tiers recopié), rangés par fonction. "
        "Chaque script se lance depuis la racine du dépôt : `python -m outils.<groupe>.<script>` "
        "ou `node outils/<groupe>/<script>.js`. Les tests sont dans [`tests/`](../tests).",
        "",
        "| Groupe | Rôle | Scripts |",
        "|---|---|---:|",
    ]
    for group, (title, _) in GROUPS.items():
        lines.append(f"| [`{group}/`](#{group}) | {title} | {len(rows[group])} |")
    for group, (title, intro) in GROUPS.items():
        lines += ["", f"## {group}", "", f"**{title}.** {intro}", ""]
        docs = sorted(p.name for p in (root / "outils" / group).glob("*.md"))
        if docs:
            lines.append("Documentation : " + " · ".join(f"[{d}]({group}/{d})" for d in docs))
            lines.append("")
        lines += ["| Script | Objet |", "|---|---|"]
        for name, text in rows[group]:
            lines.append(f"| [{name}]({group}/{name}) | {text.replace('|', '/') or '—'} |")
    lines += [
        "",
        "## Limites",
        "",
        "Ces outils contrôlent des formats, des chronologies et des calculs. Ils ne prouvent ni "
        "l'authenticité d'une source, ni la légalité ANJ d'un marché, ni la rentabilité d'un pari.",
        "",
    ]
    return "\n".join(lines)


def theme(name: str) -> str:
    for label, pattern in THEMES:
        if re.search(pattern, name):
            return label
    return THEMES[-1][0]


def producers(root: Path) -> tuple[dict[str, set], dict[str, set]]:
    """Fichier docs/x.json -> workflows qui le publient / scripts qui le citent."""
    workflows: dict[str, set] = {}
    scripts: dict[str, set] = {}
    for wf in sorted((root / ".github" / "workflows").glob("*.yml")):
        for name in set(re.findall(r"docs/([\w.-]+\.json)", wf.read_text(encoding="utf-8"))):
            workflows.setdefault(name, set()).add(wf.name)
    for folder in ("outils", "modeles", "api_revue"):
        for p in (root / folder).rglob("*"):
            if p.suffix not in (".py", ".js") or "__pycache__" in p.parts:
                continue
            for name in set(re.findall(r"([\w.-]+\.json)", p.read_text(encoding="utf-8"))):
                scripts.setdefault(name, set()).add(str(p.relative_to(root)))
    return workflows, scripts


def stamp(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "illisible"
    if isinstance(data, dict):
        for key in ("generated_at_utc", "updated_at_utc", "generated_at", "generated", "as_of"):
            if isinstance(data.get(key), str):
                return data[key][:16].replace("T", " ")
    return "—"


def render_data(root: Path) -> str:
    workflows, scripts = producers(root)
    files = sorted((root / "docs").glob("*.json"))
    by_theme: dict[str, list[Path]] = {}
    for f in files:
        by_theme.setdefault(theme(f.name), []).append(f)
    lines = [
        "# Données de Revue",
        "",
        "<!-- Fichier généré par `python -m outils.controles.inventaire_depot` : ne pas éditer à la main. -->",
        "",
        "## Où sont les données ?",
        "",
        "Toutes les données publiées sont des fichiers JSON dans [`docs/`](../docs). Ce dossier est "
        "**aussi la racine du site GitHub Pages**, et les workflows y écrivent directement. "
        "Ne pas les déplacer : les pages, l'API (`api_revue/`) et les robots en dépendent.",
        "",
        "- **Instantanés** (`*-latest.json`) : remplacés à chaque exécution.",
        "- **Registres** (`*-ledger.json`, `*-history.json`) : historiques en ajout seul ; une "
        "prévision figée n'est jamais réécrite.",
        "- **Rapports** (`parite-*`, `*-audit*`, `*-performance.json`) : résultats de vérification "
        "et métriques recalculés.",
        "",
        "## Règles pour une nouvelle source de données",
        "",
        "Documenter : propriétaire, URL, licence/CGU, autorisation d'extraction, sports et marchés, "
        "fraîcheur, quota et prix, schéma, fuseau horaire, limites, politique d'archivage. "
        "**Aucune clé API, aucun jeton ni donnée personnelle dans Git** : les secrets restent dans "
        "les secrets GitHub Actions. Les jeux de données sous licence (Opta, etc.) ne sont jamais publiés.",
        "",
        "## Sources externes utilisées",
        "",
        "| Source | Usage | Outils |",
        "|---|---|---|",
        "| API officielle NHL (api-web.nhle.com) | Calendrier, scores, statistiques | `outils/collecte/nhl_official_stats_revue.py`, `outils/collecte/scoreboard_revue.py` |",
        "| MoneyPuck (téléchargements CSV, usage non commercial) | xG équipes et gardiens NHL | `outils/collecte/moneypuck_feed.py`, `outils/collecte/moneypuck_goalies_feed.py` |",
        "| ESPN (API publiques site.api.espn.com) | Scores, gardiens probables, stats NBA/football | `outils/collecte/nhl_espn_goalies.py`, `outils/collecte/probe_*.py` |",
        "| MLB Stats API | Lanceurs probables | `outils/collecte/mlb_official_pitchers.py` |",
        "| PulseScore / The Odds API (clé en secret) | Cotes de bookmakers FR observées | `outils/collecte/pulsescore_v2.py`, `outils/suivi/revue_engine_v2.py` |",
        "| Dépôt public Clairvoyance (lecture seule) | Comparaisons de parité, audits | `outils/clairvoyance/` |",
        "",
        f"## Inventaire ({len(files)} fichiers)",
        "",
    ]
    for label, _ in THEMES:
        group = by_theme.get(label)
        if not group:
            continue
        lines += [f"### {label}", "", "| Fichier | Généré | Ko | Publié par | Produit par |", "|---|---|---:|---|---|"]
        for f in group:
            wf = ", ".join(sorted(workflows.get(f.name, ()))) or "—"
            sc = ", ".join(f"`{s}`" for s in sorted(scripts.get(f.name, ()))[:3]) or "—"
            size = round(f.stat().st_size / 1024)
            lines.append(f"| [{f.name}](../docs/{f.name}) | {stamp(f)} | {size} | {wf} | {sc} |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root)
    stray = stray_tools(root)
    if stray:
        raise SystemExit("Scripts hors groupe dans outils/ : " + ", ".join(stray))
    (root / "outils" / "README.md").write_text(render_tools(root), encoding="utf-8")
    (root / "catalogue" / "DONNEES.md").write_text(render_data(root), encoding="utf-8")
    print("outils/README.md et catalogue/DONNEES.md regénérés")


if __name__ == "__main__":
    main()
