"""Banc d'essai NHL contre la cote de clôture — implémentation originale Revue.

Question : sur 2011-2021, les modèles NHL de Revue apportent-ils une information
que la cote d'ouverture n'a pas déjà, au point de battre la clôture ?

Construit avec les enseignements de la recherche GitHub du 12/10/2026 :
- données : archive moneyline ouverture/clôture NHL de FinnedAI/sportsbookreview-scraper
  (seule partie cohérente de l'archive), téléchargée à un commit épinglé, jamais versionnée ;
- chronologie : un match du jour d n'est prédit qu'avec les résultats des jours <= d - décalage ;
  le décalage 2 sert de contrôle car l'heure de publication de l'ouverture est inconnue ;
- classement dynamique (idée kickscore) en FILTRAGE seulement, jamais lissé avec le futur ;
- retrait de marge choisi sur les saisons d'entraînement (REV-IMPLIED-01) ;
- hyperparamètres, mélange modèle/marché et choix du modèle réglés sur 2011-2014 puis FIGÉS ;
  évaluation sur 2015-2021 ; seuil de pari fixé d'avance (EV > 3 %, comme sharp_ev_v1) ;
- verdict avec les seuils de la règle de décision Revue (volume, ROI, CLV, calibration).

Ce n'est pas un suivi en conditions réelles : bookmaker non identifié, heures
d'ouverture et de clôture non datées, données arrêtées en 2021.

Exemple : ``python -m outils.suivi.banc_nhl_cloture --sortie docs/banc-nhl-cloture.json``
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from modeles.simulations import nhl_independant as revue_nhl
from outils.controles.calibration_devig import METHODES, americaine_vers_decimale, evaluer
from outils.suivi.regle_decision import RULE, mean_ci

COMMIT = "1a820e50c6fbd0276cde073c22bfffae78930868"
URL = ("https://raw.githubusercontent.com/FinnedAI/sportsbookreview-scraper/"
       f"{COMMIT}/data/nhl_archive_10Y.json")
SAISONS_ENTRAINEMENT = range(2011, 2015)   # 2011-12 à 2014-15
SAISONS_TEST = range(2015, 2022)           # 2015-16 à 2021-22
SEUIL_EV = 0.03                            # fixé avant tout résultat, comme sharp_ev_v1
NOMS = {"Phoenix": "Coyotes", "Arizonas": "Coyotes", "NY Islanders": "Islanders",
        "Tampa": "Lightning", "Tampa Bay": "Lightning", "SeattleKraken": "Kraken",
        "WinnipegJets": "Jets", "St.Louis": "Blues"}


@dataclass(frozen=True)
class Match:
    jour: date
    saison: int
    dom: str
    ext: str
    buts_dom: int
    buts_ext: int
    ouverture: tuple[float, float]   # cotes décimales domicile, extérieur
    cloture: tuple[float, float]

    @property
    def victoire_dom(self) -> int:
        return 1 if self.buts_dom > self.buts_ext else 0


# --------------------------------------------------------------------------- données

def telecharger(cache: Path) -> list[dict]:
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=60) as r:
            cache.write_bytes(r.read())
    return json.loads(cache.read_text(encoding="utf-8"))


def _cotes(r: dict, moment: str) -> tuple[float, float] | None:
    try:
        cotes = (americaine_vers_decimale(float(r[f"home_{moment}_ml"])),
                 americaine_vers_decimale(float(r[f"away_{moment}_ml"])))
    except (KeyError, TypeError, ValueError):
        return None
    if any(not math.isfinite(c) or c <= 1 for c in cotes):
        return None
    somme = 1 / cotes[0] + 1 / cotes[1]
    return cotes if 1.0 < somme < 1.15 else None


def nettoyer(brut: list[dict]) -> tuple[list[Match], dict]:
    """Normalise les noms, écarte lignes vides, nuls, cotes incohérentes et doublons."""
    matchs, vus, exclus = [], set(), defaultdict(int)
    for r in brut:
        dom, ext = r.get("home_team"), r.get("away_team")
        if not isinstance(dom, str) or not isinstance(ext, str):
            exclus["equipe_absente"] += 1
            continue
        dom, ext = NOMS.get(dom, dom), NOMS.get(ext, ext)
        try:
            bd, be = int(r["home_final"]), int(r["away_final"])
            jour = datetime.strptime(str(int(float(r["date"]))), "%Y%m%d").date()
            saison = int(r["season"])
        except (KeyError, TypeError, ValueError):
            exclus["score_ou_date_invalide"] += 1
            continue
        if bd == be:
            exclus["nul"] += 1
            continue
        ouv, clo = _cotes(r, "open"), _cotes(r, "close")
        if ouv is None or clo is None:
            exclus["cotes_incoherentes"] += 1
            continue
        cle = (jour, dom, ext)
        if cle in vus:
            exclus["doublon"] += 1
            continue
        vus.add(cle)
        matchs.append(Match(jour, saison, dom, ext, bd, be, ouv, clo))
    matchs.sort(key=lambda m: (m.jour, m.dom))
    return matchs, dict(exclus)


# --------------------------------------------------------------------------- marché

def choisir_devig(matchs: list[Match]) -> tuple[str, dict]:
    """Méthode retenue sur l'entraînement seulement : > 2 erreurs-types, sinon multiplicative."""
    mesure = evaluer((list(m.cloture), 1 - m.victoire_dom) for m in matchs
                     if m.saison in SAISONS_ENTRAINEMENT)
    meilleure = "multiplicative"
    for nom, r in mesure["methodes"].items():
        if r["erreur_type"] and r["diff_vs_multiplicative"] < -2 * r["erreur_type"] and \
                r["diff_vs_multiplicative"] < mesure["methodes"][meilleure]["diff_vs_multiplicative"]:
            meilleure = nom
    return meilleure, mesure


def proba_marche(cotes: tuple[float, float], methode: str) -> float:
    return METHODES[methode](list(cotes))[0]


# --------------------------------------------------------------------------- modèles

def _jour_utc(jour: date, heure: int) -> datetime:
    return datetime(jour.year, jour.month, jour.day, heure, tzinfo=timezone.utc)


def predictions_revue(matchs: list[Match], decalage: int = 1) -> dict[int, tuple[float, float]]:
    """Rejoue le modèle NHL de production (``nhl_independant.predict``) jour par jour.

    Retourne {indice du match: (probabilité par défaut, variante « research_prior_fade »)}.
    Les matchs sont convertis en ``Game`` à 17 h UTC ; l'instant de calcul est le jour
    d - décalage + 1 à 12 h UTC, donc seuls les matchs des jours <= d - décalage sont connus.
    """
    par_saison: dict[int, list[revue_nhl.Game]] = defaultdict(list)
    ids = {}
    for i, m in enumerate(matchs):
        g = revue_nhl.Game(id=f"{m.jour.isoformat()}-{m.dom}-{m.ext}", start_utc=_jour_utc(m.jour, 17),
                           home=m.dom, away=m.ext, state="OFF", home_goals=m.buts_dom, away_goals=m.buts_ext)
        par_saison[m.saison].append(g)
        ids[g.id] = i
    sorties = {}
    for saison, jeux in par_saison.items():
        anterieure = par_saison.get(saison - 1, [])
        for jour in sorted({g.start_utc.date() for g in jeux}):
            cible = [replace(g, state="FUT", home_goals=None, away_goals=None)
                     for g in jeux if g.start_utc.date() == jour]
            connus = [g for g in jeux if g.start_utc.date() <= jour - timedelta(days=decalage)]
            calcul = _jour_utc(jour - timedelta(days=decalage - 1), 12)
            for p in revue_nhl.predict(anterieure, connus + cible, calcul, jour, days=1):
                sorties[ids[p["event_id"]]] = (p["probabilities"]["home_win"],
                                               p["research_prior_fade"]["prob_home"])
    return sorties


def _phi(x: float) -> float:
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def _Phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


@dataclass(frozen=True)
class ParamsFiltre:
    derive_jour: float      # variance ajoutée par jour sans match (force qui évolue)
    avantage_dom: float
    retour_saison: float    # part de la force conservée d'une saison à l'autre
    variance_initiale: float = 1.0
    bruit_match: float = 1.0


def predictions_filtre(matchs: list[Match], p: ParamsFiltre, decalage: int = 1) -> dict[int, float]:
    """Forces gaussiennes par équipe mises à jour par filtrage (type TrueSkill/Kalman, probit).

    Chaque prédiction n'utilise que les matchs des jours <= d - décalage : aucun lissage.
    """
    mu: dict[str, float] = defaultdict(float)
    var: dict[str, float] = defaultdict(lambda: p.variance_initiale)
    dernier: dict[str, tuple[date, int]] = {}

    def etat(eq: str, jour: date, saison: int) -> tuple[float, float]:
        """Force et incertitude à la date donnée, sans modifier l'état (dérive + retour d'intersaison)."""
        m, v = mu[eq], var[eq]
        if eq in dernier:
            jour_prec, saison_prec = dernier[eq]
            if saison_prec != saison:
                m *= p.retour_saison
                v += (1 - p.retour_saison ** 2) * p.variance_initiale
            v += p.derive_jour * (jour - jour_prec).days
        return m, min(p.variance_initiale, v)

    def proba(m: Match) -> tuple[float, float, tuple[float, float], tuple[float, float]]:
        eh, ea = etat(m.dom, m.jour, m.saison), etat(m.ext, m.jour, m.saison)
        c = math.sqrt(p.bruit_match + eh[1] + ea[1])
        return (eh[0] - ea[0] + p.avantage_dom) / c, c, eh, ea

    sorties, j = {}, 0
    for i, m in enumerate(matchs):
        while j < len(matchs) and matchs[j].jour <= m.jour - timedelta(days=decalage):
            g = matchs[j]
            t, c, eh, ea = proba(g)
            signe = 1 if g.victoire_dom else -1
            v = _phi(signe * t) / max(_Phi(signe * t), 1e-12)
            w = v * (v + signe * t)
            mu[g.dom] = eh[0] + signe * eh[1] / c * v
            mu[g.ext] = ea[0] - signe * ea[1] / c * v
            var[g.dom] = eh[1] * max(1e-4, 1 - eh[1] / c ** 2 * w)
            var[g.ext] = ea[1] * max(1e-4, 1 - ea[1] / c ** 2 * w)
            dernier[g.dom] = dernier[g.ext] = (g.jour, g.saison)
            j += 1
        sorties[i] = _Phi(proba(m)[0])
    return sorties


def regler_filtre(matchs: list[Match], decalage: int = 1) -> tuple[ParamsFiltre, list[dict]]:
    """Grille d'hyperparamètres évaluée UNIQUEMENT sur les saisons d'entraînement."""
    essais = []
    entr = [i for i, m in enumerate(matchs) if m.saison in SAISONS_ENTRAINEMENT]
    for derive in (0.00005, 0.0002, 0.0008):
        for dom in (0.10, 0.15, 0.20, 0.25):
            for retour in (0.25, 0.5, 0.75):
                for v0 in (0.01, 0.03, 0.08):
                    p = ParamsFiltre(derive, dom, retour, v0)
                    pred = predictions_filtre(matchs, p, decalage)
                    essais.append({"params": p.__dict__, "logloss_entrainement": round(
                        _logloss([pred[i] for i in entr], [matchs[i].victoire_dom for i in entr]), 6)})
    meilleur = min(essais, key=lambda e: e["logloss_entrainement"])
    return ParamsFiltre(**meilleur["params"]), essais


# --------------------------------------------------------------------------- mélange avec le marché

def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _logloss(p: list[float], y: list[int]) -> float:
    return -sum(math.log(max(q if t else 1 - q, 1e-12)) for q, t in zip(p, y)) / len(y)


def ajuster_logistique(x: list[list[float]], y: list[int], iterations: int = 30) -> list[float]:
    """Régression logistique (constante incluse) par Newton-Raphson, sans dépendance."""
    k = len(x[0]) + 1
    b = [0.0] * k
    for _ in range(iterations):
        g = [0.0] * k
        h = [[1e-9 * (i == j) for j in range(k)] for i in range(k)]
        for xi, yi in zip(x, y):
            z = [1.0] + xi
            p = 1 / (1 + math.exp(-sum(bj * zj for bj, zj in zip(b, z))))
            for a in range(k):
                g[a] += (yi - p) * z[a]
                for c in range(k):
                    h[a][c] += p * (1 - p) * z[a] * z[c]
        b = [bi + di for bi, di in zip(b, _resoudre(h, g))]
    return b


def _resoudre(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col] / m[col][col]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def appliquer_logistique(b: list[float], xi: list[float]) -> float:
    return 1 / (1 + math.exp(-(b[0] + sum(bj * x for bj, x in zip(b[1:], xi)))))


# --------------------------------------------------------------------------- évaluation

def comparer(probas: dict[str, list[float]], y: list[int], reference: str) -> dict:
    sortie = {}
    pertes_ref = [-math.log(max(p if t else 1 - p, 1e-12)) for p, t in zip(probas[reference], y)]
    for nom, ps in probas.items():
        pertes = [-math.log(max(p if t else 1 - p, 1e-12)) for p, t in zip(ps, y)]
        diff = mean_ci([a - b for a, b in zip(pertes, pertes_ref)], RULE["z"])
        sortie[nom] = {"logloss": round(sum(pertes) / len(y), 5),
                       "brier": round(sum((p - t) ** 2 for p, t in zip(ps, y)) / len(y), 5),
                       f"diff_vs_{reference}": None if nom == reference else diff}
    return sortie


def simuler_paris(matchs: list[Match], probas: list[float], methode: str) -> dict:
    """Mise de 1 à la cote d'OUVERTURE si EV > SEUIL_EV ; CLV mesuré contre la clôture sans marge."""
    profits, clv, battu = [], [], []
    for m, p in zip(matchs, probas):
        for cote, q, gagne, cote_clo, idx in ((m.ouverture[0], p, m.victoire_dom, m.cloture[0], 0),
                                              (m.ouverture[1], 1 - p, 1 - m.victoire_dom, m.cloture[1], 1)):
            if q * cote - 1 <= SEUIL_EV:
                continue
            pc = proba_marche(m.cloture, methode)
            pc = pc if idx == 0 else 1 - pc
            profits.append(cote - 1 if gagne else -1.0)
            clv.append(cote * pc - 1)
            battu.append(1.0 if cote > cote_clo else 0.0)
    return {"paris": len(profits), "roi": mean_ci(profits, RULE["z"]), "clv": mean_ci(clv, RULE["z"]),
            "part_cote_superieure_a_la_cloture": round(sum(battu) / len(battu), 4) if battu else None}


def verdict(paris: dict, calibration: dict | None) -> dict:
    roi, clv = paris["roi"], paris["clv"]
    criteres = {
        "volume": paris["paris"] >= RULE["min_settled"],
        "roi": bool(roi and roi["ci95"] and roi["ci95"][0] > 0),
        "clv": bool(clv and clv["ci95"] and clv["ci95"][0] > 0 and clv["n"] >= RULE["min_clv_samples"]),
        "calibration": bool(calibration and calibration["ci95"] and calibration["ci95"][1] < 0),
    }
    if all(criteres.values()):
        texte = "prometteur"
    elif paris["paris"] >= RULE["min_for_stop"] and roi and roi["ci95"] and roi["ci95"][1] < 0:
        texte = "abandon"
    else:
        texte = "non concluant"
    return {"criteres": criteres, "verdict": texte}


def executer(matchs: list[Match], decalage: int = 1) -> dict:
    methode, mesure_devig = choisir_devig(matchs)
    revue = predictions_revue(matchs, decalage)
    params, grille = regler_filtre(matchs, decalage)
    filtre = predictions_filtre(matchs, params, decalage)
    idx = [i for i in range(len(matchs)) if i in revue]
    entr = [i for i in idx if matchs[i].saison in SAISONS_ENTRAINEMENT]
    test = [i for i in idx if matchs[i].saison in SAISONS_TEST]
    ouv = {i: proba_marche(matchs[i].ouverture, methode) for i in idx}
    clo = {i: proba_marche(matchs[i].cloture, methode) for i in idx}
    modeles = {"revue_nhl": {i: revue[i][0] for i in idx}, "revue_prior_fade": {i: revue[i][1] for i in idx},
               "filtre_dynamique": filtre}

    # Mélanges ouverture + modèle, ajustés sur l'entraînement ; le meilleur (log-loss d'entraînement) est retenu.
    melanges, coefs = {}, {}
    y_entr = [matchs[i].victoire_dom for i in entr]
    for nom, pm in modeles.items():
        b = ajuster_logistique([[_logit(ouv[i]), _logit(pm[i])] for i in entr], y_entr)
        coefs[nom] = [round(v, 4) for v in b]
        melanges[nom] = {i: appliquer_logistique(b, [_logit(ouv[i]), _logit(pm[i])]) for i in idx}
    choix = min(melanges, key=lambda n: _logloss([melanges[n][i] for i in entr], y_entr))

    def bloc(indices: list[int]) -> dict:
        y = [matchs[i].victoire_dom for i in indices]
        probas = {"marche_cloture": [clo[i] for i in indices], "marche_ouverture": [ouv[i] for i in indices]}
        probas.update({n: [pm[i] for i in indices] for n, pm in modeles.items()})
        probas.update({f"ouverture+{n}": [pm[i] for i in indices] for n, pm in melanges.items()})
        return {"matchs": len(indices), "contre_cloture": comparer(probas, y, "marche_cloture"),
                "contre_ouverture": comparer(probas, y, "marche_ouverture")}

    resultats = {"entrainement": bloc(entr), "test": bloc(test)}
    paris = {}
    for nom in ("revue_nhl", f"ouverture+{choix}"):
        source = modeles.get(nom) or melanges[choix]
        paris[nom] = simuler_paris([matchs[i] for i in test], [source[i] for i in test], methode)
    principal = f"ouverture+{choix}"
    verdicts = {nom: {"strategie": nom, **verdict(paris[nom], resultats["test"]["contre_ouverture"][nom][
        "diff_vs_marche_ouverture"])} for nom in paris}
    return {
        "decalage_jours": decalage,
        "retrait_de_marge": {"methode_retenue": methode, "mesure_entrainement": mesure_devig},
        "filtre_dynamique": {"params_retenus": params.__dict__, "configurations_essayees": len(grille)},
        "melanges": {"coefficients_constante_ouverture_modele": coefs, "retenu_sur_entrainement": choix},
        "resultats": resultats,
        "paris_test_cote_ouverture": paris,
        "strategie_principale": principal,
        "verdicts": verdicts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache", type=Path, default=Path("/tmp/revue-cache/nhl_archive_10Y.json"))
    parser.add_argument("--sortie", type=Path)
    args = parser.parse_args()
    matchs, exclus = nettoyer(telecharger(args.cache))
    rapport = {
        "outil": "outils/suivi/banc_nhl_cloture.py",
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"depot": "FinnedAI/sportsbookreview-scraper", "commit": COMMIT, "fichier": "data/nhl_archive_10Y.json",
                   "audit": "analyses/sportsbookreview-scraper/AUDIT.md"},
        "protocole": {"saisons_entrainement": f"{SAISONS_ENTRAINEMENT.start}-{SAISONS_ENTRAINEMENT.stop - 1}",
                      "saisons_test": f"{SAISONS_TEST.start}-{SAISONS_TEST.stop - 1}",
                      "seuil_ev": SEUIL_EV, "regle_decision": RULE["version"],
                      "limites": ["bookmaker non identifié", "heures d'ouverture et de clôture inconnues",
                                  "but de prolongation ou de tirs au but inclus dans le score final",
                                  "données arrêtées en 2021-22"]},
        "matchs_retenus": len(matchs), "lignes_exclues": exclus,
        "analyses": [executer(matchs, 1), executer(matchs, 2)],
    }
    texte = json.dumps(rapport, indent=1, ensure_ascii=False)
    if args.sortie:
        args.sortie.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
