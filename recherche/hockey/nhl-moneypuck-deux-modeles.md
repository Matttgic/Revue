# NHL — MoneyPuck : réplication Clairvoyance vs variante prudente

## Portée et provenance

- Source xG équipes et gardiens : **[MoneyPuck.com](https://moneypuck.com/data.htm)**, téléchargements officiels saisonniers, usage personnel non commercial avec crédit.
- Matchs, dates et Elo : NHL Web API + Elo recalculé indépendamment par Revue.
- Modèle de référence : **formule Python NHL Clairvoyance**, reproduite et comparée fonction par fonction avec le dépôt source. **Ce n'est pas une reproduction de la base Elo, des gardiens titulaires, ni des prédictions réelles** de Clairvoyance.
- Modèle de recherche : `revue_nhl_low_sample_shrink_v1`, **création indépendante** qui ne modifie pas la formule source, mais stabilise ses entrées.

## Pourquoi deux modèles ?

Quelques matchs en début de saison peuvent produire des xG% ou des % d'arrêts extrêmement instables. La formule Clairvoyance a une composante gardien assez sensible à cet aléa. **Ne jamais confondre une probabilité affichée avec une rentabilité ou une probabilité calibrée.**

La variante de recherche préserve la formule originale et applique d'abord les priors **fixés avant l'évaluation** :

```text
xg_5v5_ajusté = (xg_courant * matchs_courants + xg_prior * 12)
                / (matchs_courants + 12)
xg_prior = xG% 5v5 de la saison précédente de la même équipe
           (seulement si >= 20 matchs), sinon 50 %

save_pct_ajusté = (save_pct_courant * matchs_du_gardien + 0.905 * 8)
                  / (matchs_du_gardien + 8)
```

Les poids **12**, **8**, et le niveau **0,905** sont des hypothèses de recherche pré-déclarées, **pas des hyperparamètres calibrés**. Le gardien pris en compte est le plus utilisé de l'équipe, **pas le titulaire annoncé**. L'absence de gardien n'autorise pas à en inventer un.

## Conditions de sélection des données

1. Match futur seulement ; timestamp NHL avec fuseau ; situation équipe `5on5` ; saison courante authentifiée.
2. Source MoneyPuck et collecte horodatées avant l'heure de prédiction ; aucune utilisation de données publiées après le match.
3. Elo calculé uniquement à partir des matchs officiels terminés avant la prévision, chaque match une seule fois.
4. La saison précédente est un prior optionnel. Si indisponible ou horodatée après la prévision, repli explicite sur **50 %**, jamais déguisé en saison actuelle.
5. Aucun résultat et aucune cote future utilisés pour sélectionner ou ajuster la variante.

## Protocole prospectif

Chaque match prévu est verrouillé **au moins 20 min avant le début**. Une probabilité enregistrée ne doit jamais être réécrite. À réception du score final NHL, le suivi calcule :

`Brier = (probabilité de victoire domicile - résultat_domicile_0_ou_1)²`

- **Référence :** moyenne Brier de la formule Clairvoyance sur les matchs déjà réglés.
- **Comparaison équitable :** Brier de la référence et de la variante sur **exactement les mêmes matchs** qui avaient deux prévisions verrouillées avant le coup d'envoi.
- **Delta :** Brier variante moins Brier référence ; une valeur négative est favorable, mais ne prouve pas à elle seule une supériorité future.
- **Seuil :** indicateurs exploratoires avant 100 matchs réglés ; pas d'activation de paris automatiques ni de revendication de rendement.

Les tests unitaires couvrent la formule inchangée, la séparation des modèles, les priors absents, les valeurs invalides, les horodatages et l'immutabilité du suivi.

## Résultats officiels sans recalcul des modèles

Le workflow `.github/workflows/nhl-settlement-officiel.yml` interroge **toutes les quatre heures** uniquement les tableaux de scores NHL aux dates nécessaires (fuseau **America/New_York**, différent de l'UTC et de Paris), avec un plafond de 14 dates par exécution. Il ne télécharge aucun nouveau CSV MoneyPuck et **ne crée ni ne réécrit de prévision**.

Seuls les événements qui correspondent **exactement** à l'identifiant, aux deux clubs et à l'heure de début verrouillés peuvent être réglés. Un score live, un match reporté, un calendrier différent, une réponse d'API mal formée ou un score contradictoire ne permettent pas un règlement supposé. Quand aucun résultat nouveau n'arrive, aucune publication Git ne doit être effectuée.

Le journal conserve distinctement les anciens pronostics verrouillés sans variante : ils pourront être réglés pour le modèle Clairvoyance, mais **jamais appariés après coup** au modèle prudent.

Pour interpréter les performances, nous publions également :

- **Brier de référence neutre à 50 %** : 0,25 par rencontre binaire.
- **Log Loss neutre à 50 %** : ln(2) ≈ 0,693147.
- **Brier Skill vs référence neutre** : 1 − Brier moyen / 0,25 ; une valeur négative signifie pire que 50 %.
- **Log Loss des deux variantes sur les mêmes événements appariés** : inférieur = meilleur.
- Les chiffres restent **descriptifs et expérimentaux** avant au moins 100 résultats appariés et ne constituent pas une preuve de rentabilité.

Site : `docs/nhl-clairvoyance.html`, onglet *Suivi / résultats NHL* avec historiques des verrouillages et scores officiels.

## Fichiers

- `outils/clairvoyance_nhl_moneypuck_shadow.py` : production des prévisions de référence + recherches.
- `outils/nhl_moneypuck_prudent.py` : transformation indépendante des entrées.
- `outils/nhl_shadow_tracker.py` : journal prospectif et Brier apparié.
- `docs/nhl-clairvoyance-shadow-latest.json` : prévisions horodatées.
- `docs/nhl-shadow-performance.json` : indicateurs vérifiables.
- `docs/nhl-clairvoyance.html` : affichage adapté au mobile.

**Important :** les données, méthodes et performances sont utilisées comme expérimentation personnelle non commerciale, sans conseil de mise. La mention « 100 % parité » dans d'autres audits couvre des fonctions ciblées et des fixtures comparées, jamais l'intégralité du dépôt, de ses sources de données ou de sa performance.
