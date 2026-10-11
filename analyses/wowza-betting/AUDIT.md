# Audit — NevixAA/wowza-betting

- **URL originale :** [github.com/NevixAA/wowza-betting](https://github.com/NevixAA/wowza-betting)
- **Commit audité :** [`87c4229dbb326306df8db7eb591bc8a857454058`](https://github.com/NevixAA/wowza-betting/commit/87c4229dbb326306df8db7eb591bc8a857454058) (`2026-10-11`, `auto: player props 2026-10-11 16:31 UTC`)
- **Date d'audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré dans ce commit. `DISCLAIMER.md` porte sur la responsabilité liée à l'usage; il ne remplace pas une licence de droit d'auteur. Ne pas reprendre le code, les modèles ou les données sans autorisation.
- **Maintenance :** forte activité visible, avec un commit de génération de props daté du jour de l'audit et 22 workflows GitHub suivis.
- **Stack :** Python, pandas, scikit-learn, LightGBM, Streamlit, API-Football, football-data.co.uk, FPL; intégrations d'alertes, modèles sérialisés et automatisation GitHub Actions.

## Avis

**Très intéressant comme dossier de recherche et d'ingénierie; je ne traiterais aucun de ses modèles comme un avantage de pari démontré.** Sa vraie valeur pour Revue est sa documentation des échecs : une fuite d'étiquette de la méta-couche en production, des données et des marchés mal alignés, des seuils choisis a posteriori, et plusieurs analyses qui concluent explicitement que le marché fait mieux. L'ajout le plus réutilisable est un cadre de comparaison des modèles et des prix; l'un de ses garde-fous en production demeure néanmoins incomplet.

## Résumé technique

Le dépôt présente une plateforme football automatisée sur environ 19 ligues, avec O/U 2,5, BTTS, O/U 1,5 et 3,5, des marchés à la mi-temps, des signaux live et de mouvement des cotes, sept familles de props, ainsi que des projections fantasy FPL. Le modèle d'équipe principal combine logistique, Gradient Boosting et LightGBM avec calibrage; des variantes de format et des challengers sont conservés séparément. L'interface est une application Streamlit multi-pages. Les actions collectent les données, prédisent, règlent les résultats, enregistrent les cotes et publient des résumés.

Le checkout contient 391 fichiers suivis, environ **462 Mo** de données, historiques de prix et de résultats, artefacts Parquet/CSV et pickles de modèles. Il fonctionne ainsi comme un snapshot opérationnel de la plateforme, pas seulement comme du code. Aucun de ces artefacts n'a été copié dans Revue.

## Ce que le dépôt a réellement mesuré

### Modèles et marché

Le rapport de comparaison champion/challenger du 4 octobre (dans le clone audité) score les modèles et le marché dé-viggué sur des mêmes fixtures. Pour le marché standard O/U 2,5, le meilleur candidat affiché, HGB, a un log-loss de **0,68752** contre **0,67702** pour le marché; sur le nouveau format, les meilleurs candidats affichés restent également derrière le marché. L'étude V11 rapporte un Brier de **0,2405** pour le marché seul et **0,2404** pour marché + Wowza : différence négligeable, aide dans 10 segments sur 20 et **zéro sélection** admissible à la mise au seuil testé. Ce sont les calculs et artefacts de l'auteur, pas une reproduction indépendante de la plateforme.

Le bilan BTTS semblait plus prometteur : le rapport du 1er octobre donne +30,60 unités sur 100 paris sélectionnés, avec 64 paris en Argentine représentant 85 % du profit. Le registre au 4 octobre affiche 105 paris et +31,91 unités; la confirmation prospective n'avait commencé que sur 4 des 150 paris prévus. Un examen a posteriori de 16 cellules, l'absence de changement de régime et la concentration géographique rendent le premier résultat exploratoire. La CLV Argentine publiée était négative (−2,04 % sur 51 paris; l'intervalle publié incluait zéro), ce qui affaiblit l'interprétation d'un avantage de prix. Il ne faut pas présenter le ROI de ce petit échantillon sans ces réserves.

Pour les props joueurs, le README affirme qu'aucun avantage de pari n'a été trouvé malgré des AUC annoncées entre 0,62 et 0,85. L'artefact de readiness signale que le règlement était aligné sur seulement 3 des 9 marchés; les autres sont bloqués et ne permettent pas de citer leurs ROI/CLV comme mesures fiables du bon événement. La prévision FPL est également derrière `ep_next` du jeu officiel sur les deux journées évaluables dans le fichier fourni (n=575 joueur-journées, MAE 2,164 contre 1,535), résultat encore très court.

### Fuite de validation et garde de promotion

Dans `src/model.py`, le méta-modèle logistique est ajusté sur les prédictions des bases **et les labels du bloc appelé test**, puis mesuré sur ces mêmes lignes. Ce bloc a donc déjà été vu par la couche réellement servie. Le harness à quatre blocs chronologiques FIT/CAL/META/HOLDOUT dans `src/model_validation.py` est explicitement un outil de recherche; les rapports indiquent que la version corrigée reste un challenger et n'est pas la méta-couche de production.

La protection actuellement appelée par `pipeline.py` bloque une dégradation du log-loss moyen des **modèles de base** sur un holdout commun; le modèle livré, lui, ajoute ensuite la méta-couche. La porte statistique plus stricte est exécutée en shadow/log-only, et ne décide pas du remplacement. Le rapport P0 du 4 octobre rejoue 91 décisions historiques : l'ancienne tolérance a promu 88 candidats, dont 29 avaient un log-loss dégradé. C'est un argument concret pour mesurer les promotions sur mêmes lignes; ce n'est pas une preuve que la porte live actuelle protège le modèle servi, puisque le score qu'elle suit ignore la méta-couche. L'identifiant `dataset_id` du harness est aussi calculé à partir du nombre de lignes, des bornes de dates, des variables et du taux de base, et non d'une empreinte des identifiants de fixtures.

Le projet a correctement identifié que les seuils dépendent du chemin de résolution de production : une précédente analyse lisait des valeurs dans `config.py` alors que les paramètres approuvés et `gate_resolver` déterminaient les seuils actifs. Cette séparation entre paramètres visibles, paramètres effectivement résolus et politique de mise est une bonne exigence d'audit.

## Risques de données et d'exploitation

- **Étiquettes fabriquées en historique :** l'enquête sur le modèle mi-temps trouve qu'environ 74 % des labels d'entraînement avaient été artificiellement convertis en négatifs par comparaison `NaN >= 1`; les taux impossibles et le AUC prétendument fort disparaissent après correction. Le dépôt rapporte avoir corrigé le chemin et fermé la piste comme sans pouvoir prédictif. C'est un précédent important : les valeurs manquantes doivent rester inconnues, jamais être interprétées silencieusement comme zéro.
- **Lignée du dataset :** le readiness du 4 octobre estime 23 169 fixtures « échouées » (28,65 % des lignes disponibles) entre la source canonique et le jeu v9, et environ 2 900 duplications. Le simple fait d'ajouter plus de lignes n'améliorait que marginalement le log-loss hors échantillon; la lignée et la déduplication doivent être traitées avant de revendiquer la couverture accrue.
- **Fraîcheur et identité :** les notes du 8 octobre documentent un ID API incorrect pour Ligue 2, donc des prix absents de façon irrécupérable pendant plusieurs mois, ainsi que des props attribuant des joueurs à d'anciens clubs (400 lignes sur un tableau de 2 581) avant l'ajout d'un contrôle d'effectif. Ces réparations récentes sont utiles, mais montrent qu'un nom résolu ou un calendrier chargé ne garantit pas l'identité correcte de la ligue, du joueur ou de l'événement.
- **Cotes et clôture :** l'archive sépare la maison, le marché, le côté, la ligne, le temps avant coup d'envoi et les prix post-match. Le code explique pourquoi une quote inchangée doit être observée de nouveau près du match pour prouver qu'elle était toujours disponible. Néanmoins, le rapport P0 précise que les trois types de CLV étaient ajoutés mais n'avaient pas encore de consommateur confirmé; la chaîne complète n'est pas validée ici.
- **Données à fort volume :** un historique est encore écrit dans le dépôt Git et le projet décrit lui-même le risque de limite de 100 Mo par fichier et de croissance du répertoire `.git`. L'archive temporelle mérite une politique de stockage versionnée et partitionnée, avec provenance/droits par source.

## Idées retenues et relation à Revue

1. **Promotion de modèle :** distinguer un garde-fou contre une régression évidente d'une porte exigeant amélioration matérielle et reproductible; scorer champion et challenger sur les mêmes fixtures, journaliser la base de comparaison et laisser une période prospective trancher. La piste est cataloguée, pas réimplémentée.
2. **CLV avec trois questions séparées :** prix d'entrée vs clôture du même bookmaker (qualité d'exécution), vs marché sharp dé-viggué (information de marché), ou vs médiane dé-vigguée d'au moins trois bookmakers cotés des deux côtés (consensus). Une fermeture absente, post-coup d'envoi ou à un seul côté doit produire un statut « non mesurable ».
3. **Pré-enregistrement :** le registre fige période, taille minimale, statistique primaire, intervalles par blocs et règles d'exclusion avant confirmation. L'étude BTTS montre pourquoi il faut enregistrer l'hypothèse avant de sélectionner après coup le meilleur couple ligue/marché.

Revue possède déjà un suivi prospectif de prix au même bookmaker et un cadre de décision ROI/CLV. La typologie multi-référence peut le compléter; la méthode de promotion champion/challenger est un nouveau contrôle de cycle de modèle. Aucune stratégie football positive n'est ajoutée : les propres résultats du dépôt montrent le marché devant ou des échantillons trop petits et trop sélectionnés.

## Vérifications effectuées

- Commit `main` cloné en checkout propre; 162 fichiers Python analysés par le parseur AST : aucune erreur de syntaxe.
- Les rapports, manifestes, jeux de données résumés, tests déclarés et code actif ont été examinés statiquement.
- Les dépendances n'ont pas été installées; la suite annoncée dans le README (306 tests) n'a pas été lancée. Aucun pickle n'a été chargé et aucun workflow, service, API-Football, modèle de prédiction ou envoi Telegram n'a été exécuté.
- Aucun examen exhaustif de sécurité ou vérification des droits/conditions d'usage de chaque source de données n'a été effectué.
- Aucun code, modèle, fichier de cotes, ledger, historique de joueurs ou autre artefact du dépôt n'a été copié dans Revue.

## Verdict

**Documenter et réimplémenter sélectivement des contrôles, sans réutiliser le moteur ni reprendre ses résultats comme preuve de performance.** Le projet est une référence de processus parce qu'il publie des erreurs et ferme des hypothèses après échec. Sa principale limite pour la prédiction reste décisive : la méta-couche évaluée a vu les labels de son holdout, et les propres comparaisons favorisent le marché. Le BTTS récent est un cas d'étude de sélection et de confirmation, pas une recommandation de pari.

## Fichiers consultés

- [README et statut des modèles](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/README.md)
- [Rapport champion/challenger et replay](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/docs/P0_CHAMPION_CHALLENGER_REPORT.md)
- [Validation leak-free, version recherche](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/src/model_validation.py)
- [Stack servi](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/src/model.py)
- [Porte de promotion](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/pipeline.py)
- [Gate statistique champion/challenger](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/src/promotion_gate.py)
- [Étude de validation BTTS](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/docs/BTTS_EDGE_VALIDATION.md)
- [Registre préenregistré](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/registry/preregistered_hypotheses.json)
- [Évaluation des cotes de clôture](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/src/clv_types.py)
- [Capture sur une échelle de coup d'envoi](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/src/book_quotes.py)
- [Étude du modèle mi-temps](https://github.com/NevixAA/wowza-betting/blob/87c4229dbb326306df8db7eb591bc8a857454058/docs/HT_MODEL_INVESTIGATION.md)
