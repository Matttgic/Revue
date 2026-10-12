# Revue ciblée — nflverse/nflfastR

**Avis : Référence des modèles EP/WP NFL ; `vegas_wp` incorpore la ligne de clôture et les modèles sont ajustés sur tout l'historique.**

- Source : https://github.com/nflverse/nflfastR
- Version examinée : [`701bbf38bc1c030ff9f1f4825a23191287d3903c`](https://github.com/nflverse/nflfastR/tree/701bbf38bc1c030ff9f1f4825a23191287d3903c) ; branche `master` ; dernier commit le 2026-09-18.
- Consultation : 2026-10-12.
- Famille : NFL · play-by-play, EP et WP ; stack : R.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Deux modèles de probabilité de victoire en cours de match : avec et sans `spread_line`. La version « vegas » suppose la ligne `spread_line` connue ; l'instant de capture de cette ligne dans nflverse doit être vérifié (ouverture ou clôture) avant tout usage.
- Si `spread_line` manque, le code impose 1,5 point en faveur du domicile et affiche un avertissement.
- `data-raw/MODELS.R` entraîne EP, WP et CP sur `full_train` : les EP/WP historiques sont des valeurs dans l'échantillon.

## Limites et points à contrôler

- Utiliser `vegas_wp` ou un EPA cumulé basé sur ces modèles comme variable pré-match revient à injecter le marché (peut-être la clôture) et des paramètres ajustés sur le futur.

## Enseignement pour Revue

Fiche : [REV-NFLFASTR-01](REV-NFLFASTR-01_probabilite-ancree-sur-la-ligne.md).

**Comparaison avec le catalogue :** Complète [nflreadpy](../nflreadpy/AUDIT.md), [nflverse-data](../nflverse-data/AUDIT.md), [cfbfastR](../cfbfastR/AUDIT.md) (même famille de modèles).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `R/helper_add_ep_wp.R`, `R/ep_wp_calculators.R`, `data-raw/MODELS.R`.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [DESCRIPTION](https://github.com/nflverse/nflfastR/blob/701bbf38bc1c030ff9f1f4825a23191287d3903c/DESCRIPTION)
- [R/helper_add_ep_wp.R](https://github.com/nflverse/nflfastR/blob/701bbf38bc1c030ff9f1f4825a23191287d3903c/R/helper_add_ep_wp.R)
- [R/ep_wp_calculators.R](https://github.com/nflverse/nflfastR/blob/701bbf38bc1c030ff9f1f4825a23191287d3903c/R/ep_wp_calculators.R)
- [data-raw/MODELS.R](https://github.com/nflverse/nflfastR/blob/701bbf38bc1c030ff9f1f4825a23191287d3903c/data-raw/MODELS.R)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
