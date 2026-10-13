"""Bounded ESPN public game logs, using the existing radar's ESPN athlete IDs.
No odds or inferred missing statistics. Regular season only, previous + current.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE = 'https://site.web.api.espn.com/apis/common/v3/sports/hockey/nhl/athletes'
FIELDS = {'goals': 'goals', 'assists': 'assists', 'points': 'points', 'shots': 'shotsTotal'}


def count(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return int(n) if math.isfinite(n) and n >= 0 and n.is_integer() else None
    except (ValueError, TypeError):
        return None


def parse_log(payload, season, as_of):
    names = payload.get('names') or []
    if not all(name in names for name in FIELDS.values()):
        raise ValueError('Unsupported game log columns')
    events = payload.get('events') or {}
    found = {}
    for group in payload.get('seasonTypes') or []:
        # ESPN returns postseason even when seasontype=2 is requested.
        if group.get('displayName') != f'{season-1}-{str(season)[-2:]} Regular Season':
            continue
        for category in group.get('categories') or []:
            if category.get('type') != 'event':
                continue
            for row in category.get('events') or []:
                eid = str(row.get('eventId') or '')
                event = events.get(eid) or {}
                try:
                    date = datetime.fromisoformat(event['gameDate'].replace('Z', '+00:00'))
                    if date >= as_of or not event.get('gameResult'):
                        continue
                except (KeyError, TypeError, ValueError):
                    continue
                stats = dict(zip(names, row.get('stats') or []))
                values = {key: count(stats.get(column)) for key, column in FIELDS.items()}
                # No participation inferred from an all-missing statistical row.
                if all(value is None for value in values.values()):
                    continue
                found[eid] = {'event_id': eid, 'date': date.isoformat(), 'season': season,
                              'opponent': (event.get('opponent') or {}).get('abbreviation'),
                              'home': {'vs': True, '@': False}.get(event.get('atVs')),
                              **values}
    return sorted(found.values(), key=lambda r: (r['date'], r['event_id']), reverse=True)


def collect(profiles, previous, as_of, max_players=16, fetch=None):
    def network(url):
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=20) as response:
            return json.load(response)
    fetch = fetch or network
    season = int(str(profiles['season'])[-4:])
    ids = {str(p['player_id']) for rows in profiles.get('teams', {}).values() for p in rows}
    cache = {pid: {**value, 'games': [g for g in value.get('games', []) if g.get('season') in (season, season-1)]}
             for pid, value in previous.get('players', {}).items() if pid in ids}
    ordered = sorted(ids, key=lambda pid: (cache.get(pid, {}).get('attempted_at', ''), pid))
    for pid in ordered[:max_players]:
        logs, diagnostics = [], []
        for year in (season, season-1):
            try:
                body = fetch(f'{SOURCE}/{pid}/gamelog?season={year}&seasontype=2')
                logs.extend(parse_log(body, year, as_of))
                diagnostics.append({'season': year, 'status': 'ok'})
            except Exception as error:
                # Do not expose URLs, headers or server response bodies.
                diagnostics.append({'season': year, 'status': 'unavailable', 'error': type(error).__name__})
        cache[pid] = {'attempted_at': as_of.isoformat(), 'games': sorted(logs, key=lambda g: (g['date'], g['event_id']), reverse=True),
                      'diagnostics': diagnostics, 'status': 'ok' if all(d['status'] == 'ok' for d in diagnostics) else 'partial' if logs else 'unavailable'}
    return {'schema_version': 1, 'generated_at_utc': as_of.isoformat(), 'source': 'ESPN public NHL game logs',
            'season_type': 'regular', 'players': cache,
            'coverage': {'requested_players': len(ids), 'players_with_games': sum(bool(p['games']) for p in cache.values())},
            'odds_status': 'unavailable_no_verified_player_market_feed', 'odds': []}


def encode_report(report):
    """Lossless standard JSON: one player per line, stable and diffable."""
    compact = lambda value: json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    fields = []
    for key, value in report.items():
        if key == 'players':
            rows = [f'    {compact(pid)}:{compact(player)}' for pid, player in sorted(value.items())]
            encoded = '{\n' + ',\n'.join(rows) + '\n  }'
        else:
            encoded = compact(value)
        fields.append(f'  {compact(key)}:{encoded}')
    return '{\n' + ',\n'.join(fields) + '\n}\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profiles', default='docs/nhl-players-latest.json')
    parser.add_argument('--output', default='docs/nhl-player-history.json')
    parser.add_argument('--max-players', type=int, default=16)
    args = parser.parse_args()
    path = Path(args.output)
    old = json.loads(path.read_text()) if path.exists() else {}
    report = collect(json.loads(Path(args.profiles).read_text()), old, datetime.now(timezone.utc), args.max_players)
    path.write_text(encode_report(report), encoding='utf-8')
    print(json.dumps(report['coverage']))


if __name__ == '__main__':
    main()
