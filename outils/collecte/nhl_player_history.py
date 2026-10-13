"""Bounded ESPN public game logs, using the existing radar's ESPN athlete IDs.
No odds or inferred missing statistics. Regular seasons, bounded older-season fallback.
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


def unique_games(games):
    """A player appearance is counted only once across cache and responses."""
    found = {str(g['event_id']): g for g in games if g.get('event_id')}
    return sorted(found.values(), key=lambda g: (g['date'], str(g['event_id'])), reverse=True)


def coverage(players, requested):
    counts = {metric: sum(sum(count(g.get(metric)) is not None for g in unique_games(p.get('games', []))) >= 20
                         for p in players.values()) for metric in FIELDS}
    complete = sum(sum(all(count(g.get(m)) is not None for m in FIELDS) for g in unique_games(p.get('games', []))) >= 20
                   for p in players.values())
    return {'requested_players': requested, 'players_with_games': sum(bool(p.get('games')) for p in players.values()),
            'observations': sum(len(unique_games(p.get('games', []))) for p in players.values()),
            'players_with_20_complete_observations': complete,
            'proportion_with_20_complete_observations': complete / requested if requested else None,
            'players_with_20_by_metric': counts}


def collect(profiles, previous, as_of, max_players=256, fetch=None):
    def network(url):
        with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=20) as response:
            return json.load(response)
    fetch = fetch or network
    season = int(str(profiles['season'])[-4:])
    ids = {str(p['player_id']) for rows in profiles.get('teams', {}).values() for p in rows}
    cache = {}
    for pid, value in previous.get('players', {}).items():
        if pid not in ids:
            continue
        # Retain bounded older seasons used to complete a recent 20-game sample.
        games = [g for g in value.get('games', []) if g.get('season') in range(season-3, season+1)]
        stamps = dict(value.get('season_collected_at') or {})
        for diag in value.get('diagnostics', []):
            if diag.get('status') == 'ok' and value.get('attempted_at'):
                stamps.setdefault(str(diag['season']), value['attempted_at'])
        cache[pid] = {**value, 'games': unique_games(games), 'season_collected_at': stamps}
    ordered = sorted(ids, key=lambda pid: (cache.get(pid, {}).get('attempted_at', ''), pid))
    requests = 0
    for pid in ordered[:max_players]:
        old = cache.get(pid, {})
        logs = list(old.get('games', []))
        stamps = dict(old.get('season_collected_at', {}))
        diagnostics = []
        # Current + previous season, then at most two older seasons when needed.
        for year in range(season, season-4, -1):
            if year < season-1 and sum(all(count(g.get(m)) is not None for m in FIELDS) for g in unique_games(logs)) >= 20:
                break
            stamp = stamps.get(str(year))
            try:
                age = (as_of-datetime.fromisoformat(stamp.replace('Z', '+00:00'))).total_seconds() if stamp else None
            except (ValueError, TypeError):
                age = None
            if year < season and age is not None and 0 <= age < 7*86400:
                diagnostics.append({'season': year, 'status': 'ok', 'cached': True})
                continue
            requests += 1
            try:
                body = fetch(f'{SOURCE}/{pid}/gamelog?season={year}&seasontype=2')
                observed = parse_log(body, year, as_of)
                # A short response must not erase previously observed appearances.
                logs = unique_games(logs + observed)
                stamps[str(year)] = as_of.isoformat()
                diagnostics.append({'season': year, 'status': 'ok', 'observations': len(observed)})
            except Exception as error:
                diagnostic = {'season': year, 'status': 'unavailable', 'error': type(error).__name__}
                if getattr(error, 'code', None) in (403, 404, 429):
                    diagnostic['http_status'] = error.code
                diagnostics.append(diagnostic)
                # Respect denied/rate-limited access; do not try older URLs for that player.
                if getattr(error, 'code', None) in (403, 429):
                    break
        cache[pid] = {'attempted_at': as_of.isoformat(), 'games': unique_games(logs),
                      'season_collected_at': stamps, 'diagnostics': diagnostics,
                      'status': 'ok' if all(d['status'] == 'ok' for d in diagnostics) else 'partial' if logs else 'unavailable'}
    return {'schema_version': 2, 'generated_at_utc': as_of.isoformat(), 'source': 'ESPN public NHL game logs',
            'season_type': 'regular', 'players': cache, 'requests_made': requests,
            'players_attempted': min(max_players, len(ids)),
            'coverage': coverage(cache, len(ids)),
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
    parser.add_argument('--max-players', type=int, default=256)
    args = parser.parse_args()
    path = Path(args.output)
    old = json.loads(path.read_text()) if path.exists() else {}
    report = collect(json.loads(Path(args.profiles).read_text()), old, datetime.now(timezone.utc), args.max_players)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(encode_report(report), encoding='utf-8')
    temporary.replace(path)
    print(json.dumps({**report['coverage'], 'players_attempted': report['players_attempted'], 'requests_made': report['requests_made']}))


if __name__ == '__main__':
    main()
