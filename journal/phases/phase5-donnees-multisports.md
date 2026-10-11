# Phase 5 — Source data readiness / NHL NBA MLB football

Nouveau contrôle `outils/controles/phase5_donnees_multisports.py` et page
`docs/phase5-donnees.html` (Lab Revue). Résultats machine-readable :
`docs/phase5-sources-latest.json`. Exécution automatique et tests adversariaux.

**NBA :** comparer les 30 valeurs d'efficacité historiques aux
statistiques régulières actuelles. Les matchs de présaison ne
constituent pas une saison NBA régulière. Ne pas annoncer current
si seul le prior 2025–26 existe.

**NHL :** vérifier MoneyPuck `all` vs `5on5`, gardiens officiels saison/type,
absence de doublons, égalité des saisons et prise de l'instantané avant
le match. Le backend Clairvoyance utilise `all`, Revue avait commencé
sur `5on5`. Le modèle source style reste un scénario : SQL Elo inaccessible,
configuration publique par défaut 2025–26 playoffs vs scénario 2026–27
saison régulière, gardien de référence « le plus utilisé » ≠ titulaire
confirmé. Utilisation MoneyPuck personnelle non commerciale avec attribution,
pas d'extension de droits présumée.

**MLB :** rejouer indépendamment l'Elo ESPN tout en distinguant strictement
le repli original Elo 1500 : impossible de recréer le SQL Elo initial et le
classement temporel des paris source sur ces seuls historiques.

**Football :** vrai volume tirs ESPN et possessions, mais **0 statistique
xG Opta** ni licence d'ingestion correspondante ; aucune conversion
artificielle de tirs en xG sous le nom de Clairvoyance.

Les nombres sont des **observations de Revue**, pas une parité
sur les données utilisées en production par Clairvoyance.
Aucun nouvel appel API payant, aucune modification des prévisions gelées,
aucune mise réelle et CFB exclu.
