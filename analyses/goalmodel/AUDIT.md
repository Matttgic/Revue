# Revue ciblée — opisthokonta/goalmodel

**Avis : Très bonne référence méthodologique pour dépasser le Poisson simple.**

- Source demandée : https://github.com/opisthokonta/goalmodel
- URL résolue : https://github.com/opisthokonta/goalmodel
- Version examinée : [`84ecd6c2bbad3ccb967abf88ef49e5bcd074e545`](https://github.com/opisthokonta/goalmodel/tree/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · distributions de scores ; stack : R / Rcpp.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **GPL-3 déclarée dans DESCRIPTION** ([texte à cette version](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/DESCRIPTION)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Modèles attaque/défense, avantage domicile, correction Dixon–Coles, binomiale négative et Conway–Maxwell–Poisson.
- La couche de prédiction transforme les intensités en scores, 1N2, BTTS et totaux ; la documentation décrit aussi l’inversion de probabilités de marché vers des buts attendus.
- Le code avertit que les prédictions après un ajustement gaussien repassent par une loi de Poisson ; il signale une approximation de troncature pour CMP surdispersé.

## Limites et points à contrôler

- Une meilleure vraisemblance sur l’échantillon d’ajustement ne démontre pas une meilleure prévision ni un rendement.
- Il faut contrôler la masse de la grille de scores et sélectionner la dispersion sur des fenêtres antérieures.
- R et les tests du paquet n’ont pas été exécutés.

## Enseignement pour Revue

Tester si la dispersion apporte un gain stable sur les totaux et BTTS ; conserver Poisson/Dixon–Coles comme références.

**Comparaison avec le catalogue :** Ajoute une comparaison explicite des distributions à la famille Poisson déjà présente ; alternative R à penaltyblog.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Documentation et fonctions de prédiction examinées ; aucune performance reproduite.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/README.md)
- [DESCRIPTION](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/DESCRIPTION)
- [R/goalmodel_predict.R](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/R/goalmodel_predict.R)
- [R/goalmodel_fit.R](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/R/goalmodel_fit.R)
- [R/cmp.r](https://github.com/opisthokonta/goalmodel/blob/84ecd6c2bbad3ccb967abf88ef49e5bcd074e545/R/cmp.r)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
