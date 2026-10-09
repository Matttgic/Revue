# Revue — Bibliothèque de stratégies de paris sportifs

**Revue** est une bibliothèque de recherche **traçable, structurée et testable** : modèles statistiques, algorithmes, méthodologies, sources de données et outils inspirés de dépôts GitHub tiers.

> **Principe : une idée intéressante n'est pas une stratégie rentable démontrée.** Aucun rendement n'est garanti. La bibliothèque distingue hypothèse, code reproductible, backtest et validation hors échantillon.

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
