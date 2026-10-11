# Audit — georgedouzas/sports-betting

- **Source :** https://github.com/georgedouzas/sports-betting
- **Auteur :** Georgios Douzas
- **Commit examiné :** `eb4cedf376663fac68f508e50b83fd832e74dfd4` (`main`), version annoncée 0.15.1; commit daté du 28 juillet 2026
- **Consultation :** 11 octobre 2026
- **Licence :** MIT dans le dépôt. Elle couvre ce code, pas nécessairement les données ni les flux de cotes utilisés. Aucun fichier tiers n'a été copié dans Revue.
- **Stack :** Python 3.11–3.13, pandas, scikit-learn, pytest; interfaces Python, CLI et MCP; Playwright facultatif pour l'exécution.
- **État :** version publiée et tests/CI configurés dans le dépôt; dernier commit examiné remonte à juillet 2026.

## Résumé technique

Bibliothèque logicielle de recherche de stratégies : un `DataLoader` assemble un flux de statistiques et un flux de cotes, puis produit les variables `X`, résultats `Y` et prix `O`. Les sources comprennent notamment football-data.co.uk, Odds API et des exemples basketball/EuroLeague. Le modèle de prévision est un estimateur scikit-learn enveloppé par un « bettor »; les outils comprennent `ClassifierBettor`, `OddsComparisonBettor`, une recherche d'hyperparamètres et un backtest chronologique. Le paquet expose aussi une CLI et un serveur MCP. Un module distinct sait surveiller un événement et placer un pari réel quand il est explicitement armé.

La meilleure contribution est le modèle de données par instantanés (`preplay`, `inplay`, `postplay`) : le code associe les variables disponibles et les prix observés à un moment donné, et borne les entrées au moment de pari. Cinq tests ciblés dans `test_leakage.py` couvrent notamment l'exclusion du score de mi-temps pour un prix pré-match. Ces tests n'ont pas été exécutés dans l'environnement de cet audit.

## Idées identifiées

| Idée | Sport | Marché | Données | Intérêt | Destination |
|---|---|---|---|---|---|
| Borner les variables à l'instant où le prix est offert; refuser une demande de variables plus tardives | Tous sports | Tous marchés | Instantanés horodatés de statistiques et de cotes | Élevé comme contrôle de validité d'un backtest; aucune preuve d'avantage prédictif | [REV-GDSB-01](REV-GDSB-01_horizon-point-in-time.md) |
| Comparer le prix offert à une moyenne de prix de marché ajustée par `alpha` | Multi-sports | Marchés à issues mutuellement exclusives | Cotes de plusieurs fournisseurs, prix offert | Baseline lisible; le paramètre et la rentabilité ne sont pas validés; proche des baselines de comparaison/dé-vig déjà cataloguées | Documenté ici, sans ligne distincte |

## Vérifications et limites

- **Installation / exécution :** non tentées; `pytest` n'est pas installé dans l'environnement, donc ni tests ciblés ni suite complète n'ont été lancés.
- **Tests :** le dépôt contient une suite organisée par modules et des tests de non-fuite temporelle; leur présence n'est pas un résultat d'exécution.
- **Rendement :** le README publie cinq plis d'exemple avec un ROI entre −15,8 % et +54,1 %. Ce sont les résultats de l'auteur sur son jeu d'exemple; ni les données ni les chiffres n'ont été reproduits. Ils ne démontrent pas une rentabilité prospective. Aucun CLV ni intervalle d'incertitude n'est fourni dans cet exemple.
- **Validation temporelle :** `backtest()` trie les lignes par date et emploie `TimeSeriesSplit`, ce qui est chronologique à l'échelle des lignes. Le découpage ne groupe pas explicitement les matchs d'une même date/heure; des événements simultanés ou des dates sans heure doivent être contrôlés pour éviter un partage entre entraînement et test. La date résolue par une source et l'horodatage de publication de chaque variable restent aussi à auditer.
- **Sources de données :** la structure par instantané aide à éviter les fuites, mais ne peut corriger un fournisseur qui étiquette mal un champ, fournit une statistique révisée après coup ou omet son heure réelle de disponibilité. Les cotes historiques d'Odds API sont payantes et soumises aux conditions du fournisseur. Les droits de réutilisation/redistribution des flux n'ont pas été vérifiés.
- **Probabilités :** `OddsComparisonBettor` utilise l'inverse de la moyenne des cotes retenues, soustrait un `alpha` constant et compare le produit probabilité × prix à 1. Cela ne constitue pas en soi une probabilité indépendante ou calibrée; ses résultats doivent être comparés au marché et testés hors échantillon.
- **Exécution réelle :** la documentation avertit que l'automatisation web enfreint les conditions de presque tous les bookmakers et peut faire fermer le compte. Le mode réel est opt-in mais place automatiquement une mise après armement. Cette capacité n'a pas été exécutée ni reprise dans Revue.
- **Sécurité :** inspection statique limitée. Le guide recommande des variables d'environnement pour les secrets; aucun audit des dépendances ni test de sécurité n'a été effectué.
- **Score :** non attribué; les tests et performances n'ayant pas été reproduits.

## Verdict

**Réimplémenter et étudier uniquement le garde-fou de disponibilité point-in-time**, qui apporte un contrôle précis à Revue : un modèle ne peut exploiter que les variables déjà disponibles lorsque le prix à évaluer était coté. Le dossier catalogue l'idée séparément, sans intégrer la bibliothèque complète. Garder `OddsComparisonBettor` comme référence à comparer aux baselines déjà présentes, sans en faire une nouvelle méthode distincte. Ne pas tirer de conclusion de rentabilité à partir des chiffres d'exemple.

Avant tout test, créer des instantanés documentés par source/champ, grouper les coupures par instant commun, comparer à une probabilité de marché correctement dé-margée et publier Brier/log-loss, ROI, CLV, taille d'échantillon et incertitude sur une période jamais utilisée pour choisir les paramètres.

## Références examinées

Liens épinglés au commit audité : [README et résultat exemple](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/README.md), [guide du moment de pari](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/docs/practice/betting_moment.md), [extraction des instantanés](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/src/sportsbet/dataloaders/_base.py), [tests anti-fuite](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/tests/dataloaders/test_leakage.py), [backtest](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/src/sportsbet/evaluation/_model_selection.py), [règle de comparaison des cotes](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/src/sportsbet/evaluation/_rules.py), [avertissements d'exécution](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/docs/overview/user_guide/execution.md), [licence MIT](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/LICENSE), [dépendances et versions Python](https://github.com/georgedouzas/sports-betting/blob/eb4cedf376663fac68f508e50b83fd832e74dfd4/pyproject.toml).

## Provenance et modifications

Consultation en lecture seule du commit ci-dessus. Aucun code, modèle entraîné, pari, secret, jeu de données ou dépôt tiers n'a été importé. Les seuls changements sont les notes d'audit et la fiche dans ce dossier, ainsi que leurs entrées d'index.
