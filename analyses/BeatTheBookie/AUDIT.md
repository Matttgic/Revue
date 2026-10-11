# Audit — Lisandro79/BeatTheBookie

- **Source :** https://github.com/Lisandro79/BeatTheBookie
- **Auteurs du papier cité :** Lisandro Kaunitz, Shenjun Zhong et Javier Kreiner
- **Commit examiné :** `7add209d0d097af0f8b714e388cf05849db7f969` (`master`), 5 octobre 2021
- **Date de consultation :** 11 octobre 2026
- **Licence du code :** GNU GPL v3. Le README décrit des bases de données hébergées séparément; leur licence et leurs droits de redistribution ne sont pas précisés par cette licence logicielle.
- **État :** dépôt ancien, sans suite de tests ni intégration continue repérée; dernières modifications examinées en 2021.
- **Stack :** MATLAB/Octave, anciens scripts Python, PHP et SQL/MySQL.

## Résumé et méthode

Le dépôt accompagne l'article de 2017 [*Beating the bookies with their own numbers*](https://arxiv.org/abs/1710.02824). Il compare la moyenne des cotes de plusieurs bookmakers au meilleur prix disponible sur un même marché 1N2. Pour chaque issue, l'implémentation utilise `q = 1 / cote_moyenne − 0,05`, calcule `q × meilleure_cote − 1`, exige plus de trois prix valides et mise une unité fixe sur l'issue présentant la valeur calculée la plus élevée si elle est positive.

La variante temporelle parcourt des snapshots horaires entre cinq et une heure avant le coup d'envoi et prend le premier instant admissible; le générateur prépare jusqu'à 72 heures de prix par bookmaker et par issue. Une mise fixe de 50 est utilisée dans les exemples principaux. Le dépôt comprend aussi des contrôles aléatoires, des graphiques de calibration et une analyse de transactions de paper trading et de paris réels.

## Données et reproductibilité

Le README annonce trois historiques : 880 494 matchs de football et cotes de clôture sur 912 ligues (2000–2015), puis 31 074 et 82 786 matchs avec séries de cotes en 2015–2016. Il précise que les dumps MySQL sont d'environ 1,8 Go et les distribue par liens Google Drive/Dropbox. Aucun fichier de données n'est suivi dans le dépôt Git; les CSV de paper trading et de paris réels sont eux aussi externes. Le code seul ne suffit donc pas à reproduire les courbes ou les résultats rapportés.

Le README décrit une plage de données de clôture allant de 2000 à 2015, alors que le SQL d'export suivi dans Git filtre du 1er janvier 2005 au 1er juillet 2015. Ce décalage doit être résolu avant de prétendre reproduire exactement l'expérience.

La comparaison est une hypothèse de probabilité, pas une probabilité calibrée : la correction additive de 5 points est fixe pour les issues, ligues et périodes. Comme la moyenne et le maximum proviennent du même groupe de bookmakers, le choix du maximum après avoir examiné toutes les offres est exposé à un biais de sélection. Les prix de clôture ne prouvent pas qu'un client pouvait encore obtenir le maximum au moment de miser; la variante par séries horaires réduit ce problème, sans fournir à elle seule un registre d'exécution auditable.

## Vérifications et limites

- **Exécution et tests :** aucune suite de tests n'est fournie. La reproduction n'a pas été exécutée : les données externes manquent et Octave n'est pas installé dans l'environnement d'audit.
- **Résultats :** le dépôt fournit le code des figures de l'article, mais pas les sorties de calcul ni les registres nécessaires dans le checkout. La série de paper trading/paris réels annoncée dans le README n'a pas pu être contrôlée; rentabilité indépendante non démontrée ici.
- **Erreur de calcul observée :** dans `Figure3.m`, `real_betting_return` divise le profit de paper trading (`money_paperTrading(end)`) par le nombre de paris réels. Le profit réel est calculé séparément, mais le rendement réel imprimé n'utilise pas le bon numérateur.
- **Scripts Python :** `Figure2A.py` utilise `xrange`, incompatible avec Python 3, et remplit `sample_mean_odds` avec les colonnes de cotes maximales. Le README recommande plutôt les scripts MATLAB; cette version Python n'est donc pas une voie de reproduction fiable sans correction.
- **Inférence :** le témoin reprend les fréquences d'issues de la stratégie estimées sur l'échantillon étudié. Les scripts tirent les matchs sans remplacement dans chaque simulation (les mêmes matchs peuvent revenir dans des simulations différentes). Ce contrôle ne remplace pas une période de test chronologique ni une validation prospective. Les interceptions utilisées pour l'« accuracy attendue » sont calculées sur les mêmes données historiques.
- **Droits des données :** aucune licence explicite des archives de cotes n'est indiquée dans le dépôt; vérifier auprès du fournisseur avant tout usage ou redistribution.
- **Sécurité :** les scripts PHP d'export contiennent des identifiants MySQL d'exemple en dur (`root` / `toor`). Ne pas les réutiliser; ils n'ont pas été exécutés.
- **Interface en ligne :** le README renvoie à une adresse IP et un port historiques; leur disponibilité actuelle n'est pas confirmée.
- **Score :** non attribué; résultats et données ne sont pas reproductibles à partir du checkout seul.

## Idée retenue et décision

La valeur documentaire est réelle : cet article est une origine importante de la méthode de comparaison au consensus que le dépôt `georgedouzas/sports-betting` cite et que la stratégie `REV-SBT-01` représente déjà dans Revue. Je conserve donc la provenance, la variante horaire et les limites dans ce dossier source, **sans créer une entrée méthode en double**. La grosse base historique pourrait servir à une réplication si ses fichiers et droits sont obtenus; en l'état, ses résultats ne doivent pas être utilisés comme preuve de rendement.

Pour une réplication : obtenir un instantané immuable des données et les droits associés; comparer à une baseline de marché dé-margée indépendante; fixer `alpha` uniquement sur une fenêtre d'entraînement; évaluer sur des dates ultérieures, par ligue et par période; mesurer Brier/log-loss, ROI, CLV, disponibilité effective du meilleur prix et incertitude; auditer les transactions réelles séparément du paper trading.

## Références examinées

Liens épinglés au commit audité : [README et description des jeux](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/README.md), [stratégie sur cotes de clôture](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/src/strategies/beatTheBookie.m), [stratégie temporelle](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/src/strategies/beatTheBookie_timeseries.m), [comparaison historique et témoin aléatoire](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/src/Figure2A.m), [paper/real betting et rendement imprimé](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/src/Figure3.m), [export SQL CSV](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/sql/closing_odds_csv_export.sql), [générateur PHP des séries](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/src/generate_odds_series_csv.php), [licence GPL-3.0](https://github.com/Lisandro79/BeatTheBookie/blob/7add209d0d097af0f8b714e388cf05849db7f969/LICENSE).

## Provenance et modifications

Dépôt source consulté en lecture seule au commit indiqué. Aucun code, fichier de données, secret d'accès ou résultat n'a été importé dans Revue. Seul cet audit, son index de dossier et les entrées centrales d'inventaire ont été ajoutés.
