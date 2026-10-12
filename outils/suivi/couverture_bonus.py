"""Conversion des bonus d'opérateurs français (freebets, paris remboursés) — implémentation originale Revue.

Seules stratégies à gain mathématiquement garanti repérées dans les 66 dépôts audités
(méthode REV-PRETR-01, réécrite) : on ne prédit rien, on couvre TOUTES les issues d'un
marché chez des opérateurs agréés, à des cotes observées au même instant.

Calculs sur le tableau de cotes de Revue (``docs/engine-v2-latest.json``), avec les règles de
sécurité de ``outils/controles/controle_couverture_cotes.py`` (qui traite déjà les surebets) :
football seulement, règlement à 90 minutes, match à plus de 20 minutes, cotes de moins de 70 minutes.
Les autres sports sont exclus tant que l'égalité des règles de prolongation entre opérateurs
n'est pas établie.

- **surebet** (calcul de contrôle) : Σ 1/meilleure cote < 1 ;
- **freebet** (mise non rendue) : freebet F sur l'issue i chez l'opérateur du bonus, couverture
  en argent réel des autres issues j : mise_j = F (o_i − 1) / o_j ; gain garanti
  F (o_i − 1)(1 − Σ_{j≠i} 1/o_j) ;
- **1er pari remboursé en freebet** : mise S sur i ; si i perd, freebet S valorisé c (taux de
  conversion espéré, hypothèse) ; mise_j = S (o_i − c) / o_j ; gain égalisé
  S (o_i − 1) − S (o_i − c) Σ_{j≠i} 1/o_j. Par défaut c = 0,6 : taux de conversion des
  freebets mesuré sur les cotes françaises observées par Revue (0,56 à 0,62 le 12/10/2026).

Limites : les cotes bougent (refaire le calcul juste avant de miser), un opérateur peut
refuser ou limiter une mise, les conditions des offres (cote minimale, délai, montant) doivent
être lues sur le site de l'opérateur. Aucun pari n'est placé par Revue.

Exemple : ``python -m outils.suivi.couverture_bonus --freebet 10 --operateur winamax_fr``
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from outils.controles.controle_couverture_cotes import MAX_AGE, MIN_START, SOCCER

ECART_MAX_SECONDES = 900   # toutes les cotes d'une couverture doivent dater du même quart d'heure
ARRONDI = 0.1              # mises arrondies à 10 centimes


def _instant(texte: str) -> datetime:
    return datetime.fromisoformat(texte.replace("Z", "+00:00"))


def marches(tableau: dict, maintenant: datetime | None = None) -> list[dict]:
    """Regroupe les cotes par (match, marché, ligne) : football, 90 minutes, match pas trop proche."""
    maintenant = maintenant or datetime.now(timezone.utc)
    sortie = []
    for ev in tableau.get("odds_board", {}).get("events", []):
        try:
            debut = _instant(ev["start_utc"])
        except (KeyError, TypeError, ValueError):
            continue
        if ev.get("league") not in SOCCER or debut - maintenant < MIN_START:
            continue
        groupes: dict[tuple, dict] = {}
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk.get("period_rule") != "90min":
                    continue
                for oc in mk.get("outcomes", []):
                    cle = (mk.get("market"), mk.get("period_rule"), oc.get("line"))
                    g = groupes.setdefault(cle, {"cotes": {}, "operateurs_par_issue": {}})
                    prix = oc.get("price")
                    if not isinstance(prix, (int, float)) or prix <= 1:
                        continue
                    g["cotes"].setdefault(oc["selection"], []).append(
                        {"operateur": bk["bookmaker"], "cote": float(prix), "quote_at": mk.get("quote_at")})
        for (marche, periode, ligne), g in groupes.items():
            issues = set(g["cotes"])
            attendues = {"h2h": [{"home", "draw", "away"}], "totals": [{"over", "under"}]}
            if not any(issues == a for a in attendues.get(marche, [])):
                continue
            sortie.append({"ligue": ev.get("league"), "match": f"{ev.get('home')} – {ev.get('away')}",
                           "debut_utc": ev.get("start_utc"), "marche": marche, "periode": periode,
                           "ligne": ligne, "cotes": g["cotes"]})
    return sortie


def _meilleure(cotes: list[dict], exclure: str | None = None, autour: dict | None = None) -> dict | None:
    """Meilleure cote, hors ``exclure``, et contemporaine de la cote ``autour`` si fournie."""
    candidats = [c for c in cotes if c["operateur"] != exclure] if exclure else cotes
    if autour is not None:
        candidats = [c for c in candidats if _coherent([autour, c])]
    return max(candidats, key=lambda c: c["cote"]) if candidats else None


def _coherent(cotes: list[dict]) -> bool:
    instants = [_instant(c["quote_at"]) for c in cotes if c.get("quote_at")]
    return len(instants) == len(cotes) and (max(instants) - min(instants)).total_seconds() <= ECART_MAX_SECONDES


def _arrondi(x: float) -> float:
    return round(round(x / ARRONDI) * ARRONDI, 2)


def _resultats(mises: dict[str, dict], gains_issue: dict[str, float], engage: float) -> dict:
    """Bénéfice net exact par issue après arrondi des mises."""
    nets = {i: round(gains_issue[i] - engage, 2) for i in gains_issue}
    return {"mises": mises, "argent_engage": round(engage, 2), "benefice_par_issue": nets,
            "benefice_garanti": min(nets.values())}


def surebet(m: dict, budget: float = 100.0) -> dict | None:
    meilleures = {i: _meilleure(c) for i, c in m["cotes"].items()}
    somme = sum(1 / b["cote"] for b in meilleures.values())
    if somme >= 1 or not _coherent(list(meilleures.values())):
        return None
    retour = budget / somme
    mises = {i: {**b, "mise": _arrondi(retour / b["cote"])} for i, b in meilleures.items()}
    engage = sum(x["mise"] for x in mises.values())
    plan = _resultats(mises, {i: x["mise"] * x["cote"] for i, x in mises.items()}, engage)
    return {**_entete(m), "type": "surebet", "rendement": round(1 / somme - 1, 4), **plan}


def freebet(m: dict, operateur: str, montant: float, cote_min: float = 1.0) -> dict | None:
    """Meilleure issue pour jouer un freebet (mise non rendue) chez ``operateur``."""
    meilleur = None
    for i, cotes in m["cotes"].items():
        fb = next((c for c in cotes if c["operateur"] == operateur), None)
        if not fb or fb["cote"] < cote_min:
            continue
        couverture = {j: _meilleure(c, autour=fb) for j, c in m["cotes"].items() if j != i}
        if any(v is None for v in couverture.values()) or not _coherent([fb, *couverture.values()]):
            continue
        taux = (fb["cote"] - 1) * (1 - sum(1 / b["cote"] for b in couverture.values()))
        if meilleur is None or taux > meilleur[0]:
            meilleur = (taux, i, fb, couverture)
    if meilleur is None:
        return None
    taux, i, fb, couverture = meilleur
    mises = {i: {**fb, "mise": montant, "nature": "freebet"}}
    mises.update({j: {**b, "mise": _arrondi(montant * (fb["cote"] - 1) / b["cote"]), "nature": "argent"}
                  for j, b in couverture.items()})
    engage = sum(x["mise"] for j, x in mises.items() if j != i)
    gains = {j: (montant * (fb["cote"] - 1) if j == i else x["mise"] * x["cote"]) for j, x in mises.items()}
    return {**_entete(m), "type": "freebet", "operateur_bonus": operateur, "montant_bonus": montant,
            "taux_conversion": round(taux, 4), **_resultats(mises, gains, engage)}


def pari_rembourse(m: dict, operateur: str, montant: float, conversion: float = 0.6,
                   cote_min: float = 1.0) -> dict | None:
    """« 1er pari remboursé en freebet si perdant » chez ``operateur``, couvert ailleurs."""
    meilleur = None
    for i, cotes in m["cotes"].items():
        pr = next((c for c in cotes if c["operateur"] == operateur), None)
        if not pr or pr["cote"] < cote_min:
            continue
        couverture = {j: _meilleure(c, exclure=operateur, autour=pr) for j, c in m["cotes"].items() if j != i}
        if any(v is None for v in couverture.values()) or not _coherent([pr, *couverture.values()]):
            continue
        taux = pr["cote"] - 1 - (pr["cote"] - conversion) * sum(1 / b["cote"] for b in couverture.values())
        if meilleur is None or taux > meilleur[0]:
            meilleur = (taux, i, pr, couverture)
    if meilleur is None:
        return None
    taux, i, pr, couverture = meilleur
    mises = {i: {**pr, "mise": montant, "nature": "argent, remboursé en freebet si perdant"}}
    mises.update({j: {**b, "mise": _arrondi(montant * (pr["cote"] - conversion) / b["cote"]), "nature": "argent"}
                  for j, b in couverture.items()})
    engage = sum(x["mise"] for x in mises.values())
    gains = {j: (montant * pr["cote"] if j == i else x["mise"] * x["cote"] + conversion * montant)
             for j, x in mises.items()}
    plan = _resultats(mises, gains, engage)
    plan["benefice_si_freebet_converti"] = plan.pop("benefice_garanti")
    sans_conversion = {j: round(gains[j] - engage - (0 if j == i else conversion * montant), 2) for j in gains}
    return {**_entete(m), "type": "pari_rembourse", "operateur_bonus": operateur, "montant_bonus": montant,
            "hypothese_conversion_freebet": conversion, "taux": round(taux, 4), **plan,
            "perte_maximale_avant_conversion_du_freebet": min(sans_conversion.values())}


def _entete(m: dict) -> dict:
    return {k: m[k] for k in ("ligue", "match", "debut_utc", "marche", "periode", "ligne")}


def rapport(tableau: dict, freebet_montant: float = 10.0, rembourse_montant: float = 100.0,
            conversion: float = 0.6, cote_min: float = 1.0, top: int = 3,
            maintenant: datetime | None = None) -> dict:
    maintenant = maintenant or datetime.now(timezone.utc)
    try:
        age = maintenant - _instant(tableau["generated_at_utc"])
    except (KeyError, TypeError, ValueError):
        age = None
    perime = age is None or age > MAX_AGE
    ms = [] if perime else marches(tableau, maintenant)
    operateurs = sorted({c["operateur"] for m in ms for cotes in m["cotes"].values() for c in cotes})
    par_operateur = {}
    for op in operateurs:
        fb = [p for m in ms if (p := freebet(m, op, freebet_montant, cote_min))]
        pr = [p for m in ms if (p := pari_rembourse(m, op, rembourse_montant, conversion, cote_min))]
        par_operateur[op] = {
            "freebet": sorted(fb, key=lambda p: -p["benefice_garanti"])[:top],
            "pari_rembourse": sorted(pr, key=lambda p: -p["benefice_si_freebet_converti"])[:top],
        }
    surebets = sorted((p for m in ms if (p := surebet(m))), key=lambda p: -p["rendement"])
    return {
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_cotes": {"fichier": "docs/engine-v2-latest.json", "genere_le": tableau.get("generated_at_utc"),
                         "statut": tableau.get("odds_status"),
                         "utilisable": not perime,
                         "motif": "cotes de plus de 70 minutes : recalcul impossible sans nouvelles cotes" if perime else None},
        "perimetre": "football, 1N2 et +/- à 90 minutes, matchs commençant dans plus de 20 minutes",
        "parametres": {"freebet": freebet_montant, "pari_rembourse": rembourse_montant,
                       "conversion_freebet_supposee": conversion, "cote_min": cote_min,
                       "ecart_max_entre_cotes_s": ECART_MAX_SECONDES},
        "marches_complets": len(ms), "operateurs": operateurs,
        "surebets": surebets, "par_operateur": par_operateur,
        "voir_aussi": "docs/couvertures-mathematiques.html (contrôle détaillé des surebets)",
        "avertissement": ("Recalculer juste avant de miser : les cotes bougent. Lire les conditions de chaque offre "
                          "(cote minimale, délai, montant). Un gain n'est garanti que si toutes les mises sont acceptées "
                          "aux cotes indiquées. Jeu réservé aux majeurs ; opérateurs agréés ANJ uniquement."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tableau", type=Path, default=Path("docs/engine-v2-latest.json"))
    parser.add_argument("--freebet", type=float, default=10.0, help="montant du freebet (mise non rendue)")
    parser.add_argument("--rembourse", type=float, default=100.0, help="mise d'un pari remboursé si perdant")
    parser.add_argument("--conversion", type=float, default=0.6, help="valeur espérée d'1 € de freebet")
    parser.add_argument("--cote-min", type=float, default=1.0)
    parser.add_argument("--operateur", help="n'afficher que cet opérateur (ex. winamax_fr)")
    parser.add_argument("--sortie", type=Path)
    args = parser.parse_args()
    r = rapport(json.loads(args.tableau.read_text(encoding="utf-8")), args.freebet, args.rembourse,
                args.conversion, args.cote_min)
    if args.operateur:
        r["par_operateur"] = {k: v for k, v in r["par_operateur"].items() if k == args.operateur}
    texte = json.dumps(r, indent=1, ensure_ascii=False)
    if args.sortie:
        args.sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
