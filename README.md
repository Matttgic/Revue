# Revue — Bibliothèque de stratégies de paris sportifs

**Revue** est une bibliothèque de recherche **traçable, structurée et testable** : modèles statistiques, algorithmes, méthodologies, sources de données et outils inspirés de dépôts GitHub tiers.

> **Principe : une idée intéressante n'est pas une stratégie rentable démontrée.** Aucun rendement n'est garanti. La bibliothèque distingue hypothèse, code reproductible, backtest et validation hors échantillon.

## Engine V2 — reconstruction indépendante du fonctionnement Clairvoyance

- [Tableau de bord « Engine V2 »](docs/engine-v2.html) : radar de cotes réelles, simulations et suivi en unités fictives.
- [Moteur original Python](outils/revue_engine_v2.py) : prix Betclic/Winamax/Unibet/PMU/NetBet, Pinnacle seulement pour comparaison, contrôle strict pré-match, règlement des matchs, historique.
- [Guide d'utilisation Android et configuration de clé](outils/ENGINE-V2-README.md) ; [GitHub Actions Engine V2](.github/workflows/revue-engine-v2.yml).
- [Dernier rapport moteur](docs/engine-v2-latest.json) et [registre paper](docs/engine-v2-ledger.json).

**Première validation technique : 21 tests passés sur GitHub (09/10/2026).** La collecte de cotes est **désactivée tant que le secret THE_ODDS_API_KEY n'est pas configuré** ; aucune opportunité fictive ni ROI inventé. Pas de paris en argent réel. Cette V2 ne prétend pas reproduire l'ensemble des fichiers originaux ni démontrer une stratégie rentable.

## Revue élargie — 19 flux détectés + profils NHL (prototype)

Le moteur récupère les compétitions de football, basket, football américain, baseball et NHL ainsi que les matchs ATP/WTA, UFC et Liiga. **Flux joignable ne signifie pas prédiction validée.**

- [Tableau de bord multisports](docs/multisports.html) · [JSON multisports](docs/multisports-latest.json)
- [Tennis, UFC et Liiga](modeles/simulations/SPORTS_INDIVIDUELS_README.md) · [JSON des derniers événements](docs/individual-latest.json)
- [Radar NHL buteurs / passeurs / points / tirs](docs/nhl-joueurs.html) · [224 profils NHL calculés le 09/10/2026](docs/nhl-players-latest.json)
- [Architecture de l'actualisation sur GitHub Actions](.github/workflows/multisports-independent.yml)
- [Brier / log loss par compétition](docs/qualite-modeles.html) · [résultats vérifiables](docs/backtests-multisports.json) · [méthodologie](outils/BACKTESTS_MULTISPORTS.md) (aucun ROI sans cotes).

À vérifier : les compétitions encore sans flux autorisé (SHL, National League Suisse, Extraliga Tchéquie), les compositions/titularisations, les cotes françaises et les backtests hors échantillon. **Aucune méthode de paris profitable validée.**

## Tableau de bord multisports — 14 flux connectés (prototype)

- [Moteur multisports original](modeles/simulations/multisports_independant.py) et [documentation détaillée](modeles/simulations/MULTISPORTS-README.md).
- [Tableau de bord mobile](docs/multisports.html) : football, basket, football américain, baseball et NHL ; nécessite GitHub Pages pour une adresse de site publique.
- [Prédictions réellement générées](docs/multisports-latest.json) et [workflow d'actualisation](.github/workflows/multisports-independent.yml).
- **Vérification du 09/10/2026 :** 14 flux ESPN/NHL répondent, 133 rencontres sur trois jours et 99 probabilités. D'autres compétitions restent explicitement sans source (hockey européen, tennis, MMA). Les chiffres changent à chaque exécution.
- **Aucune EV réelle ni retour prouvé** : modèles exploratoires non calibrés, pas encore de cote de bookmaker français ni de props joueurs.

## Premier modèle exécutable : NHL Independent (prototype)

- [Moteur Python original Elo + Poisson](modeles/simulations/nhl_independant.py) et [documentation](modeles/simulations/NHL-INDEPENDANT-README.md)
- [Dernières probabilités NHL](docs/nhl-model-latest.json) (fichier calculé réellement depuis l'API NHL)
- [Interface mobile](docs/nhl-model.html) (affichage comme site si GitHub Pages est activé pour /docs)
- [Tests GitHub Actions](.github/workflows/nhl-independent.yml) : 13 tests réussis, rafraîchissement automatisé

**Important :** modèle non calibré, sans données de gardien confirmé, sans prix de bookmaker français et sans stratégie de pari validée. Aucun code du dépôt Clairvoyance non licencié n'a été copié.

## Organisation

```text
Revue/
├── catalogue/                 # Index et fiches synthétiques par idée
│   └── INDEX.md
├── analyses/                  # Audits de dépôts tiers (source, licence, limites, verdict)
├── strategies/
│   ├── football/
│   ├── tennis/
│   ├── basketball/
│   ├── hockey-nhl/
│   ├── baseball/
│   ├── multisports/
│   └── transversales/         # Arbitrage, EV+, boosts, marchés, risk management
├── modeles/
│   ├── probabilites/          # Probabilités, calibration et modèles prédictifs
│   ├── machine-learning/
│   └── simulations/
├── data-sources/              # APIs, scrapers autorisés, formats, normalisation
├── outils/                    # Calculs de cotes, EV, retrait de marge, backtests
├── tests/                     # Tests unitaires, de non-régression et anti-fuite
├── templates/                 # Modèles de fiches et grilles d'évaluation
├── recherche/                 # Pistes prometteuses non validées
└── archives/                  # Approches rejetées / dépréciées et justification
```

Les dossiers sont créés lors des premières intégrations (Git n'enregistre pas les dossiers vides).

## Parcours d'un dépôt tiers

1. **Auditer** : objectif réel, sources, dépendances, licence, sécurité, maintenance et qualité du code.
2. **Extraire** : recenser les idées et sélectionner les modules réellement utiles ; éviter le copier-coller indiscriminé.
3. **Classer** : `analyses/` pour l'audit, `recherche/` pour l'hypothèse, `strategies/` ou `modeles/` pour l'implémentation exploitable, `outils/` pour les briques communes.
4. **Documenter** : auteur, URL, commit/source, licence, sport, marché, données nécessaires, hypothèses, cas d'usage et limites.
5. **Tester** : tests automatisés, absence de fuite temporelle et, si les données le permettent, backtest chronologique avec coûts réalistes.
6. **Statuer** : `À étudier`, `Prototype`, `Testé`, `Validé hors échantillon`, `Rejeté`. Une stratégie « testée » n'est pas automatiquement rentable.

## Critères d'évaluation

| Critère | Points |
|---|---:|
| Idée et utilité réelle | 20 |
| Qualité / reproductibilité du code | 20 |
| Données disponibles et légalité d'accès | 15 |
| Validité statistique, absence de biais | 20 |
| Possibilité de backtester hors échantillon | 15 |
| Maintenance, sécurité, intégration | 10 |
| **Total** | **100** |

**Score d'intérêt documentaire, jamais probabilité de gain.** Une licence incompatible, des données obtenues illicitement ou des failles critiques bloquent l'importation de code même si le score est élevé. Sans licence explicite, documenter les idées sans recopier le code.

## Mesures minimales des stratégies

Pour chaque test : nombre de paris, période, marché, bookmaker, cotes obtenables au moment du pari, mise/gestion du risque, ROI net, profit en unités, drawdown, CLV si disponible, intervalle d'incertitude, ventilation par saison et validation chronologique. Documenter les paris sans résultat et les lignes/cotes manquantes.

## Cadre français

Pour une exploitation en France, distinguer les sports, compétitions et **types de paris** autorisés par l'ANJ, la disponibilité des cotes chez les opérateurs agréés et le droit d'utilisation des données/API. Une stratégie non compatible peut rester archivée pour la recherche, **sans être présentée comme directement exploitable**.

## Ajout d'un nouveau dépôt

Transmettre l'URL GitHub. Chaque nouvelle source aura une fiche d'analyse, un verdict argumenté, une attribution, un emplacement clair et, si la copie est autorisée et pertinente, des modules isolés avec tests. Les versions sources doivent rester identifiables.

Consulter [le catalogue](catalogue/INDEX.md) et [le protocole d'évaluation](templates/PROTOCOLE.md).
