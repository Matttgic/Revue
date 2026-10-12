"""Expérience hors ligne : sensibilité des probabilités aux méthodes de dé-vig.

Implémentation Revue ; aucune collecte, aucun ordre, aucun changement de ledger.
Shin est résolu par bissection de l'équation publiée, sans code tiers importé.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from outils.controles.sensibilite_devig import comparer_methodes


def shin(cotes: list[float]) -> list[float]:
    # Réutilise la validation existante des cotes et du nombre d'issues.
    base = comparer_methodes(cotes)
    q = [1.0 / float(x) for x in cotes]
    total = sum(q)
    if total < 1 - 1e-12:
        raise ValueError("Shin : livre à marge négative hors périmètre")
    if abs(total - 1) <= 1e-12:
        return [x / total for x in q]
    if len(q) == 2:
        p = base['probabilites'].get('additive')
        if p is None:
            raise ValueError("Shin : probabilités invalides")
        return p

    def probabilities(z):
        return [2 * x*x / total /
                (math.sqrt(z*z + 4*(1-z)*x*x/total) + z) for x in q]

    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if sum(probabilities(mid)) > 1:
            lo = mid
        else:
            hi = mid
    p = probabilities((lo + hi) / 2)
    if abs(sum(p) - 1) > 1e-10 or any(not 0 < x < 1 for x in p):
        raise ValueError("Shin : convergence insuffisante")
    return p


def aware(value):
    if not isinstance(value, str):
        raise ValueError('Horodatage absent')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('Fuseau absent')
    return dt


def analyse(payload: dict, max_age_seconds: int = 1800,
            max_pair_seconds: int = 60) -> dict:
    """Analyse au moment du snapshot, jamais comme cotes actuelles.

    Périmètre initial : marchés football 90min, 1N2 et totaux demi-entiers.
    Exclut les entiers/quarts (push/split) dont le règlement n'est pas modélisé.
    """
    if max_age_seconds < 0 or max_pair_seconds < 0:
        raise ValueError('Tolérances négatives')
    board = payload.get('odds_board', payload)
    at = aware(board['generated_at_utc'])
    rejected = Counter()
    accepted = []
    for event in board.get('events', []):
        identity = (event.get('league'), event.get('event_id'))
        if not all(identity):
            rejected['event_identity_missing'] += 1
            continue
        for book in event.get('bookmakers', []):
            for market in book.get('markets', []):
                if market.get('period_rule') != '90min':
                    rejected['outside_football_90min_scope'] += 1
                    continue
                try:
                    observed = aware(market['quote_at'])
                    start = aware(event['start_utc'])
                    if not observed <= at < start or (at-observed).total_seconds() > max_age_seconds:
                        raise ValueError('Chronologie ou fraîcheur')
                except (ValueError, TypeError, KeyError):
                    rejected['invalid_time'] += 1
                    continue
                try:
                    outcomes = market['outcomes']
                    kind = market['market']
                    labels = ['home', 'draw', 'away'] if kind == 'h2h' else ['over', 'under']
                    if kind not in ('h2h', 'totals') or len(outcomes) != len(labels):
                        raise ValueError('Marché incomplet')
                    by_label = {o['selection']: o for o in outcomes}
                    if set(by_label) != set(labels):
                        raise ValueError('Issues dupliquées ou incohérentes')
                    line = None
                    if kind == 'totals':
                        lines = {float(o['line']) for o in outcomes}
                        if len(lines) != 1:
                            raise ValueError('Lignes différentes')
                        line = lines.pop()
                        if not math.isfinite(line) or line < 0 or line % 1 != .5:
                            raise ValueError('Règlement avec push/split hors périmètre')
                    prices = [float(by_label[k]['price']) for k in labels]
                    methods = comparer_methodes(prices)['probabilites']
                    if sum(1/x for x in prices) < 1-1e-12:
                        raise ValueError('Marge négative à examiner séparément')
                    methods['shin'] = shin(prices)
                    if not isinstance(book.get('bookmaker'), str) or not book['bookmaker']:
                        raise ValueError('Bookmaker absent')
                except (ValueError, TypeError, KeyError, OverflowError):
                    rejected['invalid_or_unsupported_market'] += 1
                    continue
                accepted.append({
                    'league': identity[0], 'event_id': identity[1],
                    'home': event.get('home'), 'away': event.get('away'),
                    'start_utc': event['start_utc'], 'bookmaker': book['bookmaker'],
                    'market': kind, 'line': line, 'period_rule': '90min',
                    'quote_at': market['quote_at'],
                    'quote_time_source': market.get('quote_time_source'),
                    'labels': labels, 'prices': prices, 'probabilities': methods,
                    'max_dispersion_pp': 100 * max(
                        max(p[i] for p in methods.values()) - min(p[i] for p in methods.values())
                        for i in range(len(labels))),
                })
    def key(row):
        return (row['league'], row['event_id'], row['start_utc'], row['market'], row['line'])
    # Une source ambiguë à plusieurs cotations pour un même marché est exclue.
    counts = Counter((key(r), r['bookmaker']) for r in accepted)
    unique = [r for r in accepted if counts[(key(r), r['bookmaker'])] == 1]
    rejected['duplicate_market_rows'] = len(accepted)-len(unique)
    comparisons = []
    for target in unique:
        for reference in unique:
            if key(target) != key(reference) or target['bookmaker'] == reference['bookmaker']:
                continue
            if abs((aware(target['quote_at'])-aware(reference['quote_at'])).total_seconds()) > max_pair_seconds:
                continue
            for i, label in enumerate(target['labels']):
                values = {method: p[i]*target['prices'][i]-1
                          for method,p in reference['probabilities'].items()}
                comparisons.append({
                    'league': target['league'], 'event_id': target['event_id'],
                    'market': target['market'], 'line': target['line'], 'selection': label,
                    'target_bookmaker': target['bookmaker'],
                    'reference_bookmaker': reference['bookmaker'],
                    'price': target['prices'][i], 'hypothetical_ev_by_method': values,
                    'sign_changes': min(values.values()) < 0 < max(values.values()),
                })
    return {
        'experiment': 'market_probability_sensitivity_v1',
        'snapshot_at': at.isoformat(),
        'parameters': {'max_age_seconds': max_age_seconds, 'max_pair_seconds': max_pair_seconds},
        'scope': 'football_90min_h2h_and_half_goal_totals',
        'accepted_markets': len(unique), 'rejected': dict(rejected),
        'methods': ['multiplicative', 'puissance', 'additive_if_valid', 'shin'],
        'markets': sorted(unique,key=lambda r: -r['max_dispersion_pp']),
        'comparisons': comparisons,
        'sign_changes': sum(c['sign_changes'] for c in comparisons),
        'conclusion': 'Sensibilité mathématique seulement : ni probabilités calibrées, ni rentabilité vérifiée.',
    }


def render(report):
    lines = ['# Première expérience — sensibilité des probabilités de marché', '',
             f"Snapshot : {report['snapshot_at']}. Lecture historique, pas de prix live.", '',
             f"**{report['accepted_markets']} marchés retenus**, {len(report['comparisons'])} comparaisons dirigées entre bookmakers et issues ; **{report['sign_changes']} changements de signe** de l’écart théorique selon la méthode.", '',
             'Les comparaisons sont dépendantes et ne sont pas un nombre de paris indépendants.', '',
             f"Empreinte SHA256 de l’entrée : `{report.get('input_sha256', 'non fournie')}`.", '',
             '## Dix marchés les plus sensibles', '',
             '| Rencontre | Bookmaker | Marché / ligne | Écart maximal entre méthodes (points de %) |',
             '|---|---|---|---:|']
    for r in report['markets'][:10]:
        lines.append(f"| {r['home']} – {r['away']} | {r['bookmaker']} | {r['market']} / {r['line']} | {r['max_dispersion_pp']:.3f} |")
    lines += ['', '## Exclusions', '']
    lines += [f'- {reason} : {n}' for reason,n in report['rejected'].items()]
    lines += ['', '## Interprétation', '',
              'Un changement de signe signifie que la même cote paraît supérieure ou inférieure à une référence selon la formule choisie. Cela ne prouve pas quelle formule est correcte. Les autres bookmakers peuvent partager des informations ; leurs probabilités ne sont pas une vérité indépendante.', '',
              'La comparaison porte sur des marchés complets du même match, de la même période et de la même ligne ; une référence ne se compare pas à elle-même. Les lignes entières et les quarts sont exclus. Les règles NHL non vérifiées restent exclues. Additif et Shin sont équivalents pour deux issues : quatre noms ne représentent alors pas quatre avis indépendants.', '',
              'Les observations sont rapprochées à 60 secondes au plus. Un horodatage de collecte ne prouve pas la fraîcheur interne de chaque bookmaker. Aucun résultat de match, aucune commission ni simulation de remplissage ne sont évalués ici ; aucun ROI calculé.', '',
              report['conclusion'], '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    report = analyse(json.loads(raw))
    report['input_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'resultats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (args.output/'RESULTATS.md').write_text(render(report))
    print(json.dumps({k:report[k] for k in ['accepted_markets','rejected','sign_changes']},ensure_ascii=False))


if __name__ == '__main__':
    main()
