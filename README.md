# Revue — Reproduction des modèles Clairvoyance

> **Mission prioritaire : reproduire fidèlement les modèles du dépôt [Purple-Wraith/clairvoyance-backend](https://github.com/Purple-Wraith/clairvoyance-backend), et non inventer des modèles de remplacement.**

- **Parité des fonctions ciblées :** [44 sur 44, soit 100 % du catalogue vérifié](docs/parite-modeles-clairvoyance.json), **pas 98 % du dépôt complet**, ni une équivalence des prédictions sur données réelles.
- **Tests face au code original :** [5 232 comparaisons identiques](docs/parite-modeles-clairvoyance.json) pour les calculs Python et JavaScript sélectionnés, avec entrées de test communes (les formulations textuelles des props ne sont pas copiées). [Rapport frontend](docs/parite-clairvoyance-frontend.json) · [rapport NBA](docs/parite-clairvoyance-nba-source.json). La chaîne complète d’acquisition, les données Opta autorisées et les prédictions en conditions réelles ne sont pas encore identiques.
- **Méthode et statut exact des modèles :** [documentation reproduction](modeles/reproduction/README.md) · [tableau de bord gaming parité](docs/parite-clairvoyance.html) · [tests automatisés à la source](.github/workflows/parite-clairvoyance-predictor.yml).
- **NBA sur données réelles :** [30 équipes calculées avec la formule originale de forces/Elo et les statistiques ESPN avancées 2025–2026](docs/clairvoyance-nba-advanced-ratings.json) (ORTG, DRTG, rythme et marges). [460 tests de parité exacts](docs/parite-clairvoyance-espn-nba.json) des transformations ESPN. La saison 2026–2027 n'est pas encore disponible via ESPN pour ces statistiques : les équipes restent sur les données de saison régulière antérieure, sans intégrer les résultats de présaison. BBRef SRS/Opta, blessures, compositions et parité des probabilités finales restent incomplets.
- **CFB exclu** à la demande de l'utilisateur.
- **MoneyPuck NHL (usage strictement personnel, non commercial)** : [laboratoire xG + gardiens](docs/moneypuck.html) · [statistiques des équipes](docs/moneypuck-nhl-latest.json) · [GSAx des gardiens](docs/moneypuck-goalies-latest.json) · [collecteur d'équipes](outils/moneypuck_feed.py) · [collecteur de gardiens](outils/moneypuck_goalies_feed.py) · [tests](tests/test_moneypuck_feed.py) · [actualisation quotidienne](.github/workflows/moneypuck-official.yml). Le flux télécharge **uniquement les CSV de saison explicitement proposés** sur [MoneyPuck.com](https://moneypuck.com/data.htm), cite la source sur chaque écran et ne republie pas les fichiers bruts. Deux saisons restent séparées (actuelle et précédente), sans présenter des observations historiques comme des prédictions. Le `iceTime` CSV est en **secondes** : le rapport dérivé corrige la conversion `stat × 3600 / iceTime`, sans modifier le parseur de référence dont la parité est conservée. Le [moteur NHL expérimental](docs/nhl-model.html) affiche ces xG **en contexte seulement**, sans les intégrer à ses probabilités. Les rapports de gardiens contiennent le **GSAx** (= xG encaissés − buts encaissés), mais aucune donnée de titulaire confirmé : `starter_status=unknown` et `confirmed_starters=false`. Les commits automatiques de données provoquent une republication GitHub Pages par `workflow_run` après réussite du collecteur. Ni cotes ni rentabilité prouvée.

- **Comparaison NHL MoneyPuck à deux modèles (recherche)** : [protocole et formules](recherche/hockey/nhl-moneypuck-deux-modeles.md) · [stabilisation petits échantillons](outils/nhl_moneypuck_prudent.py) · [tests dédiés](tests/test_nhl_moneypuck_prudent.py) · [comparaison des Brier appariés](docs/nhl-shadow-performance.json). Formule Clairvoyance d'origine **inchangée** ; variante indépendante qui réduit le poids des xG sur 3–5 matchs et des arrêts instables grâce à des priors déclarés. Un même journal conserve les deux probabilités avant le début du match. Les anciennes prévisions verrouillées ne sont **jamais rétroactivement complétées** avec la nouvelle variante. Aucun modèle n'est encore calibré ou validé sur un nombre suffisant de rencontres.\n- **NHL Clairvoyance / SHADOW sur sources réelles** : [tableau interactif](docs/nhl-clairvoyance.html) · [dernier JSON](docs/nhl-clairvoyance-shadow-latest.json) · [calcul Python](outils/clairvoyance_nhl_moneypuck_shadow.py) · [tests anti-fuite](tests/test_clairvoyance_nhl_moneypuck_shadow.py) · [actualisation autonome](.github/workflows/nhl-clairvoyance-moneypuck-shadow.yml). L'algorithme applique la **formule de prédiction NHL ciblée de Clairvoyance**, vérifiée par tests de parité, aux xG% et aux statistiques de gardiens **réellement collectés** dans MoneyPuck, et à un **proxy Elo recalculé dans Revue** depuis l'historique NHL. Ce n'est **pas** une reproduction de la base Elo du dépôt tiers ni une parité de prédictions finales sur données identiques. Les données sources et leur horodatage doivent précéder le coup d'envoi. Le gardien le plus utilisé n'est **pas** un titulaire confirmé. Modèle SHADOW non calibré, sans cotes, sans recommandation de mise ni garantie de ROI. **Suivi prospectif réel :** [registre figé avant les matchs](docs/nhl-shadow-ledger.json) · [Brier et nombre de résultats](docs/nhl-shadow-performance.json) · [moteur de règlement](outils/nhl_shadow_tracker.py). Chaque prévision est verrouillée une seule fois à au moins 20 minutes du coup d'envoi, puis réglée à partir du score officiel ; aucune ancienne probabilité n'est réécrite. 18 prévisions verrouillées lors de la première exécution du 10 octobre 2026, 0 résultat encore réglé à ce stade.\n
- Les modèles exploratoires Elo, Poisson, MC et Bayes écrits précédemment dans `modeles/simulations/` sont **des expériences distinctes** et ne sont **jamais comptabilisés comme des reproductions**. Les anciennes estimations de 30–35 % mélangeaient fonctionnalités du site et innovations et ne mesuraient pas la fidélité.

## Bibliothèque expérimentale préexistante (hors périmètre de reproduction)

**Revue** est une bibliothèque de recherche **traçable, structurée et testable** : modèles statistiques, algorithmes, méthodologies, sources de données et outils inspirés de dépôts GitHub tiers.

> **Principe : une idée intéressante n'est pas une stratégie rentable démontrée.** Aucun rendement n'est garanti. La bibliothèque distingue hypothèse, code reproductible, backtest et validation hors échantillon.

**Audit Opta :** Clairvoyance intègre les xG, xGA, PPDA, statistiques d'équipes et Opta Power Rankings via The Analyst, mais **Revue n'a pas encore d'accès autorisé à ces données**, et notre modèle n'est pas la copie exacte de son moteur. [Voir l'audit et les écarts](analyses/2026-10-09_Clairvoyance_Opta_modele_ecarts.md).

## Football : mesures d'équipes et comparaison prospective

- [Statistiques ESPN dérivées](docs/football-espn-team-features.json) : tirs, tirs cadrés, possession, passes, interceptions et tacles ; ni xG ni Opta.
- [Collecteur indépendant](modeles/simulations/football_espn_statistiques.py) : historiques horodatés, identifiants d'équipe stables, plafond de requêtes et cache.
- [Registre pré-match](docs/football-shadow-ledger.json) et [score de qualité Brier/log loss](docs/football-shadow-performance.json) : modèle historique contre modèle enrichi ; aucune rentabilité supposée.
- Dernier contrôle du 9 octobre 2026 : 72 matchs avec statistiques, 23 profils d'équipes et 34 prévisions enregistrées en comparaison prospective. Les données de tirs sont actives sur 4 prévisions archivées, et les résultats ne sont pas encore disponibles.

## Football avancé — nouveau candidat testé, sans reprise de code tiers

- [Interface de comparaison football](docs/football-avance.html) et [JSON des probabilités / backtests](docs/football-advanced-shadow.json)
- [Modèle indépendant](modeles/simulations/football_avance_independant.py) et [méthodologie + performances](modeles/simulations/FOOTBALL-AVANCE-README.md)
- 13 tests passés sur GitHub ; calculs de forme, Elo, Poisson corrigé Dixon-Coles, xG/power rating **uniquement** si données autorisées et antérieures au match disponibles.
- Au premier backtest du 9/10/2026, 18 matchs en Liga (Brier un peu meilleur), 60 en MLS (Brier un peu moins bon), trop peu ailleurs. **N'est pas utilisé dans les picks papier**.
- Le fichier de snapshots statistiques licenciés est ignoré par Git, pour ne pas publier des données protégées par inadvertance.

## Engine V2 — reconstruction indépendante du fonctionnement Clairvoyance

- [Portail web Revue](docs/index.html) et [tableau « Engine V2 »](docs/engine-v2.html) : radar de cotes réelles, simulations et suivi en unités fictives.
- [Moteur original Python](outils/revue_engine_v2.py) : prix Betclic/Winamax/Unibet/PMU/NetBet via PulseScore Pro (prioritaire) ou The Odds API ; Pinnacle seulement pour comparaison lorsqu'il est réellement disponible, contrôle strict pré-match, règlement des matchs, historique.
- [Guide d'utilisation Android et configuration de clé](outils/ENGINE-V2-README.md) ; [GitHub Actions Engine V2](.github/workflows/revue-engine-v2.yml).
- [Dernier rapport moteur](docs/engine-v2-latest.json) et [registre paper](docs/engine-v2-ledger.json).

**Première validation technique : 36 tests Engine V2 + PulseScore passés sur GitHub (09/10/2026).** La collecte de cotes est **désactivée tant que PULSESCORE_API_KEY ou THE_ODDS_API_KEY n'est pas configuré** ; aucune opportunité fictive ni ROI inventé. Pas de paris en argent réel. Cette V2 ne prétend pas reproduire l'ensemble des fichiers originaux ni démontrer une stratégie rentable.

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
