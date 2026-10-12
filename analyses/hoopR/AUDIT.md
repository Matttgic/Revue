# Revue ciblée — sportsdataverse/hoopR

**Avis : Client R très actif (dernier commit 11/10/2026) pour NBA et NCAA ; utile pour les données de match, pas pour l'historique des blessures.**

- Source : https://github.com/sportsdataverse/hoopR
- Version examinée : [`ad593c7f46e92c8bda5ff2415a5b575a1e1c0a56`](https://github.com/sportsdataverse/hoopR/tree/ad593c7f46e92c8bda5ff2415a5b575a1e1c0a56) ; branche `main` ; dernier commit le 2026-10-11.
- Consultation : 2026-10-12.
- Famille : NBA / NCAA basket · données ; stack : R.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : MIT.

## Ce que la source permet d'établir

- Sources : ESPN (dont aides `event_betting`, `futures`, `powerindex`, `injuries`), NBA Stats, Basketball-Reference, CollegeBasketballData (`cbbd_lines`, clé requise).
- Les fonctions `load_*` lisent des assets de release `sportsdataverse-data`, reconstruits la nuit : même réserve que nflverse sur les fichiers remplaçables.

## Limites et points à contrôler

- Les points d'accès « blessures » donnent un état courant, pas un historique daté : inutilisables pour un backtest sans archivage propre.

## Enseignement pour Revue

Brique de collecte NBA/NCAAB ; archiver soi-même les blessures et lignes à chaque collecte.

**Comparaison avec le catalogue :** Complète [nba_api](../nba_api/AUDIT.md) et `REV-ERIKNBA-02` (disponibilité pré-match).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README, DESCRIPTION et liste des fonctions. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/sportsdataverse/hoopR/blob/ad593c7f46e92c8bda5ff2415a5b575a1e1c0a56/README.md)
- [DESCRIPTION](https://github.com/sportsdataverse/hoopR/blob/ad593c7f46e92c8bda5ff2415a5b575a1e1c0a56/DESCRIPTION)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
