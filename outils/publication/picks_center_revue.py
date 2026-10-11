"""Revue's independently implemented picks screen, driven by observed saved data.

Behavioural reference: public Clairvoyance front-end displays today's proposals,
locked selections, settled history and performance. Its public lock_timing.py
explicitly separates pregame locks from in-progress/postgame ones. This code
does not copy original code; it applies verified Revue source/provenance policy.

No bookmaker calls, real bets, original database, settled result simulation
or fabricated positive expected value.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,json,math

MIN_LEAD=timedelta(minutes=20)
RESEARCH_TAG="revue_experimental_not_calibrated"
SETTLED={"won","lost","push"}
PAPER_STATUSES=SETTLED|{"pending","unverified"}

def dt(value):
    if not isinstance(value,str):raise ValueError("Missing event timestamp")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Timezone mandatory")
    return t.astimezone(timezone.utc)

def finite(value,minimum=None,maximum=None):
    if type(value) not in (int,float) or not math.isfinite(value):
        return False
    return (minimum is None or value>=minimum) and (maximum is None or value<=maximum)

def group_id(d):
    ln=d.get("line")
    l="none" if ln is None else str(float(ln)).rstrip("0").rstrip(".")
    return "|".join([d["league"],d["event_id"],d["market"],d["side"],l])

def board(engine,ledger,now):
    if now.tzinfo is None:raise ValueError("Clock must have UTC offset")
    now=now.astimezone(timezone.utc)
    if (engine.get("mode")!="PAPER_ONLY" or
        engine.get("candidate_count")!=len(engine.get("candidates") or []) or
        not isinstance(engine.get("candidates"),list) or
        ledger.get("paper_only") is not True or
        ledger.get("real_bets_enabled") is not False or
        ledger.get("static_snapshot") is not True or
        not isinstance(ledger.get("records"),list) or
        ledger.get("source")!="Revue independent paper ledger, NOT Clairvoyance SQL"):
        raise ValueError("Untrusted engine or independent paper-ledger contract")
    observed=dt(engine.get("generated_at_utc"))
    ledger_time=dt(ledger.get("generated_at_utc"))
    if observed>now+timedelta(minutes=2) or ledger_time>now+timedelta(minutes=2):
        raise ValueError("Future timestamp in source")
    rejected=defaultdict(int)
    raw_groups={}
    seen=set()
    for r in engine["candidates"]:
        if not isinstance(r,dict):rejected["malformed_candidate"]+=1;continue
        league=str(r.get("league") or "")
        if league=="CFB":rejected["cfb_excluded"]+=1;continue
        ident=str(r.get("selection_id") or "")
        if not ident or ident in seen:rejected["duplicate_candidate"]+=1;continue
        seen.add(ident)
        event_id=str(r.get("event_id") or "")
        try:
            start=dt(r.get("start_utc"))
            qt=dt(r.get("quote_at"))
            model_t=dt(r.get("model_at"))
        except (ValueError,TypeError):
            rejected["timestamp_unverifiable"]+=1;continue
        if qt>start-MIN_LEAD or model_t>qt or qt>now:
            rejected["invalid_pregame_chronology"]+=1;continue
        price=r.get("bookmaker_price")
        prob=r.get("p_model")
        if (not finite(price,1.0000000001,1000) or
            not finite(prob,0,1) or
            not isinstance(r.get("bookmaker"),str) or
            not r["bookmaker"].endswith("_fr") or
            r.get("market_rule_verified") is not True or
            r.get("chronology")!="pre_valide" or
            r.get("status")!="EXPERIMENTAL_PAPER_ONLY"):
            rejected["source_market_or_probability_unverifiable"]+=1;continue
        market,side=r.get("market"),r.get("side")
        if market not in ("h2h","totals") or side not in ("home","away","draw","over","under"):
            rejected["invalid_market_side"]+=1;continue
        ln=r.get("line")
        if (market=="h2h" and (ln is not None or side not in ("home","away","draw"))) or (
            market=="totals" and (not finite(ln,.5,50) or side not in ("over","under"))):
            rejected["incompatible_line_and_selection"]+=1;continue
        home,away=r.get("home"),r.get("away")
        if (not isinstance(home,str) or not home or
            not isinstance(away,str) or not away or home==away or not event_id):
            rejected["invalid_fixture_identity"]+=1;continue
        selection={"league":league,"event_id":event_id,"home":home,"away":away,
                   "start_utc":start.isoformat(),"market":market,"side":side,
                   "line":float(ln) if ln is not None else None}
        key=group_id(selection)
        g=raw_groups.setdefault(key,{"key":key,**selection,
              "bookmakers":[],"research_only":True,"real_bet":False,
              "model_is_calibrated":False,"qualified_positive_ev":False,
              "available_as_real_market":False})
        if any(g[k]!=selection[k] for k in ("league","event_id","home","away","start_utc","market","side","line")):
            raise ValueError("Selection ID reused across conflicting games")
        g["bookmakers"].append({
            "bookmaker":r["bookmaker"],"selection_id":ident,
            "decimal_odds":float(price),"quote_at_utc":qt.isoformat(),
            "p_model_experimental":float(prob),"model_at_utc":model_t.isoformat(),
            "p_peer_books_no_vig":float(r["p_peer_books_no_vig"])
                if finite(r.get("p_peer_books_no_vig"),0,1) else None,
            "peer_books_count":r.get("peer_books_count") if type(r.get("peer_books_count")) is int else None,
            "odds_source_is_snapshot":True})
    candidates=[]
    for g in raw_groups.values():
        books=g["bookmakers"]
        # Drop exact repeated bookmaker on the same matched event/market.
        if len({r["bookmaker"] for r in books})!=len(books):
            rejected["duplicate_bookmaker_in_same_market"]+=1
            continue
        books.sort(key=lambda x:(-x["decimal_odds"],x["bookmaker"]))
        best=books[0]
        g["best_observed_price"]={"bookmaker":best["bookmaker"],
            "decimal_odds":best["decimal_odds"],"quote_at_utc":best["quote_at_utc"]}
        g["books_count"]=len(books)
        g["visible_as_upcoming_at_export"]=(
            dt(g["start_utc"])>=now+MIN_LEAD and now-observed<=timedelta(hours=3))
        g["selection_label"]={"home":g["home"],"away":g["away"],"draw":"Nul",
                              "over":"Plus de","under":"Moins de"}[g["side"]]
        candidates.append(g)
    candidates.sort(key=lambda x:(not x["visible_as_upcoming_at_export"],
                                  x["start_utc"],-x["best_observed_price"]["decimal_odds"],x["key"]))
    records=[];id_seen=set()
    for rec in ledger["records"]:
        if not isinstance(rec,dict):raise ValueError("Malformed paper record")
        rid=str(rec.get("id") or "")
        if rid in id_seen or not rid:raise ValueError("Duplicated paper bet ID")
        id_seen.add(rid)
        if rec.get("league")=="CFB":continue
        if (rec.get("is_real_bet") is not False or
            rec.get("status") not in PAPER_STATUSES):
            raise ValueError("Unexpected source betting or settlement status")
        try:
            kick=dt(rec["start_utc"]);lock=dt(rec["locked_at_utc"])
            quoted=dt(rec["quote_at_utc"])
        except (KeyError,ValueError,TypeError) as exc:
            raise ValueError("Paper records must carry immutable temporal evidence") from exc
        pregame=lock<=kick-MIN_LEAD and quoted<=lock
        status=rec["status"]
        if status in SETTLED and not (pregame and rec.get("verified_pre_match") is True):
            # Source may contain impossible grades; never silently show ROI.
            raise ValueError("A settled paper bet is not a verified pregame selection")
        if rec.get("status")=="unverified" and not rec.get("exclusion_reason"):
            raise ValueError("Unverified bet missing exclusion evidence")
        pnl=rec.get("paper_profit_units")
        stake=rec.get("paper_stake_units")
        quote=rec.get("decimal_odds")
        if (not finite(stake,.000001,100000) or
            not finite(quote,1.0000001,1000) or
            (status in SETTLED and not finite(pnl,-100000,100000)) or
            (status not in SETTLED and pnl is not None)):
            raise ValueError("Malformed paper stake, odds or profit")
        if status=="won" and abs(pnl-stake*(quote-1))>.011:
            raise ValueError("Impossible paper win profit")
        if status=="lost" and abs(pnl+stake)>.011:
            raise ValueError("Impossible paper loss profit")
        if status=="push" and abs(pnl)>.011:
            raise ValueError("Impossible paper push profit")
        records.append({
            "id":rid,"league":rec["league"],"event_id":str(rec["event_id"]),
            "home":rec["home"],"away":rec["away"],"start_utc":kick.isoformat(),
            "locked_at_utc":lock.isoformat(),"quote_at_utc":quoted.isoformat(),
            "market":rec.get("market"),"side":rec.get("side"),
            "line":rec.get("line"),"outcome":rec.get("outcome"),
            "bookmaker":rec.get("bookmaker"),"decimal_odds":float(quote),
            "paper_stake_units":float(stake),
            "status":status,"exclusion_reason":rec.get("exclusion_reason"),
            "score":rec.get("score"),
            "paper_profit_units":round(float(pnl),3) if pnl is not None else None,
            "verified_pregame":pregame and rec.get("verified_pre_match") is True,
            "real_bet":False})
    records.sort(key=lambda x:(x["start_utc"],x["id"]),reverse=True)
    settled=[r for r in records if r["status"] in SETTLED]
    total_stakes=sum(x["paper_stake_units"] for x in settled)
    net=sum(x["paper_profit_units"] for x in settled)
    counts={key:sum(1 for x in records if x["status"]==key)
             for key in ("won","lost","push","pending","unverified")}
    source_summary=ledger.get("summary") or {}
    # Recomputing from validated records prevents the UI reporting inaccurate
    # denominators or inflated profits supplied in the summary.
    if (source_summary.get("total")!=len(records) or
        source_summary.get("settled")!=len(settled) or
        any(source_summary.get(k)!=counts[v]
            for k,v in (("won","won"),("lost","lost"),("push","push"),
                        ("pending","pending"),("excluded_or_unverified","unverified"))) or
        not finite(source_summary.get("paper_profit_units"),-100000,100000) or
        abs(source_summary["paper_profit_units"]-net)>.012):
        raise ValueError("Paper report contradicts underlying records")
    margin=round(100*net/total_stakes,2) if total_stakes else None
    by_league={}
    for league in sorted({r["league"] for r in records}):
        arr=[r for r in records if r["league"]==league]
        done=[r for r in arr if r["status"] in SETTLED]
        s=sum(r["paper_stake_units"] for r in done)
        money=sum(r["paper_profit_units"] for r in done)
        by_league[league]={"total":len(arr),"settled":len(done),
            "wins":sum(r["status"]=="won" for r in done),
            "losses":sum(r["status"]=="lost" for r in done),
            "profit_units":round(money,3),"roi_percent":round(100*money/s,2) if s else None}
    return {"generated_at_utc":now.isoformat(),
        "status":"revue_independent_picks_hub_static_research_paper_only",
        "research_model_calibrated":False,"verified_real_ev":False,
        "live_bookmaker_prices":False,"real_bets_enabled":False,
        "original_clairvoyance_sql_parity":False,
        "source_engine_generated_at_utc":observed.isoformat(),
        "source_ledger_generated_at_utc":ledger_time.isoformat(),
        "source_candidate_count":len(engine["candidates"]),
        "unique_research_selections":len(candidates),
        "upcoming_research_selections":sum(x["visible_as_upcoming_at_export"] for x in candidates),
        "excluded_candidate_records":dict(rejected),
        "paper_summary":{
            "total":len(records),"settled":len(settled),
            "wins":counts["won"],"losses":counts["lost"],"pushes":counts["push"],
            "pending":counts["pending"],"excluded":counts["unverified"],
            "paper_profit_units":round(net,3),"paper_roi_percent":margin,
            "settled_stake_units":round(total_stakes,3),
            "profitable_strategy_proven":False},
        "performance_by_league":by_league,
        "research_selections":candidates,
        "paper_records":records,
        "note":"Independent functional reconstruction of public browsing/tracking concepts, never a copy of original UI or proprietary SQL. 'Best' means highest archived French bookmaker price for the SAME event and selection, not confirmed EV, valid current odds or guaranteed advantage."}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--docs",default="docs")
    cli.add_argument("--output",default="docs/picks-center-latest.json")
    args=cli.parse_args();root=Path(args.docs)
    def read(p):return json.loads((root/p).read_text(encoding="utf-8"))
    doc=board(read("engine-v2-latest.json"),
              read("revue-control-ledger-latest.json"),datetime.now(timezone.utc))
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Picks hub:",doc["unique_research_selections"],"research choices,",
          doc["upcoming_research_selections"],"observed upcoming,",
          doc["paper_summary"]["settled"],"verified paper settlements. 0 real bets.")

if __name__=="__main__":main()
