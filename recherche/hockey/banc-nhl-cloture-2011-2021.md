# REV-BANC-NHL-01 — Les modèles NHL de Revue contre la cote de clôture (2011-2021)

- Statut : **Testé — rentabilité infirmée pour le modèle seul** (backtest historique, pas un suivi réel).
- Outil : [`outils/suivi/banc_nhl_cloture.py`](../../outils/suivi/banc_nhl_cloture.py) · tests : [`tests/test_banc_nhl_cloture.py`](../../tests/test_banc_nhl_cloture.py) · résultats : [`docs/banc-nhl-cloture.json`](../../docs/banc-nhl-cloture.json).
- Données : moneylines d'ouverture et de clôture NHL de [sportsbookreview-scraper](../../analyses/sportsbookreview-scraper/AUDIT.md), commit épinglé, 13 658 matchs retenus (10 lignes sans équipe, 5 cotes incohérentes, 4 doublons, 1 date invalide exclus). Données téléchargées à l'exécution, jamais versionnées.

## Ce qui est construit, et d'où vient chaque choix

| Choix | Leçon d'origine |
|---|---|
| Chaque match du jour d est prédit avec les seuls résultats des jours ≤ d − 1 ; variante ≤ d − 2, car l'heure de l'ouverture est inconnue | Fuites relevées dans [nhl-savant](../../analyses/nhl-savant/AUDIT.md), [NBA-ML](../../analyses/NBA-Machine-Learning-Sports-Betting/AUDIT.md) ; test d'absence de fuite automatisé |
| Modèle de production `nhl_independant.predict` rejoué tel quel, plus sa variante `research_prior_fade` | Mesurer ce qui tourne réellement, pas une réécriture |
| Nouveau challenger : forces gaussiennes par équipe mises à jour par **filtrage** (probit, dérive quotidienne, retour d'intersaison) | [kickscore](../../analyses/kickscore/REV-KICKSCORE-01_filtrage-vs-lissage.md) : filtrer, jamais lisser |
| Mélange logistique « ouverture + modèle » : le modèle apporte-t-il une information que l'ouverture n'a pas ? | Shrinkage vers le marché, [REV-ERIKNBA-01](../../analyses/nba-betting/REV-ERIKNBA-01_market-shrinkage-et-cloture.md) |
| Retrait de marge choisi sur l'entraînement (> 2 erreurs-types, sinon multiplicative) → multiplicative | [REV-IMPLIED-01](../../analyses/implied/REV-IMPLIED-01_choix-devig-par-marche.md) |
| Hyperparamètres (108 configurations), mélange et modèle retenu réglés sur 2011-2014, **figés**, évalués sur 2015-2021 | [SoccerPredictor](../../analyses/SoccerPredictor/AUDIT.md), [dashee87](../../analyses/dashee87-blogScripts/AUDIT.md) : ne jamais choisir sur le test |
| Seuil de pari fixé d'avance (EV > 3 %, comme `sharp_ev_v1`), mise de 1 à la cote d'ouverture, CLV contre la clôture sans marge | [Règle de décision](../../outils/suivi/regle_decision.py) |

## Résultats sur 2015-2021 (8 900 matchs, décalage 1 jour)

| Probabilités | Log-loss | Écart à la clôture (IC 95 %) |
|---|---:|---|
| Marché — clôture | **0,66756** | — |
| Marché — ouverture | 0,66986 | +0,0023 [+0,0008 ; +0,0038] |
| Modèle Revue NHL (production) | 0,67627 | +0,0087 [+0,0061 ; +0,0113] |
| Modèle Revue, variante `prior_fade` | 0,67824 | +0,0107 [+0,0078 ; +0,0135] |
| Filtre dynamique (nouveau) | 0,67644 | +0,0089 [+0,0063 ; +0,0115] |
| Ouverture + meilleur modèle (mélange) | 0,66988 | +0,0023 [+0,0007 ; +0,0040] |

Paris à la cote d'ouverture quand l'EV dépasse 3 % :

| Stratégie | Paris | ROI (IC 95 %) | CLV moyen (IC 95 %) | Cote > clôture | Verdict (règle Revue) |
|---|---:|---|---|---:|---|
| Modèle Revue NHL seul | 4 450 | **−4,1 %** [−7,1 ; −1,1] | −2,8 % [−3,2 ; −2,4] | 40 % | **abandon** |
| Ouverture + modèle | 0 | — | — | — | non concluant (aucun pari) |

Le décalage de 2 jours donne les mêmes conclusions (ROI −4,2 %, CLV −2,8 %).

## Ce que ça veut dire

1. **Le modèle NHL de Revue est moins juste que la cote d'ouverture** (écart +0,0064 de log-loss par match) et nettement moins que la clôture. Ses « value bets » sont surtout ses erreurs : il parie contre le marché, et le marché bouge contre lui (CLV −2,8 %, 60 % des paris pris à une cote égale ou inférieure à la clôture).
2. **Il n'ajoute aucune information au marché.** Dans le mélange ajusté sur 2011-2014, le coefficient du modèle est proche de zéro ou négatif (−0,03 pour le modèle de production, +0,01 pour le filtre) ; le mélange ne pose donc aucun pari.
3. **Le filtre dynamique égale le modèle de production** (0,67644 contre 0,67627) avec un mécanisme plus simple, sans dépasser le marché non plus.
4. **Le coefficient de l'ouverture dans le mélange est d’environ 1,12 à 1,17 (> 1)** : les cotes d'ouverture de cette archive sont légèrement trop prudentes sur les favoris, ce que confirmait déjà leur calibration. C'est la seule piste qui reste, mais l'écart est faible et l'archive n'identifie pas le bookmaker.

## Conséquences pour Revue

- Ne pas utiliser le modèle NHL seul pour sélectionner des paris. C'est cohérent avec la règle v2, qui sélectionne déjà par référence sharp (Orbit Exchange en NHL), et non par le modèle.
- Un futur modèle NHL ne mérite le suivi papier que s'il réduit la log-loss **par rapport à l'ouverture** sur ce banc, avec un mélange qui lui donne un poids positif. Les variables candidates absentes ici (gardien confirmé [REV-CLAIR-02](nhl-gardien-titulaire.md), xG [REV-NHLSAV-01](../../analyses/nhl-savant/REV-NHLSAV-01_xg-regression-poisson.md), repos) peuvent être branchées sur le même banc.

## Limites

Bookmaker inconnu, heures d'ouverture et de clôture inconnues, données arrêtées en 2021-22, buts de prolongation et de tirs au but inclus dans les scores (ce qui affecte un peu les taux de buts du modèle), saison 2011-12 sans saison précédente pour le modèle de production. Un résultat négatif sur 2015-2021 n'exclut pas qu'un autre modèle fonctionne ; il montre que celui-ci ne fonctionne pas.
