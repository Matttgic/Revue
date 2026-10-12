# Revue ciblée — HarryShomer/Hockey-Scraper

**Avis : Scraper NHL de référence (PBP + présences depuis 2007-08) ; officiellement non maintenu, mais ses points d'accès répondent encore.**

- Source : https://github.com/HarryShomer/Hockey-Scraper
- Version examinée : [`983ffc4640fa29b62eb9af93fcf753c15b4cf471`](https://github.com/HarryShomer/Hockey-Scraper/tree/983ffc4640fa29b62eb9af93fcf753c15b4cf471) ; branche `master` ; dernier commit le 2024-06-26.
- Consultation : 2026-10-12.
- Famille : Hockey NHL · collecte play-by-play et présences ; stack : Python.
- Priorité de recherche : **P2** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : GPL-3 (setup.py ; LICENSE.txt présent).

## Ce que la source permet d'établir

- Le README annonce « This repository is no longer maintained ».
- Le code utilise déjà la nouvelle API (`api-web.nhle.com/v1/...`), l'API shiftcharts et les rapports HTML. Le 12/10/2026, quatre points d'accès testés répondent en HTTP 200 (calendrier, PBP JSON, rapport HTML PL, shiftcharts).
- Fusion PBP + présences (`merge_pbp_shifts.py`) : base nécessaire pour des variables par ligne/joueur sur la glace.

## Limites et points à contrôler

- Le module ESPN pointe vers d'anciennes URL `espn.com/nhl/gamecast/data/masterFeed` non vérifiées.
- GPL-3 : pas de copie dans Revue.

## Enseignement pour Revue

Source alternative ou de contrôle pour les collecteurs NHL de Revue ; à doubler d'un test de schéma, puisque personne ne corrigera les ruptures.

**Comparaison avec le catalogue :** Complète `outils/collecte/` (NHL, MoneyPuck) ; recoupe hockeyR pour la même source NHL.

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Inventaire des URL du code et quatre requêtes HTTP réelles ; scraper non exécuté.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [README.rst](https://github.com/HarryShomer/Hockey-Scraper/blob/983ffc4640fa29b62eb9af93fcf753c15b4cf471/README.rst)
- [setup.py](https://github.com/HarryShomer/Hockey-Scraper/blob/983ffc4640fa29b62eb9af93fcf753c15b4cf471/setup.py)
- [hockey_scraper/nhl/pbp/json_pbp.py](https://github.com/HarryShomer/Hockey-Scraper/blob/983ffc4640fa29b62eb9af93fcf753c15b4cf471/hockey_scraper/nhl/pbp/json_pbp.py)
- [hockey_scraper/nhl/shifts/json_shifts.py](https://github.com/HarryShomer/Hockey-Scraper/blob/983ffc4640fa29b62eb9af93fcf753c15b4cf471/hockey_scraper/nhl/shifts/json_shifts.py)
- [hockey_scraper/utils/merge_pbp_shifts.py](https://github.com/HarryShomer/Hockey-Scraper/blob/983ffc4640fa29b62eb9af93fcf753c15b4cf471/hockey_scraper/utils/merge_pbp_shifts.py)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
