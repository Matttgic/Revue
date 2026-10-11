# Revue ciblée — gotoConversion/goto_conversion

**Avis : Formule à comparer ; paquet actuel trop hétérogène pour une adoption directe.**

- Source demandée : https://github.com/gotoConversion/goto_conversion
- URL résolue : https://github.com/gotoConversion/goto_conversion
- Version examinée : [`4c5c07e126fb4f574035dcbf62b6182d7764ba6c`](https://github.com/gotoConversion/goto_conversion/tree/4c5c07e126fb4f574035dcbf62b6182d7764ba6c) ; branche `main`.
- Consultation : 2026-10-11.
- Famille : Multi-sports · retrait de marge ; stack : Python.
- Priorité de recherche : **P2** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **Texte MIT ; titulaire indiqué Python Packaging Authority** ([texte à cette version](https://github.com/gotoConversion/goto_conversion/blob/4c5c07e126fb4f574035dcbf62b6182d7764ba6c/LICENSE.txt)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- goto_conversion retire une marge selon des poids sqrt(1−p), puis prévoit un repli multiplicatif pour certaines cotes imprudentes.
- efficient_shin_conversion construit des z par issue et renormalise. Sur [2,6 ; 2,4 ; 4,3], son écart maximal à Shin itératif vaut 0,00287707 ; les fonctions ne sont donc pas interchangeables numériquement.
- Le même module contient des fonctions de conversion d’images et de paraphrase sans rapport avec les cotes.

## Limites et points à contrôler

- Les récompenses Kaggle affichées dans le README ne démontrent pas un ROI de paris.
- Les blocs except larges peuvent masquer la cause d’une erreur. Examiner les entrées, probabilités négatives et chemins numpy avant réutilisation.
- La licence contient un crédit générique ; sa présence ne certifie pas toute la provenance.

## Enseignement pour Revue

Comparer mathématiquement les conversions, sans ajouter les fonctions annexes au projet.

**Comparaison avec le catalogue :** Complète Shin et le dé-vig déjà catalogué ; contre-exemple utile à l’assimilation nom de méthode = calcul identique.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Quatre fonctions mathématiques extraites par AST, chemin listes Python exécuté ; imports annexes et paquet complet non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/gotoConversion/goto_conversion/blob/4c5c07e126fb4f574035dcbf62b6182d7764ba6c/README.md)
- [goto_conversion/__init__.py](https://github.com/gotoConversion/goto_conversion/blob/4c5c07e126fb4f574035dcbf62b6182d7764ba6c/goto_conversion/__init__.py)
- [LICENSE.txt](https://github.com/gotoConversion/goto_conversion/blob/4c5c07e126fb4f574035dcbf62b6182d7764ba6c/LICENSE.txt)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
