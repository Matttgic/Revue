# REV-CLAIR-02 — NHL : utilité du gardien titulaire confirmé

**Statut : À étudier.** Références : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_goalie_starter.py et https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/_nhl_goalies.py

## Hypothèse
Le remplacement de la qualité « gardien principal » par celle du titulaire effectif pourrait améliorer une prédiction ML/O-U, mais uniquement si l'identité du titulaire est **connue au moment de la décision**.

## Variables
- Qualité GSAx / 60 avec régression vers la moyenne et historiques datant d'avant le match.
- Statistiques gardiens antérieures : tirs reçus, arrêts, minutes, début de saison.
- Statut de starter : `confirmed` / `projected` / `unknown`; source et première heure d'observation.

## Deux tests distincts
1. **Oracle rétrospectif :** véritable gardien du box score post-match. Mesure le potentiel maximal théorique du signal, pas un système utilisable.
2. **Déploiement réel :** seulement starter confirmé avec horodatage antérieur au début du match, ou scénario projected explicitement probabilisé. Comparer à baseline qui ne connaît que le gardien principal.

Mesures par saison gelée : log loss, Brier, différence appariée de pertes, disponibilité et couverture du starter, ROI aux cotes réelles.

## Droits de données
L'auteur désactive par défaut l'extension MoneyPuck vers des fichiers dont l'utilisation automatisée n'est pas expressément autorisée ; obtenir les permissions nécessaires plutôt que recopier le scraper.

**Verdict :** prioritaire pour recherche NHL ; ne pas supposer que le gardien annoncé explique seul un edge.
