# Revue

Catalogue personnel de **méthodes, stratégies, modèles et données de paris sportifs** trouvés en explorant des dépôts GitHub publics. Chaque dépôt est audité. Les idées utiles sont documentées. Les modèles sont soit reproduits et vérifiés contre l'original, soit réécrits indépendamment. Leur valeur réelle est mesurée de façon prospective, sans argent réel.

> **Principe :** une méthode documentée, reproduite ou « testée » n'est pas une méthode rentable. Seuls des paris enregistrés **avant** le match, à des **cotes réellement observées** et en nombre suffisant peuvent démontrer un avantage.

Site : [matttgic.github.io/Revue](https://matttgic.github.io/Revue/) · Journal de développement : [journal/](journal/README.md)

## Où en est-on ?

| Sujet | État | Détail |
|---|---|---|
| **Clairvoyance** (Purple-Wraith) | Rentabilité affichée **non démontrée** : sur 125 paris pré-match à cote observée, ROI +2,7 %, IC 95 % [−9,8 % ; +15,1 %] | [Vérification](analyses/2026-10-11_Clairvoyance_verification_rentabilite_et_reproduction.md) · [agrégats](docs/clairvoyance-rentabilite-audit.json) |
| Reproduction Clairvoyance | 44 fonctions modèle identiques à l'original (re-vérifiées chaque jour) ; couche de sélection des paris non reproduite | [Modèles](catalogue/MODELES.md) · [parité](docs/parite-modeles-clairvoyance.json) |
| Modèles Revue | 9 modèles de recherche suivis de façon prospective, non calibrés | [Modèles](catalogue/MODELES.md) |
| Catalogue | 4 dépôts audités, 33 entrées (méthodes, modèles, outils), aucune rentabilité prouvée | [Analyses](analyses/README.md) · [Méthodes](catalogue/INDEX.md) |

## Organisation

```text
Revue/
├── README.md              ← vous êtes ici
├── catalogue/             ← POINT D'ENTRÉE : index des méthodes, modèles et données
│   ├── INDEX.md           │  méthodes / stratégies (une ligne par idée)
│   ├── MODELES.md         │  modèles reproduits et modèles Revue
│   └── DONNEES.md         │  jeux de données publiés et sources (généré)
├── analyses/              ← un audit par dépôt GitHub examiné (source, licence, verdict)
├── recherche/             ← fiches de méthodes par sport : hockey/, football/, basketball/, …
├── modeles/
│   ├── reproduction/      ← réécritures vérifiées contre l'original
│   └── simulations/       ← modèles originaux Revue
├── outils/                ← scripts, rangés par fonction (index : outils/README.md)
│   ├── clairvoyance/      │  parité et audits du dépôt Clairvoyance
│   ├── collecte/          │  acquisition de données (NHL, MoneyPuck, ESPN, cotes)
│   ├── suivi/             │  prévisions figées, règlement, évaluation, journal papier
│   ├── controles/         │  qualité : cotes, chronologie, marge, intégrité
│   └── publication/       │  construction des écrans du site
├── docs/                  ← site GitHub Pages ET données publiées (*.json) — ne pas déplacer
├── api_revue/, api/       ← API en lecture seule (Vercel)
├── tests/                 ← tests Python (unittest) et JavaScript (node --test)
├── templates/             ← fiches à copier : source, stratégie, protocole d'évaluation
├── archives/              ← méthodes rejetées et pourquoi
├── journal/               ← historique de développement (phases 1 à 14)
└── .github/workflows/     ← collecte, suivi et vérifications automatiques
```

## Ajouter un dépôt découvert

1. **Auditer** : créer `analyses/AAAA-MM-JJ_proprietaire_depot.md` depuis [templates/FICHE_SOURCE.md](templates/FICHE_SOURCE.md). Préciser l'objectif, le commit, la licence, les données et la sécurité. Si la rentabilité est affichée, la **recalculer** : pré-match seulement, cotes réellement observées (voir [outils/clairvoyance/audit_rentabilite_clairvoyance.py](outils/clairvoyance/audit_rentabilite_clairvoyance.py)).
2. **Extraire** chaque idée utile dans `recherche/<sport>/`, depuis [templates/FICHE_STRATEGIE.md](templates/FICHE_STRATEGIE.md), et ajouter une ligne à [catalogue/INDEX.md](catalogue/INDEX.md).
3. **Reproduire** si c'est pertinent : `modeles/reproduction/` + un vérificateur de parité. Sans licence explicite, réécrire sans copier, et ne jamais republier le code ni les données sous licence.
4. **Mesurer** de façon prospective (`outils/suivi/`) avant toute conclusion. Statuts : `À étudier`, `Prototype`, `Testé`, `Validé hors échantillon`, `Rejeté` (→ [archives/](archives/README.md)).

Critères d'évaluation et mesures minimales d'un test : [templates/PROTOCOLE.md](templates/PROTOCOLE.md).

## Cadre français

Pour une exploitation en France, vérifier pour chaque sport, compétition et type de pari qu'il est autorisé par l'ANJ et disponible chez un opérateur agréé. Vérifier aussi le droit d'utiliser les données ou l'API. Une méthode incompatible reste cataloguée pour la recherche, **sans être présentée comme exploitable**.

## Automatisation (GitHub Actions)

| Rythme | Rôle | Workflows |
|---|---|---|
| Toutes les heures | Écrans du site, règlement des paris papier, prédictions publiées par Clairvoyance figées avant match | `match-center-revue`, `picks-center-revue`, `donnees-prioritaires`, `phase6-predictions` |
| 3 à 6 fois par jour | Cotes réelles et journal papier, prédictions des modèles Revue, données et suivi NHL, contrôles de fraîcheur | `revue-engine-v2`, `pulsescore-radar-6h`, `multisports-independent`, `nhl-*`, `moneypuck-official`, `phase2/7/9/11/14`, `health-revue` |
| 1 fois par jour | Données NBA/MLB (exigées < 48 h), santé CI, API | `clairvoyance-nba-advanced`, `mlb-source-elo-gap`, `github-actions-monitor`, `api-vercel-smoke` |
| Le lundi | Parité et audits de Clairvoyance, diagnostics d'écarts | `parite-*`, `audit-*clairvoyance*`, `clairvoyance-real-output-gap`, `phase1/4/5`, … |
| Sur modification ou à la main | Tests ciblés, sondes d'API | `tests` (suite complète), `arcade-v3-tests`, `probe-*`, `check-pulsescore`, … |

Les échecs sur `main` ouvrent automatiquement une issue (`ci-failure-alerts`). Les seuils de fraîcheur (phase 9 : santé < 12 h, phase 7 < 15 h ; phase 14 : phase 11 < 24 h ; phase 11 : NBA/MLB < 48 h) imposent les rythmes minimaux ci-dessus.

## Lancer les vérifications

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py"     # tests Python
for f in tests/*.js tests/*.cjs; do node --test "$f"; done  # tests JavaScript
python -m outils.controles.inventaire_depot              # regénérer outils/README.md et catalogue/DONNEES.md
```

Les secrets (clés d'API de cotes) restent dans les secrets GitHub Actions, jamais dans Git.
