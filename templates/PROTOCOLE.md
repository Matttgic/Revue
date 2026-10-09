# Protocole d'audit et de sélection

## 1. Filtre préalable
- Source GitHub exacte et commit de référence enregistrés.
- Licence examinée dans sa version exacte ; **absence de licence ≠ permission de copier**.
- Pas de secret dans le code, pas d'exécution arbitraire ou dépendance suspecte.
- Provenance et conditions d'utilisation des données explicites.
- Sports, compétitions et marchés compatibles avec l'utilisation envisagée (notamment ANJ en France).

Si un filtre bloque, ne **pas importer** le code. Une fiche d'analyse purement descriptive reste possible.

## 2. Notation d'intérêt /100 (pas une fiabilité des paris)
| Dimension | Maximum |
|---|---:|
| Utilité de l'idée / originalité opérationnelle | 20 |
| Qualité logicielle et reproductibilité | 20 |
| Accès légitime à des données suffisantes | 15 |
| Solidité statistique / risques de biais | 20 |
| Testabilité sur historique indépendant | 15 |
| Maintenance, sécurité, facilité d'intégration | 10 |

Noter les dimensions seulement sur preuves vérifiables. Si les informations manquent : marquer **NC** et indiquer qu'il s'agit d'un score partiel, pas /100.

Repères de tri **indicatifs**, uniquement si le dossier est suffisamment documenté :
- 80–100 : priorité d'examen/expérimentation.
- 60–79 : intéressant sous conditions.
- 40–59 : conserver l'idée dans la recherche, sans promotion automatique.
- 0–39 : faible priorité ou rejet argumenté.

Ces seuils ne constituent pas une preuve de rentabilité.

## 3. Protocole de test
1. Fixer la date et le moment où chaque prédiction aurait réellement été calculable.
2. Utiliser uniquement les informations **connues avant le pari** ; empêcher fuite de données et confusion entraînement/test.
3. Séparer chronologiquement entraînement, validation et test. Garder le test final intact ; utiliser validation glissante si possible.
4. Comparer une baseline simple : consensus / cotes sans marge, favori ou modèle naïf.
5. Rejouer les cotes réellement proposées à cet instant, délais d'actualisation, limites de mise et éventuels coûts.
6. Suivre en unités, à mise plate par défaut : profit net, ROI, nombre de paris, drawdown maximum, volatilité et incertitude.
7. Sur les probabilités, vérifier Brier score, log loss, calibration par déciles et dérive dans le temps.
8. Si disponible, suivre CLV comme indicateur secondaire, sans le traiter comme preuve suffisante de profit.
9. Donner résultats par sport, ligue, saison, marché, tranche de cotes et bookmaker pour éviter qu'un agrégat cache un biais.
10. Suivre également tous les paris perdus, annulés, sans cote exploitable et sans résultat.

## 4. Verdict
- **Copier / adapter** : licence compatible, module utile, provenance préservée ; code audité, tests exigés pour l'intégration.
- **Réimplémenter l'idée** : méthode intéressante mais code inutilisable ou non copiable ; réécriture indépendante conforme.
- **Documenter seulement** : idée non démontrée, données indisponibles, preuves incomplètes.
- **Écarter** : aucun usage pertinent ou risque/contrainte rédhibitoire.

Toute fiche doit distinguer **résultat observé** et **hypothèse**.
