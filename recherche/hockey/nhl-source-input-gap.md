# Écart des entrées NHL : audit sans paris

Clairvoyance utilise les statistiques MoneyPuck de situation **all** et le gardien NHL Edge ayant le plus de matchs, tandis que le SHADOW Revue utilise le **5on5** et des gardiens MoneyPuck historiques. Ce comparateur ne modifie aucune prévision gelée. Il applique la même formule à des entrées différentes avec **l'Elo proxy Revue**, sans supposer disposer de la base de données SQL originale.

- Code autonome : `outils/nhl_source_input_gap.py`
- Sorties mesurées : `docs/nhl-source-input-delta.json`
- Tests : `tests/test_nhl_source_input_gap.py`
- Mise à jour : `.github/workflows/nhl-source-input-gap.yml`

Les deux ratios xG proviennent d'un même instantané MoneyPuck vérifié. Le gardien officiel provient parfois d'un **instantané plus récent** que le modèle gelé : les deltas sont un diagnostic de sensibilité pré-match, **pas** un backtest à horodatage identique. Si deux gardiens ont le même nombre de matchs, aucun choix arbitraire n'est effectué. Aucun pari réel, aucune cote inventée.

**Blocage supplémentaire** : le code public `app/config.py` du backend original affiche des valeurs par défaut pour les *playoffs 2025-26* (`NHL_SEASON=20252026`, `NHL_GAME_TYPE=3`), tandis que Revue observe la *saison régulière 2026-27*. La configuration du service original réellement déployé n'est pas connue. Le parseur original reprend `xGoalsPercentage` brut, potentiellement sous forme 0–1, alors que la formule divise la différence par 100. Le diagnostic utilise explicitement l'échelle 0–100 et ne revendique pas une identité de comportement SQL.

## Étude de la normalisation MoneyPuck (0–1 contre 0–100)

Le code source public original lit `xGoalsPercentage` en nombre sans remise à l'échelle, puis le modèle applique `(xG_domicile - xG_extérieur) / 100 × 0,3`. Dans Revue, le modèle shadow travaillait auparavant à l'échelle 0–100. Un **nouveau scénario indépendant** utilise l'échelle brute hypothétique **0–1** (celle des fractions sauvegardées par Revue) avec l'Elo Revue constant et les mêmes gardiens ; il mesure la différence entre ces deux conventions et respecte l'arrondi du prédicteur.

Il s'agit d'une étude conditionnelle : la **valeur précise effectivement enregistrée dans la SQL originale, la saison active, les Elo et les titulaires ne sont pas connus**. Cet audit ne remplace ni les prévisions figées ni le calcul des picks. Colonnes de sortie : `all_xg_raw_fraction_only_home_probability`, `all_xg_raw_fraction_and_official_goalie_home_probability`, `raw_fraction_vs_pct_points_scale_change_pp`. Les indicateurs sont exclusivement des sensibilités, non des preuves de reproduction exacte.

Données MoneyPuck destinées à une étude personnelle non commerciale, créditées à MoneyPuck.com : https://moneypuck.com/data.htm.
