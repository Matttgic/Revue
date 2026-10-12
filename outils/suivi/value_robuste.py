"""Stratégie prospective originale : prix français contre référence sharp.

Les seuils sont figés par version. Aucun compte ni ordre bookmaker.
Une sélection exige une EV hypothétique >= 3% sous toutes les méthodes.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path

from experiences.probabilites_marche.comparer import shin
from outils.controles.sensibilite_devig import comparer_methodes

RULE = {
    'id': 'football_robust_sharp_v1', 'adopted_on': '2026-10-12',
    'leagues': ['PL','LALIGA','SERIEA','BUNDESLIGA','LIGUE1'],
    'reference_books': ['pinnacle','ps3838'],
    'methods': ['multiplicative','additive','puissance','shin'],
    'min_edge': .03, 'min_odds': 1.30, 'max_odds': 3.50,
    'max_quote_age_seconds': 300, 'max_pair_seconds': 60,
    'kickoff_buffer_seconds': 1200, 'max_reference_margin': .08,
    'paper_stake_units': 1., 'max_open_bets': 5, 'max_daily_bets': 5,
    'min_settled_for_assessment': 300,
}
RULE_HASH = hashlib.sha256(json.dumps(RULE,sort_keys=True).encode()).hexdigest()


def scan(models: dict, odds: dict, now: datetime) -> dict:
    from outils.suivi.revue_engine_v2 import timestamp, match_fixture, FR_BOOKS
    from outils.controles.consensus_quotations import outcome_key
    reasons=Counter(); candidates=[]; watch=[]; quotes=[]
    if now.tzinfo is None:raise ValueError('UTC timestamp required')
    for league in RULE['leagues']:
        games=[{**g,'_league':league} for g in models.get('competitions',{}).get(league,{}).get('games',[])]
        for event in odds.get(league,[]):
            game=match_fixture(event,games,league)
            if not game:
                reasons['unmatched_event']+=1;continue
            start=timestamp(game.get('start_utc'))
            if not start or (start-now).total_seconds()<=RULE['kickoff_buffer_seconds']:
                reasons['started_or_too_close']+=1;continue
            rows=[]
            for book in event.get('bookmakers',[]):
                ident=book.get('key')
                if ident not in FR_BOOKS and ident not in RULE['reference_books']:continue
                for market in book.get('markets',[]):
                    kind=market.get('key')
                    if kind not in ('h2h','totals'):continue
                    raw=str(market.get('raw_market_name') or '').lower()
                    period=str(market.get('period') or '').upper()
                    if period not in ('','FULL_TIME','MATCH','GAME') or any(
                        word in raw for word in ('extra time','including overtime','penalty shoot','half','quarter','corner','card','player','team total')):
                        reasons['wrong_period_or_market']+=1;continue
                    at=timestamp(market.get('last_update') or book.get('last_update'))
                    if not at or not 0<=(now-at).total_seconds()<=RULE['max_quote_age_seconds']:
                        reasons['stale_quote']+=1;continue
                    buckets={}; malformed=False
                    for outcome in market.get('outcomes',[]):
                        key=outcome_key(outcome,kind,game)
                        try:price=float(outcome['price'])
                        except (ValueError,TypeError,KeyError):malformed=True;break
                        if not key or key in buckets or not math.isfinite(price) or price<=1:
                            malformed=True;break
                        buckets[key]=price
                    if kind=='h2h':
                        valid=set(buckets)=={'home','draw','away'}; line=None
                        keys=['home','draw','away']
                    else:
                        line_keys={key.split('@')[1] for key in buckets if '@' in key}
                        line=float(next(iter(line_keys))) if len(line_keys)==1 else None
                        valid=(line is not None and line>=0 and line%1==.5 and
                               set(buckets)=={f'over@{line}',f'under@{line}'})
                        keys=[f'over@{line}',f'under@{line}']
                    if malformed or not valid:
                        reasons['incomplete_or_unsupported_market']+=1;continue
                    prices=[buckets[k] for k in keys]
                    rows.append({'bookmaker':ident,'market':kind,'line':line,'keys':keys,
                                 'prices':prices,'quote_at':at.isoformat(),
                                 'quote_time_source':market.get('observed_origin') or 'provider_last_update'})
            def key(r):return (r['bookmaker'],r['market'],r['line'])
            counts=Counter(key(r) for r in rows)
            rows=[r for r in rows if counts[key(r)]==1]
            for row in rows:
                for i,label in enumerate(row['keys']):
                    quotes.append({'league':league,'event_id':str(game['event_id']),
                                   'market':row['market'],'line':row['line'],'side':label.split('@')[0],
                                   'bookmaker':row['bookmaker'],'price':row['prices'][i],
                                   'quote_at':row['quote_at']})
                if row['bookmaker'] not in FR_BOOKS:continue
                references=[]
                for ref in rows:
                    if ref['bookmaker'] not in RULE['reference_books'] or ref['market']!=row['market'] or ref['line']!=row['line']:continue
                    if abs((timestamp(ref['quote_at'])-timestamp(row['quote_at'])).total_seconds())>RULE['max_pair_seconds']:continue
                    margin=sum(1/p for p in ref['prices'])-1
                    if not -1e-12<=margin<=RULE['max_reference_margin']:continue
                    try:
                        methods=comparer_methodes(ref['prices'])['probabilites']
                        methods['shin']=shin(ref['prices'])
                        if set(methods)!=set(RULE['methods']):continue
                    except ValueError:continue
                    references.append((ref,methods))
                if not references:
                    reasons['no_complete_fresh_sharp_reference']+=1;continue
                for i,label in enumerate(row['keys']):
                    price=row['prices'][i]
                    if not RULE['min_odds']<=price<=RULE['max_odds']:continue
                    # Minimum over ALL valid references and methods, rather
                    # than selecting whichever reference makes a price pass.
                    estimates={ref['bookmaker']:{method:p[i] for method,p in methods.items()}
                               for ref,methods in references}
                    low=min(p for ref in estimates.values() for p in ref.values())
                    high=max(p for ref in estimates.values() for p in ref.values())
                    edge=price*low-1;required=(1+RULE['min_edge'])/low
                    record={'selection_rule':RULE['id'],'rule_hash':RULE_HASH,
                        'selection_id':f"{league}|{game['event_id']}|{row['market']}|{label}|{row['bookmaker']}",
                        'league':league,'event_id':str(game['event_id']),
                        'home':game['home'],'away':game['away'],'start_utc':start.isoformat(),
                        'market':row['market'],'side':label.split('@')[0],'line':row['line'],
                        'bookmaker':row['bookmaker'],'bookmaker_price':price,
                        'quote_at':row['quote_at'],'quote_time_source':row['quote_time_source'],
                        'reference_evidence':[{**ref,'probabilities':methods} for ref,methods in references],
                        'p_min':low,'p_max':high,'edge_min':edge,'edge_max':price*high-1,
                        'minimum_required_price':required,'observed_at':now.isoformat(),
                        'market_rule_verified':True,'paper_stake_units':RULE['paper_stake_units']}
                    if edge>=RULE['min_edge']:candidates.append(record)
                    else:watch.append(record);reasons['below_robust_threshold']+=1
    order=lambda c:(-c['edge_min'],c['start_utc'],c['selection_id'])
    return {'generated_at_utc':now.isoformat(),'rule':RULE,'rule_hash':RULE_HASH,
            'candidates':sorted(candidates,key=order),'watchlist':sorted(watch,key=order)[:12],
            'diagnostics':dict(reasons),'quotes':quotes}


def update(report: dict, ledger: dict, history: dict, now: datetime) -> tuple[dict,dict]:
    from outils.suivi.revue_engine_v2 import timestamp
    from outils.suivi.regle_decision import mean_ci
    ledger=deepcopy(ledger)
    if ledger.get('rule_hash',RULE_HASH)!=RULE_HASH:raise ValueError('Rule changed: create a new strategy ledger')
    ledger.update(rule=RULE,rule_hash=RULE_HASH)
    bets=ledger.setdefault('bets',[]); excluded=[]
    # No result can finance another lock: flat unit stake, open exposure cap.
    results={lg:{str(e['id']):e for e in data.get('events',[]) if e.get('complete')}
             for lg,data in history.get('leagues',{}).items()}
    for bet in bets:
        start=timestamp(bet.get('start_utc'));lock=timestamp(bet.get('locked_at'))
        if (bet.get('rule_hash')!=RULE_HASH or not start or not lock or lock>=start):
            excluded.append(bet.get('id'));continue
        if bet.get('status')!='pending' or start>=now:continue
        result=results.get(bet['league'],{}).get(bet['event_id'])
        if not result:continue
        try:
            h,a=float(result['home_score']),float(result['away_score'])
            if not all(math.isfinite(x) and x>=0 and x.is_integer() for x in (h,a)):continue
        except (ValueError,KeyError,TypeError):continue
        if bet['market']=='h2h':
            winner='home' if h>a else 'away' if a>h else 'draw'
            outcome='won' if bet['side']==winner else 'lost'
        else:
            total=h+a;line=bet['line']
            outcome='push' if total==line else 'won' if (
                total>line if bet['side']=='over' else total<line) else 'lost'
        bet.update(status=outcome,score={'home':h,'away':a},settled_at=now.isoformat(),
                   profit_units=bet['paper_stake_units']*(bet['bookmaker_price']-1) if outcome=='won' else
                   -bet['paper_stake_units'] if outcome=='lost' else 0.)
    source=report.get('value_scan');stamp=timestamp(source.get('generated_at_utc')) if source else None
    fresh=bool(stamp and 0<=(now-stamp).total_seconds()<=RULE['max_quote_age_seconds'])
    if source and source.get('provider_status') not in (None,'active_pulsescore','active_the_odds_api'):
        fresh=False
    candidates=source.get('candidates',[]) if fresh else []
    if source and source.get('rule_hash')!=RULE_HASH:raise ValueError('Scan rule mismatch')
    if fresh:
        for bet in bets:
            if bet.get('status')!='pending':continue
            start=timestamp(bet['start_utc']);lock=timestamp(bet['locked_at'])
            if not lock<=now<start:continue
            for q in source.get('quotes',[]):
                if all(q.get(k)==bet.get(k) for k in ('league','event_id','market','line','side','bookmaker')):
                    at=timestamp(q.get('quote_at'))
                    if at and lock<at<start and 0<=(now-at).total_seconds()<=RULE['max_quote_age_seconds']:
                        bet['last_observed_quote']={'price':q['price'],'quote_at':q['quote_at']}
    seen={(b.get('league'),b.get('event_id')) for b in bets}
    today=now.astimezone(timezone.utc).date()
    daily=sum(timestamp(b['locked_at']).date()==today for b in bets if timestamp(b.get('locked_at')))
    opened=sum(b.get('status')=='pending' for b in bets)
    for candidate in candidates:
        start=timestamp(candidate.get('start_utc'));quote=timestamp(candidate.get('quote_at'))
        ident=(candidate.get('league'),candidate.get('event_id'))
        if not start or not quote or not quote<=stamp<=now or (start-now).total_seconds()<=RULE['kickoff_buffer_seconds']:continue
        if (now-quote).total_seconds()>RULE['max_quote_age_seconds'] or candidate.get('edge_min',-1)<RULE['min_edge']:continue
        if ident in seen or daily>=RULE['max_daily_bets'] or opened>=RULE['max_open_bets']:continue
        bets.append({**candidate,'id':f"robust-{len(bets)+1:06d}",
                     'locked_at':now.isoformat(),'status':'pending'})
        seen.add(ident);daily+=1;opened+=1
    settled=[b for b in bets if b.get('status') in ('won','lost','push') and b.get('id') not in excluded]
    stake=sum(b['paper_stake_units'] for b in settled);profit=sum(b['profit_units'] for b in settled)
    returns=[b['profit_units']/b['paper_stake_units'] for b in settled]
    interval=mean_ci(returns,1.96)
    clv=[]
    for bet in settled:
        q=bet.get('last_observed_quote');start=timestamp(bet['start_utc'])
        if q and timedelta(0)<start-timestamp(q['quote_at'])<=timedelta(minutes=90):
            clv.append(bet['bookmaker_price']/q['price']-1)
    total=peak=drawdown=0.
    for b in sorted(settled,key=lambda b:(b['settled_at'],b['id'])):
        total+=b['profit_units'];peak=max(peak,total);drawdown=max(drawdown,peak-total)
    return {'generated_at_utc':now.isoformat(),'strategy':RULE['id'],'rule':RULE,'rule_hash':RULE_HASH,
        'scan_at':stamp.isoformat() if stamp else None,'status':'fresh_snapshot' if fresh else 'waiting_for_fresh_scan',
        'provider_status':source.get('provider_status') if source else None,
        'candidates':candidates,'watchlist':source.get('watchlist',[]) if fresh else [],
        'diagnostics':source.get('diagnostics',{}) if source else {},
        'performance':{'settled':len(settled),'pending':sum(b.get('status')=='pending' for b in bets),
            'stake_units':stake,'profit_units':profit,'roi_pct':100*profit/stake if stake else None,
            'return_interval':interval,'max_drawdown_units':drawdown,'closing_proxy':mean_ci(clv,1.96),
            'excluded_ids':excluded,'verdict':'insufficient_data' if len(settled)<RULE['min_settled_for_assessment'] else 'assessment_required'},
        'bets':bets,'real_bets_enabled':False,
        'warning':'Avantage théorique selon des prix de référence ; rentabilité non démontrée.'},ledger


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan',default='docs/engine-v2-latest.json')
    parser.add_argument('--history',default='docs/multisports-history.json')
    parser.add_argument('--ledger',default='docs/value-robuste-ledger.json')
    parser.add_argument('--output',default='docs/value-robuste-latest.json')
    args=parser.parse_args();path=Path(args.ledger)
    ledger=json.loads(path.read_text()) if path.exists() else {'bets':[]}
    report,ledger=update(json.loads(Path(args.scan).read_text()),ledger,
                         json.loads(Path(args.history).read_text()),datetime.now(timezone.utc))
    for target,data in [(Path(args.output),report),(path,ledger)]:
        target.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(f"Value robuste: {report['status']} — {len(report['candidates'])} candidats")


if __name__=='__main__':main()
