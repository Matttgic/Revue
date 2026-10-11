# Revue ciblée — mberk/shin

**Avis : Petite référence utile pour comparer les probabilités implicites.**

- Source demandée : https://github.com/mberk/shin
- URL résolue : https://github.com/mberk/shin
- Version examinée : [`ae460853fabeca7d512bbf7de8aaa55dc17f3485`](https://github.com/mberk/shin/tree/ae460853fabeca7d512bbf7de8aaa55dc17f3485) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · retrait de marge ; stack : Python / Rust.
- Priorité de recherche : **P1** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **MIT** ([texte à cette version](https://github.com/mberk/shin/blob/ae460853fabeca7d512bbf7de8aaa55dc17f3485/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Implémente Shin avec paramètre z, tolérance et diagnostic de convergence ; solveur Rust et solution Python.
- Le README précise que le cas à deux issues équivaut à la méthode additive.
- Optimiseur Python isolé reproduit sur [2,6 ; 2,4 ; 4,3] : [0,3729940603 ; 0,4047794109 ; 0,2222265287], somme à 1 à environ 5e−13 près.

## Limites et points à contrôler

- z est un paramètre du modèle, pas une mesure indépendante de paris informés.
- Une probabilité sans marge ne devient pas une probabilité vraie ; choisir une méthode sur le passé et vérifier par marché. La convergence doit être contrôlée.
- Extension Rust et installation du paquet non testées ; le contrôle extrait uniquement la fonction Python par AST.

## Enseignement pour Revue

Ajouter Shin au benchmark du retrait de marge, avec normalisation et power, sur des matchs communs.

**Comparaison avec le catalogue :** Complète la piste de dé-vig existante ; ne justifie pas une nouvelle stratégie de value à elle seule.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Exemple numérique vérifié avec optimiseur Python isolé ; aucun backtest de paris.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/mberk/shin/blob/ae460853fabeca7d512bbf7de8aaa55dc17f3485/README.md)
- [python/shin/__init__.py](https://github.com/mberk/shin/blob/ae460853fabeca7d512bbf7de8aaa55dc17f3485/python/shin/__init__.py)
- [src/lib.rs](https://github.com/mberk/shin/blob/ae460853fabeca7d512bbf7de8aaa55dc17f3485/src/lib.rs)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
