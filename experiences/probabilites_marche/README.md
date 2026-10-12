# Comparateur de probabilités de marché

**Question : un écart de prix persiste-t-il lorsqu’on change la façon de retirer la marge du bookmaker de référence ?**

Cette première expérience transforme des idées du catalogue en un outil exécutable sur les données Revue. Elle réutilise les fonctions originales multiplicative/additive/power de `outils/controles/sensibilite_devig.py` et ajoute une résolution indépendante de l’équation de Shin par bissection. Aucun code tiers copié ni dépendance ajoutée.

## Sources des idées

- [mberk/shin](../../analyses/shin/AUDIT.md) : équation probabiliste, convergence et équivalence additive à deux issues. Références de l’équation : Shin (1992), DOI `10.2307/2234526`, et Shin (1993), DOI `10.2307/2234240`.
- [penaltyblog](../../analyses/penaltyblog/AUDIT.md) : comparer plusieurs hypothèses sur une même entrée.
- [goto_conversion](../../analyses/goto_conversion/AUDIT.md) : ne pas assimiler un nom de fonction à une méthode identique ; goto n’est pas implémenté dans cette première version.
- [Betting-Dashboard](../../analyses/Betting-Dashboard/AUDIT.md) : sensibilité au retrait de marge et comparaison aux autres sources.
- [OddsHarvester](../../analyses/OddsHarvester/AUDIT.md) et [soccerdata](../../analyses/soccerdata/AUDIT.md) : importance de la période, de la ligne et des horodatages.

## Exécution

Depuis la racine de Revue, Python standard suffit :

```bash
python -m unittest experiences.probabilites_marche.test_comparer
python -m experiences.probabilites_marche.comparer docs/engine-v2-latest.json --output /tmp/revue-comparaison-marche
```

Le programme lit le tableau `odds_board` de l’entrée, puis écrit `resultats.json` et `RESULTATS.md` dans le dossier demandé. Il ne modifie pas l’entrée, n’envoie aucune requête réseau et ne crée aucun pari.

L’[observation enregistrée](observation-2026-10-12/RESULTATS.md) a utilisé `docs/engine-v2-latest.json` au commit `4e46a9b6db62d47e3a460d2d083194b1fd902c06`. Pour rejouer cette entrée précise :

```bash
git show 4e46a9b6db62d47e3a460d2d083194b1fd902c06:docs/engine-v2-latest.json > /tmp/revue-entree-20261012.json
python -m experiences.probabilites_marche.comparer /tmp/revue-entree-20261012.json --output /tmp/revue-rejeu-20261012
```

SHA256 attendu : `9321d83af18e681d68b5bf0f2f0e9ef89456da12c54037ff628565278efa2d37`.

## Contrat de comparaison

- Marchés football marqués `90min` dans la source, complets : 1N2 ou over/under sur une même demi-ligne. Ce marquage est repris du tableau existant ; le programme ne revérifie pas le contrat du bookmaker à la source.
- Cotes numériques finies supérieures à 1 ; marchés à marge négative exclus de ce premier périmètre.
- Observation avec fuseau, au plus 30 minutes avant le snapshot ; snapshot antérieur au match. Il s’agit d’une relecture historique, pas d’une promesse de fraîcheur actuelle.
- Même ligue, identifiant de rencontre, début, marché et ligne ; bookmaker de référence différent du bookmaker évalué ; observations distantes de 60 secondes au maximum.
- Duplications ambiguës exclues. Totaux entiers/quarts exclus car leurs remboursements et divisions de mise nécessitent un autre calcul.
- Toutes les sorties valides sont conservées ; aucun choix de méthode sur les gains. L’additif indisponible n’est pas remplacé silencieusement.

Pour chaque référence et issue, le calcul `p_méthode × cote_cible − 1` est une **espérance hypothétique sous cette référence**, sans preuve de calibration. Les comparaisons sont dirigées et dépendantes. Un signe positif n’est pas un conseil de mise. Les chances estimées par plusieurs bookmakers ne sont pas forcément indépendantes.

## Validation

Neuf tests couvrent l’exemple numérique publié de Shin, les cas à deux issues, les permutations, les entrées invalides, la chronologie, les marchés incomplets, les doublons, les lignes différentes, les conditions de règlement et l’absence de comparaison à soi-même. Ils vérifient aussi que l’entrée n’est pas modifiée.

Résultat exécuté : **51 marchés retenus, 160 comparaisons, 13 changements de signe**. Les 69 lignes hors périmètre football et les cinq marchés invalides ou non pris en charge sont comptabilisés. L’expérience ne permet pas de choisir la meilleure méthode : cela nécessitera des issues réellement réglées sur des périodes réservées.
