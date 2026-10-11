"""Robustesse du retrait de marge — implémentation originale Revue.

Comparaison méthodologique sur un marché complet (2 issues ou 1N2).
N'est ni un modèle de pronostic ni un détecteur de paris gagnants.
"""

from __future__ import annotations

import math
from typing import Sequence


def _preparer(cotes: Sequence[float]) -> list[float]:
    """Transforme les cotes décimales en probabilités brutes."""
    try:
        valeurs = [float(c) for c in cotes]
    except (ValueError, TypeError) as exc:
        raise ValueError("Cotes non numériques") from exc
    if len(valeurs) not in (2, 3):
        raise ValueError("Fournir toutes les issues : 2 ou 3 cotes")
    if any(not math.isfinite(c) or c <= 1.0 for c in valeurs):
        raise ValueError("Toutes les cotes doivent être finies et > 1")
    return [1.0 / c for c in valeurs]


def _normaliser(probabilites: list[float]) -> list[float]:
    somme = sum(probabilites)
    if not somme or not math.isfinite(somme):
        raise ValueError("Probabilités invalides")
    return [p / somme for p in probabilites]


def multiplicative(cotes: Sequence[float]) -> list[float]:
    """Répartit proportionnellement la marge entre les issues."""
    return _normaliser(_preparer(cotes))


def additive(cotes: Sequence[float]) -> list[float] | None:
    """Retire la même marge absolue à chaque issue, si possible."""
    brutes = _preparer(cotes)
    correction = (sum(brutes) - 1.0) / len(brutes)
    ajustees = [p - correction for p in brutes]
    if any(p <= 0.0 or not math.isfinite(p) for p in ajustees):
        return None
    return _normaliser(ajustees)


def puissance(cotes: Sequence[float]) -> list[float]:
    """Cherche un exposant commun pour obtenir une somme proche de un."""
    brutes = _preparer(cotes)
    borne_basse, borne_haute = 0.0, 2.0
    while sum(p ** borne_haute for p in brutes) > 1.0:
        borne_haute *= 2.0
        if borne_haute > 16384:
            raise ValueError("Aucune racine stable trouvée")
    for _ in range(100):
        milieu = (borne_basse + borne_haute) / 2.0
        if sum(p ** milieu for p in brutes) > 1.0:
            borne_basse = milieu
        else:
            borne_haute = milieu
    exposant = (borne_basse + borne_haute) / 2.0
    return _normaliser([p ** exposant for p in brutes])


def comparer_methodes(cotes: Sequence[float]) -> dict:
    """Écart de probabilité entre trois hypothèses, en points de pourcentage.

    La dispersion indique une incertitude méthodologique, PAS un signal EV+.
    Les cotes doivent provenir du même bookmaker, même marché, même instant.
    """
    brutes = _preparer(cotes)
    sorties = {
        "multiplicative": multiplicative(cotes),
        "puissance": puissance(cotes),
    }
    add = additive(cotes)
    if add is not None:
        sorties["additive"] = add
    dispersion = []
    for i in range(len(brutes)):
        estimations = [p[i] for p in sorties.values()]
        dispersion.append(100.0 * (max(estimations) - min(estimations)))
    return {
        "nombre_issues": len(brutes),
        "marge_brute_pp": 100.0 * (sum(brutes) - 1.0),
        "probabilites": sorties,
        "dispersion_pp": dispersion,
        "note": "Ce ne sont pas des probabilités vérifiées hors échantillon.",
    }
