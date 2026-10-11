# Audit — vishalkiritnaik-a11y/nfl-sports-betting

- **URL originale :** [github.com/vishalkiritnaik-a11y/nfl-sports-betting](https://github.com/vishalkiritnaik-a11y/nfl-sports-betting)
- **Commit audité :** [`382d9d4fc9b8c8432889cde424e7103520ad8c0d`](https://github.com/vishalkiritnaik-a11y/nfl-sports-betting/commit/382d9d4fc9b8c8432889cde424e7103520ad8c0d) (`main`, vu le 2026-10-11)
- **Date d'audit :** 2026-10-11
- **Licence :** aucun fichier de licence repéré. Aucune copie de code ou de données.
- **Contenu :** pipeline Python, tableau de bord React/TypeScript, workflow GitHub Actions, sources nflverse/Open-Meteo et intégration facultative avec The Odds API. La base SQLite de prévisions et un état de run sont versionnés.

## Mon avis

**Projet propre, explicite sur ses limites et avec une piste anytime-TD intéressante.** Le README annonce que le marché de clôture prédit mieux que son modèle de match et que ses simulations à la clôture perdent de l'argent. C'est une présentation honnête, qui permet de séparer ingénierie utile et résultat commercial.

Le modèle anytime-touchdown est la contribution la plus distincte à Revue : il projette les occasions d'équipe par zone, les répartit entre joueurs avec un shrinkage hiérarchique, puis estime la probabilité de marquer au moins un touchdown. Le résultat probabiliste walk-forward publié est encourageant; les cotes anytime-TD historiques manquent, donc ni l'avantage sur le marché ni le ROI ne sont démontrés.

## Modèles et résultats rapportés

- **Match NFL :** Elo, EPA/success rate offensifs et défensifs ajustés à l'adversaire, QB, équipes spéciales, turnovers, pression, red zone, repos, voyage et météo. Une ridge prédit la marge puis la transforme en probabilité via une loi normale; une logistique prédit aussi le gagnant. Leurs probabilités sont moyennées, et leur désaccord diminue la confiance. Le total a son propre modèle ridge.
- **Anytime-TD :** modèle d'occasions × taux par occasion, détaillé dans [REV-VISHAL-01](REV-VISHAL-01_anytime-td-opportunity-model.md). Les historiques, le modèle d'occasions et la calibration sont construits par saison walk-forward.
- **Marché :** le modèle de match est évalué face au consensus de clôture sans marge. Le README rapporte log-loss `0,632` et Brier `0,221` contre `0,613` et `0,213` pour le marché; les simulations de mises à prix de clôture rendent environ `−5 %` moneyline, `−5 %` spread et `−2 %` totaux aux seuils présentés.
- **Modèle anytime-TD :** le README rapporte, sur environ 29 000 lignes joueur-match walk-forward en 2022–2026, log-loss `0,395` contre `0,446` pour le taux de base, Brier `0,122` et AUC `0,74`. Ces scores concernent les joueurs ayant pris au moins un snap offensif. L'auteur précise qu'il n'existe pas de cotes anytime-TD historiques gratuites pour comparer le modèle au prix ou mesurer le ROI.

Le dépôt garde les prévisions pré-kickoff dans une base SQLite append-only et ne retient pour le suivi que la dernière prévision horodatée avant le coup d'envoi. Dans l'archive examinée, cette base avait 10 runs et 14 rencontres distinctes prédites; les tables de résultat de match et de joueur étaient encore vides. C'est donc une bonne infrastructure de suivi en devenir, pas un historique prospectif déjà évalué.

## Limites et points de vigilance

- **Cotes anytime-TD :** l'intégration The Odds API exige une clé, et la collecte anytime-TD nécessite un plan payant. Les cotes de propositions historiques ne sont pas présentes dans les artefacts du commit. Le modèle ne peut pas encore démontrer une value sur ces prix.
- **Population de calibration :** les lignes d'apprentissage/backtest ne portent que sur les joueurs ayant joué au moins un snap offensif. Le score de calibration est donc conditionnel à la participation effective. Pour comparer des tickets, Revue devra appliquer les règles de non-participation/annulation propres au bookmaker et vérifier que les prédictions prospectives suivent la même population.
- **Marché de match :** les lignes nflverse servent de consensus de clôture dans les comparaisons. Le README reconnaît que le modèle et les stratégies simples perdent aux prix de clôture. Les simulations historiques ne sont pas une preuve de prix exécutable au moment où un utilisateur décide.
- **Issues nulles :** les matchs nuls sont exclus du modèle binaire; les probabilités sont conditionnelles à un résultat décisif. Le traitement des égalités et leur règlement doivent rester cohérents avec chaque marché.
- **Licence :** son absence bloque la reprise du code; les architectures mathématiques peuvent seulement inspirer des expériences indépendantes.

## Décision pour Revue

Cataloguer le modèle anytime-TD comme **À étudier** et le conserver dans ce dossier isolé. C'est une piste plus ciblée que les modèles NFL généraux : allocation hiérarchique des touches/cibles dans les zones de score, puis séparation des occasions et de la finition. Tester d'abord ses probabilités pré-match avec une population et des règles de règlement explicites. Les odds de match, les odds de touchdowns, le calibrage et le journal prospectif doivent être évalués séparément. Aucun code, historique ou bundle n'est importé dans les modèles Revue.

## Vérifications effectuées

- Le clonage Git en lecture seule a demandé une authentification; la page publique et l'archive `main` ont permis d'inspecter le commit `382d9d4`. Aucun jeton ou secret n'a été utilisé.
- Lecture du README, des modules `td_model`, `tddata`, `evaluate`, du schéma SQLite, des tests et du workflow. L'archive SQLite a été interrogée en lecture seule.
- Aucun pipeline, navigateur applicatif, workflow GitHub ou appel météo/cotes n'a été exécuté. Les tests cités sont ceux déclarés par le dépôt/son workflow, pas une exécution indépendante pendant cet audit.
