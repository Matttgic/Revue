# Revue ciblée — danmorse314/hockeyR

**Avis : Bon client R du play-by-play NHL avec xG public ; xG historique dans l'échantillon d'entraînement et données hors saison 2023-24 non mises à jour.**

- Source : https://github.com/danmorse314/hockeyR
- Version examinée : [`e8a11bd30755e2e015e26e18cd766bf36939a8d2`](https://github.com/danmorse314/hockeyR/tree/e8a11bd30755e2e015e26e18cd766bf36939a8d2) ; branche `master` ; dernier commit le 2024-03-14.
- Consultation : 2026-10-12.
- Famille : Hockey NHL · play-by-play et xG ; stack : R.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Deux modèles xG XGBoost (5 contre 5 et situations spéciales) sont livrés dans `sysdata.rda` ; variables : distance, angle, rebond (≤ 2 s), rush (≤ 4 s depuis zone neutre/défensive), traversée de l'enclave, type de l'événement précédent, indicatrices d'époque.
- Le scraper a été adapté à la nouvelle API NHL (v1.4.0).
- Le dépôt compagnon `hockeyR-data` (dernier commit 25/06/2024) s'arrête à la saison 2023-24.

## Limites et points à contrôler

- Les modèles xG ont été entraînés sur des saisons qu'ils servent ensuite à décrire : l'xG d'un match ancien contient de l'information des saisons suivantes. Pour une variable pré-match, ré-entraîner l'xG sur les seules saisons antérieures.
- Dernier commit du paquet en mars 2024.

## Enseignement pour Revue

Piste pour reconstruire un xG NHL indépendant de MoneyPuck dans Revue, à condition de l'entraîner saison par saison.

**Comparaison avec le catalogue :** Complète [nhl-savant](../nhl-savant/AUDIT.md) et `REV-CLAIR-01` (xG MoneyPuck) avec un xG ouvert et documenté.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture de `R/calculate_xg.R`, `R/prepare_xg_data.R`, NEWS, README ; dépôt de données inspecté (commit et taille des fichiers).

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/README.md)
- [DESCRIPTION](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/DESCRIPTION)
- [LICENSE](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/LICENSE)
- [NEWS.md](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/NEWS.md)
- [R/calculate_xg.R](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/R/calculate_xg.R)
- [R/prepare_xg_data.R](https://github.com/danmorse314/hockeyR/blob/e8a11bd30755e2e015e26e18cd766bf36939a8d2/R/prepare_xg_data.R)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
