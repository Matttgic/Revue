# Audit — mkboggs92-cloud/ncsun

- **Source :** https://github.com/mkboggs92-cloud/ncsun
- **Auteur :** mkboggs92-cloud
- **Commit consulté :** `b1110434bdad50d38a1aeba96316a5b90cb8e345` (branche `main`)
- **Date :** 2026-10-09
- **Licence :** aucune licence explicite repérée dans les métadonnées ni à la racine. **Import de code et de données tiers bloqué** jusqu'à autorisation/licence établie.
- **Stack publiée :** site statique GitHub Pages, JavaScript/HTML et fichiers JSON de paris.
- **Pipeline des prédictions :** scripts Python, archives de cotes, entraînements et extractions décrits dans le README mais **non présents** dans ce dépôt.
- **Verdict :** **RECHERCHE DOCUMENTÉE** ; ne pas considérer les méthodes comme reproduites, validées ou exploitables en France.

## Éléments recensés

| Domaine | Méthode ou composant | Intérêt | Fiche |
|---|---|---|---|
| NCAAB | Fading de surperformance aux tirs + dérive de rating + ensemble | élevé : hypothèses précises | [NCAA](../recherche/basketball/ncaab-luck-fade.md) |
| NFL | Modèles de statistiques de receveurs, effectifs actifs, blend marché | élevé : usage des blessures et de la composition | [NFL](../recherche/football-americain/nfl-receiving-props.md) |
| UFC | Bradley-Terry, historique de KO/décisions, cote d'ouverture, value | élevé : marchés spécifiques | [UFC](../recherche/mma/ufc-ko-fade.md) |
| Multi-sports | Modèle de données de pari commun, suivi ROI/CLV, classement des signaux | élevé : outil transverse | [Architecture](../recherche/transversales/registre-paris.md) |
| College football | Paris choisis manuellement, non issus d'un moteur prédictif | limité pour la modélisation | conserver la référence source |
| MLB | Adaptateur générique préparé, sans pipeline MLB publié | faible à cette date | pas de fiche de stratégie active |
| UFC DFS | Projections et compositions DraftKings US | hors périmètre prioritaire FR | pas d'import |

## Contrôle arithmétique des historiques

Lecture des JSON publiés à ce commit; addition du **profit déclaré par pari**, sans reconstruction indépendante des cotes ni des résultats officiels. Les chiffres décrivent donc des backtests **déclarés par l'auteur**, non des performances certifiées.

| Source JSON | Pari(s) notés | Gagnés | Perdus | Profit théorique déclaré (1u/paris) | ROI recalculé |
|---|---:|---:|---:|---:|---:|
| [NCAA](https://github.com/mkboggs92-cloud/ncsun/blob/main/ncaab_backtest.json) | 2 476 | 1 420 | 1 056 | +228,92u | +9,25 % |
| [NFL](https://github.com/mkboggs92-cloud/ncsun/blob/main/nfl_backtest.json) | 864 | 472 | 392 | +140,80u | +16,30 % |
| [UFC](https://github.com/mkboggs92-cloud/ncsun/blob/main/ufc_backtest.json) | 544 | 297 | 247 | +171,75u | +31,57 % |

Pour NCAA la somme provient du champ `p` (profit ou perte), pour NFL/UFC du champ `u`. Les paris des trois ensembles portent sur des cotes américaines d'opérateurs principalement états-uniens. Aucun de ces pourcentages ne prédit le rendement d'un bookmaker français.

### Signaux crédibles

1. Décalage temporel annoncé : modèles et statistiques construits sans scores futurs (« point-in-time », walk-forward).
2. Prix réellement datés revendiqués, résultats et montants par pari dans les fichiers consultables.
3. Différenciation entre suivi live, simulation rétrospective et « paper tracking ».
4. Traçabilité des segments : saison, marché, cote, tier, bookmaker; analyse possible des résultats et de la CLV.
5. Documentation publique d'hypothèses, limites et règles de sélection.

### Risques / impossibilités de conclure

1. **Licence manquante** : la publication sur GitHub ne donne pas automatiquement le droit de redistribuer des fichiers.
2. **Code de calcul manquant** : impossible de reconstruire les séries de probabilités, features, entraînements, éditions de cotes ou appels API uniquement avec le dépôt.
3. **Surajustement** : l'auteur indique lui-même avoir ajusté plusieurs règles et seuils sur les saisons présentées.
4. **Biais du choix des cotes** : notamment pour les props UFC évaluées à une « meilleure cote de clôture » ; sans journal horodaté indépendant, l'accessibilité et le caractère exécutable du prix ne sont pas prouvés.
5. **Biais de sélection** : les modèles et « tiers » non rentables peuvent avoir été éliminés lors de la conception.
6. **Contexte France** : marchés NCAA/UFC/NFL, cotes et opérateurs US; statut ANJ précis et disponibilité en France non vérifiés.

## Critères de Revue (sur 100)

| Critère | Diagnostic |
|---|---|
| Idée et utilité | fort potentiel documentaire |
| Code | affichage fourni ; moteur de prédiction absent |
| Données | historiques de paris disponibles ; données d'entraînement absentes |
| Validité statistique | walk-forward annoncé, non auditable intégralement |
| Backtest indépendant | impossible actuellement sans reconstituer le pipeline |
| Maintenance / sécurité | dépôt récent; audit de sécurité complet non réalisé |

**Score chiffré : NC** (trop d'éléments essentiels non vérifiables). Aucun rang de rentabilité attribué.

## Décision et suites

- **Conserver les idées** dans `recherche/` avec leurs sources et risques.
- **Ne copier aucun fichier ni code du dépôt tiers** sans licence claire ou permission de l'auteur.
- Pour promouvoir un modèle : construire sa propre implémentation, obtenir des données licites, vérifier horaires de publication des cotes, tester walk-forward et faire un suivi prospectif hors échantillon.
- Une stratégie doit être étiquetée `Prototype` uniquement après l'implémentation autonome; `Testé` seulement après un test enregistré.

Source technique : [README](https://github.com/mkboggs92-cloud/ncsun/blob/main/README.md), [adaptateur basketball](https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/ncaab.js), [NFL](https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/nfl.js), [UFC](https://github.com/mkboggs92-cloud/ncsun/blob/main/sports/ufc.js).
