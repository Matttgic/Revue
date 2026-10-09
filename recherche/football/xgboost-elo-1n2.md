# REV-VCHEQUE-01 — Elo + modèle supervisé 1N2

**Statut : À étudier / modèle source non validé indépendamment.**

- **Sport / marchés :** football, résultat 1N2 pré-match
- **Source :** https://github.com/VCheque/Football-Betting/blob/main/sports_betting/xgboost_models.py
- **Origine :** VCheque/Football-Betting, consulté 2026-10-09, commit `62158a22ad12da23825f4e4674397ddddf945972`
- **Licence :** absente; fiche de recherche originale uniquement.

## Hypothèse

Combiner un rating d'équipe durable (Elo), la forme courte (5 derniers), les facteurs structurels domicile/extérieur et le contexte du match pour estimer la distribution `P(1), P(N), P(2)`. L'écart de niveau Elo pourrait corriger le bruit de la forme récente.

## Variables identifiées dans le projet

20 variables : points récents, attaque et défense, discipline et corners, repos, fatigue, points par match, H2H et différence de buts H2H, blessures, force de composition, indice de championnat, rendement spécifique domicile/extérieur, tendance des 5 derniers, indicateur de rivalité, tirs cadrés, écart Elo, rang domicile, rang extérieur.

Le projet entraîne un **XGBClassifier multiclasses** avec décroissance du poids des matchs anciens, mais **ne réalise pas la calibration isotone revendiquée** sur son chemin principal.

## Plan de test indépendant

- Baselines : fréquences des résultats, Elo probabilisé et consensus de cotes 1N2 dé-margées.
- Toutes les features et cotes doivent précéder **l'heure** du match, pas uniquement sa date.
- Diviser chronologiquement : apprentissage, calibration, validation, test final. Ne jamais utiliser test pour choisir les hyperparamètres.
- Elo : mise à jour après le coup de sifflet final uniquement ; équipe promue ou changement de ligue à traiter.
- Mesurer : log loss multiclasses, Brier, calibration par tranche, stabilité par saison/ligue, profit au prix bookmaker réel, ROI, CLV, drawdown.
- Tester suppression de variables par familles, pour établir si `elo_gap` et `home_rank` apportent une amélioration.
- Même contexte historique pour chaque approche; décotes et frais explicites.

## Limites

Pas de benchmark chiffré démontrant que le modèle surpasse les bookmakers, pas de moteur de calibration effectif dans le parcours audité, incohérences possibles sur l'heure des rencontres jouées le même jour.

**Verdict :** candidat prioritaire pour une **réimplémentation autonome** et une expérience football 1N2; aucune promesse d'EV positive.
