import unittest
from datetime import datetime, timezone
from outils.collecte.nhl_player_history import parse_log, collect, count

NOW = datetime(2026, 10, 13, tzinfo=timezone.utc)


def fixture():
    # Synthetic schema fixture, not published observations.
    event = {'gameDate': '2026-01-01T00:00:00Z', 'gameResult': 'W', 'atVs': '@', 'opponent': {'abbreviation': 'BOS'}}
    row = {'eventId': '1', 'stats': ['1', '0', '1', '3']}
    return {'names': ['goals', 'assists', 'points', 'shotsTotal'], 'events': {'1': event},
            'seasonTypes': [{'displayName': '2025-26 Regular Season', 'categories': [{'type': 'event', 'events': [row, row]}]},
                            {'displayName': '2025-26 Postseason', 'categories': [{'type': 'event', 'events': [{'eventId': '2', 'stats': ['9']*4}]}]}]}


class HistoryTests(unittest.TestCase):
    def test_named_stats_regular_only_deduplicated(self):
        result = parse_log(fixture(), 2026, NOW)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['shots'], 3)
        self.assertFalse(result[0]['home'])
        self.assertEqual(result[0]['assists'], 0)

    def test_missing_values_venue_and_opponent_not_invented(self):
        data = fixture()
        data['seasonTypes'][0]['categories'][0]['events'][0]['stats'] = ['-', '0', None, '']
        data['events']['1'].pop('atVs')
        data['events']['1'].pop('opponent')
        row = parse_log(data, 2026, NOW)[0]
        self.assertIsNone(row['goals'])
        self.assertIsNone(row['shots'])
        self.assertIsNone(row['home'])
        self.assertIsNone(row['opponent'])

    def test_future_and_unfinished_games_excluded(self):
        data = fixture()
        data['events']['1']['gameDate'] = '2027-01-01T00:00:00Z'
        self.assertEqual(parse_log(data, 2026, NOW), [])
        data['events']['1']['gameDate'] = '2026-01-01T00:00:00Z'
        data['events']['1'].pop('gameResult')
        self.assertEqual(parse_log(data, 2026, NOW), [])

    def test_unknown_schema_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_log({'names': []}, 2026, NOW)
        for bad in (None, '', '-', 'nan', -1, 2.5, 'inf', True):
            self.assertIsNone(count(bad))

    def test_bounded_fetch_partial_failure_no_secret_leak(self):
        urls = []
        def fetch(url):
            urls.append(url)
            if 'season=2027' in url:
                raise RuntimeError('sensitive body must not appear')
            return fixture()
        profiles = {'season': 20262027, 'teams': {'ANA': [{'player_id': '1'}, {'player_id': '2'}]}}
        report = collect(profiles, {}, NOW, max_players=1, fetch=fetch)
        self.assertEqual(len(urls), 2)
        self.assertEqual(len(report['players']), 1)
        self.assertEqual(report['players']['1']['status'], 'partial')
        self.assertNotIn('sensitive', str(report))
        self.assertEqual(report['odds'], [])
        # Oldest or unrequested players are attempted first on the next run.
        updated = collect(profiles, report, NOW, max_players=1, fetch=fetch)
        self.assertIn('2', updated['players'])

    def test_rollover_discards_older_season_cache(self):
        profiles = {'season': 20262027, 'teams': {'ANA': [{'player_id': '1'}]}}
        previous = {'players': {'1': {'attempted_at': NOW.isoformat(), 'games': [
            {'season': 2025}, {'season': 2026}, {'season': 2027}]}}}
        report = collect(profiles, previous, NOW, max_players=0)
        self.assertEqual([g['season'] for g in report['players']['1']['games']], [2026, 2027])
