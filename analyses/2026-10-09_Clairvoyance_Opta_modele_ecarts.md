# Clairvoyance vs Revue — audit Opta et modèle original (09/10/2026)

## Ce que possède réellement Clairvoyance

Dans le dépôt source https://github.com/Purple-Wraith/clairvoyance-backend, le script `scripts/scrape_opta_stats.py` décrit la collecte depuis les pages publiques `theanalyst.com`, qui diffusent des statistiques construites sur des données Opta et des **Opta Power Rankings**.

Fichiers observés au 09/10/2026 :

| Source originale | Équipes dans attacking | Champs observés |
|---|---:|---|
| `docs/pl_opta_stats.json` | 20 | xG, buts, tirs, xG par tir ; passes, PPDA, séquences, xGA, Power Rankings |
| `docs/bl_opta_stats.json` | 18 | mêmes sections |
| `docs/ita_opta_stats.json` | 20 | mêmes sections |
| `docs/liga_opta_stats.json` | 20 | mêmes sections |
| `docs/mls_opta_stats.json` | 30 | mêmes sections |
| `docs/cl_opta_stats.json` | 36 | mêmes sections, 81 équipes dans les ratings |

Le JSON Opta original comporte notamment `attacking`, `passing`, `pressing`, `sequences`, `defending`, `powerRankings` et des timestamps `lastUpdated`, `powerRankingsUpdated`. Il s'agit de *statistiques d'équipes* et non nécessairement de statistiques Opta de chaque joueur.

L'application originale `docs/app.html` et `scripts/auto_lock_settle.py` combinent, selon les sports et les marchés, ces données, un modèle de simulation, des facteurs domicile, des données d'effectif, les cotes et le suivi des décisions. Les résultats annoncés dans `docs/engine_performance.json` incluent expressément des décisions après le début du match et des décisions à horodatage de verrouillage inconnu. On ne peut pas les considérer comme une preuve de rentabilité vérifiée au moment de la prise de pari.

## Ce que Revue possède réellement

- Calendriers et scores ESPN / NHL / Liiga ; Elo et Poisson originaux.
- Radar de profils joueurs NHL à partir de statistiques ESPN, sans titulaire confirmé.
- Collecte de cotes réelles française via PulseScore Pro **validée le 09/10/2026** : 32 requêtes au premier scan, 53 correspondances candidates et 14 simulations générées initialement.
- Rapprochement équipe/heure, contrôle de chronologie et journal de simulation.
- Backtests Brier/log loss sur historiques de scores.

**Manques par rapport au modèle d'origine :**
1. Aucun des six jeux de données Opta n'est importé ou recalculé dans le modèle Revue, faute de source Opta autorisée configurée.
2. Pas d'ajustement automatique xG/xGA, pressing et power ratings issus d'Opta.
3. Pas de réplique identique des pondérations, simulations et algorithmes propres au projet tiers (absence de licence explicite).
4. Pas de validation à grande échelle hors échantillon sur les prix effectivement observés.
5. Pas de tous les modèles de joueurs, handicaps, lignes alternatives, gardiens/alignements du tiers.

## Contrôle des marchés hockey après premier scan

Le premier scan PulseScore a trouvé des prix de hockey NHL. **Le champ générique FULL_TIME et un nombre de buts ne suffisent pas à savoir si le pari est réglé sur le temps réglementaire ou prolongations comprises** : la modélisation du résultat final NHL ne correspondrait alors pas au bon marché.

Les **10 simulations NHL initiales ont été placées dans l'état `market_rule_unverified`**, exclues de tout bilan de rendement, tant qu'une identification plus solide du règlement du marché n'est pas disponible. Quatre autres simulations restent en attente. Ce contrôle évite de gonfler artificiellement un ROI papier.

## Étapes pour une intégration Opta autorisée

1. Obtenir l'accès contractuellement permis aux statistiques Opta/The Analyst pour cette utilisation (lire les conditions et droits de redistribution).
2. Développer un connecteur indépendant qui conserve `observed_at`, `published_at`, compétition/saison, identité stable d'équipe et provenance.
3. Refaire l'identification d'équipes de manière univoque (aucune approximation silencieuse), gérer clubs promus/relégués, séparer compétitions UEFA.
4. Ajouter un blend xG/xGA + Power Rankings **comme candidat à tester**, sans changer immédiatement le moteur de production.
5. Test walk-forward historique **sans fuite** comparé au modèle Elo/Poisson actuel et au consensus bookmaker ; retenir l'enrichissement uniquement s'il améliore Brier/log loss et calibration hors échantillon.
6. Compléter les règles de marché exactes, notamment NHL prolongation/shootout, et consolider le suivi prospectif.

**Important :** l'accès public à une page ne prouve pas le droit de recopier ses bases statistiques, et le dépôt tiers n'a pas de licence explicite. Les sources ont été auditées, **pas copiées** dans Revue.
