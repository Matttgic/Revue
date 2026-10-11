# Audit — 1canhhoa/sports-betting-toolbox

- **Source :** https://github.com/1canhhoa/sports-betting-toolbox
- **Commit examiné :** `7941e20ab089a54d4ca3bd69064133c4239c07e5` (`main`), 2026-09-14
- **Date de consultation :** 2026-10-11
- **Licence :** MIT présente. Le fichier porte l’avis de copyright « 2019 Georgios Douzas »; toute réutilisation future du code doit conserver cet avis et la licence. Aucun code ni donnée n’a été copié dans Revue.
- **Stack :** TypeScript/Node, Vitest, Vercel AI SDK/OpenAI, CSV distant et Redis facultatif.
- **But :** CLI de prévision football 1N2 par LLM ou statistiques simples; chargement des historiques et cotes, proposition de paris et backtest chronologique.
- **Verdict :** **petit outil lisible, mais sans preuve de qualité prédictive ou de rentabilité**. La seule piste distincte retenue est un dé-vig additif avec seuil fixe comme baseline à comparer. Le pari n’est pas fondé sur un signal indépendant du marché.

## Fonctionnement observé

La commande de prévision charge un CSV distant, construit les bilans domicile/extérieur, le face-à-face et le taux de nuls, puis appelle par défaut un LLM. Le prompt fournit au LLM le bilan agrégé et une probabilité de base, mais pas de cotes ni d’historique d’information point-in-time. L’API demande au modèle des probabilités et un niveau de confiance; le code renormalise les trois probabilités pour que leur somme fasse 1. Cela ne calibre ni les probabilités ni le niveau de confiance.

Le mode statistique mélange les taux victoire/nul/défaite des équipes et un prior fixe `42/26/32`, applique un poids du face-à-face plafonné à 35 % et appelle « confiance » une fonction du nombre de matchs connus. Le calcul est compréhensible comme baseline descriptive, mais ses coefficients ne sont pas évalués.

La stratégie `OddsComparisonBettor` transforme chaque cote décimale `o` en probabilité implicite `1/o`, lui soustrait un `alpha` identique pour chaque issue (0,03 dans la CLI), borne à zéro, puis renormalise les issues complémentaires. Elle sélectionne ensuite une issue si `p × cote > 1` et, en marché exclusif, ne garde que le meilleur rendement estimé. Le backtest classe les lignes par date et applique une validation à fenêtre croissante. La CLI ne demande que deux splits.

## Reproductibilité et qualité des preuves

- **Données :** les combinaisons de données documentées sont des saisons 2020, téléchargées depuis un dépôt GitHub externe de données football; la commande de prévision utilise par défaut Angleterre division 1 année 2020 et ajoute un CSV de fixtures. Ce n’est pas un flux de forme récente garanti en 2026. L’horodatage auquel les cotes historiques étaient réellement disponibles n’est pas décrit ici.
- **Backtest :** le code produit nombre de paris, rendement par pari, ROI sur la bankroll initiale et solde final par split. Aucun résultat chiffré de backtest n’est publié dans le README ou la documentation examinée; le dépôt ne fournit ni CLV ni analyse d’incertitude.
- **Signal de prix :** la CLI sélectionne le bookmaker choisi à la fois pour créer l’estimation implicite et pour comparer au prix offert. Il s’agit donc d’un retrait de marge appliqué à la même grille de cotes, pas d’une estimation indépendante de la probabilité. Le `alpha=0,03` fixe peut mal représenter la marge réelle selon le bookmaker, le marché et l’issue.
- **Prévision LLM :** pas de benchmark de calibration, de comparaison au marché, de suivi prospectif ou de backtest présenté. « Calibrated probabilities » est une consigne du prompt, pas un résultat expérimental.
- **Contexte des équipes :** `buildMatchContext()` agrège tous les résultats non-fixtures qui lui sont transmis et ne prend pas de date cible; l’utiliser sur une cible historique peut inclure des rencontres ultérieures. La résolution par inclusion de sous-chaîne peut également confondre des noms proches.
- **Tests :** les fichiers Vitest couvrent la forme de sortie, les extracteurs, le cache et une vérification de dimensions de la stratégie sur quelques lignes factices. Ils ne vérifient pas les retours du backtest, la calibration LLM ou un résultat hors échantillon.
- **Exécution :** l’installation a échoué avant les tests et la compilation : npm signale `ENOVERSIONS — No versions available for pino-ulid`. Le dépôt ne versionne pas de lockfile npm. Le workflow CI et `CONTRIBUTING.md` invoquent PDM/Python et `pyproject.toml`, alors que le checkout contient un projet TypeScript et aucun `pyproject.toml`; ce pipeline semble désynchronisé avec le code actuel.
- **Données et droits :** MIT s’applique au code du dépôt, pas automatiquement au dataset GitHub externe ni aux prix historiques. Vérifier séparément les conditions de redistribution et d’usage des cotes.

## Décision

Conserver une seule ligne de catalogue, comme baseline de retrait de marge par soustraction additive fixe; elle complète la fiche existante sur la sensibilité au dé-vig, sans remplacer les autres méthodes. Marquer **À étudier**, car les cotes sources, la sélection du paramètre `alpha` et la validation ne sont pas reproduites. Ne pas cataloguer la sortie LLM comme modèle prédictif éprouvé.

Pour en faire un test valable, comparer plusieurs méthodes de dé-vig sur les mêmes issues, retirer la marge des cotes d’un consensus horodaté séparé du bookmaker exécuté, fixer `alpha` uniquement sur l’entraînement, puis mesurer Brier/log-loss, ROI, CLV et intervalles sur une période ultérieure et assez grande. Ajouter des snapshots actuels et datés pour toute prévision prospective.

Références : [README](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/README.md), [stratégie OddsComparison](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/src/strategies/oddsCompare.ts), [backtest](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/src/strategies/backtest.ts), [prédiction LLM](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/src/predict/aiModel.ts), [contexte](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/src/predict/teamContext.ts), [licence](https://github.com/1canhhoa/sports-betting-toolbox/blob/7941e20ab089a54d4ca3bd69064133c4239c07e5/LICENSE).
