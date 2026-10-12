import copy
import unittest

from experiences.probabilites_marche.comparer import analyse, shin


def sample():
    def market(prices):
        return {'market':'h2h','period_rule':'90min','quote_at':'2026-10-12T10:00:00Z',
                'outcomes':[{'selection':k,'price':v} for k,v in zip(['home','draw','away'],prices)]}
    return {'generated_at_utc':'2026-10-12T10:00:00Z','events':[
        {'league':'PL','event_id':'1','home':'A','away':'B','start_utc':'2026-10-12T12:00:00Z',
         'bookmakers':[{'bookmaker':'a','markets':[market([2.6,2.4,4.3])]},
                       {'bookmaker':'b','markets':[market([2.7,2.35,4.2])]}]}]}


class MethodsTests(unittest.TestCase):
    def test_published_shin_example(self):
        p=shin([2.6,2.4,4.3])
        for a,b in zip(p,[.37299406033208965,.4047794109200184,.2222265287474275]):
            self.assertAlmostEqual(a,b,places=10)
        self.assertAlmostEqual(sum(p),1,places=12)

    def test_two_outcomes_and_no_margin(self):
        self.assertEqual(shin([2.,2.]),[.5,.5])
        p=shin([1.5,2.74]);expected=1/1.5-((1/1.5+1/2.74)-1)/2
        self.assertAlmostEqual(p[0],expected,places=12)

    def test_invalid_and_underround(self):
        for values in ([1,2],[float('nan'),2],[float('inf'),2],[3,3],[2],[2,3,4,5]):
            with self.subTest(values=values),self.assertRaises(ValueError):shin(values)

    def test_permutation(self):
        self.assertAlmostEqual(shin([4.3,2.6,2.4])[0],shin([2.6,2.4,4.3])[2],places=12)


class ContractTests(unittest.TestCase):
    def test_complete_market_no_self_reference_and_input_unchanged(self):
        src=sample();before=copy.deepcopy(src);r=analyse(src)
        self.assertEqual(r['accepted_markets'],2)
        self.assertEqual(len(r['comparisons']),6)
        self.assertEqual(src,before)
        self.assertTrue(all(x['target_bookmaker']!=x['reference_bookmaker'] for x in r['comparisons']))

    def test_missing_timezone_postmatch_and_stale_quotes(self):
        for value in ('2026-10-12T10:00:00','2026-10-12T12:01:00Z','2026-10-12T08:00:00Z'):
            src=sample();src['events'][0]['bookmakers'][0]['markets'][0]['quote_at']=value
            with self.subTest(value=value):self.assertEqual(analyse(src)['rejected']['invalid_time'],1)
        src=sample();src['events'][0]['start_utc']='2026-10-12T09:59:00Z'
        self.assertEqual(analyse(src)['accepted_markets'],0)

    def test_missing_draw_and_duplicates(self):
        src=sample();books=src['events'][0]['bookmakers'];books[0]['markets'][0]['outcomes'].pop()
        self.assertEqual(analyse(src)['accepted_markets'],1)
        src=sample();src['events'][0]['bookmakers'].append(copy.deepcopy(src['events'][0]['bookmakers'][0]))
        r=analyse(src);self.assertEqual(r['accepted_markets'],1);self.assertEqual(r['comparisons'],[])

    def test_different_lines_never_compared_and_push_rejected(self):
        src=sample()
        for book,line in zip(src['events'][0]['bookmakers'],[2.5,3.5]):
            m=book['markets'][0];m['market']='totals';m['outcomes']=[
                {'selection':k,'line':line,'price':1.9} for k in ['over','under']]
        self.assertEqual(analyse(src)['comparisons'],[])
        src['events'][0]['bookmakers'][0]['markets'][0]['outcomes'][0]['line']=3.5
        self.assertEqual(analyse(src)['accepted_markets'],1)
        for outcome in src['events'][0]['bookmakers'][1]['markets'][0]['outcomes']:outcome['line']=3
        self.assertEqual(analyse(src)['accepted_markets'],0)

    def test_nhl_unverified_and_asynchronous_quotes_excluded(self):
        src=sample();src['events'][0]['bookmakers'][0]['markets'][0]['period_rule']='overtime_rule_unverified'
        self.assertEqual(analyse(src)['accepted_markets'],1)
        src=sample();src['events'][0]['bookmakers'][0]['markets'][0]['quote_at']='2026-10-12T09:58:00Z'
        self.assertEqual(analyse(src)['comparisons'],[])


if __name__=='__main__':unittest.main()
