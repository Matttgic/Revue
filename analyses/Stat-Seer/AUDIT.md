# Audit — derekj987/Stat-Seer

- **Source :** https://github.com/derekj987/Stat-Seer
- **Auteur indiqué :** Derek (nom d’utilisateur GitHub `derekj987`)
- **Commit examiné :** `1016bf6193c8ef03de1f756202c887baa829d2f1` (`main`), 2026-10-11
- **Date de consultation :** 2026-10-11
- **Licence :** aucune licence explicite repérée à la racine ou dans l’arbre suivi au commit examiné. Pas de reprise de code ni de données.
- **Stack observée :** analyses Python (pandas, NumPy, scikit-learn, SciPy), application Next.js/TypeScript, PostgreSQL/Supabase et GitHub Actions.
- **But :** application de conseil NFL et laboratoire de modèles sur les spreads, totaux et paris joueurs. Le dépôt distingue explicitement le prix (Value Finder), le modèle sans ligne (The Model) et l’information contextuelle (Context).
- **Verdict :** **documentation de recherche utile, aucune rentabilité démontrée ni code importé**. Le modèle de part de snaps est une piste de prévision du rôle des joueurs; les rapports publiés ne valident pas un avantage sur les cotes.

## Éléments recensés

| Domaine | Idée ou résultat | Statut de la preuve | Fiche |
|---|---|---|---|
| NFL — joueurs | Prévoir la part de snaps avec historique récent, rôle relatif et informations médicales pré-match; gain d’erreur rapporté surtout lors d’un changement de rôle | Walk-forward auteur 2022–2024; résultats non reproduits ici; ne mesure pas les paris | [Part de snaps](nfl-snap-share-role-change.md) |
| NFL — props | Séparer volume et efficacité; régresser l’efficacité plutôt que extrapoler une courte série de yards | Corrélations et MAE walk-forward publiés; test rapporté contre la ligne de clôture inférieur au seuil de rentabilité | [Volume et efficacité](nfl-volume-versus-efficiency.md) |
| NFL — spreads | Évaluer les demi-points selon la distribution empirique des marges et les key numbers 3/7 | Historique auteur de 6 967 matchs; variante initiale erronée puis resserrée; aucun ROI de paris prouvé | [Lignes alternatives](nfl-key-numbers-pricing.md) |

## Résultats publiés par l’auteur

Le rapport `analysis/FINDINGS.md` annonce 60 858 semaines-joueurs (RB/WR/TE), dont 17 404 prédictions de test walk-forward sur 2022–2024. La MAE de part de snaps publiée passe de 0,1112 pour la persistance de la semaine précédente à 0,1047 pour le modèle (+5,9 %). Sur les semaines où un signal de changement défini avant le match se déclenche, la MAE passe de 0,1223 à 0,1123 (+8,2 %, n=9 345); sans signal, le gain annoncé est de 2,6 % (n=8 059).

Ces chiffres concernent l’erreur de prévision des snaps pour les joueurs ayant joué. Ils ne sont ni un taux de paris gagnants, ni un retour sur investissement, ni une comparaison aux lignes de bookmakers. Le rapport `docs/EMPIRICAL_REFERENCE.md` donne aussi un test 2024 de projections contre les lignes de clôture : 6 457 props, 50,2 % de réussite au total contre environ 52,4 % de seuil à −110. L’auteur conclut que ses projections de volume et d’efficacité ne battent pas le marché.

## Contrôles et limites

- **Chronologie :** `analysis/model.py` entraîne chaque semaine sur `t < semaine test`; le test principal utilise les saisons 2022–2024. `analysis/features.py` décale les historiques de snaps et limite la variable déclarée `vacated_out` au statut Out/Doubtful du rapport hebdomadaire. Le walk-forward et plusieurs tests négatifs sont documentés.
- **Disponibilité et composition :** l’estimand est `E[share | active]`; le dépôt reconnaît qu’il lui manque un modèle d’activation et que les rapports d’absence ne capturent qu’une partie des inactifs de dernière minute. En outre, `grp_prior_sum`, `grp_n_active` et `depth_rank` sont construits depuis les lignes de snaps de la semaine cible. Leur disponibilité réelle avant le coup d’envoi doit être démontrée avec des effectifs datés d’avant-match avant d’utiliser ces variables en production; ceci est un risque à vérifier, pas une fuite démontrée ici.
- **Conversion en paris :** la part de snaps ne donne pas à elle seule carries, targets, yards ou probabilité over/under. Le rapport source dit que la couche availability manque. Pour les yards, la projection volume × efficacité égale à peu près la moyenne saisonnière et ne bat pas le close dans le test 2024 publié.
- **Marché des matchs :** sur 6 967 matchs NFL (1999–2025), le dépôt rapporte un écart moyen résultat–spread de +0,069 point et une MAE de marché inférieure au modèle de marge. Ses propres tests ATS et de totaux ne montrent pas de taux dont l’intervalle de confiance dépasse le seuil −110.
- **Lignes alternatives :** `analysis/alt_lines.py` est la première variante; elle utilise une fenêtre ±1,5 point et son propre commentaire indique que ce mélange crée une fausse fréquence de couverture de base de 53,9 %. `analysis/alt_lines_v2.py` resserre les spreads à ±0,5 et impose un contrôle de ligne de base proche de 50 %. Il faut retenir la correction et non les résultats initiaux.
- **Données :** les séries publiques nflverse peuvent être téléchargées par `analysis/fetch_data.py` (environ 150 Mo selon le README). Les validations historiques de cotes joueurs interrogent `prop_snapshots` dans Supabase et exigent des identifiants/configuration non fournis par les fichiers publics. Les licences des fournisseurs et de leurs données restent à examiner pour tout usage.
- **Tests et sécurité :** aucun fichier de tests Python évident au commit; le workflow CI visible vérifie le typage et les dépendances web, et configure des analyses Semgrep et gitleaks non bloquantes. Le dépôt complet et son application n’ont pas fait l’objet d’un audit de sécurité.
- **Exécution :** code non installé ni exécuté durant cet audit. Aucune API payante ni clé n’a été sollicitée.

## Intérêt (barème Revue /100)

**Score global : NC.** Les idées et des résultats empiriques sont bien documentés, mais la reproduction indépendante, l’accès à l’historique de cotes, la confirmation de la disponibilité pré-match de certaines variables, les autorisations de données et la licence du code restent insuffisamment établis pour noter sans spéculer.

## Décision

- Conserver trois pistes de recherche dans le catalogue avec statut **À étudier**.
- Ne pas copier les scripts : aucune licence explicite n’a été trouvée.
- Pour la part de snaps, reproduire la comparaison avec une cohorte de test chronologique intacte et un instant de prédiction fixé; vérifier que chaque membre du groupe et chaque variable étaient connus à cet instant.
- Avant toute prétention d’avantage, transformer les prévisions en distributions de props et les comparer aux cotes réellement accessibles avant match, au consensus sans marge et à la ligne de clôture; publier CLV, calibration, ROI et intervalles d’incertitude.

Références primaires : [README](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/README.md), [CLAUDE.md](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/CLAUDE.md), [FINDINGS.md](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/analysis/FINDINGS.md), [référence empirique](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/docs/EMPIRICAL_REFERENCE.md), [modèle de snaps](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/analysis/model.py), [features](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/analysis/features.py), [lignes alternatives v2](https://github.com/derekj987/Stat-Seer/blob/1016bf6193c8ef03de1f756202c887baa829d2f1/analysis/alt_lines_v2.py).
