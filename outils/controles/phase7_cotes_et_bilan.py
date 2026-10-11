"""Phase 7: strict PulseScore price provenance and independent settled paper audit.
Read-only: no authenticated calls, order placement, SQL parity, or invented EV.
"""
from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path

V="revue_phase7_price_integrity_v1"
BOOKS={"betclic_fr","winamax_fr","unibet_fr","pmu_fr"}
SETTLED={"won","lost","push"}
LEAD=timedelta(minutes=20)
MAX_LOCK_QUOTE_AGE=timedelta(minutes=30)

def dt(x):
    if not isinstance(x,str):raise ValueError("Missing timestamp")
    try:t=datetime.fromisoformat(x.replace("Z","+00:00"))
    except ValueError as err:raise ValueError("Bad timestamp") from err
    if t.tzinfo is None:raise ValueError("Timestamp missing timezone")
    return t.astimezone(timezone.utc)

def number(x,lo,hi):
    return type(x) in (float,int) and math.isfinite(x) and lo<=x<=hi

def sources(radar,now):
    if (radar.get("version")!="revue_pulsescore_six_hour_radar_v1"
        or radar.get("status")!="observed"
        or radar.get("provider")!="PulseScore"
        or radar.get("market_prices_are_live") is not False
        or radar.get("positive_ev_verified") is not False
        or radar.get("model_is_calibrated") is not False
        or radar.get("real_bets_enabled") is not False):
        raise ValueError("Invalid PulseScore source or unsafe live-price claim")
    observed=dt(radar["generated_at_utc"])
    if observed>now+timedelta(minutes=2):raise ValueError("Future radar")
    events=radar.get("observations") or []
    if len(events)!=radar.get("matches_observed"):raise ValueError("Radar events count mismatch")
    by_event={};market_rows=0;book_rows=Counter();periods=Counter();kinds=Counter();timestamps=Counter()
    for event in events:
        league=event.get("league")
        if league=="CFB":continue
        key=str(league)+":"+str(event.get("event_id"))
        if key in by_event:raise ValueError("Duplicate radar fixture")
        if (not event.get("home") or not event.get("away")
            or event["home"]==event["away"]):
            raise ValueError("Radar missing teams")
        kickoff=dt(event["start_utc"])
        by_event[key]=event
        seen=set()
        for book in event.get("bookmakers") or []:
            bookmaker=book.get("bookmaker")
            if bookmaker not in BOOKS:raise ValueError("Unsupported bookmaker")
            for market in book.get("markets") or []:
                kind=market.get("market")
                if kind not in ("h2h","totals"):raise ValueError("Unexpected market")
                quote=dt(market["quote_at"])
                if quote>observed+timedelta(minutes=2) or quote>kickoff-LEAD:
                    raise ValueError("Post-start or future quote")
                origin=market.get("quote_time_source")
                if origin not in ("provider","fetch_observation","last_update"):
                    raise ValueError("Quote without observation provenance")
                selections=market.get("outcomes") or []
                if not selections:raise ValueError("Missing selections")
                for pick in selections:
                    side=pick.get("selection");line=pick.get("line")
                    if side not in ("home","away","draw","over","under"):
                        raise ValueError("Unknown selection")
                    if not number(pick.get("price"),1.00001,1000):
                        raise ValueError("Invalid decimal odds")
                    if kind=="totals" and (side not in ("over","under") or not number(line,0,500)):
                        raise ValueError("Malformed total")
                    if kind=="h2h" and (side not in ("home","away","draw") or line is not None):
                        raise ValueError("Malformed moneyline")
                    sig=(bookmaker,kind,side,line)
                    if sig in seen:raise ValueError("Duplicate selection in bookmaker quote")
                    seen.add(sig)
                market_rows+=1;book_rows[bookmaker]+=1;kinds[kind]+=1
                periods[market.get("period_rule") or "unspecified"]+=1
                timestamps[origin]+=1
    if market_rows!=radar.get("market_rows_observed"):raise ValueError("Market count mismatch")
    summary={"observed_at_utc":observed.isoformat(),
             "age_minutes":round((now-observed).total_seconds()/60,1),
             "fixtures":len(by_event),"market_rows":market_rows,
             "market_rows_by_kind":dict(kinds),
             "market_rows_by_bookmaker":dict(book_rows),
             "bookmakers_observed":sorted(book_rows),
             "bookmakers_supported":sorted(BOOKS),
             "bookmakers_without_quotes":sorted(BOOKS-set(book_rows)),
             "period_rules":dict(periods),
             "quote_timestamp_source":dict(timestamps),
             "bookability_verified":False}
    return by_event,summary

def exact_quotes(record,event):
    market=("h2h" if record["market"]=="two_way_moneyline_unverified_period"
            else "totals" if record["market"]=="nhl_total_unverified_period" else None)
    if market is None:return []
    selected=[]
    for book in event.get("bookmakers") or []:
        for group in book.get("markets") or []:
            if group.get("market")!=market:continue
            outcomes=group.get("outcomes") or []
            options=[o for o in outcomes if o.get("selection")==record["side"]
                     and (market=="h2h" or o.get("line")==record.get("line"))]
            if len(options)!=1:continue
            if market=="totals":
                complementary=[o for o in outcomes if o.get("line")==record.get("line")
                               and o.get("selection") in ("over","under")]
                if len(complementary)!=2 or {o["selection"] for o in complementary}!={"over","under"}:
                    continue
            elif set(o.get("selection") for o in outcomes) not in ({"home","away"},{"home","draw","away"}):
                continue
            selected.append({
                "bookmaker":book["bookmaker"],
                "decimal_odds":options[0]["price"],
                "quote_at_utc":group["quote_at"],
                "period_rule":group.get("period_rule"),
                "rule_proven_by_provider":group.get("period_rule_source")=="provider_verified"})
    return selected

def compare_locks(ledger,market_events,now):
    if ledger.get("version")!="revue_phase6_pregame_source_predictions_v1":
        raise ValueError("Not Phase6 source observations")
    if not isinstance(ledger.get("entries"),dict):raise ValueError("Missing prospective entries")
    rows=[];counts=Counter();total_quotes=0
    for key,pred in sorted(ledger["entries"].items()):
        if (key!=pred.get("id") or pred.get("source_model_lock_proven") is not False
            or pred.get("original_sql_identical") is not False
            or pred.get("same_market_rules_verified") is not False
            or pred.get("real_bet") is not False):
            raise ValueError("Tampered source forecast")
        lock,kick=dt(pred["locked_at_utc"]),dt(pred["kickoff_utc"])
        if lock>kick-LEAD or lock>now+timedelta(minutes=2):
            raise ValueError("Late source forecast")
        event=market_events.get(pred["league"]+":"+str(pred["event_id"]))
        matches=[]
        if event is None:state="no_same_event_quote"
        elif (pred["home"]!=event["home"] or pred["away"]!=event["away"]
              or abs((kick-dt(event["start_utc"])).total_seconds())>300):
            state="fixture_identity_or_start_differs"
        else:
            matches=exact_quotes(pred,event);total_quotes+=len(matches)
            if not matches:state="no_identical_selection_and_line"
            else:
                # A quote before an observed lock cannot certify a market
                # price at lock unless its observation is sufficiently recent.
                # The archived feed does not certify the quote is bookable.
                contemporaneous=[q for q in matches
                    if lock-MAX_LOCK_QUOTE_AGE<=dt(q["quote_at_utc"])<=lock]
                verified=[q for q in contemporaneous if q["rule_proven_by_provider"]
                          and q["period_rule"] in ("including_ot_confirmed","90min")]
                if not contemporaneous:state="quote_not_observed_near_lock"
                elif not verified:state="unverified_bookmaker_market_period"
                else:state="historical_period_and_time_consistent_not_live"
        counts[state]+=1
        archived=max(matches,key=lambda q:q["decimal_odds"]) if matches else None
        rows.append({
            "phase6_selection_id":key,
            "league":pred["league"],"event_id":str(pred["event_id"]),
            "market":pred["market"],"side":pred["side"],"line":pred.get("line"),
            "source_original_probability":pred["original_probability"],
            "revue_comparison_probability":pred.get("revue_probability"),
            "status":state,"matching_quotes":len(matches),
            "best_historical_quote":({
                "bookmaker":archived["bookmaker"],
                "decimal_odds":archived["decimal_odds"],
                "quote_at_utc":archived["quote_at_utc"],
                "not_a_bookable_offer":True} if archived else None),
            "verified_positive_ev":False,
            "automatic_real_bet":False})
    return rows,{
        "source_predictions_checked":len(rows),
        "same_selection_historical_market_rows":total_quotes,
        "source_selections_with_exact_archived_prices":sum(r["matching_quotes"]>0 for r in rows),
        "verified_bookable_market_prices":0,
        "verified_positive_ev":0,
        "statuses":dict(counts)}

def audit_paper(doc):
    if (doc.get("status")!="revue_independent_picks_hub_static_research_paper_only"
        or doc.get("real_bets_enabled") is not False
        or doc.get("research_model_calibrated") is not False
        or doc.get("verified_real_ev") is not False
        or doc.get("live_bookmaker_prices") is not False):
        raise ValueError("Paper hub claims unverified calibration")
    records=doc.get("paper_records")
    if not isinstance(records,list):raise ValueError("Missing graded paper archive")
    seen=set();counts=Counter();net=stake_total=0;by_market=defaultdict(lambda:[0.,0.,0])
    for row in records:
        rid=row.get("id")
        if not isinstance(rid,str) or not rid or rid in seen:raise ValueError("Duplicate paper bet")
        seen.add(rid)
        if row.get("real_bet") is not False:raise ValueError("Real bet mixed with paper")
        status=row.get("status")
        if status not in ("won","lost","push","pending","unverified"):
            raise ValueError("Unknown paper result")
        kickoff,lock,quote=(dt(row[n]) for n in ("start_utc","locked_at_utc","quote_at_utc"))
        if not quote<=lock<=kickoff-LEAD:raise ValueError("Paper timestamp chronology invalid")
        if not number(row.get("decimal_odds"),1.00001,1000) or not number(row.get("paper_stake_units"),.00001,1000):
            raise ValueError("Invalid paper odds/stake")
        pnl=row.get("paper_profit_units");units=row["paper_stake_units"]
        if status in SETTLED:
            if row.get("verified_pregame") is not True:raise ValueError("Paper result has no pregame lock")
            correct=units*(row["decimal_odds"]-1) if status=="won" else -units if status=="lost" else 0.
            if not number(pnl,-10000,100000) or abs(pnl-correct)>.011:
                raise ValueError("Paper payout not computed from frozen quote")
            net+=pnl;stake_total+=units
            vals=by_market[row["market"]];vals[0]+=pnl;vals[1]+=units;vals[2]+=1
        elif pnl is not None:raise ValueError("Non-settled paper has fictitious profit")
        if status=="unverified" and not row.get("exclusion_reason"):
            raise ValueError("Unverified paper market lacks exclusion")
        counts[status]+=1
    existing=doc.get("paper_summary") or {}
    if (existing.get("total")!=len(records) or
        existing.get("settled")!=sum(counts[s] for s in SETTLED) or
        existing.get("pending")!=counts["pending"] or
        existing.get("excluded")!=counts["unverified"] or
        abs(existing.get("paper_profit_units",float("inf"))-net)>.011):
        raise ValueError("Paper summary differs from individually settled bets")
    return {
        "total":len(records),"settled":sum(counts[s] for s in SETTLED),
        "wins":counts["won"],"losses":counts["lost"],"pushes":counts["push"],
        "pending":counts["pending"],"excluded_unverified":counts["unverified"],
        "net_paper_units":round(net,2),"settled_stakes_units":round(stake_total,2),
        "paper_roi_settled_only_pct":round(100*net/stake_total,2) if stake_total else None,
        "markets":{m:{"settled":int(v[2]),"profit_units":round(v[0],2),
                      "roi_pct":round(100*v[0]/v[1],2)} for m,v in by_market.items()},
        "sample_under_100_settled":sum(counts[s] for s in SETTLED)<100,
        "profitable_strategy_proven":False,"realized_personal_profit":False,
        "origin":"Revue independent settled paper bets, NOT source Clairvoyance history"}

def build(radar,phase6,picks,now):
    if now.tzinfo is None:raise ValueError("UTC aware clock required")
    now=now.astimezone(timezone.utc)
    byevent,quotes=sources(radar,now)
    rows,join=compare_locks(phase6,byevent,now)
    paper=audit_paper(picks)
    return {
        "version":V,"generated_at_utc":now.isoformat(),
        "status":"observed_quote_provenance_and_separate_paper_audit_only",
        "quote_sources":quotes,"phase6_join":join,"paper_performance":paper,
        "compared_source_selections":rows,
        "verified_live_quotes":False,"verified_positive_EV_opportunities":0,
        "bookmaker_period_rules_verified":False,
        "source_model_predictions_calibrated":False,"profitable_strategy_proven":False,
        "no_paid_api_requests":True,"no_retroactive_bets":True,
        "real_bets_enabled":False,"source_paper_ledgers_modified":False,
        "CFB_excluded":True,
        "disclaimer":"Archived PulseScore bookmaker observations have no verified current bookability. Real decision time/market rules/model calibration remain unverified. Paper ROI is small-sample virtual performance of Revue, never actual profit."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--radar",default="docs/pulsescore-radar-latest.json")
    p.add_argument("--source-picks",default="docs/phase6-pregame-ledger.json")
    p.add_argument("--paper",default="docs/picks-center-latest.json")
    p.add_argument("--output",default="docs/phase7-prices-performance-latest.json")
    args=p.parse_args()
    docs=[json.loads(Path(f).read_text(encoding="utf-8")) for f in
          (args.radar,args.source_picks,args.paper)]
    report=build(*docs,datetime.now(timezone.utc))
    destination=Path(args.output);destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Phase7:",report["quote_sources"]["market_rows"],"price markets",
          report["phase6_join"]["source_selections_with_exact_archived_prices"],"historic matches",
          report["paper_performance"]["settled"],"settled paper bets; no real EV")

if __name__=="__main__":main()
