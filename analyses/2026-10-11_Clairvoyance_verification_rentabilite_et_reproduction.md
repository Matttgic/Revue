# Clairvoyance : vérification de la rentabilité et de la reproduction dans Revue

- **Source auditée :** [Purple-Wraith/clairvoyance-backend](https://github.com/Purple-Wraith/clairvoyance-backend), commit `0d900f51` (2026-10-10 20:19 MT), registre public `docs/picks_backup.json` (4 026 paris).
- **Date :** 2026-10-11.
- **Outil reproductible :** [`outils/clairvoyance/audit_rentabilite_clairvoyance.py`](../outils/clairvoyance/audit_rentabilite_clairvoyance.py) → [`docs/clairvoyance-rentabilite-audit.json`](../docs/clairvoyance-rentabilite-audit.json) (agrégats seulement, aucun pari recopié). Workflow quotidien : [`audit-rentabilite-clairvoyance.yml`](../.github/workflows/audit-rentabilite-clairvoyance.yml).

## Verdict

**La rentabilité affichée par Clairvoyance n'est pas démontrée.** Le site affiche environ **+978 unités, 70 % de réussite, ROI ≈ +25 %**. Une fois retirés les paris qui ne sont pas de vraies prévisions, puis ceux dont la cote n'a pas été observée sur le marché, **il reste 125 paris**. Leur ROI est de **+2,7 %**, avec un intervalle de confiance à 95 % de **[−9,8 % ; +15,1 %]**, c'est-à-dire **indiscernable de zéro**.

| Sous-ensemble (paris réglés, hors combinés) | n | Réussite | Proba. implicite des cotes | ROI | IC 95 % |
|---|---:|---:|---:|---:|---|
| Tout, tel que publié | 3 940 | 69,9 % | 56,9 % | **+24,6 %** | [+21,9 ; +27,3] |
| Verrouillés **après** le coup d'envoi | 182 | 84,1 % | 55,6 % | +58,5 % | [+43,9 ; +73,2] |
| Heure de match **inconnue** (incluse dans les chiffres publics) | 2 605 | 71,1 % | 56,3 % | +28,1 % | [+24,9 ; +31,4] |
| …dont verrou daté **> 300 jours avant** le match (saisie a posteriori) | 313 | 83,7 % | 56,2 % | +51,2 % | [+43,2 ; +59,3] |
| **Pré-match** (verrouillés avant le coup d'envoi) | 1 153 | 65,0 % | 58,5 % | +11,4 % | [+6,5 ; +16,3] |
| ↳ cote par défaut **−110** (non observée) | 748 | 57,8 % | 52,5 % | +10,0 % | [+3,2 ; +16,7] |
| ↳ cote « juste » du modèle **1/p** (non observée) | 198 | 83,3 % | 71,9 % | +16,1 % | [+8,5 ; +23,8] |
| ↳ cote **estimée** | 51 | 70,6 % | 72,6 % | −2,9 % | [−20,2 ; +14,5] |
| ↳ **cote de marché observée** | **125** | 68,8 % | 66,9 % | **+2,7 %** | **[−9,8 ; +15,1]** |

### Pourquoi les chiffres publics sont gonflés

1. **Paris verrouillés après le début du match.** L'auteur le reconnaît dans `scripts/lock_timing.py` : environ 93 % de réussite contre 66 % pour les verrouillages avant le début. Pourtant, `docs/engine_performance.json` déclare encore la base suivante : *« all locks (including picks locked after the game started) »*.
2. **Heure de match inconnue = comptée.** 2 605 paris (MLB, WNBA, tennis, NBA, NHL…) n'ont aucune heure de début vérifiable. Ils sont tout de même inclus dans les chiffres publics.
3. **Horodatages impossibles.** 313 paris réglés portent un `lockedAt` daté de plus de 300 jours avant le match. Ce sont typiquement les « historical wins » injectées en dur dans `docs/app.html` (`seedHistoricalProps`) ou des saisies a posteriori. Ils affichent 84 % de réussite et +160 unités.
4. **Cotes non observées.** Sur les 1 153 paris réellement pré-match, 946 sont comptés à une cote qui n'a jamais été relevée chez un bookmaker :
   - **−110 par défaut** appliqué à des marchés où ce prix n'existe pas : « Équipe +1,5 » ou « Under 3,5 » en football (cote réelle ≈ 1,15–1,45), handicaps ±1,5 en hockey, victoire sèche en 1X2. Les gains « football total/handicap » (+22,6 %) viennent de là ;
   - ou la **cote juste du modèle** (`decOdds = 1/winProb`) : par construction, ce n'est pas un prix de marché.
5. **Probabilités sur-confiantes.** Sur les paris pré-match, la probabilité annoncée est de 69,9 % pour 65,0 % de réussite. Pour le football US (spread/total), c'est 74,6 % annoncés pour 55,6 % réalisés. L'auteur l'a lui-même mesuré dans le commit `fe5eba7a` du 10/10 : sur le CFB O/U, *« Platt slope −0.17, the stated p carried no information »*. Il a donc ajouté un plafond de confiance (voir plus bas).

**Seul résultat honnête possible :** les 125 paris pré-match à cote de marché, tous datés du 2 au 10 octobre 2026 et principalement en hockey. Leur probabilité est déjà mélangée avec la cote du marché (`marketProb`, `blendAlpha`). Le résultat est cohérent avec « pas d'avantage » : NHL +1,7 % (n=58), SHL −12,1 % (n=17). Il faudrait **plusieurs milliers** de paris pré-match à cote observée pour détecter un avantage réaliste de 2–3 %.

## État de la reproduction dans Revue (travail de ChatGPT)

### Ce qui est juste

- Les **44 fonctions mathématiques** cataloguées (Elo MLB/NHL du backend, Monte-Carlo/Bayes/Ensemble NHL-NBA-NFL, xG/Poisson/handicap football, ensembles hockey européen, prétraitements NBA, forme, gardiens, blessures, props NBA) donnent des sorties **identiques** au code original sur des entrées de test. J'ai relancé toutes les vérifications contre le commit actuel `0d900f51` :
  - prédicteurs : 43 comparaisons ;
  - prétraitements NBA : 446 ;
  - frontend : 6 263 ;
  - parseur MoneyPuck : 203 ;
  - parseur ESPN NBA : 460 ;
  - classificateur temporel : 9 001 opérations ;
  - NHL style backend : 24.
- **Prudence méthodologique :** pas de copie du code tiers, verdict « rentabilité non validée », journal papier séparé du ROI. C'est la bonne posture.

### Ce que j'ai corrigé

| Problème | Correction |
|---|---|
| Parité **cassée** sur le source actuel. Clairvoyance a ajouté le 10/10 un plafond de confiance non-moneyline (`MARKET_P_CEILING`, `_mktCeiling`, `_capMktP` : CFB/NFL 0,62, le reste 0,68). `_generateNBAProps` l'utilise désormais et le vérificateur plantait (`_capMktP is not defined`). | Nouveau module [`frontend_clairvoyance_market_ceiling.js`](../modeles/reproduction/frontend_clairvoyance_market_ceiling.js). Plafond appliqué dans `nbaProps` (probabilité, grade, cote). Le vérificateur injecte les fonctions source et ajoute 1 520 comparaisons directes du plafond. J'ai vérifié que le test échoue sans le plafond. Rapports de parité regénérés sur `0d900f51`. |
| Pari papier `paper-000026` (Lorient–Paris FC) marqué « gagné » **sans score ni heure de règlement**, alors que l'outil de règlement écrit toujours ces preuves. | Score vérifié sur ESPN (événement 401876445 : Lorient 1-0 Paris FC). Preuve ajoutée, avec une note signalant l'ajout a posteriori. |
| 2 tests figeaient la taille d'un registre **vivant** (`settled == 1`) et cassaient dès qu'un nouveau match NHL était réglé. | Ces tests comparent désormais au registre lui-même. **852 tests Python et 53 tests JS passent.** |
| L'analyse précédente reprenait les chiffres publics (« 3 816 paris, +965,78 u ») sans recalculer le ROI pré-match ni la provenance des cotes. | Outil d'audit reproductible et testé (11 tests), plus ce rapport. |

### Ce qui n'est PAS encore « pareil »

Les 44 fonctions sont la **couche modèle**. Or les paris de Clairvoyance sortent d'une **couche de sélection** que Revue ne reproduit pas encore :

1. `sportCalibrate` (constantes `SPORT_CAL`) et la correction adaptative `window._calAdjProb`. Elle est recalculée à partir de `docs/adaptive_weights.json` **et du `localStorage` du navigateur du propriétaire**. Les probabilités vivantes dépendent donc d'un état qui n'est pas entièrement public. Pour la rejouer, il faudrait relire l'historique Git de `adaptive_weights.json` à chaque heure de verrouillage.
2. `_evalMkts` / `tier()` : seuils OPTIMAL/PREMIUM, re-tarification de l'EV et plafond appliqué aux cartes CFB/NFL/football.
3. Les règles de verrouillage automatique de `scripts/auto_lock_settle.py` : cote réelle exigée en hockey, bande de sélection CFB, lignes alternatives à prix **estimé**, portes « gardien/lineup confirmé ».
4. Les données : Opta (sous droits), FBref, QuantHockey, MoneyPuck, ESPN, aux mêmes instants que le source.

**Priorité recommandée :** ne pas chercher à reproduire la couche de sélection pour « copier la rentabilité ». Les chiffres ci-dessus montrent qu'il n'y a pas de rentabilité prouvée à copier. Mieux vaut d'abord accumuler, dans Revue, des prévisions **horodatées avant match** et confrontées à des **cotes réellement observées** (journal papier déjà en place, `engine-v2-ledger.json`), puis juger sur la CLV et le ROI à cote observée.

## Autres risques relevés dans Revue

- **58 workflows GitHub Actions**, dont 49 poussent sur `main`, plusieurs fois par jour. 18 d'entre eux utilisent `git pull --rebase -X theirs` : en cas de conflit, la version locale du job écrase silencieusement les mises à jour concurrentes du même fichier JSON. Il serait sage de regrouper les publications dans un seul job séquentiel.
- Le `README.md` est un journal de phases empilées (« Phase 1… Phase 14 ») plus qu'une porte d'entrée. Le verdict de rentabilité devrait y figurer en tête, d'où l'encadré ajouté.
