# REV-CLAIR-03 — Couvertures de lignes alternatives pour hockey / NBA

**Statut : À étudier.** Source : https://github.com/Purple-Wraith/clairvoyance-backend/blob/main/scripts/backtest_alt_lines.py

## Concept
Partir d'une ligne principale historique et estimer la fréquence de couverture de lignes plus conservatrices (par exemple O/U autour du total bookmaker), avec règles de push et contexte propre à chaque ligue. Pour les handicaps, estimer la distribution de la marge de victoire.

Le script de la source teste NHL, NBA et 4 ligues de hockey européen, et signale explicitement le **but accordé pour le résultat des tirs au but NHL**, qu'il faut exclure du total pour la comparaison aux règles de règlement des bookmakers (à vérifier chez l'opérateur cible).

## Conditions
- Distinction des lignes `x.0`, `x.5`, handicaps entiers et marchés alternatifs autorisés.
- Comparer **probabilité de gagner / de push / de perdre** et EV à la **cote spécifique de la ligne alternative**; une ligne plus facile a normalement une cote moins favorable.
- Ne jamais conclure que « +70% de réussite » => profit.
- Ne pas transférer une courbe NHL aux championnats européens sans validation des distributions et des règles.

**Verdict :** méthode statistique prometteuse pour explorer des marchés à forte réussite; aucune rentabilité démontrée sans cotes alternatives.
