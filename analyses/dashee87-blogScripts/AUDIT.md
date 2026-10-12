# Revue ciblée — dashee87/blogScripts

**Avis : Tutoriel Dixon–Coles avec décroissance temporelle très cité ; pédagogique, mais le choix de ξ est fait sur la période évaluée.**

- Source : https://github.com/dashee87/blogScripts
- Version examinée : [`526bca57777258e55a140e557e3fa3b813441780`](https://github.com/dashee87/blogScripts/tree/526bca57777258e55a140e557e3fa3b813441780) ; branche `master` ; dernier commit le 2018-09-13.
- Consultation : 2026-10-12.
- Famille : Football · tutoriel Dixon–Coles ; stack : Python / R.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Implémentation complète : vraisemblance DC, correction τ, décroissance exp(−ξ·t), conversion en 1N2.
- `build_temp_model` entraîne sur les matchs antérieurs à chaque fenêtre de trois jours puis score la fenêtre : la prédiction d'un match est bien hors échantillon.
- La contrainte d'identification `sum(x[:20]) - 20` est codée pour 20 équipes. Sur cinq saisons de Premier League il y a plus de 20 équipes : la contrainte porte alors sur les 20 premières par ordre alphabétique. Cela ne change pas les probabilités, seulement l'échelle des paramètres.

## Limites et points à contrôler

- ξ est retenu en comparant le score prédictif sur les mêmes saisons que celles rapportées : sélection d'hyperparamètre dans l'échantillon d'évaluation.
- Optimisation `minimize` par boucle Python sur chaque ligne : très lent.
- Aucune comparaison au marché.

## Enseignement pour Revue

Réutiliser le protocole « entraîner avant la fenêtre, scorer la fenêtre », mais choisir ξ sur des saisons antérieures à celles rapportées.

**Comparaison avec le catalogue :** Recoupe [mezzala](../mezzala/AUDIT.md) (poids exponentiels) et [penaltyblog](../penaltyblog/AUDIT.md). N'ajoute pas de méthode nouvelle au catalogue.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du script `dixon_coles_decay_xi_5season.py`. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [LICENSE](https://github.com/dashee87/blogScripts/blob/526bca57777258e55a140e557e3fa3b813441780/LICENSE)
- [README.md](https://github.com/dashee87/blogScripts/blob/526bca57777258e55a140e557e3fa3b813441780/README.md)
- [Python/2018-09-13-dixon-coles-and-time-weighting/dixon_coles_decay_xi_5season.py](https://github.com/dashee87/blogScripts/blob/526bca57777258e55a140e557e3fa3b813441780/Python/2018-09-13-dixon-coles-and-time-weighting/dixon_coles_decay_xi_5season.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
