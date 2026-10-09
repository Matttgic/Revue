#!/usr/bin/env python3
"""Revue Engine V2 — an ORIGINAL, dry-run-only multisport odds and paper ledger.

Independent implementation of: real French bookmaker quotes, optional sharp
baseline, rigorous pre-start timestamps, stable paper locks, later settlement.

No bookmaker account actions; no real stakes; no automatic bet placement.
No API key => all odds/EV omitted, not invented. Models are not calibrated.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from outils.chronologie_pre_match import Decision, classifier, PRE_VALIDE

UTC=timezone.utc
PARIS=ZoneInfo("Europe/Paris")
BASE="https://api.the-odds-api.com/v4"
FR_BOOKS={"betclic_fr","netbet_fr","pmu_fr","unibet_fr","winamax_fr"}
SHARP="pinnacle"
SOURCED_BOOKS=sorted(FR_BOOKS | {SHARP})
ODDS_SPORTS={
 "NBA":"basketball_nba","WNBA":"basketball_wnba","NCAAB":"basketball_ncaab",
 "NFL":"americanfootball_nfl",
 "MLB":"baseball_mlb","NHL":"icehockey_nhl",
 "PL":"soccer_epl","LALIGA":"soccer_spain_la_liga",
 "SERIEA":"soccer_italy_serie_a","BUNDESLIGA":"soccer_germany_bundesliga",
 "LIGUE1":"soccer_france_ligue_one","MLS":"soccer_usa_mls",
 # UCL knockout score may include extra time. Disable paper odds until
 # first-90-minute scores are recorded separately from match finals.
}
NHL_FULL={
"ANA":"Anaheim Ducks","BOS":"Boston Bruins","BUF":"Buffalo Sabres",
"CAR":"Carolina Hurricanes","CBJ":"Columbus Blue Jackets","CGY":"Calgary Flames",
"CHI":"Chicago Blackhawks","COL":"Colorado Avalanche","DAL":"Dallas Stars",
"DET":"Detroit Red Wings","EDM":"Edmonton Oilers","FLA":"Florida Panthers",
"LAK":"Los Angeles Kings","MIN":"Minnesota Wild","MTL":"Montreal Canadiens",
"NJD":"New Jersey Devils","NSH":"Nashville Predators","NYI":"New York Islanders",
"NYR":"New York Rangers","OTT":"Ottawa Senators","PHI":"Philadelphia Flyers",
"PIT":"Pittsburgh Penguins","SEA":"Seattle Kraken","SJS":"San Jose Sharks",
"STL":"St Louis Blues","TBL":"Tampa Bay Lightning","TOR":"Toronto Maple Leafs",
"UTA":"Utah Mammoth","VAN":"Vancouver Canucks","VGK":"Vegas Golden Knights",
"WPG":"Winnipeg Jets","WSH":"Washington Capitals"}
ALIASES={"st":"saint","st.":"saint"}
MIN_EV=0.04
MIN_STAKE_ODDS=1.30
MAX_STAKE_ODDS=3.5
QUOTE_MAX_AGE=timedelta(minutes=50)
PREDICTION_MAX_AGE=timedelta(hours=6)
KICKOFF_BUFFER=timedelta(minutes=20)


def timestamp(value) -> datetime | None:
    if not isinstance(value,str):
        return None
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.astimezone(UTC) if d.tzinfo else None
    except ValueError:
        return None


def normalize(name: str,league:str="")->str:
    name=NHL_FULL.get(name,name) if league=="NHL" else name
    s=unicodedata.normalize("NFKD",str(name))
    s="".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s=re.sub(r"[^a-z0-9 ]+"," ",s).strip()
    words=[ALIASES.get(w,w) for w in s.split() if w not in ("fc","cf","sc","hc","bk")]
    return " ".join(words)


def same_team(a:str,b:str,league:str="")->bool:
    a,b=normalize(a,league),normalize(b,league)
    if a==b and len(a)>2:return True
    short,long=(a,b) if len(a)<len(b) else (b,a)
    # ESPN often uses just cityless nicknames, e.g. "Eagles".
    # Only suffix match on a substantial nickname (no "FC"/"United" shortcuts).
    return (len(short)>=5 and short not in ("united","city") and
            (long.endswith(" "+short) or long.startswith(short+" ")))


def match_fixture(quote:dict, games:list[dict],league:str)->dict|None:
    """Both team names and kickoff must agree, then candidate MUST be unique."""
    odds_time=timestamp(quote.get("commence_time"))
    if odds_time is None:return None
    candidates=[]
    for game in games:
        start=timestamp(game.get("start_utc"))
        if start is None or abs((odds_time-start).total_seconds())>120*60:
            continue
        if same_team(game.get("home",""),quote.get("home_team",""),league) and same_team(
            game.get("away",""),quote.get("away_team",""),league
        ):
            candidates.append(game)
    return candidates[0] if len(candidates)==1 else None


def price_probabilities(game:dict,market:str,outcome:dict) -> tuple[float,str] | None:
    p=game.get("probabilities")
    if not isinstance(p,dict):return None
    name=str(outcome.get("name") or "")
    h,a=game.get("home",""),game.get("away","")
    point=outcome.get("point")
    if market=="h2h":
        if name.lower()=="draw" and "draw_90" in p:return p["draw_90"],"draw"
        if same_team(name,h,game.get("_league","")):
            key="home_win_90" if "home_win_90" in p else "home_win"
            return (p[key],"home") if key in p else None
        if same_team(name,a,game.get("_league","")):
            key="away_win_90" if "away_win_90" in p else "away_win"
            return (p[key],"away") if key in p else None
    if market=="totals" and name in ("Over","Under"):
        try:
            line=float(point)
        except (ValueError,TypeError):
            return None
        metric=f"over_{str(line).replace('.','_')}"
        if metric not in p:return None
        prob=p[metric] if name=="Over" else 1-p[metric]
        return prob,name.lower()
    return None


def same_market_book(book:dict,market_key:str,selection:dict)->float|None:
    """De-vig only apples-to-apples outcomes (same total line)."""
    markets=[x for x in book.get("markets",[]) if x.get("key")==market_key]
    if len(markets)!=1:return None
    outcomes=markets[0].get("outcomes") or []
    line=selection.get("point")
    relevant=[x for x in outcomes if market_key=="h2h" or x.get("point")==line]
    if market_key=="h2h" and len(relevant) not in (2,3):return None
    if market_key=="totals" and {x.get("name") for x in relevant}!={"Over","Under"}:return None
    try:
        denom=sum(1/float(x["price"]) for x in relevant)
        matched=[x for x in relevant if x["name"]==selection["name"]]
        if len(matched)!=1 or denom<=0:return None
        return 1/float(matched[0]["price"])/denom
    except (ValueError,ZeroDivisionError,TypeError,KeyError):
        return None


def quote_book_valid(book:dict,market:dict,now:datetime) -> datetime|None:
    observed=timestamp(market.get("last_update") or book.get("last_update"))
    if observed is None or observed>now or now-observed>QUOTE_MAX_AGE:
        return None
    return observed


def _api(url:str)->tuple[list,dict]:
    """Never echo URL: API key is in its query string."""
    try:
        with urlopen(Request(url,headers={"Accept":"application/json"}),timeout=20) as resp:
            body=json.loads(resp.read().decode("utf-8"))
            meta={
                "remaining":resp.headers.get("x-requests-remaining"),
                "used":resp.headers.get("x-requests-used"),
                "last":resp.headers.get("x-requests-last"),
            }
            if not isinstance(body,list):
                raise ValueError("Non-list odds response")
            return body,meta
    except HTTPError as err:
        raise RuntimeError(f"HTTP {err.code} from odds provider") from None
    except (URLError,TimeoutError,ValueError) as err:
        raise RuntimeError(f"{type(err).__name__} from odds provider") from None


def download_odds(api_key:str, sports:list[str],max_sports:int=14) -> tuple[dict,dict]:
    """Only sports with a predicted upcoming fixture; two markets, one region."""
    odds={}
    errors={}
    spent=[]
    min_remaining=150
    for league in sports[:max_sports]:
        sport=ODDS_SPORTS[league]
        has_total=league=="NHL" or league in {
            "PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS"
        }
        params=urlencode({
            "apiKey":api_key,"bookmakers":",".join(SOURCED_BOOKS),
            "markets":"h2h,totals" if has_total else "h2h",
            "oddsFormat":"decimal",
            "dateFormat":"iso",
        })
        try:
            events,quota=_api(f"{BASE}/sports/{sport}/odds/?{params}")
            odds[league]=events
            spent.append({"league":league,"returned":len(events),"last_cost":quota["last"]})
            if quota.get("remaining") and int(quota["remaining"])<min_remaining:
                errors["quota"]="Pause: moins de 150 crédits restants."
                break
        except RuntimeError as err:
            errors[league]=str(err)
    return odds,{"requests":spent,"errors":errors,"sports_requested":len(spent)}


def market_recommendations(data:dict, odds:dict,now:datetime,
                           max_candidates:int=300)->tuple[list[dict],dict]:
    """Research-only mispricing watch. No real bets are proposed or placed."""
    model_stamp=timestamp(data.get("generated_at_utc"))
    diagnostics=defaultdict(int)
    if model_stamp is None or model_stamp>now or now-model_stamp>PREDICTION_MAX_AGE:
        return [],{"model_stale":1}
    candidates=[]
    for league,raw in odds.items():
        section=data.get("competitions",{}).get(league,{})
        scheduled=[]
        for game in section.get("games",[]):
            if game.get("status")=="prototype_non_calibre" and game.get("probabilities"):
                scheduled.append({**game,"_league":league})
        for event in raw:
            game=match_fixture(event,scheduled,league)
            if not game:
                diagnostics["unmatched"]+=1
                continue
            start=timestamp(game["start_utc"])
            if start<=now+KICKOFF_BUFFER:
                diagnostics["too_close_or_started"]+=1
                continue
            books=event.get("bookmakers") or []
            pinnacle=next((b for b in books if b.get("key")==SHARP),None)
            for book in books:
                bk=str(book.get("key") or "")
                if bk not in FR_BOOKS:continue
                for market in book.get("markets") or []:
                    mk=market.get("key")
                    if mk not in ("h2h","totals"):continue
                    outcomes=market.get("outcomes") or []
                    if mk=="h2h":
                        soccer="draw_90" in game["probabilities"]
                        has_draw=any(str(x.get("name","")).lower()=="draw" for x in outcomes)
                        if soccer!=has_draw or len(outcomes)!=(3 if soccer else 2):
                            diagnostics["market_rule_incompatible"]+=1
                            continue
                    # PulseScore FULL_TIME is not enough to prove whether
                    # a hockey market includes OT. NHL model uses game incl OT.
                    is_pulse=str(event.get("id") or "").startswith("review:")
                    if league=="NHL" and is_pulse:
                        label=str(market.get("raw_market_name") or "").lower()
                        period=str(market.get("period") or "").upper()
                        explicit_ot=(period in ("GAME_INCLUDING_OVERTIME","INCLUDING_OVERTIME")
                            or any(fragment in label for fragment in (
                                "incl ot","including ot","including overtime",
                                "overtime included","prolongation incl",
                                "prolongations incl","incluant prolongation",
                                "incl. prolongation","avec prolongation")))
                        if not explicit_ot:
                            diagnostics["nhl_overtime_market_not_verified"]+=1
                            continue
                    observed=quote_book_valid(book,market,now)
                    if observed is None:
                        diagnostics["stale_or_missing_bookmaker_time"]+=1
                        continue
                    for outcome in outcomes:
                        selection=price_probabilities(game,mk,outcome)
                        if selection is None:continue
                        prob,side=selection
                        try:
                            price=float(outcome["price"])
                        except (KeyError,TypeError,ValueError):
                            continue
                        if not math.isfinite(price) or price<MIN_STAKE_ODDS or price>MAX_STAKE_ODDS:
                            continue
                        if not 0.28<=prob<=0.84:continue
                        ev=prob*price-1
                        if ev<MIN_EV:continue
                        fair_p=None
                        if pinnacle:
                            sharp_market=next((z for z in pinnacle.get("markets",[])
                                               if z.get("key")==mk),None)
                            if sharp_market and quote_book_valid(pinnacle,sharp_market,now):
                                fair_p=same_market_book(pinnacle,mk,outcome)
                        # Pure price consensus: other FR books only, same
                        # verified event/market/line and fresh timestamps.
                        from outils.consensus_quotations import peer_consensus
                        peer=peer_consensus(event,game,mk,outcome,bk,now)
                        consensus=peer.get("p_no_vig")
                        gate=classifier(Decision(
                            evenement_id=str(game["event_id"]),
                            verrouille_le=now,debut_evenement=start,
                            cote_observee_le=observed,derniere_feature_publiee_le=model_stamp
                        ))
                        if gate!=PRE_VALIDE:
                            diagnostics["bad_timing"]+=1
                            continue
                        # Model confidence is unknown. Sharp de-vig is displayed
                        # as external corroboration, NEVER called a true fair price.
                        selection_id=f"{league}|{game['event_id']}|{mk}|{side}|{outcome.get('point')}|{bk}"
                        candidates.append({
                            "selection_id":selection_id,"league":league,
                            "event_id":str(game["event_id"]),
                            "odds_event_id":str(event.get("id") or ""),
                            "home":game["home"],"away":game["away"],
                            "start_utc":game["start_utc"],
                            "market":mk,"side":side,"line":outcome.get("point"),
                            "outcome":str(outcome.get("name") or ""),
                            "bookmaker":bk,"bookmaker_price":price,
                            "p_model":round(prob,5),
                            "p_sharp_no_vig":round(fair_p,5) if fair_p is not None else None,
                            "p_peer_books_no_vig":consensus,
                            "peer_books_count":peer.get("peer_count",0),
                            "peer_price_delta":round(price*consensus-1,5) if consensus is not None else None,
                            "peer_confirmation":"observed_prices_only_not_true_edge",
                            "ev_model":round(ev,5),
                            "quote_at":observed.isoformat(),
                            "quote_time_source":market.get("observed_origin") or "provider_last_update",
                            "model_at":model_stamp.isoformat(),
                            "observed_at":now.isoformat(),
                            "chronology":gate,
                            "market_rule_verified":True,
                            "status":"EXPERIMENTAL_PAPER_ONLY",
                            "note":"Estimation non calibrée; aucune EV démontrée.",
                        })
                        diagnostics["passing_filter"]+=1
    candidates.sort(key=lambda x:(-x["ev_model"],x["start_utc"],x["selection_id"]))
    return candidates[:max_candidates],dict(diagnostics)


def _outcome_from_score(bet:dict,home:float,away:float)->str|None:
    market=bet["market"]
    side=bet["side"]
    if market=="h2h":
        if home==away and side!="draw":return None
        # League-specific h2h settlement rule: 90m for soccer; incl extra
        # time/overtime elsewhere. ESPN scores may differ on rare forfeits.
        return ("won" if ((side=="draw" and home==away) or
                          (side=="home" and home>away) or
                          (side=="away" and away>home)) else "lost")
    if market=="totals":
        total=home+away
        line=bet.get("line")
        if not isinstance(line,(float,int)):return None
        if total==line:return "push"
        return "won" if (total>line if side=="over" else total<line) else "lost"
    return None


def _nhl_final(event_id:str,start_utc:str,cache:dict) -> tuple[float,float]|None:
    """One date request per day; missing/blocked NHL endpoints remain pending."""
    day=(timestamp(start_utc) or datetime.now(UTC)).astimezone(ZoneInfo("America/New_York")).date().isoformat()
    if day not in cache:
        try:
            with urlopen(Request(f"https://api-web.nhle.com/v1/score/{day}",
                     headers={"Accept":"application/json"}),timeout=17) as response:
                cache[day]=json.loads(response.read().decode("utf-8")).get("games",[])
        except Exception:
            cache[day]=[]
    for entry in cache[day]:
        if str(entry.get("id"))!=event_id:continue
        if str(entry.get("gameState","")).upper() not in ("OFF","FINAL"):return None
        home,away=entry.get("homeTeam") or {},entry.get("awayTeam") or {}
        if not isinstance(home.get("score"),int) or not isinstance(away.get("score"),int):
            return None
        a,b=home["score"],away["score"]
        period=(entry.get("gameOutcome") or {}).get("lastPeriodType")
        return float(a),float(b),str(period or "UNKNOWN").upper()
    return None


def settle_ledger(ledger:dict,cache:dict,now:datetime,
                  nhl_loader=None)->dict:
    """Settle archived paper entries ONLY from observed final scores."""
    history=cache.get("leagues") or {}
    indexes={}
    for lg,record in history.items():
        indexes[lg]={str(x.get("id")):x for x in record.get("events",[]) if x.get("complete")}
    nhl_cache={}
    for bet in ledger.get("bets",[]):
        if bet.get("status")!="pending":continue
        # Legacy Pulse NHL picks lacked documented OT vs regulation
        # settlement semantics. Quarantine rather than claim a paper win.
        if bet.get("league")=="NHL" and bet.get("market_rule_verified") is not True:
            bet["status"]="market_rule_unverified"
            bet["settlement_note"]="NHL market period not proven to include overtime."
            continue
        start=timestamp(bet.get("start_utc"))
        if start is None or start>=now:continue
        league=bet.get("league")
        score=None
        if league=="NHL":
            score=(nhl_loader or _nhl_final)(bet["event_id"],bet["start_utc"],nhl_cache)
        elif league in indexes:
            recorded=indexes[league].get(str(bet.get("event_id")))
            if recorded:
                score=(recorded.get("home_score"),recorded.get("away_score"))
        if score is None or len(score)<2 or any(x is None for x in score[:2]):
            continue
        h,a=float(score[0]),float(score[1])
        if league=="NHL" and bet["market"]=="totals":
            # Missing shootout classification => do not misgrade.
            period=score[2] if len(score)>=3 else None
            if period is None or period=="UNKNOWN":
                continue
            if period=="SO" and abs(h-a)==1:
                if h>a:h-=1
                else:a-=1
        outcome=_outcome_from_score(bet,h,a)
        if outcome is None:continue
        bet["status"]=outcome
        bet["settled_at"]=now.isoformat()
        bet["score"]={"home":score[0],"away":score[1]}
        bet["paper_units_returned"]=(
            bet["bookmaker_price"] if outcome=="won" else
            1 if outcome=="push" else 0
        )
    return ledger


def paper_locks(candidates:list[dict],ledger:dict,now:datetime,
                per_day_limit:int=25) -> dict:
    """At most ONE research paper selection per event. No financial action."""
    bets=ledger.setdefault("bets",[])
    seen={(b.get("league"),b.get("event_id")) for b in bets}
    today=now.astimezone(PARIS).date()
    n_today=sum(timestamp(b.get("locked_at")).astimezone(PARIS).date()==today
                for b in bets if timestamp(b.get("locked_at")))
    for c in candidates:
        key=(c["league"],c["event_id"])
        if key in seen or n_today>=per_day_limit:continue
        start=timestamp(c["start_utc"])
        quote=timestamp(c["quote_at"])
        model=timestamp(c["model_at"])
        if not all([start,quote,model]):continue
        gate=classifier(Decision(c["event_id"],now,start,quote,model))
        if gate!=PRE_VALIDE or start-now<KICKOFF_BUFFER:continue
        bet={**c,"id":f"paper-{len(bets)+1:06d}",
             "locked_at":now.isoformat(),"status":"pending",
             "paper_stake_units":1.0}
        bets.append(bet)
        seen.add(key);n_today+=1
    return ledger


def verified_pre_match(b:dict) -> bool:
    """Recompute temporal provenance from raw fields, never trust a status tag."""
    if b.get("chronology")!=PRE_VALIDE:
        return False
    if b.get("league")=="NHL" and b.get("market_rule_verified") is not True:
        return False
    lock=timestamp(b.get("locked_at"))
    start=timestamp(b.get("start_utc"))
    odds_time=timestamp(b.get("quote_at"))
    model_time=timestamp(b.get("model_at"))
    if not all((lock,start,odds_time,model_time)):
        return False
    gate=classifier(Decision(
        evenement_id=str(b.get("event_id") or ""),
        verrouille_le=lock, debut_evenement=start,
        cote_observee_le=odds_time,derniere_feature_publiee_le=model_time))
    return (
        gate==PRE_VALIDE and start-lock>=KICKOFF_BUFFER
        and lock-odds_time<=QUOTE_MAX_AGE
        and lock-model_time<=PREDICTION_MAX_AGE
    )


def ledger_statistics(ledger:dict)->dict:
    bets=ledger.get("bets",[])
    graded=[b for b in bets if b.get("status") in ("won","lost","push")
            and verified_pre_match(b)]
    unknown=[b for b in bets if not verified_pre_match(b)]
    pnl=sum(float(b.get("paper_units_returned",0))-float(b.get("paper_stake_units",1))
            for b in graded)
    invested=sum(float(b.get("paper_stake_units",1)) for b in graded)
    wins=sum(b["status"]=="won" for b in graded)
    losses=sum(b["status"]=="lost" for b in graded)
    return {
        "paper_only":True,"n_paper":len(bets),"pending":sum(b.get("status")=="pending" for b in bets),
        "graded_pre_start":len(graded),"wins":wins,"losses":losses,
        "pushes":sum(b["status"]=="push" for b in graded),
        "excluded_unsafe_timestamps":len(unknown),
        "paper_profit_units":round(pnl,4),
        "paper_roi_pct":round(100*pnl/invested,2) if invested else None,
        "note":"ROI papier uniquement pour les sélections strictement pré-match.",
    }


def execute(models:dict,history:dict,ledger:dict,now:datetime,
            api_key:str="",max_sports:int=14,nhl_loader=None,
            pulsescore_key:str="") -> tuple[dict,dict]:
    # Each run may settle old paper picks even if no API key is configured.
    settle_ledger(ledger,history,now,nhl_loader)
    eligible=[
        k for k in ODDS_SPORTS
        if any(g.get("probabilities") and g.get("status")=="prototype_non_calibre"
            and (timestamp(g.get("start_utc")) or now)<=now+timedelta(days=3)
            and (timestamp(g.get("start_utc")) or now)>now+KICKOFF_BUFFER
               for g in models.get("competitions",{}).get(k,{}).get("games",[]))
    ]
    odds,meta=({},{"status":"disabled_no_key","requests":[],"errors":{}})
    model_stamp=timestamp(models.get("generated_at_utc"))
    usable_model=(model_stamp is not None and model_stamp<=now and
                  now-model_stamp<=PREDICTION_MAX_AGE)
    if (api_key or pulsescore_key) and not usable_model:
        meta={"status":"disabled_stale_model","requests":[],"errors":{
            "models":"Aucune cote demandée : prédictions anciennes ou non horodatées."}}
    elif pulsescore_key:
        # PulseScore Pro: one standardized REST schema per French bookmaker.
        # No code or data is copied from the unrelated Clairvoyance project.
        from outils.pulsescore_v2 import scan as pulse_scan
        odds,diag=pulse_scan(pulsescore_key,models,now,max_calls=32,
                             days_horizon=24)
        meta={
            "status":"active_pulsescore",
            "requests":[{"provider":"PulseScore","calls":diag["requests"],
                         "matched_events":diag["matched_events"]}],
            "errors":diag.get("errors",{}),"details":diag,
        }
    elif api_key:
        odds,meta=download_odds(api_key,eligible,max_sports)
        meta["status"]="active_the_odds_api" if meta["requests"] else "no_odds_returned"
    # Prices for ALL matched markets, not only positive-EV candidates.
    # Strictly observed prices with market/time provenance, no extra API calls.
    from outils.tableau_cotes import build_board
    odds_board=build_board(models,odds,now)
    picks,notes=market_recommendations(models,odds,now)
    paper_locks(picks,ledger,now)
    # Observe subsequent real prices of the EXACT locked paper market only.
    # Historical price data is never synthesized from latest odds.
    from outils.historique_cotes_clv import observe as follow_prices
    from outils.historique_cotes_clv import report as closing_report
    observations=follow_prices(ledger,odds,now)
    price_tracking=closing_report(ledger,now)
    price_tracking["scan_observations"]=observations
    report={
        "generated_at_utc":now.isoformat(),
        "engine":"Revue Engine V2 — indépendant / expérimental",
        "mode":"PAPER_ONLY",
        "odds_status":meta["status"],
        "coverage":{"eligible_leagues":eligible,
                    "requested":meta["requests"],"api_errors":meta["errors"],
                    "provider_scan_details":{
                        "horizon_hours":(meta.get("details") or {}).get("horizon_hours"),
                        "truncated":(meta.get("details") or {}).get("truncated"),
                        "matched_leagues":(meta.get("details") or {}).get("matched_leagues",{}),
                    },
                    "model_generated_at_utc":models.get("generated_at_utc")},
        "bookmakers_fr":sorted(FR_BOOKS),
        "odds_board":odds_board,
        "candidate_count":len(picks),
        "candidates":picks[:100],
        "diagnostics":notes,
        "paper":ledger_statistics(ledger),
        "price_tracking":price_tracking,
        "warning":"Aucun modèle calibré. EV supposée, non vérifiée. Aucun pari réel automatique.",
    }
    return report,ledger


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predictions",default="docs/multisports-latest.json")
    p.add_argument("--history",default="docs/multisports-history.json")
    p.add_argument("--ledger",default="docs/engine-v2-ledger.json")
    p.add_argument("--output",default="docs/engine-v2-latest.json")
    p.add_argument("--max-sports",type=int,default=14)
    args=p.parse_args()
    if not 1<=args.max_sports<=14:p.error("max-sports between 1 and 14")
    now=datetime.now(UTC)
    models=json.loads(Path(args.predictions).read_text(encoding="utf-8"))
    history=json.loads(Path(args.history).read_text(encoding="utf-8"))
    path=Path(args.ledger)
    try:
        ledger=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(ledger.get("bets"),list):
            raise ValueError("bad ledger")
    except FileNotFoundError:
        ledger={"version":1,"started_at":now.isoformat(),"bets":[]}
    report,ledger=execute(models,history,ledger,now,
                          api_key=os.environ.get("ODDS_API_KEY",""),
                          pulsescore_key=os.environ.get("PULSESCORE_API_KEY",""),
                          max_sports=args.max_sports)
    for target,obj in ((Path(args.output),report),(path,ledger)):
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Odds: {report['odds_status']} — paper: {report['paper']}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
