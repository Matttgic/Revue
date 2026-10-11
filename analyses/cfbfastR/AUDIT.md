# Revue ciblée — sportsdataverse/cfbfastR

**Avis : Intéressant pour les modèles de situation et les contrats de variables.**

- Source demandée : https://github.com/sportsdataverse/cfbfastR
- URL résolue : https://github.com/sportsdataverse/cfbfastR
- Version examinée : [`b70abc835594f974ec4f93c9d8c7271d58370583`](https://github.com/sportsdataverse/cfbfastR/tree/b70abc835594f974ec4f93c9d8c7271d58370583) ; branche `main`.
- Consultation : 2026-10-11.
- Famille : Football américain NCAA · données et modèles EP/WP ; stack : R / modèles externes.
- Priorité de recherche : **P2** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT pour le code ; droits des sources à vérifier** ([texte à cette version](https://github.com/sportsdataverse/cfbfastR/blob/b70abc835594f974ec4f93c9d8c7271d58370583/LICENSE.md)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Interface de données CollegeFootballData et chargement de données publiées ; modèles de points attendus et probabilité de victoire.
- model_cards.R lit la liste ordonnée des variables et le contrat d’ère du modèle publié.
- Le commentaire documente un ancien décalage d’encodage d’ère ; le cache de fiche est lié à la date du booster pour éviter une fiche obsolète.

## Limites et points à contrôler

- Les modèles EP/WP décrivent une situation de jeu ; ils ne prouvent pas une stratégie rentable sur les lignes bookmaker.
- Une date de fichier est un garde-fou utile mais une empreinte du modèle et de sa fiche est plus forte pour figer une expérience.
- Dépendances, clés API et assets modèles non chargés ; performances non reproduites.

## Enseignement pour Revue

Sauvegarder avec chaque modèle le schéma ordonné, les transformations, la période d’entraînement et les empreintes des assets.

**Comparaison avec le catalogue :** Ajoute une méthode de contrôle des artefacts qui complète les gates et réparations de sports_prediction_model.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Contrat des model cards examiné ; modèles non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/sportsdataverse/cfbfastR/blob/b70abc835594f974ec4f93c9d8c7271d58370583/README.md)
- [R/model_cards.R](https://github.com/sportsdataverse/cfbfastR/blob/b70abc835594f974ec4f93c9d8c7271d58370583/R/model_cards.R)
- [DESCRIPTION](https://github.com/sportsdataverse/cfbfastR/blob/b70abc835594f974ec4f93c9d8c7271d58370583/DESCRIPTION)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
