# Revue — des dépôts aux expériences

Objectif : transformer les enseignements du catalogue en composants mesurables pour un outil d’aide à l’analyse des paris. Chaque idée doit relier **source → hypothèse → expérience → résultat → décision**.

Les dossiers d’analyse restent indépendants. Cet espace contient nos expériences ; les modèles et journaux existants restent inchangés. Le premier prototype lit une copie logique des données publiées sans déclencher de collecte.

[Prix et rendement](value-robuste/README.md) ajoute maintenant une stratégie à seuils figés, une cote minimale à vérifier, un registre distinct et un écran public. Elle attend un relevé sharp complet récent ; aucune rentabilité n’est présumée.

## Première réalisation

[Comparateur de probabilités de marché](probabilites_marche/README.md) : multiplicatif, additif, power et Shin appliqués aux mêmes cotes. [Résultat exécuté](probabilites_marche/observation-2026-10-12/RESULTATS.md) : 51 marchés, 160 comparaisons dirigées, 13 changements de signe selon la méthode. Ce sont des mesures de sensibilité, pas des paris gagnants ni un classement des méthodes par rentabilité.

[Revue des fusions Claude du 12 octobre](revue-claude-2026-10-12.md) : apports vérifiés, limites et articulation avec ce prototype.

## Produit visé

Un dossier par rencontre qui répond clairement à quatre questions : quelles données étaient disponibles, quelles probabilités donnent les modèles et le marché, quelles hypothèses changent le diagnostic, et qu’a montré le suivi des prévisions précédentes ? Le dossier doit aussi pouvoir conclure « informations insuffisantes ».

On peut s’appuyer sur les écrans et collecteurs déjà présents dans Revue. Il manque surtout une chaîne d’expérimentation traçable reliant les nouvelles idées au produit. Ajouter un modèle ou une moyenne de modèles sans expérience comparative ne résout pas ce manque.

| Composant | Enseignements à exploiter | Travail concret | État |
|---|---|---|---|
| Cotes comparables | OddsHarvester, soccerdata, nba-betting ; collecte de Claude | Identité match/marché/période/ligne, horodatage et qualité | Collecte existante ; contrats vérifiés dans le prototype football ; limites Orbit documentées |
| Probabilités du marché | Shin, penaltyblog, goto_conversion, Betting-Dashboard | Comparer les hypothèses de retrait de marge sans prendre l’une pour la vérité | Première expérience exécutée |
| Probabilités sportives | penaltyblog, goalmodel, regista, sports-model | Elo, Poisson/DC, puis dispersion ; mêmes matchs, validation chronologique | Prochaine expérience à construire ; pas encore réalisée ici |
| Variables nouvelles | socceraction, pybaseball, nflreadpy | Ajouter xT/VAEP ou variables de joueurs une famille à la fois | Dépend des données disponibles et de leurs droits |
| Comparaison et promotion | wowza-betting, cfbfastR, sports_prediction_model | Contrat des variables, même cohorte pour candidats et référence, test final gelé | À relier à l’évaluation prospective existante |
| Suivi économique | flumine, sports-betting, nba-betting | Règlement différé, exposition, prix exécutable, commissions, CLV | À expérimenter séparément ; aucun moteur existant modifié |

## Critères de progression

1. **Données** : observations datées, règles de marché définies et fichiers d’entrée identifiables. Un dataset corrigé après coup n’est pas automatiquement une archive pré-match.
2. **Probabilités** : battre une baseline simple et comparer au marché sur les mêmes matchs hors échantillon ; rapporter Brier, log-loss et calibration.
3. **Décision** : fixer les seuils avant le test final, enregistrer les abstentions et mesurer l’exposition.
4. **Économie** : suivre prospectivement prix et règlements ; mesurer incertitude, ROI net, drawdown et CLV. Aucun gain n’est présumé.

La première expérience vérifie la solidité d’un calcul. Elle ne franchit pas encore les critères de prédiction ou d’économie. La suite recommandée est un benchmark football limité à une compétition disposant d’un historique licite de résultats et de cotes, avec les dates effectivement disponibles. Ne pas sélectionner la compétition d’après un ROI déjà observé.
