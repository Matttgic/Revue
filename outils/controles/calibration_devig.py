"""Calibration des méthodes de retrait de marge sur des cotes historiques — implémentation originale Revue.

Question posée : sur un marché donné, quelle conversion « cotes → probabilités »
prédit le mieux les résultats réglés ? On compare, sur les MÊMES matchs, la
log-loss de chaque méthode à celle de la normalisation multiplicative, avec une
erreur-type de la différence appariée.

Ce n'est ni un modèle de pronostic ni un détecteur de value : une meilleure
conversion du prix d'un bookmaker ne crée aucun avantage contre ce bookmaker.
Le résultat dépend du sport, du marché, du bookmaker et de l'instant de collecte ;
il doit être recalculé sur la source de cotes réellement utilisée.

Entrées acceptées (fichiers téléchargés par l'utilisateur, jamais versionnés) :
- ``--xgabora Matches.csv`` : jeu Club-Football-Match-Data (cotes Bet365 1N2 et +/-2,5) ;
- ``--sbr dossier/`` : archives JSON sportsbookreview (moneylines américaines NHL/NBA/NFL/MLB).

Exemple : ``python -m outils.controles.calibration_devig --xgabora /tmp/Matches.csv``
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Callable, Iterable, Sequence

from outils.controles.sensibilite_devig import additive, multiplicative, puissance

MARGE_MAX = 0.15  # au-delà, la ligne est traitée comme une erreur de saisie


def _brutes(cotes: Sequence[float]) -> list[float]:
    return [1.0 / float(c) for c in cotes]


def _bissection(f: Callable[[float], float], bas: float, haut: float, iterations: int = 80) -> float:
    """Racine de f sur [bas, haut] ; f(bas) et f(haut) doivent être de signes opposés."""
    f_bas = f(bas)
    for _ in range(iterations):
        milieu = (bas + haut) / 2.0
        f_milieu = f(milieu)
        if (f_milieu > 0) == (f_bas > 0):
            bas, f_bas = milieu, f_milieu
        else:
            haut = milieu
    return (bas + haut) / 2.0


def shin(cotes: Sequence[float]) -> list[float]:
    """Méthode de Shin résolue par bissection sur z (proportion d'initiés).

    Valable pour 2 issues ou plus : la formule de point fixe de Jullien-Salanié
    divise par (n - 2) et ne s'applique donc pas aux marchés à deux issues.
    """
    q = _brutes(cotes)
    somme = sum(q)
    if somme <= 1.0:
        return [p / somme for p in q]

    def probas(z: float) -> list[float]:
        return [(math.sqrt(z * z + 4 * (1 - z) * p * p / somme) - z) / (2 * (1 - z)) for p in q]

    z = _bissection(lambda z: sum(probas(z)) - 1.0, 0.0, 0.5)
    sortie = probas(z)
    total = sum(sortie)
    return [p / total for p in sortie]


def rapport_de_cotes(cotes: Sequence[float]) -> list[float]:
    """Odds ratio (Cheung) : p = q / (c + q - c q), c choisi pour que la somme vaille 1."""
    q = _brutes(cotes)
    if sum(q) <= 1.0:
        return [p / sum(q) for p in q]

    def probas(c: float) -> list[float]:
        return [p / (c + p - c * p) for p in q]

    c = _bissection(lambda c: sum(probas(c)) - 1.0, 1.0, 10.0)
    sortie = probas(c)
    total = sum(sortie)
    return [p / total for p in sortie]


METHODES: dict[str, Callable[[Sequence[float]], list[float] | None]] = {
    "multiplicative": multiplicative,
    "additive": additive,
    "puissance": puissance,
    "shin": shin,
    "rapport_de_cotes": rapport_de_cotes,
}


def evaluer(lignes: Iterable[tuple[Sequence[float], int]]) -> dict:
    """Log-loss moyenne par méthode et différence appariée avec la méthode multiplicative.

    ``lignes`` : (cotes décimales de toutes les issues, indice de l'issue gagnante).
    Les lignes où une méthode échoue (ex. additive négative) sont exclues pour
    TOUTES les méthodes afin de garder une comparaison sur les mêmes matchs.
    """
    pertes: dict[str, list[float]] = {m: [] for m in METHODES}
    exclues = 0
    for cotes, gagnant in lignes:
        ligne = {}
        for nom, methode in METHODES.items():
            p = methode(cotes)
            if p is None:
                break
            ligne[nom] = -math.log(max(p[gagnant], 1e-12))
        if len(ligne) != len(METHODES):
            exclues += 1
            continue
        for nom, perte in ligne.items():
            pertes[nom].append(perte)
    n = len(pertes["multiplicative"])
    resultat = {"n": n, "lignes_exclues": exclues, "methodes": {}}
    if n < 2:
        return resultat
    base = pertes["multiplicative"]
    for nom, valeurs in pertes.items():
        diffs = [a - b for a, b in zip(valeurs, base)]
        moyenne = sum(diffs) / n
        variance = sum((d - moyenne) ** 2 for d in diffs) / (n - 1)
        resultat["methodes"][nom] = {
            "logloss": round(sum(valeurs) / n, 6),
            "diff_vs_multiplicative": round(moyenne, 6),
            "erreur_type": round(math.sqrt(variance / n), 6),
        }
    return resultat


def _marge_valide(cotes: Sequence[float]) -> bool:
    if any(not math.isfinite(c) or c <= 1.0 for c in cotes):
        return False
    somme = sum(1.0 / c for c in cotes)
    return 1.0 < somme < 1.0 + MARGE_MAX


def _flottant(valeur) -> float:
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return float("nan")


def lignes_xgabora(chemin: Path, marche: str) -> Iterable[tuple[list[float], int]]:
    """1N2 (``1n2``) ou +/-2,5 buts (``ou25``) à partir de Matches.csv."""
    with open(chemin, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if marche == "1n2":
                cotes = [_flottant(r["OddHome"]), _flottant(r["OddDraw"]), _flottant(r["OddAway"])]
                gagnant = {"H": 0, "D": 1, "A": 2}.get(r["FTResult"])
            else:
                cotes = [_flottant(r["Over25"]), _flottant(r["Under25"])]
                buts = _flottant(r["FTHome"]) + _flottant(r["FTAway"])
                gagnant = None if math.isnan(buts) else (0 if buts > 2.5 else 1)
            if gagnant is not None and _marge_valide(cotes):
                yield cotes, gagnant


def americaine_vers_decimale(cote: float) -> float:
    if cote > 0:
        return 1.0 + cote / 100.0
    if cote < 0:
        return 1.0 + 100.0 / abs(cote)
    return float("nan")


def lignes_sbr(chemin: Path, moment: str = "close") -> Iterable[tuple[list[float], int]]:
    """Moneyline domicile/extérieur d'une archive sportsbookreview ; nuls exclus."""
    for r in json.loads(Path(chemin).read_text(encoding="utf-8")):
        dom, ext = _flottant(r.get(f"home_{moment}_ml")), _flottant(r.get(f"away_{moment}_ml"))
        score_dom, score_ext = _flottant(r.get("home_final")), _flottant(r.get("away_final"))
        if any(math.isnan(v) for v in (dom, ext, score_dom, score_ext)) or score_dom == score_ext:
            continue
        cotes = [americaine_vers_decimale(dom), americaine_vers_decimale(ext)]
        if _marge_valide(cotes):
            yield cotes, (0 if score_dom > score_ext else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--xgabora", type=Path, help="Matches.csv de Club-Football-Match-Data")
    parser.add_argument("--sbr", type=Path, help="dossier contenant nhl.json, nba.json, ...")
    parser.add_argument("--sorties", type=Path, help="fichier JSON de résultats (facultatif)")
    args = parser.parse_args()
    resultats = {}
    if args.xgabora:
        for marche in ("1n2", "ou25"):
            resultats[f"xgabora_{marche}"] = evaluer(lignes_xgabora(args.xgabora, marche))
    if args.sbr:
        for fichier in sorted(args.sbr.glob("*.json")):
            resultats[f"sbr_{fichier.stem}_close"] = evaluer(lignes_sbr(fichier, "close"))
    texte = json.dumps(resultats, indent=1, ensure_ascii=False)
    if args.sorties:
        args.sorties.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
