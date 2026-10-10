# Validation prospective NHL : calibration des probabilités

## Objectif

Vérifier **sans fuite chronologique** si une transformation des probabilités
rend les prévisions plus proches de la fréquence réelle des victoires NHL.
Deux séries sont observées **séparément** :

1. Formule NHL Clairvoyance avec les entrées NHL / MoneyPuck de Revue.
2. Variante indépendante Revue Prudent.

Chaque événement utilisé doit posséder une prévision **verrouillée au moins
20 minutes avant le coup d'envoi**, un résultat officiel NHL, des buts finaux
cohérents, un horodatage de résolution postérieur au match et une probabilité
définie dans l'intervalle ouvert (0, 1). Les rencontres sans prévision
Revue Prudent d'époque **ne sont jamais reconstruites rétroactivement**.

## Découpage temporel fixe

- **Phase 1 (entraînement)** : les **100 premiers** résultats authentiquement
  réglés, ordonnés par instant de résolution officiel constaté dans le journal.
  Les paramètres sont figés sur ce groupe, dans l'ordre chronologique connu.
- **Phase 2 (test non utilisé dans l'entraînement)** : les prochains matchs
  verrouillés **dont l'heure de début est strictement ultérieure** au dernier
  instant de résolution utilisé pour entraîner le calibrateur.
- **Seuil d'affichage d'un premier test** : **40 matchs de test**. Ce minimum
  n'est **pas** une démonstration de significativité statistique.
- **Aucune sélection automatique** d'un modèle ni déploiement de prédictions
  ajustées dans les paris : un résultat positif est étiqueté
  `experimental_holdout_better` et reste uniquement une observation de
  recherche à confirmer sur davantage de données.

Un ancien match réglé tardivement peut contribuer au futur bilan brut,
mais n'entre pas rétrospectivement dans l'échantillon de test s'il avait
commencé avant la fin de l'entraînement.

## Calibrateur étudié

```text
p_calibrée = sigmoid( a + b * logit(p_brute) )
logit(p) = log(p / (1-p))
sigmoid(z) = 1 / (1+exp(-z))
```

Les paramètres `a` et `b` sont ajustés **sur l'entraînement exclusivement**
par minimisation de la Log Loss et régularisation de Ridge fixe
`0.1 * (a² + (b-1)²)`, avec `b` contraint à l'intervalle [0, 3].
Cette transformation est une hypothèse expérimentale
pré-déclarée, **pas** la formule d'origine Clairvoyance.

Le rapport présente la courbe empirique par tranches de probabilité
[0–20[, [20–40[, [40–60[, [60–80[, [80–100 %], puis, lorsqu'un test indépendant
existe, les scores **Brier** et **Log Loss**, avant et après calibration.

Deux repères sont mesurés **uniquement sur le test** :

- Modèle original, non calibré, sur **les mêmes rencontres**.
- Prédiction constante égale au taux de victoires à domicile
  **calculé exclusivement sur les 100 rencontres d'entraînement**.

Un meilleur Brier combiné à une meilleure Log Loss est encourageant, mais
ne démontre ni une calibration parfaite, ni une rentabilité contre des cotes
du bookmaker. La couverture des bookmakers français, le retrait de marge,
le CLV et les cotes historiques restent des problèmes séparés.

## Intégration

- Générateur : `outils/nhl_calibration_prospective.py`.
- Tests unitaires : `tests/test_nhl_calibration_prospective.py`.
- Entrée de référence : `docs/nhl-shadow-ledger.json`.
- Rapport : `docs/nhl-calibration-latest.json`.
- Publication automatique après **nouveaux résultats officiels** :
  `.github/workflows/nhl-settlement-officiel.yml`, sans appel
  MoneyPuck additionnel.
- Visualisation : `docs/nhl-clairvoyance.html`, section
  **CALIBRATION / VALIDATION**.

**État initial du 10 octobre 2026 :** zéro match réglé pour chacun des
deux modèles NHL. Il n'existe pas encore de calibrateur entraîné à
partir de ce journal ; aucun chiffre de performance future ne peut être
déduit du seul fait que le programme et ses tests fonctionnent.
