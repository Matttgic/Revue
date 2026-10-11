# Revue ciblée — mcekovic/tennis-crystal-ball

**Avis : Très riche pour étudier le tennis ; adoption complète coûteuse.**

- Source demandée : https://github.com/mcekovic/tennis-crystal-ball
- URL résolue : https://github.com/mcekovic/tennis-crystal-ball
- Version examinée : [`fcda1e607deb289369a0ce37d0f8c756b97910a6`](https://github.com/mcekovic/tennis-crystal-ball/tree/fcda1e607deb289369a0ce37d0f8c756b97910a6) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Tennis · Elo, matchs et tournois ; stack : Java / PostgreSQL / Spring.
- Priorité de recherche : **P2** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **Apache-2.0 pour le code ; données amont distinctes** ([texte à cette version](https://github.com/mcekovic/tennis-crystal-ball/blob/fcda1e607deb289369a0ce37d0f8c756b97910a6/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Elo général et par surface, prédictions de matchs et projections de tournois.
- RankingMatchPredictor transforme les écarts Elo en probabilités ; les classes d’issue décrivent la structure jeu/set/match.
- InMatchPredictor ajuste les probabilités service/retour vers une probabilité de match cible ; le README documente des chargeurs basés sur des données Jeff Sackmann anciennes.

## Limites et points à contrôler

- Les données amont Jeff Sackmann testées aujourd’hui renvoient 404 ; cela ne prouve pas une suppression définitive, mais bloque cette voie de reproduction dans la session.
- Le normaliseur inspecté utilise une boucle sans borne explicite ; vérifier convergence et domaine des entrées avant usage.
- La causalité complète des classements, le tuning et les performances face aux cotes restent non vérifiés.

## Enseignement pour Revue

Comparer Elo par surface à une conversion service/retour → match, en distinguant formats best-of et règles de tie-break.

**Comparaison avec le catalogue :** Complète ATPBetting et le modèle Elo tennis de Revue avec une décomposition liée aux règles du jeu.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Classes de prédiction ciblées lues ; application Java et base non lancées.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/mcekovic/tennis-crystal-ball/blob/fcda1e607deb289369a0ce37d0f8c756b97910a6/README.md)
- [tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/RankingMatchPredictor.java](https://github.com/mcekovic/tennis-crystal-ball/blob/fcda1e607deb289369a0ce37d0f8c756b97910a6/tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/RankingMatchPredictor.java)
- [tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/InMatchPredictor.java](https://github.com/mcekovic/tennis-crystal-ball/blob/fcda1e607deb289369a0ce37d0f8c756b97910a6/tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/InMatchPredictor.java)
- [tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/MatchOutcome.java](https://github.com/mcekovic/tennis-crystal-ball/blob/fcda1e607deb289369a0ce37d0f8c756b97910a6/tennis-stats/src/main/java/org/strangeforest/tcb/stats/model/prediction/MatchOutcome.java)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
