"""Contrôle chronologique original pour Revue — pré-match seulement.

N'authentifie ni un fournisseur de cotes, ni des statistiques, ni un opérateur.
Ne jamais convertir un timestamp absent en heure approximative.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

PRE_VALIDE = "pre_valide"
TARDIF = "tardif"
INDETERMINE = "indetermine"
COTE_NON_VERIFIABLE = "cote_non_verifiable"
FEATURE_NON_VERIFIABLE = "feature_non_verifiable"

ETATS = (
    PRE_VALIDE,
    TARDIF,
    INDETERMINE,
    COTE_NON_VERIFIABLE,
    FEATURE_NON_VERIFIABLE,
)


@dataclass(frozen=True)
class Decision:
    evenement_id: str
    verrouille_le: datetime | None
    debut_evenement: datetime | None
    cote_observee_le: datetime | None
    derniere_feature_publiee_le: datetime | None


def _date_verifiable(dt: datetime | None) -> bool:
    return (
        isinstance(dt, datetime)
        and dt.tzinfo is not None
        and dt.utcoffset() is not None
    )


def classifier(decision: Decision) -> str:
    """Retourne une catégorie pour l'audit pré-match, jamais une estimation."""
    if not _date_verifiable(decision.verrouille_le):
        return INDETERMINE
    if not _date_verifiable(decision.debut_evenement):
        return INDETERMINE

    lock = decision.verrouille_le
    kickoff = decision.debut_evenement
    if lock >= kickoff:
        return TARDIF

    if (
        not _date_verifiable(decision.cote_observee_le)
        or decision.cote_observee_le > lock
    ):
        return COTE_NON_VERIFIABLE

    if (
        not _date_verifiable(decision.derniere_feature_publiee_le)
        or decision.derniere_feature_publiee_le > lock
    ):
        return FEATURE_NON_VERIFIABLE

    return PRE_VALIDE


def bilan(decisions: Iterable[Decision]) -> dict[str, int]:
    """Compte tous les statuts, sans masquer les cas exclus du backtest."""
    comptes = Counter(classifier(d) for d in decisions)
    return {etat: comptes.get(etat, 0) for etat in ETATS}


def admissible_backtest(decision: Decision) -> bool:
    """Seule une décision intégralement vérifiable est retenue."""
    return classifier(decision) == PRE_VALIDE
