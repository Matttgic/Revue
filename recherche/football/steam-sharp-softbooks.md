# REV-BLUMMA-01 — Steam + réaction différée d'un bookmaker

**Statut : À étudier | source https://github.com/blummabet/Betting-Dashboard (auteur blummabet, licence non spécifiée).**

## Hypothèse
Quand un bookmaker de référence modifie rapidement sa probabilité, les prix chez certains autres bookmakers peuvent réagir avec retard. L'opportunité **n'existe que si la cote encore proposée est réellement accessible et favorable**, pas parce que le prix sharp a bougé.

## Sources techniques
[steam_engine.py](https://github.com/blummabet/Betting-Dashboard/blob/main/steam_engine.py), [lead_lag_bias.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/lead_lag_bias.py), [multi_book_steam.py](https://github.com/blummabet/Betting-Dashboard/blob/main/sharp_signals/multi_book_steam.py).

## Règles de reconstruction indépendante
- Snapshot `opening`, `current` et quote du bookmaker cible **avec horodatages, ID match et ligne identique**.
- Mouvement mesuré en probabilité **sans marge** sur issues complètes ; conserver la variation brute aussi.
- Distinguer le déclencheur (mouvement sharp) de la preuve de value (cote réellement jouable vs probabilité calibrée).
- Exclure mauvais appariements, cotes périmées, marché suspendu, prix unavailable, faibles liquidités.
- Consigner alertes ignorées et leurs résultats ; éviter de choisir un seuil « 3–6 pp » après avoir regardé les bénéfices historiques.

## Tests requis
Échantillonnage prospectif à heure fixe ou cadences comparables, CLV, ROI, délai sharp→soft, variation des seuils, par cote et marché. Comparer à suivi aveugle de mouvements aléatoires. Horodatage strict et opérateurs agréés français.

**Limite :** « sharp money » déduit d'une baisse de cote n'est pas une observation directe du flux de mises. Aucun résultat profitable reproduit.
