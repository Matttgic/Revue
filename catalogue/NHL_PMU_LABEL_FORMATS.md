# Analyse privée des formats PMU

## Observation et portée

Le run réel 38405134806 observe 573 marchés ANYTIME_GOALSCORER FULL_TIME,
573 sélections et 661 joueurs ESPN. `rawName` est un texte aux niveaux marché
et sélection ; les autres champs de nom autorisés sont absents. Aucun des deux
`rawName` n'a produit de correspondance exacte avec les contraintes du moteur.
Les seuls agrégats historiques ne permettent pas de retrouver les formats.
Aucun nouvel appel fournisseur n'est effectué pour développer cette analyse.

`schema.label_formats` ajoute des compteurs privés, sans modifier le moteur.
Deux périmètres sont indépendants : `all_references` (toutes les lignes ESPN),
`event_teams` (lignes dont l'équipe courante est observée et appartient aux deux
équipes reconnues de l'événement). Le second n'établit ni correspondance de
rencontre, ni participation, ni identité acceptable. Les références de noms NHL
proviennent d'ESPN ; ce ne sont pas deux sources d'identité indépendantes.

Pour chacun, les niveaux `market` et `selection` et la liste fixe rawName, name,
playerName, participantName, label, title ont leurs propres compteurs. Un marché
compte une fois, quelle que soit sa cardinalité ; chaque objet sélection compte
une fois. Les champs absents/non textuels comptent comme impossibles pour toutes
les méthodes. Aucun champ inconnu ou objet imbriqué n'est exploré ni exporté.

## Méthodes indépendantes

Normalisation commune : casse et accents, ponctuation séparatrice de mots ; pas
de distance d'édition, phonétique, correction d'orthographe ou alias inventé.
Cette normalisation conserve les frontières de mots, contrairement au `name_key`
compact historique. Chaque méthode compare le texte complet, sauf l'inclusion.

- `full_exact` : égalité de toute la séquence de mots du nom complet.
- `full_word_contained` : séquence complète contiguë incluse dans le libellé ;
  jamais une sous-chaîne à l'intérieur d'un mot. Peut détecter plusieurs joueurs.
- `reversed_full` : premier mot déplacé après tous les autres mots, sans supprimer
  aucun mot. Hypothèse de format prénom/nom, pas preuve des parties du nom.
- `initials_surname` : tous les mots sauf le dernier réduits à leurs initiales,
  suivis du dernier mot entier. Comparaison du libellé entier uniquement.
- `surname_only` : dernier mot seul, sans recherche partielle. La présence de
  plusieurs références partageant ce mot rend le résultat ambigu, jamais unique.

Les deux dernières méthodes et l'inversion sont des hypothèses explicites de
segmentation. Les noms composés/suffixes ne sont pas réinterprétés : le dernier
mot n'est pas une preuve de patronyme. Une référence avec moins de deux mots
n'est candidate à aucune méthode. Chaque méthode produit uniquement `unique`,
`ambiguous`, `impossible` ; leur somme égale `texts`. Les méthodes se chevauchent,
leurs résultats ne doivent pas être additionnés. Les doublons de référence ne
sont pas fusionnés pour fabriquer de l'unicité.

Compteurs descriptifs : `generic_yes_no` (oui/non/yes/no et leurs paires),
`bet_description_marker` (liste fixe de mots liés au pari),
`full_name_with_extra_text` (nom complet inclus avec texte supplémentaire),
`full_name_with_bet_description` (les deux conditions). Un mot marqueur n'est
pas une validation sémantique du pari. Un oui/non ne reçoit pas l'identité du
marché ; aucun rapprochement marché/sélection n'est accepté.

## Workflow prêt, non lancé

Le workflow existant `nhl-pmu-matching-validation.yml` est étendu avec les tests
synthétiques des formats. Toujours exclusivement manuel, autorisation booléenne
fausse par défaut et garde CLI `--authorize-one-call`. Références publiques
NHL/ESPN actualisées avant une unique tentative PulseScore PMU, sans retry,
redirection ni pagination. La même réponse en mémoire alimente les diagnostics.
Aucun appel supplémentaire n'est introduit. Une référence invalide bloque l'appel.

Aucun nom, identifiant, extrait ou réponse fournisseur n'est écrit. Le seul
artefact contient des compteurs agrégés, dans /tmp, conservés un jour sans commit
ni publication dans docs. La visibilité de l'artefact suit celle du dépôt :
ce n'est pas une garantie de confidentialité d'accès. Aucun prix n'est ajouté
au diagnostic des formats. Le workflow n'est pas lancé dans cette PR.

## Hypothèse prometteuse et validation future

L'inclusion du nom complet avec frontières de mots est la première hypothèse à
évaluer : elle peut expliquer un nom accompagné d'une description sans perdre
les mots du nom. Rien dans les agrégats actuels ne démontre qu'elle réussira.
Inversion et initiales sont des alternatives à comparer indépendamment ; le
patronyme seul est le moins probant, même unique dans une référence incomplète.

Après autorisation explicite d'une tentative : comparer les compteurs des deux
niveaux et périmètres, les ambiguïtés et les marqueurs de description. Un taux
élevé de candidats uniques mesure une couverture, pas une précision démontrée.
Confirmer ensuite dans un environnement privé autorisé, sans export de textes,
un échantillon stratifié des candidats et des rejets contre des identités
indépendamment vérifiées (équipe, rencontre, nom complet et sémantique de l'issue),
avec contre-exemples et homonymes. Mesurer faux positifs et faux négatifs avant
une éventuelle adaptation du moteur. Aucune méthode n'est activée automatiquement,
aucune probabilité ni aucun EV n'est modifié.
