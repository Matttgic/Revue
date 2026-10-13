import unittest
from datetime import datetime, timezone
from outils.collecte.nhl_player_history import parse_log, collect, count, encode_report, coverage

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
        self.assertEqual(len(urls), 4)  # bounded fallback across four regular seasons
        self.assertEqual(len(report['players']), 1)
        self.assertEqual(report['players']['1']['status'], 'partial')
        self.assertNotIn('sensitive', str(report))
        self.assertEqual(report['odds'], [])
        # Oldest or unrequested players are attempted first on the next run.
        updated = collect(profiles, report, NOW, max_players=1, fetch=fetch)
        self.assertIn('2', updated['players'])

    def test_rollover_retains_bounded_older_seasons_only(self):
        profiles = {'season': 20262027, 'teams': {'ANA': [{'player_id': '1'}]}}
        previous = {'players': {'1': {'attempted_at': NOW.isoformat(), 'games': [
            {'event_id': str(y), 'date': f'{y}-01-01T00:00:00Z', 'season': y} for y in range(2023,2028)]}}}
        report = collect(profiles, previous, NOW, max_players=0)
        self.assertEqual([g['season'] for g in report['players']['1']['games']], [2027,2026,2025,2024])

    def test_storage_is_lossless_standard_json_and_stable(self):
        import json
        report = {'source': 'Données NHL', 'players': {'2': {'games': [{'shots': 0, 'home': False, 'opponent': None}]}, '1': {'games': []}}, 'odds': []}
        encoded = encode_report(report)
        self.assertEqual(json.loads(encoded), report)
        self.assertEqual(encode_report(json.loads(encoded)), encoded)
        self.assertLess(len(encoded.splitlines()), 12)
        with self.assertRaises(ValueError):
            encode_report({'players': {}, 'bad': float('nan')})

    def test_failure_retains_observations_without_refreshing_success_timestamp(self):
        old_date = '2026-10-12T00:00:00+00:00'
        game = {'event_id':'old', 'date':'2026-10-01T00:00:00Z', 'season':2027, 'shots':3, 'goals':0, 'assists':0, 'points':0}
        old = {'players': {'1': {'games':[game], 'season_collected_at': {'2027':old_date}, 'attempted_at':old_date}}}
        def fail(url):
            raise TimeoutError('Do not publish exception contents')
        result = collect({'season':20262027,'teams':{'ANA':[{'player_id':'1'}]}},old,NOW,fetch=fail)
        player = result['players']['1']
        self.assertEqual(player['games'],[game])
        self.assertEqual(player['season_collected_at']['2027'],old_date)
        self.assertEqual(player['status'],'partial')

    def test_cached_archives_skip_requests_and_duplicates_do_not_inflate_coverage(self):
        rows = [{'event_id':str(i), 'date':f'2026-01-{i+1:02d}T00:00:00Z', 'season':2026,
                 'shots':1,'goals':0,'assists':0,'points':0} for i in range(20)]
        old = {'players': {'1': {'games':rows+[rows[0]], 'season_collected_at':{'2026':NOW.isoformat()}}}}
        urls=[]
        def fetch(url):
            urls.append(url)
            return fixture()
        report=collect({'season':20262027,'teams':{'ANA':[{'player_id':'1'}]}},old,NOW,fetch=fetch)
        self.assertEqual(len(urls),1)
        self.assertEqual(report['coverage']['observations'],20)
        self.assertEqual(report['coverage']['players_with_20_complete_observations'],1)
        self.assertTrue(report['players']['1']['diagnostics'][1]['cached'])
        report['players']['1']['games'][0]['shots']=None
        self.assertEqual(coverage(report['players'],1)['players_with_20_complete_observations'],0)

    def test_denied_source_stops_fallback_without_discarding_cache(self):
        from urllib.error import HTTPError
        urls=[]
        def denied(url):
            urls.append(url)
            raise HTTPError(url,403,'Denied',{},None)
        report=collect({'season':20262027,'teams':{'ANA':[{'player_id':'1'}]}},{},NOW,fetch=denied)
        self.assertEqual(len(urls),1)
        self.assertEqual(report['players']['1']['status'],'unavailable')
        self.assertEqual(report['players']['1']['diagnostics'][0]['http_status'],403)

    def test_bounded_older_season_fallback_reaches_twenty_real_rows(self):
        import re
        requested=[]
        def fetch(url):
            year=int(re.search(r'season=(\d+)',url).group(1))
            requested.append(year)
            data=fixture()
            data['seasonTypes']=[]
            data['events']={}
            n={2027:4,2026:0,2025:20}.get(year,0)
            rows=[]
            for i in range(n):
                eid=f'{year}-{i}'
                rows.append({'eventId':eid,'stats':['0','0','0','2']})
                data['events'][eid]={'gameDate':f'{year-1}-10-{i+1:02d}T00:00:00Z','gameResult':'W','atVs':'vs','opponent':{'abbreviation':'ANA'}}
            data['seasonTypes']=[{'displayName':f'{year-1}-{str(year)[-2:]} Regular Season', 'categories':[{'type':'event','events':rows}]}]
            return data
        result=collect({'season':20262027,'teams':{'ANA':[{'player_id':'1'}]}},{},NOW,fetch=fetch)
        self.assertEqual(requested,[2027,2026,2025])
        self.assertEqual(len(result['players']['1']['games']),24)
        self.assertEqual(result['coverage']['players_with_20_complete_observations'],1)

    def test_automatic_job_refreshes_full_radar_and_never_publishes_branch_to_main(self):
        from pathlib import Path
        import yaml
        root=Path(__file__).resolve().parents[1]
        workflow=yaml.safe_load((root/'.github/workflows/multisports-independent.yml').read_text())
        steps=workflow['jobs']['multisports']['steps']
        publishing=[s for s in steps if 'git push origin HEAD:main' in s.get('run','')]
        import inspect
        self.assertGreaterEqual(inspect.signature(collect).parameters['max_players'].default,256)
        self.assertTrue(any(s.get('run')=='python -m outils.collecte.nhl_player_history' for s in steps))
        self.assertEqual(len(publishing),1)
        self.assertEqual(publishing[0]['if'],"github.ref == 'refs/heads/main'")
        artifacts=[s for s in steps if s.get('uses')=='actions/upload-artifact@v4']
        self.assertEqual(artifacts[0]['if'],"github.ref != 'refs/heads/main'")
        self.assertEqual(artifacts[0]['with']['path'],'docs/nhl-player-history.json')
