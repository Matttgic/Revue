# Phase 12 — résultats officiels prospectifs

Le site est publié sur GitHub Pages, mais les résultats de modèle ne sont
qualifiés qu'après les scores officiels.

- **NBA, MLB, football** : les prévisions sont *figées 20 min avant match* ;
  le scoreboard ESPN fournit les finales, et le rattrapage ciblé interroge
  au maximum 12 dates de calendrier par passage pour les matchs figés
  en attente depuis moins de 21 jours. Pas de nouveau pick rétroactif.
- Contrôles stricts : même identifiant ESPN, équipes, horaire UTC, état
  `final`, score entier, fenêtre minimale de 95 min depuis le coup d'envoi
  et période sportive autorisée. Aucun règlement MLS/UCL ambigu.
- **Conflits** : si deux sources ESPN donnent des résultats différents
  pour le même match, l'issue reste *pending*, aucune statistique valide.
- **NHL** : règlement séparé avec scores officiels NHL. Audit indépendant
  de la victoire, de la probabilité figée et du Brier.
- **Marchés historiques** : 10 prix NHL au statut
  `market_rule_unverified` restent hors des résultats et ROI des mises.
  Le suivi Brier et Log Loss ne correspond pas à des unités d'argent.
- Le taux de rentabilité n'est **pas établi** et aucun modèle n'est
  déclaré calibré. Accumuler de nouveaux matchs sans extrapoler.

Contrôle des sources et mesures :
`docs/phase12-result-integrity-latest.json`,
`docs/phase12-official-finals-latest.json`,
`docs/phase12-reconciliation-latest.json`.

Automatisation : Match Center toutes les heures, NHL official results
toutes les quatre heures. Les tests unitaires sont exécutés avant
les changements de registre sur main ; aucun appel à une API de cotes
payante n'est nécessaire pour régler les résultats.
