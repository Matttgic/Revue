# Revue NHL Independent — modèle prototype exécutable

**Statut : calcul et tests opérationnels ; rentabilité et calibration non démontrées.**

Modèle original développé pour Revue à partir de concepts généraux identifiés lors de l'[audit Clairvoyance](../../analyses/2026-10-09_Purple-Wraith_clairvoyance-backend.md). Aucun code ni jeu de données du projet tiers n'a été copié (licence non précisée).

## Capacités V0.1

- [Python NHL](nhl_independant.py) : récupération du calendrier et des résultats de la saison en cours et de la précédente depuis l'API Web NHL sans clé.
- Elo, buts marqués et encaissés lissés vers la saison précédente, probabilité Poisson, indicateur simplifié de prolongation.
- Estimations moneyline et de plus de 4,5 / 5,5 / 6,5 buts pour les rencontres futures dans une fenêtre de deux jours civils à Paris.
- Horodatage, identifiant NHL et nombre de matchs historiques utilisés ; matchs démarrés exclus.
- [Tests unitaires](../../tests/test_nhl_independant.py) et [GitHub Actions](../../.github/workflows/nhl-independent.yml) pour automatiser la sortie dans [docs/nhl-model-latest.json](../../docs/nhl-model-latest.json).
- [Page adaptée au smartphone](../../docs/nhl-model.html).

## Déclenchement manuel

Depuis un smartphone, ouvrir GitHub → dépôt Revue → Actions → Revue - NHL Independent → Run workflow. Lancer aussi les tests :

    python -m unittest discover -s tests -p test_nhl_independant.py -v

Puis, sans dépendances Python externes :

    python modeles/simulations/nhl_independant.py --days 2 --output docs/nhl-model-latest.json

Une date optionnelle --date AAAA-MM-JJ ne transforme PAS la prédiction en backtest passé : le programme ne prédit que les rencontres non démarrées à l'heure réelle du calcul.

Pour voir la page comme site depuis un navigateur : Settings → Pages → Deploy from a branch → main → /docs. Le lien https://matttgic.github.io/Revue/nhl-model.html sera utilisable uniquement si GitHub Pages est activé et effectivement déployé.

## Ce que ce moteur NE fait PAS encore

- Il ne reproduit pas le système complet Clairvoyance. Aucune copie fidèle des poids ou des backtests.
- Pas de gardien titulaire confirmé, xG ou absences injectés dans le moteur V0.1 ; pas de prop buteur.
- Pas de cotes de bookmakers français, pas de calcul EV, ni de recommandation de mise.
- Probabilités **non calibrées** ; la modélisation Poisson des scores incluant prolongations reste approximative.
- Aucun historique de snapshots validés au temps T pour démontrer un rendement hors échantillon.
- L'API NHL ou les droits de réutilisation de ses données peuvent évoluer. Toute utilisation doit respecter les conditions de la source.

## Étape suivante de validation

Backtests walk-forward et Brier / log loss par saison, benchmark probabilités bookmaker hors marge avec cotes réelles au temps T, erreurs de calibration et journal paper prospectif. La précision d'un modèle et son ROI ne sont pas démontrés par le bon fonctionnement des tests unitaires.
