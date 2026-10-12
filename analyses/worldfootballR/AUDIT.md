# Revue ciblée — JaseZiv/worldfootballR

**Avis : Connecteurs football très complets, dont valeurs Transfermarkt datées et suspensions ; dépôt archivé.**

- Source : https://github.com/JaseZiv/worldfootballR
- Version examinée : [`72af453f9eeaf1199f654c9433d24d7b6afbb2f2`](https://github.com/JaseZiv/worldfootballR/tree/72af453f9eeaf1199f654c9433d24d7b6afbb2f2) ; branche `main` ; dernier commit le 2025-09-19.
- Consultation : 2026-10-12.
- Famille : Football · collecte FBref / Transfermarkt / Understat ; stack : R.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : GPL-3.

## Ce que la source permet d'établir

- Le README indique que le paquet et son dépôt de données ne sont plus maintenus.
- Fonctions Transfermarkt avec dates (`tm_player_market_values`, `tm_each_team_player_market_val`, `tm_get_suspensions`, `tm_get_risk_of_suspensions`) : la valeur marchande et la disponibilité peuvent être reliées à une date, contrairement à la valeur annuelle du tutoriel Betfair.

## Limites et points à contrôler

- Les connecteurs dépendent de sites tiers aux conditions d'utilisation restrictives ; vérifier les droits avant toute collecte.
- Aucune garantie de fonctionnement après l'archivage.

## Enseignement pour Revue

Inspirer un collecteur de suspensions et de valeurs marchandes datées, en conservant la date de capture.

**Comparaison avec le catalogue :** Complète [soccerdata](../soccerdata/AUDIT.md) (même famille de connecteurs) avec Transfermarkt.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Lecture du README, DESCRIPTION, NEWS. Non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.md](https://github.com/JaseZiv/worldfootballR/blob/72af453f9eeaf1199f654c9433d24d7b6afbb2f2/README.md)
- [DESCRIPTION](https://github.com/JaseZiv/worldfootballR/blob/72af453f9eeaf1199f654c9433d24d7b6afbb2f2/DESCRIPTION)
- [NEWS.md](https://github.com/JaseZiv/worldfootballR/blob/72af453f9eeaf1199f654c9433d24d7b6afbb2f2/NEWS.md)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
