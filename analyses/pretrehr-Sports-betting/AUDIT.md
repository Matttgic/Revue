# Audit de dépôt tiers — pretrehr/Sports-betting

- **URL originale :** https://github.com/pretrehr/Sports-betting
- **Auteur / organisation :** Raphaël Prêtre-Heckenroth
- **Commit audité :** [`9f96cf4e0020249a05617ab414b800ce7c058aef`](https://github.com/pretrehr/Sports-betting/commit/9f96cf4e0020249a05617ab414b800ce7c058aef), branche `master`, 2021-10-06
- **Date de consultation :** 2026-10-11
- **Licence :** MIT, [`LICENSE`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/LICENSE)
- **État de maintenance :** dernier commit ancien; compatibilité actuelle des scrapers non vérifiée
- **Langage / stack :** Python, PySimpleGUI, BeautifulSoup, Selenium, ChromeDriver

## Résumé technique

Assistant de consultation des cotes et de calcul de mises pour exploiter des promotions : couverture des issues (dutching), remboursements, boosts, bonus conditionnels et conversion de freebets. Les fonctions sont accessibles par CLI et interface graphique. Le dépôt intègre des scrapers pour plusieurs bookmakers et sports. L'inspection n'a pas trouvé de fonction qui place automatiquement les paris; les actions Selenium observées concernent l'interface des sites.

Il s'agit d'un calculateur de prix et de couverture, pas d'un modèle qui prédit les résultats. Une couverture théorique n'est garantie que si les issues sont exhaustives et correctement alignées, les cotes sont encore disponibles, les mises sont acceptées et les règles de règlement/promotions concordent.

## Idées identifiées

| Idée | Sport | Marché | Données | Intérêt | Destination |
|---|---|---|---|---|---|
| Répartir les mises sur toutes les issues pour égaliser les retours; adapter la cote d'un freebet (cote décimale moins 1) et couvrir les autres issues en cash | Multi-sports | Issues exhaustives, surtout 1N2 | Cotes disponibles par bookmaker et conditions détaillées de la promotion | Logique transparente, utile pour mesurer la valeur d'une promotion; aucune preuve de rentabilité réelle dans le dépôt | [REV-PRETR-01](REV-PRETR-01_optimisation-promotions-freebets.md) |

## Vérifications

- **Installation / exécution :** non testées; les scrapers et navigateurs n'ont pas été lancés.
- **Tests existants :** non lancés. `sportsbetting/basic_test.py` réalise des requêtes web et utilise Selenium/Chrome; éviter son exécution en tant que simple suite locale.
- **Syntaxe :** analyse AST des 30 fichiers Python, aucune erreur; un `SyntaxWarning` d'échappement invalide dans `interface_pysimplegui_english.py`.
- **Données / performance :** fixture locale `sportsbetting/resources/data_test.json`; aucun historique de paris réglés, journal pré-match ou résultat de ROI reproductible.
- **Résultats annoncés :** le README annonce notamment 77–85 % de conversion de certains freebets. Ce chiffre dépend des cotes et des règles; il n'est pas étayé par un échantillon historique fourni.
- **Biais / hypothèses :** certains calculs de promotions emploient des coefficients fixes, dont `0.77` et `0.8`; les règles réelles varient selon l'offre et le bookmaker.
- **Reproductibilité :** les cotes sont collectées au moment de l'usage, sans archive immuable pour refaire le calcul a posteriori.
- **Dépendances / sécurité :** `selenium>=3.141.0` n'est pas plafonné, mais le code utilise d'anciennes API Selenium; compatibilité non démontrée. Plusieurs binaires ChromeDriver sont présents dans le dépôt, sans vérification de provenance effectuée. L'import de `sportsbetting` a des effets de bord liés au ChromeDriver et aux fichiers de freebets.
- **Licence / crédit :** MIT. Aucun code ni jeu de données n'a été copié dans Revue.
- **Accès aux données :** autorisations, conditions d'utilisation et disponibilité actuelle des pages collectées à vérifier.

## Notes d'audit

| Critère | Note | Preuve |
|---|---:|---|
| Utilité de l'idée (20) | 15 | Calcul de couverture et conversion de freebets explicités dans `sportsbetting/basic_functions.py` et le README |
| Code (20) | 10 | Fonctions mathématiques directes, mais projet ancien et API navigateur possiblement obsolètes |
| Données (15) | 5 | Cotes récupérées en direct; pas d'archive immuable de marchés ou paris réglés |
| Validité statistique (20) | 12 | Algèbre vérifiable sous hypothèses; promotions complexes et hypothèses de conversion non validées empiriquement |
| Testabilité (15) | 9 | Fixture et tests présents, mais tests principaux dépendants du web/navigateur et non lancés |
| Maintenance / sécurité (10) | 3 | Dernier commit en 2021, dépendances non bornées et import avec effets de bord |

**Score indicatif : 54/100.** Il mesure l'intérêt de recherche du dépôt, pas le rendement ni la qualité prédictive.

## Verdict

**Réimplémenter l'idée générale indépendamment**, après spécification des règles de chaque promotion et vérification des règlements et limites de mise. Le calcul de base est utile comme outil de comptabilité et de répartition; l'argument de taux de conversion n'est pas une preuve de résultat. L'idée est distincte des méthodes de prédiction et du dépôt [`georgedouzas/sports-betting`](../sports-betting/README.md), qui porte sur une bibliothèque de données, modèles et backtests.

## Provenance et modifications

Références examinées au commit épinglé : [`README.md`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/README.md), [`basic_functions.py`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/sportsbetting/basic_functions.py), [`user_functions.py`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/sportsbetting/user_functions.py), [`parser_functions.py`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/sportsbetting/parser_functions.py), [`basic_test.py`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/sportsbetting/basic_test.py), [`__init__.py`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/sportsbetting/__init__.py), [`requirements.txt`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/requirements.txt) et [`LICENSE`](https://github.com/pretrehr/Sports-betting/blob/9f96cf4e0020249a05617ab414b800ce7c058aef/LICENSE).

Revue contient une analyse indépendante et une fiche descriptive, sans code ou données copiés. Aucun scraper ni pari n'a été exécuté.
