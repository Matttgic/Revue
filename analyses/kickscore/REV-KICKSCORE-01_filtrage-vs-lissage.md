# REV-KICKSCORE-01 — Forces dynamiques : filtrer pour prédire, lisser pour décrire

- Statut : **À étudier**.
- Sport : multi-sports (NHL, football, tennis). Marché/usage : victoire, 1N2, différence de score.
- Source et version : [audit du dépôt](AUDIT.md).
- Preuve : lecture ciblée du code ; protocole ci-dessous non exécuté.

## Idée

Remplacer l'Elo (K fixe) par un processus gaussien de la force de chaque équipe dont la vitesse de variation est estimée (noyaux Wiener, Matérn, constant + Wiener…). Les modèles d'observation de kickscore couvrent la victoire, le nul (marge), la différence de score et les buts (Poisson/Skellam).

## Piège à éviter

`model.fit()` combine un filtre de Kalman et un **lisseur RTS** : la force estimée au 1er novembre utilise aussi les matchs de décembre. C'est parfait pour décrire l'histoire, faux pour un backtest. Pour prédire un match à la date t :

1. n'observer que les matchs antérieurs à t ;
2. ajuster ;
3. interroger `probabilities(..., t)`.

Ré-ajuster chaque jour de match coûte cher ; regrouper par journée et réutiliser l'état précédent comme initialisation.

## Protocole proposé

Comparer, sur les mêmes matchs NHL 2011-2021 (cotes de clôture de l'archive sportsbookreview) : Elo Revue, kickscore binaire (constant + Wiener), kickscore Skellam. Mesurer log-loss et calibration contre la probabilité de clôture dé-margée ; hyperparamètres du noyau choisis sur les saisons antérieures.

## Limites

Pas de gain démontré. Coût de calcul élevé en walk-forward. Licence MIT : réutilisation possible avec mention.
