"""Validation élémentaire de cotations avant calcul d'EV (implémentation Revue).

Ne vérifie pas que le fournisseur donne réellement accès au prix.
Aucune dépendance et aucun code importé de dépôt tiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite


PROVENANCES_OBSERVEES = frozenset(
    {"api_bookmaker", "agregateur_autorise", "capture_verifiee"}
)


@dataclass(frozen=True)
class Cotation:
    bookmaker: str
    marche: str
    selection: str
    cote_decimale: float
    observee_le: datetime
    debut_evenement: datetime
    provenance: str
    identifiant_source: str


def _horodatage_valide(value: datetime) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def valider_cotation(cotation: Cotation) -> None:
    """Refuse les probabilités transformées en pseudo-cotes et prix inutilisables."""
    if cotation.provenance not in PROVENANCES_OBSERVEES:
        raise ValueError("Cote non observée ou provenance non autorisée")
    for champ in (
        cotation.bookmaker,
        cotation.marche,
        cotation.selection,
        cotation.identifiant_source,
    ):
        if not isinstance(champ, str) or not champ.strip():
            raise ValueError("Bookmaker, marché, sélection et source sont obligatoires")
    if not isfinite(cotation.cote_decimale) or cotation.cote_decimale <= 1:
        raise ValueError("La cote décimale doit être un nombre fini supérieur à 1")
    if not _horodatage_valide(cotation.observee_le):
        raise ValueError("La date de cotation doit avoir un fuseau horaire")
    if not _horodatage_valide(cotation.debut_evenement):
        raise ValueError("Le début de match doit avoir un fuseau horaire")
    if cotation.observee_le >= cotation.debut_evenement:
        raise ValueError("Cote recueillie après le début de l'événement")


def esperance_de_gain(probabilite: float, cotation: Cotation) -> float:
    """EV unitaire nette à une cote décimale externe : p * cote - 1."""
    valider_cotation(cotation)
    try:
        p = float(probabilite)
    except (TypeError, ValueError) as exc:
        raise ValueError("Probabilité non numérique") from exc
    if not isfinite(p) or not 0 <= p <= 1:
        raise ValueError("La probabilité doit être comprise entre 0 et 1")
    return p * cotation.cote_decimale - 1.0
