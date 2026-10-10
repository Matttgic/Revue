#!/usr/bin/env python3
"""Read-only cross-book mathematical cover audit from existing observed FR quotes.

No API requests, orders, bankroll handling or real bets. An inverse-price sum
below one on already OBSERVED odds is not a tradable arbitrage: odds may have
changed, stakes can be restricted, and settlement terms may differ.

Fail closed on league/period, complete 1X2 or O/U market, line, duplicate books,
malformed margins, timestamp and clock skew. Neither raw model probabilities
nor EV claims are consulted. NHL unknown overtime and all game-result two-way
markets are excluded until settlement equivalence is established.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import json
from math import isfinite
from pathlib import Path

from outils.revue_engine_v2 import timestamp

VERSION="revue_quotations_crossbook_coverage_v1"
SOCCER={"PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS"}
BOOKS={"betclic_fr","winamax_fr","unibet_fr","netbet_fr","pmu_fr"}
MAX_AGE=timedelta(minutes=70)
MAX_QUOTE_GAP=timedelta(minutes=15)
MIN_START=timedelta(minutes=20)
MIN_THEORETICAL_EDGE=0.005 # lower values drown in tick spread
MIN_MARGIN=0.94
MAX_MARGIN=1.29


def source_rows(source:dict,now:datetime)->tuple[list[dict],str]:
    if not isinstance(source,dict):return [],"invalid"
    stamp=timestamp(source.get("generated_at_utc"))
    if stamp is None or stamp>now+timedelta(minutes=2) or now-stamp>MAX_AGE:
        return [],"missing_or_stale"
    if (source.get("version")=="revue_pulsescore_six_hour_radar_v1"
        and source.get("status")=="observed"
        and source.get("provider")=="PulseScore"
        and source.get("market_prices_are_live") is False
        and source.get("positive_ev_verified") is False
        and source.get("real_bets_enabled") is False
        and source.get("existing_paper_ledger_modified") is False
        and source.get("horizon_hours")==6
        and type(source.get("request_cap")) is int
        and 1<=source["request_cap"]<=8
        and type(source.get("requests_used")) is int
        and 0<=source["requests_used"]<=source["request_cap"]
        and isinstance(source.get("observations"),list)):
        return source["observations"],"validated_snapshot_radar"
    board=source.get("odds_board") or {}
    if (source.get("mode")=="PAPER_ONLY"
        and source.get("odds_status")=="active_pulsescore"
        and isinstance(board.get("events"),list)
        and source.get("engine")=="Revue Engine V2 — indépendant / expérimental"
        and board.get("events_count")==len(board["events"])):
        return board["events"],"validated_snapshot_full"
    return [],"invalid_provenance"


def _price(o:dict):
    v=o.get("price")
    return float(v) if type(v) in (int,float) and isfinite(v) and 1.01<v<=100 else None


def _candidate(league:str,market:dict,now:datetime,start:datetime,diagnostics:Counter):
    if not isinstance(market,dict) or market.get("period_rule")!="90min":
        diagnostics["period_unverified"]+=1
        return []
    quote=timestamp(market.get("quote_at"))
    if quote is None or quote>now+timedelta(minutes=2) or quote>start-MIN_START or now-quote>MAX_AGE:
        diagnostics["quote_stale_or_invalid"]+=1
        return []
    ty=market.get("market")
    if ty not in ("h2h","totals"):return []
    items=market.get("outcomes")
    if not isinstance(items,list):return []
    if ty=="h2h":
        if len(items)!=3:return []
        required={"home","draw","away"}
        outcome={}
        for item in items:
            if item.get("selection") not in required or item.get("line") is not None:
                return []
            p=_price(item)
            if p is None or item["selection"] in outcome:return []
            outcome[item["selection"]]=p
        if set(outcome)!=required:return []
        margin=sum(1/p for p in outcome.values())
        if not MIN_MARGIN<=margin<=MAX_MARGIN:
            diagnostics["implausible_book_margin"]+=1
            return []
        return [(("h2h",None),outcome,quote)]
    grouped=defaultdict(dict)
    for item in items:
        side=item.get("selection")
        line=item.get("line")
        if side not in ("over","under") or type(line) not in (int,float) or not isfinite(line):
            return []
        # No quarter lines. Whole/half only: equal settlement boundaries
        if line<.5 or line>15 or line*2!=int(line*2):return []
        p=_price(item)
        if p is None or side in grouped[line]:return []
        grouped[line][side]=p
    valid=[]
    for line,outcome in grouped.items():
        if set(outcome)!={"over","under"}:continue
        margin=sum(1/p for p in outcome.values())
        if MIN_MARGIN<=margin<=MAX_MARGIN:valid.append((("totals",line),outcome,quote))
        else:diagnostics["implausible_book_margin"]+=1
    return valid


def analyze(boards:dict,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Timezone-aware clock required")
    now=now.astimezone(timezone.utc)
    diagnostics=Counter()
    sources={}
    possibilities=[]
    checked_events=set()
    for source_name,source in boards.items():
        if source_name not in ("radar_6h","full_scan"):
            continue
        rows,state=source_rows(source,now)
        sources[source_name]={"status":state,
            "events_considered":len(rows),
            "observed_at_utc":source.get("generated_at_utc") if isinstance(source,dict) else None}
        # We audit each source independently; mixing quotes from 2 different
        # observations could create a mathematical cover that never existed.
        event_ids=Counter((r.get("league"),str(r.get("event_id"))) for r in rows
                          if isinstance(r,dict))
        for e in rows:
            if not isinstance(e,dict):continue
            league=e.get("league")
            ident=str(e.get("event_id") or "")
            if league not in SOCCER:
                diagnostics["unsupported_or_ambiguous_settlement"]+=1
                continue
            if event_ids[(league,ident)]!=1 or not ident.isdigit():
                diagnostics["duplicate_or_invalid_fixture"]+=1
                continue
            start=timestamp(e.get("start_utc"))
            if start is None or start<=now+MIN_START:
                diagnostics["started_or_no_kickoff"]+=1
                continue
            home,away=e.get("home"),e.get("away")
            if not isinstance(home,str) or not isinstance(away,str) or home==away or not home or not away:
                diagnostics["fixture_identity_invalid"]+=1
                continue
            event_key=(source_name,league,ident)
            checked_events.add(event_key)
            markets=defaultdict(list)
            seen_books=set()
            ambiguous_event=False
            for book in e.get("bookmakers") or []:
                bk=book.get("bookmaker")
                if bk not in BOOKS:continue
                if bk in seen_books:
                    ambiguous_event=True
                    diagnostics["duplicate_bookmaker"]+=1
                    # A duplicate sportsbook entry on the same event means
                    # all of its markets are ambiguous; remove its quotes.
                    for group in markets.values():
                        group[:]=[x for x in group if x["book"]!=bk]
                    continue
                seen_books.add(bk)
                if not isinstance(book.get("markets"),list):continue
                seen_market_keys=set()
                invalid_market_keys=set()
                for m in book["markets"]:
                    for key,prices,when in _candidate(league,m,now,start,diagnostics):
                        if key in seen_market_keys:
                            invalid_market_keys.add(key)
                            continue
                        seen_market_keys.add(key)
                        markets[key].append({"book":bk,"prices":prices,"quote_at":when})
                if invalid_market_keys:
                    ambiguous_event=True
                    for key in invalid_market_keys:
                        markets[key]=[x for x in markets[key] if x["book"]!=bk]
                    diagnostics["duplicate_book_market"]+=len(invalid_market_keys)
            if ambiguous_event:
                diagnostics["ambiguous_event_skipped"]+=1
                continue
            for (market,line),offers in markets.items():
                if len(offers)<2:
                    diagnostics["not_enough_books"]+=1
                    continue
                expected=("home","draw","away") if market=="h2h" else ("over","under")
                best={}
                for side in expected:
                    choices=sorted(
                        ({"side":side,"book":o["book"],"odds":o["prices"][side],
                          "quote_at_utc":o["quote_at"].isoformat()} for o in offers),
                        key=lambda x:(-x["odds"],x["book"]),
                    )
                    best[side]=choices[0]
                if len({x["book"] for x in best.values()})<2:
                    diagnostics["one_book_all_best"]+=1
                    continue
                times=[timestamp(x["quote_at_utc"]) for x in best.values()]
                if max(times)-min(times)>MAX_QUOTE_GAP:
                    diagnostics["price_times_not_comparable"]+=1
                    continue
                overround=sum(1/x["odds"] for x in best.values())
                diagnostics["complete_cross_book_markets"]+=1
                if overround>=1-MIN_THEORETICAL_EDGE:
                    diagnostics["no_math_cover"]+=1
                    continue
                # Mathematical payout is 1/sum(1/price) per unit of TOTAL
                # theoretical exposure, not a guaranteed executable gain.
                gain=100*(1/overround-1)
                possibilities.append({
                    "league":league,"event_id":ident,"home":home,"away":away,
                    "start_utc":start.isoformat(),"source_scan":source_name,
                    "market":market,"line":line,"period_rule":"90min",
                    "outcomes":[best[s] for s in expected],
                    "bookmaker_count":len({x["book"] for x in best.values()}),
                    "quote_gap_seconds":int((max(times)-min(times)).total_seconds()),
                    "inverse_odds_sum":round(overround,8),
                    "mathematical_snapshot_excess_pct":round(gain,4),
                    "claim_executable_arbitrage":False,
                    "all_prices_confirmed_bookable":False,
                })
    possibilities.sort(key=lambda x:(-x["mathematical_snapshot_excess_pct"],x["start_utc"],x["league"]))
    return {
        "version":VERSION,"generated_at_utc":now.isoformat(),
        "status":"math_only_quotes_observed_no_bookable_confirmation",
        "source_snapshots":sources,
        "source_event_snapshots_audited":len(checked_events),
        "complete_cross_book_markets_checked":diagnostics["complete_cross_book_markets"],
        "potential_snapshot_covers":possibilities[:50],
        "potential_snapshot_cover_count":len(possibilities),
        "minimum_theoretical_excess_pct":MIN_THEORETICAL_EDGE*100,
        "quote_max_age_minutes":MAX_AGE.total_seconds()/60,
        "risk_flags":{
            "actual_prices_bookable_verified":False,
            "bookmaker_stake_limits_verified":False,
            "settlement_rules_all_sports_verified":False,
            "model_calibrated":False,
            "claim_guaranteed_profit":False,
            "claim_positive_expected_value":False,
            "real_bets_enabled":False,
            "paid_api_calls_for_this_audit":0,
        },
        "diagnostics":dict(diagnostics),
        "note":"Snapshot arithmetic only. Prices may disappear, drift, be restricted, be rejected, or settle differently. Require independent live bookmaker checks to execute; no bets recommended.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--radar",default="docs/pulsescore-radar-latest.json")
    p.add_argument("--full",default="docs/engine-v2-latest.json")
    p.add_argument("--output",default="docs/revue-crossbook-latest.json")
    args=p.parse_args()
    docs={}
    for key,path in (("radar_6h",args.radar),("full_scan",args.full)):
        try:docs[key]=json.loads(Path(path).read_text(encoding="utf8"))
        except (OSError,ValueError):docs[key]=None
    outcome=analyze(docs,datetime.now(timezone.utc))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(outcome,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf8")
    print("Cross-book observed: complete markets",outcome["complete_cross_book_markets_checked"],
          "math-only theoretical covers",outcome["potential_snapshot_cover_count"],
          "real bets",outcome["risk_flags"]["real_bets_enabled"])


if __name__=="__main__":main()
