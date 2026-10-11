# REV-LMCHUGH-01 — Ensemble NFL, marge séparée et abstention ATS

**Statut : À étudier — architecture et suivi observés; aucune rentabilité démontrée.**

- **Sport / ligue :** football américain, NFL
- **Marché :** moneyline et spread ATS
- **Origine :** [`lmchugh17/nfl-betting-model`, commit `a921499`](https://github.com/lmchugh17/nfl-betting-model/tree/a92149902ce96283e2a484802c5632f18bb7760d), `src/model.py`, `src/bet_sizing.py`, `scripts/fit_bet_sizing.py`
- **Licence :** aucune licence explicite repérée; code et bases non repris
- **Audit :** [dossier complet](AUDIT.md)

## Hypothèse à tester

Estimer deux quantités distinctes : (1) la probabilité de victoire à partir d'un ensemble d'algorithmes entraînés sur des plis temporels, et (2) la marge attendue à partir d'un régresseur séparé. Comparer la marge prévue à la ligne connue au moment du pari. Sur une fenêtre passée réservée au calibrage, mesurer si la taille de l'écart absolu prédit réellement la fréquence de couverture; s'abstenir de miser quand la probabilité estimée ne dépasse pas le seuil de rentabilité au prix accessible.

Le marché est tenu à l'écart des features d'entraînement de l'ensemble; sa ligne ne sert qu'à construire l'écart post-modèle. La règle d'abstention est le point le plus utile à isoler pour une expérience : elle permet de tester si les plus grands écarts sont plus informatifs que les petits, sans supposer qu'un score de marge se convertit automatiquement en probabilité de couverture.

## Éléments disponibles

Le holdout 2025 de l'auteur rapporte 62,46 % d'exactitude, AUC 0,696, log-loss 0,632 et Brier 0,221, mais aucune métrique ne dépasse le marché. En outre, l'auteur a comparé et choisi `N_SPLITS` sur ce holdout, ce qui le rend impropre à une estimation totalement indépendante.

Dans le snapshot Git audité, les 64 matchs 2026 prédits avant le coup d'envoi donnent ATS 25–37–2 et MAE de marge 10,96 points contre 9,91 pour la ligne. Le Brier moneyline est presque identique à Polymarket (0,23672 contre 0,23689). Depuis le redémarrage du suivi de mise en septembre, la règle a recommandé zéro mise positive sur 32 résultats observés; il n'y a donc pas de rendement réalisé à évaluer.

## Protocole proposé

- Construire une vraie archive point-in-time de rapports de blessures et de prévisions météo; pour l'historique météo, utiliser des prévisions archivées au jour de décision ou retirer ces variables du test principal.
- Découper par saison complète : choisir les features, folds, transformations et calibrage avant une saison finale intouchée. Ne plus sélectionner `N_SPLITS` sur l'année de rapport.
- Enregistrer avant match l'identifiant d'événement, le bookmaker, le spread exact (`point`), le prix, l'heure de capture, les deux probabilités, la marge prévue et la règle d'abstention.
- Comparer à une baseline de marché sur les mêmes rencontres et mêmes instants : log-loss/Brier pour la moneyline, erreur de marge, calibration de couverture, ATS, CLV et rendement après marge, avec incertitude et nombre de paris.
- Vérifier séparément si la couverture augmente par tranche de `|edge|`, puis figer à l'avance le seuil minimal d'écart et les règles de taille. Une relation estimée sur le même holdout ne sert pas de validation finale.

**Verdict :** conserver l'architecture comme hypothèse de recherche match-level NFL. Sa séparation des sorties et son abstention sont testables; les chiffres actuels n'établissent pas qu'elle améliore la ligne ni qu'elle produit un rendement positif.
