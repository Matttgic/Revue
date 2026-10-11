# Revue ciblée — Torvaney/regista

**Avis : Référence pédagogique claire ; intérêt surtout pour comprendre et étendre les formules.**

- Source demandée : https://github.com/Torvaney/regista
- URL résolue : https://github.com/Torvaney/regista
- Version examinée : [`8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933`](https://github.com/Torvaney/regista/tree/8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933) ; branche `master`.
- Consultation : 2026-10-11.
- Famille : Football · Dixon–Coles extensible ; stack : R.
- Priorité de recherche : **P2** ; ce classement exprime l’utilité pour Revue, pas la rentabilité.
- Licence observée : **GPL-3** ([texte à cette version](https://github.com/Torvaney/regista/blob/8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933/LICENSE)).
- Maintenance : version publique accessible à la consultation ; historique des commits et état complet de la CI non audités. Les indications spécifiques du README sont rapportées ci-dessous.

## Ce que la source permet d’établir

- Dixon–Coles est exprimé par formules séparées domicile/extérieur avec effets offensifs, défensifs et domicile.
- dixoncoles_ext utilise optim, BFGS par défaut, et autorise des pondérations explicites.
- Le README indique un statut expérimental et renvoie vers des exemples avec xG.

## Limites et points à contrôler

- Les poids, covariables et dates fournis par l’utilisateur déterminent la causalité ; l’API ne constitue pas à elle seule un protocole hors échantillon.
- Pas de benchmark de rentabilité reproduit ; installation R et exemples externes non exécutés.

## Enseignement pour Revue

Comparer deux implémentations Dixon–Coles sur les mêmes entrées et documenter les écarts de conventions.

**Comparaison avec le catalogue :** Confirme une méthode déjà présente ; pas de nouvelle fiche Dixon–Coles redondante.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données, de dépendances ou de modèle dans les autres projets.

## Niveau de preuve

Lecture ciblée de l’ajustement et de la correction des petits scores ; tests non exécutés.

Cette revue est ciblée, pas un audit exhaustif du dépôt ou de sa sécurité. Les suites de tests complètes ne sont pas exécutées. Aucun avantage économique n’est démontré par cet examen. Score d’intérêt chiffré : **NC**, pour éviter une précision artificielle.

## Sources consultées ou repérées

- [README.md](https://github.com/Torvaney/regista/blob/8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933/README.md)
- [R/dixoncoles.R](https://github.com/Torvaney/regista/blob/8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933/R/dixoncoles.R)
- [DESCRIPTION](https://github.com/Torvaney/regista/blob/8f114d9a0a0bbfa2a3f85be4fe2b1ded1a0d1933/DESCRIPTION)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-11/README.md) · [Index des analyses](../README.md)
