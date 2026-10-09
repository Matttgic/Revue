#!/usr/bin/env python3
"""Prospective SAME-BOOK closing price tracking for Revue paper entries.

No fabricated historical odds. Does not compute 'fair value' or wins.
Only prices actually re-observed after lock, for the EXACT same market/line.
"""
from __future__ import annotations
from datetime import datetime,timedelta
from math import isfinite
from statistics import mean

from outils.revue_engine_v2 import (
    FR_BOOKS,KICKOFF_BUFFER,match_fixture,quote_book_valid,timestamp
)
from outils.consensus_quotations import outcome_key

CLOSE_WINDOW=timedelta(minutes=90)
CLOSE_MIN_BUFFER=timedelta(minutes=5)
MAX_OBSERVATIONS_PER_PICK=36
MIN_REPEAT=timedelta(minutes=15)

def valid_hockey_period(market:dict)->bool:
    period=str(market.get("period") or "").upper()
    raw=str(market.get("raw_market_name") or "").lower()
    return period in ("GAME_INCLUDING_OVERTIME","INCLUDING_OVERTIME") or any(
        term in raw for term in ("incl ot","including overtime","overtime included",
                                 "prolongations incl","avec prolongation"))

def observe(ledger:dict,odds:dict,now:datetime)->dict:
    counts={"eligible_open":0,"new_observations":0,
            "blocked_market_or_time":0,"no_matching_quote":0}
    for bet in ledger.get("bets",[]):
        if bet.get("status")!="pending":continue
        lg=str(bet.get("league") or "")
        bk=str(bet.get("bookmaker") or "")
        if bk not in FR_BOOKS:
            continue
        start=timestamp(bet.get("start_utc"))
        locked=timestamp(bet.get("locked_at"))
        if start is None or locked is None or not locked<=now<start-KICKOFF_BUFFER:
            continue
        if lg=="NHL" and bet.get("market_rule_verified") is not True:
            continue
        counts["eligible_open"]+=1
        game={"event_id":str(bet["event_id"]),
              "home":bet.get("home"),"away":bet.get("away"),
              "start_utc":bet["start_utc"],"_league":lg}
        matches=[ev for ev in odds.get(lg,[])
                 if match_fixture(ev,[game],lg)]
        if len(matches)!=1:
            counts["no_matching_quote"]+=1
            continue
        target=(str(bet.get("side") or "").lower()
                if bet.get("market")=="h2h" else
                str(bet.get("side") or "").lower()+"@"+str(bet.get("line")))
        candidates=[]
        for book in matches[0].get("bookmakers") or []:
            if book.get("key")!=bk:continue
            for market in book.get("markets") or []:
                if market.get("key")!=bet.get("market"):
                    continue
                quote_time=quote_book_valid(book,market,now)
                if quote_time is None:
                    counts["blocked_market_or_time"]+=1
                    continue
                if lg=="NHL" and not valid_hockey_period(market):
                    counts["blocked_market_or_time"]+=1
                    continue
                matched=[out for out in market.get("outcomes") or []
                         if outcome_key(out,bet["market"],game)==target]
                if len(matched)!=1:continue
                try:price=float(matched[0]["price"])
                except (KeyError,ValueError,TypeError):continue
                if not isfinite(price) or price<=1 or price>250:continue
                candidates.append((price,quote_time))
        if len(candidates)!=1:
            counts["no_matching_quote"]+=1
            continue
        price,source_stamp=candidates[0]
        trail=bet.setdefault("odds_history",[])
        prior=trail[-1] if trail else None
        last=timestamp(prior.get("observed_at")) if prior else None
        if prior and last and now-last<MIN_REPEAT and price==prior["price"]:
            continue
        trail.append({
            "observed_at":now.isoformat(),
            "quote_at":source_stamp.isoformat(),
            "price":price,
            "bookmaker":bk,
            "same_market_line":True,
        })
        if len(trail)>MAX_OBSERVATIONS_PER_PICK:
            # Preserve first lock snapshot and most recent quotes.
            trail[:]=trail[:1]+trail[-(MAX_OBSERVATIONS_PER_PICK-1):]
        counts["new_observations"]+=1
    return counts


def closing_sample(bet:dict)->dict|None:
    """True closing PROXY: same bookmaker, newest observed within 90min before match."""
    # Legacy soccer/basketball matches were independently checked as
    # standard full-game h2h; do not mislabel all old picks as ambiguous.
    # Hockey overtime rules remain strictly explicit regardless of age.
    if bet.get("market_rule_verified") is False or (
        bet.get("league")=="NHL" and bet.get("market_rule_verified") is not True):
        return None
    start=timestamp(bet.get("start_utc"))
    locked=timestamp(bet.get("locked_at"))
    if start is None or locked is None or locked>=start:
        return None
    candidates=[]
    for obs in bet.get("odds_history") or []:
        seen=timestamp(obs.get("observed_at"))
        try:price=float(obs.get("price"))
        except (TypeError,ValueError):continue
        if (seen is not None and isfinite(price) and price>1.0
            and max(locked,start-CLOSE_WINDOW)<=seen<=start-CLOSE_MIN_BUFFER
            and obs.get("same_market_line") is True
            and obs.get("bookmaker")==bet.get("bookmaker")):
            candidates.append((seen,price))
    if not candidates:return None
    t,close=max(candidates,key=lambda x:x[0])
    try:locked_price=float(bet["bookmaker_price"])
    except (TypeError,ValueError,KeyError):return None
    if not isfinite(locked_price) or locked_price<=1:return None
    return {
        "closed_proxy_at":t.isoformat(),
        "observed_close_odds":close,
        "locked_odds":locked_price,
        "clv_pct":round(100*(locked_price/close-1),3),
        "close_type":"same_book_90m_proxy_not_verified_final_quote",
        "warning":"This is a quoted price movement, NOT realized betting profit.",
    }


def report(ledger:dict,now:datetime)->dict:
    bets=[b for b in ledger.get("bets",[])
          if b.get("market_rule_verified") is not False
          and (b.get("league")!="NHL" or b.get("market_rule_verified") is True)]
    results=[(b,closing_sample(b)) for b in bets]
    valid=[(b,x) for b,x in results if x is not None]
    return {
        "generated_at_utc":now.isoformat(),"source":"actual archived post-lock bookmaker quotes",
        "n_tracked":len(bets),"n_with_observation":sum(
            bool(b.get("odds_history")) for b in bets),
        "n_close_proxy_samples":len(valid),
        "mean_clv_pct":round(mean(v["clv_pct"] for _,v in valid),3) if valid else None,
        "recent_verified_proxy_samples":[
            {"selection_id":b.get("selection_id"),**x}
            for b,x in valid[-12:]
        ],
        "note":"Same-book 90-minute quote proxy; observed before kickoff. Not proof of positive EV.",
    }
