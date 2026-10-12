# Revue ciblée — robjhyndman/cricketdata

**Avis : Point d'entrée sérieux (auteur : Rob Hyndman) vers les données de cricket ; aucun modèle de pari.**

- Source : https://github.com/robjhyndman/cricketdata
- Version examinée : [`c87fb8cfcd4b1a39f5f5d53e0f549014debff082`](https://github.com/robjhyndman/cricketdata/tree/c87fb8cfcd4b1a39f5f5d53e0f549014debff082) ; branche `master` ; dernier commit le 2025-07-22.
- Consultation : 2026-10-12.
- Famille : Cricket · données Cricinfo et Cricsheet ; stack : R.
- Priorité de recherche : **P3** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : GPL-3.

## Ce que la source permet d'établir

- Fonctions `fetch_cricinfo`, `fetch_cricsheet`, `fetch_player_data` : formats test, ODI, T20, hommes et femmes, données balle par balle via Cricsheet.
- Le README renvoie aux conditions d'utilisation de chaque site.

## Limites et points à contrôler

- Les conditions d'utilisation d'ESPNCricinfo limitent l'extraction ; Cricsheet est la voie à privilégier.

## Enseignement pour Revue

Ouvre la porte au cricket (absent de Revue) si le marché est disponible en France.

**Comparaison avec le catalogue :** Ajoute un sport non couvert par le catalogue.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README et de la DESCRIPTION.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/robjhyndman/cricketdata/blob/c87fb8cfcd4b1a39f5f5d53e0f549014debff082/README.md)
- [DESCRIPTION](https://github.com/robjhyndman/cricketdata/blob/c87fb8cfcd4b1a39f5f5d53e0f549014debff082/DESCRIPTION)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
