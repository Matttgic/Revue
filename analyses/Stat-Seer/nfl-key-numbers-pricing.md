# REV-STATSEER-03 — Prix des demi-points NFL autour des key numbers

**Statut : À étudier — méthode empirique documentée par l’auteur, non reproduite ici.**

- **Sport / ligue :** football américain, NFL
- **Marché :** spreads et lignes alternatives
- **Origine :** [Stat-Seer, commit `1016bf6`](https://github.com/derekj987/Stat-Seer/tree/1016bf6193c8ef03de1f756202c887baa829d2f1), `analysis/alt_lines_v2.py`, `analysis/total_key_numbers.py`
- **Licence :** aucune licence explicite repérée; aucun code repris

## Hypothèse

La valeur d’un demi-point dépend du nombre franchi. Une approximation normale lisse les masses concentrées sur les marges NFL de 3 et 7. Estimer la distribution des marges près du spread réel permet de convertir une ligne alternative en probabilité de victoire conditionnelle, puis en prix juste et en prix minimal pour que l’achat de points conserve l’espérance du pari initial.

## Éléments publiés

Sur 6 967 matchs réguliers de 1999 à 2025, l’auteur rapporte une marge exactement égale à 3 dans 15,01 % des matchs et à 7 dans 9,10 %. Le tableau de son moteur estime la valeur d’un demi-point plus grande aux spreads correspondant à ces masses. La version corrigée compare les spreads à des matchs dans une fenêtre ±0,5 et exige un taux de base proche de 50 %.

Le dépôt conserve aussi la première version, qui mélangeait des spreads jusqu’à ±1,5 point. Selon le commentaire du code, ce choix gonflait le taux de couverture de base à 53,9 %, un faux signal; le resserrement l’a ramené à 50,3 %. Cet exemple est une mise en garde utile contre la sélection d’un échantillon trop large autour d’une ligne alternative.

## Limites et usage proposé

- Les fréquences historiques et la probabilité de couverture sont des estimations d’auteur; elles ne garantissent pas que le prix offert pour acheter le point soit favorable.
- La précision dépend du nombre de matchs dans chaque fenêtre et de la stabilité des marges selon les saisons; publier l’effectif par ligne et l’incertitude.
- Comparer le prix alternatif au prix du pari de base, calculer l’EV après marge et vérifier la disponibilité réelle chez un bookmaker.
- Le contexte réglementaire français et l’offre locale de spreads NFL restent à vérifier.

**Verdict :** idée arithmétique utile pour une calculatrice de line shopping; aucun avantage de pari autonome n’est démontré.
