"""Economic/temporal invariants for the independent robust paper strategy."""
import copy
from datetime import timedelta
import unittest
from tests.test_revue_engine_v2 import NOW,AT,START,iso,models,quotes
from outils.suivi.value_robuste import scan,update,RULE,RULE_HASH
from outils.collecte.pulsescore_v2 import translate_event
from tests.test_pulsescore_v2 import event


def report():return {'value_scan':scan(models(),{'PL':[quotes()]},NOW)}


class RobustStrategyTests(unittest.TestCase):
    def test_candidate_has_complete_evidence_and_conservative_edge(self):
        r=report()['value_scan'];self.assertTrue(r['candidates'])
        c=r['candidates'][0];self.assertEqual(c['side'],'home')
        self.assertGreaterEqual(c['edge_min'],RULE['min_edge'])
        self.assertGreaterEqual(c['bookmaker_price'],c['minimum_required_price'])
        p=c['reference_evidence'][0]['probabilities']
        self.assertEqual(set(p),set(RULE['methods']))
        self.assertAlmostEqual(c['p_min'],min(v[0] for v in p.values()))

    def test_edge_passing_only_some_methods_not_promoted(self):
        e=quotes();e['bookmakers'][0]['markets'][0]['outcomes'][0]['price']=2.765
        for o,p in zip(e['bookmakers'][1]['markets'][0]['outcomes'],[2.6,4.3,2.4]):o['price']=p
        r=scan(models(),{'PL':[e]},NOW)
        home=[c for c in r['candidates'] if c['market']=='h2h' and c['side']=='home']
        self.assertEqual(home,[])
        c=next(c for c in r['watchlist'] if c['side']=='home')
        self.assertLess(c['edge_min'],.03)
        self.assertGreater(c['edge_max'],.03)

    def test_fallback_is_market_specific_and_stale_reference_rejected(self):
        e=quotes();second=copy.deepcopy(e['bookmakers'][1]);second['key']='ps3838'
        e['bookmakers'][1]['last_update']=iso(NOW-timedelta(hours=2));e['bookmakers'].append(second)
        c=scan(models(),{'PL':[e]},NOW)['candidates'][0]
        self.assertEqual(c['reference_evidence'][0]['bookmaker'],'ps3838')
        second['last_update']=iso(NOW-timedelta(minutes=6))
        self.assertEqual(scan(models(),{'PL':[e]},NOW)['candidates'],[])

    def test_conflicting_reference_uses_worst_probability(self):
        e=quotes();other=copy.deepcopy(e['bookmakers'][1]);other['key']='ps3838'
        for o in other['markets'][0]['outcomes']:o['price']=3.
        e['bookmakers'].append(other)
        self.assertEqual(scan(models(),{'PL':[e]},NOW)['candidates'],[])

    def test_quote_skew_and_unsupported_market(self):
        e=quotes();e['bookmakers'][1]['last_update']=iso(NOW-timedelta(minutes=2))
        self.assertEqual(scan(models(),{'PL':[e]},NOW)['candidates'],[])
        e=quotes();e['bookmakers'][1]['markets'][0]['period']='FIRST_HALF'
        self.assertEqual(scan(models(),{'PL':[e]},NOW)['candidates'],[])
        e=quotes();e['bookmakers'][1]['markets'][0]['outcomes'].pop()
        self.assertEqual(scan(models(),{'PL':[e]},NOW)['candidates'],[])

    def test_same_event_not_locked_twice_and_inputs_immutable(self):
        src=report();ledger={'bets':[]};before=copy.deepcopy(src)
        out,new=update(src,ledger,{},NOW)
        self.assertEqual(src,before);self.assertEqual(ledger,{'bets':[]})
        self.assertEqual(len(new['bets']),1)
        _,again=update(src,new,{},NOW+timedelta(seconds=10))
        self.assertEqual(len(again['bets']),1)
        self.assertIsNone(out['performance']['roi_pct'])

    def test_no_historical_or_stale_lock(self):
        src=report()
        _,ledger=update(src,{'bets':[]},{},NOW+timedelta(minutes=6))
        self.assertEqual(ledger['bets'],[])
        src['value_scan']['generated_at_utc']=iso(NOW+timedelta(seconds=1))
        self.assertEqual(update(src,{'bets':[]},{},NOW)[1]['bets'],[])

    def test_draw_grades_home_as_loss_and_win_pnl_uses_stake(self):
        _,ledger=update(report(),{'bets':[]},{},NOW)
        result={'leagues':{'PL':{'events':[{'id':'101','complete':True,'home_score':1,'away_score':1}]}}}
        out,after=update({},ledger,result,START+timedelta(hours=3))
        self.assertEqual(after['bets'][0]['status'],'lost')
        self.assertEqual(out['performance']['profit_units'],-1)
        self.assertEqual(out['performance']['roi_pct'],-100)
        result['leagues']['PL']['events'][0]['home_score']=2
        out,after=update({},ledger,result,START+timedelta(hours=3))
        self.assertAlmostEqual(out['performance']['profit_units'],.85)
        self.assertEqual(after['bets'][0]['status'],'won')

    def test_pending_no_score_or_before_start_and_settlement_immutable(self):
        _,ledger=update(report(),{'bets':[]},{},NOW)
        out,after=update({},ledger,{},START+timedelta(hours=3))
        self.assertEqual(out['performance']['pending'],1)
        result={'leagues':{'PL':{'events':[{'id':'101','complete':True,'home_score':2,'away_score':1}]}}}
        self.assertEqual(update({},ledger,result,NOW)[1]['bets'][0]['status'],'pending')
        _,after=update({},ledger,result,START+timedelta(hours=3))
        result['leagues']['PL']['events'][0]['home_score']=0
        self.assertEqual(update({},after,result,START+timedelta(hours=4))[1]['bets'][0]['status'],'won')

    def test_rule_change_requires_new_ledger(self):
        with self.assertRaises(ValueError):update({}, {'rule_hash':'other','bets':[]},{},NOW)

    def test_exposure_limit(self):
        _,ledger=update(report(),{'bets':[]},{},NOW)
        originals=ledger['bets'][0]
        ledger['bets']=[{**originals,'id':str(i),'event_id':str(i+200)} for i in range(5)]
        _,after=update(report(),ledger,{},NOW)
        self.assertEqual(len(after['bets']),5)


class ExchangeEvidenceTests(unittest.TestCase):
    def test_missing_empty_nan_and_mismatched_back_rejected(self):
        for mode in ['missing','empty','nan','mismatch','thin']:
            raw=event()
            for m in raw['markets']:
                for s in m['selections']:
                    if mode=='empty':s['back']=[]
                    if mode in ['nan','mismatch','thin']:
                        s['back']=[{'price':1.01 if mode=='mismatch' else s['odds'],
                                    'liquidity':float('nan') if mode=='nan' else 5 if mode=='thin' else 250}]
            with self.subTest(mode=mode):self.assertIsNone(translate_event(raw,'orbit_exchange',NOW))

    def test_valid_exchange_and_normal_sportsbook(self):
        raw=event();self.assertIsNotNone(translate_event(raw,'betclic_fr',NOW))
        for m in raw['markets']:
            for s in m['selections']:s['back']=[{'price':s['odds'],'liquidity':250}]
        self.assertIsNotNone(translate_event(raw,'orbit_exchange',NOW))


if __name__=='__main__':unittest.main()
