# Revue ciblée — opisthokonta/implied

**Avis : Meilleure référence trouvée pour comparer les conversions cotes → probabilités ; la méthode Shin par défaut échoue sur les marchés à deux issues.**

- Source : https://github.com/opisthokonta/implied
- Version examinée : [`1d1c5cd548dd71bc1b9addd733db5c2db8566b71`](https://github.com/opisthokonta/implied/tree/1d1c5cd548dd71bc1b9addd733db5c2db8566b71) ; branche `master` ; dernier commit le 2026-05-23.
- Consultation : 2026-10-12.
- Famille : Multi-sports · retrait de marge ; stack : R.
- Priorité de recherche : **P1** ; ce classement exprime l'utilité pour Revue, pas la rentabilité.
- Licence observée : GPL-3 (champ `License` du DESCRIPTION ; pas de fichier LICENSE séparé).

## Ce que la source permet d'établir

- Le paquet regroupe neuf conversions : `basic` (multiplicative), `shin`, `bb` (balanced books), `wpo`, `or` (odds ratio), `power`, `additive`, `jsd` et `goto`/`ooepc`, avec références bibliographiques et un paramètre `target_probability` pour les marchés à plusieurs gagnants (top 3, qualification).
- **Défaut confirmé sous R 4.3.3** : `implied_probabilities(c(1.25, 4.00), method = 'shin')` s'arrête sur l'erreur `missing value where TRUE/FALSE needed`, de même pour `c(1.90, 1.90)`. Cause : la boucle Jullien-Salanié par défaut (`shin_method = 'js'`) divise par `n_outcomes - 2`, soit zéro sur deux issues. Avec `shin_method = 'uniroot'`, le même appel renvoie 0,775 / 0,225, identique à la méthode additive comme l'indique la vignette.
- **Second défaut** : pour `goto`/`ooepc`, le code écrit `out$zvalues <- probs` ; le champ `zvalues` contient donc les probabilités (0,230 ; 0,263 ; 0,507 sur 4,20/3,70/1,95) au lieu du scalaire z (≈ 0,00874).
- Précision de la boucle `js` : arrêt quand |Δz| ≤ ε^0,25 ≈ 1,2e-4 et conservation de l'itéré précédent. Sur 4,20/3,70/1,95, écart de probabilité maximal 1,5e-5 avec la racine exacte ; 9,6e-5 sur le cas de test à six issues.
- Sur une même cote 1,25/4,00, les méthodes donnent au favori de 0,762 (multiplicative) à 0,789 (balanced books) : 2,7 points d'écart purement méthodologiques.

## Limites et points à contrôler

- Les tests du paquet ne couvrent aucun marché à deux issues avec Shin ; la vignette affirme pourtant l'équivalence Shin = additive sur deux issues.
- Aucune méthode n'est validée empiriquement par le paquet : il convertit, il ne dit pas quelle conversion est la mieux calibrée.
- Licence GPL-3 : réécrire les formules (publiques) plutôt que copier le code dans Revue.

## Enseignement pour Revue

Utiliser `implied` comme banc de référence des formules, et choisir la méthode par mesure empirique sur la source de cotes réellement utilisée. Voir la fiche [REV-IMPLIED-01](REV-IMPLIED-01_choix-devig-par-marche.md) et l'outil Revue `outils/controles/calibration_devig.py`.

**Comparaison avec le catalogue :** Complète [shin](../shin/AUDIT.md), [goto_conversion](../goto_conversion/AUDIT.md) et `outils/controles/sensibilite_devig.py`. Contredit l'idée qu'un nom de méthode garantit un calcul identique : deux algorithmes Shin du même paquet diffèrent (et l'un échoue sur deux issues).

**Décision :** conserver cette source dans son dossier indépendant comme référence de recherche. Aucune intégration de code, de données ou de dépendance tierce dans Revue.

## Niveau de preuve

Fichier `R/implied_probabilities.R` sourcé dans R 4 isolé et exécuté sur 11 cas ; portage Python indépendant pour la racine exacte. Paquet complet et tests testthat non exécutés.

Revue ciblée, pas un audit exhaustif ni un audit de sécurité. Aucun avantage économique n'est démontré par cet examen. Score d'intérêt chiffré : **NC**.

## Fichiers lus (empreintes dans `sources.json`)

- [DESCRIPTION](https://github.com/opisthokonta/implied/blob/1d1c5cd548dd71bc1b9addd733db5c2db8566b71/DESCRIPTION)
- [R/implied_probabilities.R](https://github.com/opisthokonta/implied/blob/1d1c5cd548dd71bc1b9addd733db5c2db8566b71/R/implied_probabilities.R)
- [tests/testthat/test_1.R](https://github.com/opisthokonta/implied/blob/1d1c5cd548dd71bc1b9addd733db5c2db8566b71/tests/testthat/test_1.R)
- [vignettes/introduction.Rmd](https://github.com/opisthokonta/implied/blob/1d1c5cd548dd71bc1b9addd733db5c2db8566b71/vignettes/introduction.Rmd)
- [NEWS.md](https://github.com/opisthokonta/implied/blob/1d1c5cd548dd71bc1b9addd733db5c2db8566b71/NEWS.md)

[Comparatif de la recherche](../../recherche/panorama-github-2026-10-12/README.md) · [Index des analyses](../README.md)
