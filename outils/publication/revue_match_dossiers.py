"""Independent, source-audited per-game dossiers for Revue's personal Match Center.

Only existing timestamped public Revue JSON snapshots are used.
No bookmaker/API calls, SQL clone, prediction re-calculation, retroactive
settlement, confirmed NHL lineup, source-model parity or real bet.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,json,math

CUT_OFF=timedelta(minutes=20)
MAX_QUOTES_PER_GAME=60
MAX_TOTAL_LINES=180

def instant(value):
    if not isinstance(value,str):raise ValueError("Missing source timestamp")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Naive source timestamp")
    return t.astimezone(timezone.utc)

def price(value):
    return type(value) in (int,float) and math.isfinite(value) and 1<float(value)<=1000

def score(value):
    return type(value) in (int,float) and math.isfinite(value) and 0<=value<=500 and float(value).is_integer()

def history_index(doc,asof):
    if doc.get("version")!=1 or not isinstance(doc.get("leagues"),dict):
        raise ValueError("Unverified Revue ESPN historical result version")
    db=defaultdict(list)
    ids=set()
    for league,body in doc["leagues"].items():
        if league=="CFB" or not isinstance(body,dict):
            continue
        for row in body.get("events",[]):
            if row.get("complete") is not True:continue
            home,away=row.get("home"),row.get("away")
            hs,aws=row.get("home_score"),row.get("away_score")
            eid=str(row.get("id",""))
            start=instant(row.get("start"))
            if (not isinstance(home,str) or not isinstance(away,str) or not home
                or not away or home==away or not score(hs) or not score(aws)
                or not eid.isdecimal()):
                continue
            if start>=asof:
                # Do not infer completion of future events from untrusted feed.
                continue
            key=(league,eid)
            if key in ids:raise ValueError("Duplicate completed ESPN history ID")
            ids.add(key)
            item={"event_id":eid,"league":league,"home":home,"away":away,
                  "start_utc":start.isoformat(),"home_score":int(hs),"away_score":int(aws),
                  "source":"Revue stored ESPN historical results"}
            db[(league,home)].append(item)
            db[(league,away)].append(item)
    for rows in db.values():rows.sort(key=lambda e:(e["start_utc"],e["event_id"]),reverse=True)
    return db, len(ids)

def form_for(index,league,team,asof,start):
    # Descriptive results available in current archive, NOT frozen pre-match.
    items=[x for x in index.get((league,team),[]) if instant(x["start_utc"])<min(asof,start)][:5]
    results=[];wins=draws=losses=pf=pa=0
    for x in items:
        home=team==x["home"]
        scored=x["home_score"] if home else x["away_score"]
        conceded=x["away_score"] if home else x["home_score"]
        label="W" if scored>conceded else "D" if scored==conceded else "L"
        wins+=label=="W";draws+=label=="D";losses+=label=="L"
        pf+=scored;pa+=conceded
        results.append({**x,"side":"home" if home else "away","team_score":scored,
                        "opponent_score":conceded,"outcome":label,
                        "opponent":x["away"] if home else x["home"]})
    return {"team":team,"games":len(items),"wins":wins,"draws":draws,"losses":losses,
            "scored":pf,"conceded":pa,"recent":results,
            "is_point_in_time_feature":False,
            "not_pre_game_verified":True,
            "interpretation":"Descriptive completed ESPN results now in archive; no historic feed snapshot proof"}

def make_market_view(event,start):
    raw=[];comparables=defaultdict(list);invalid=0;seen=set()
    quotes=(event.get("quotes") or [])
    totals=(event.get("totals_quotes") or [])
    if not isinstance(quotes,list) or not isinstance(totals,list):
        raise ValueError("Malformed bookmaker feed")
    if len(quotes)>MAX_QUOTES_PER_GAME or len(totals)>MAX_QUOTES_PER_GAME:
        raise ValueError("Too many source quotes per fixture")
    for obj in quotes:
        if not isinstance(obj,dict):invalid+=1;continue
        book=obj.get("bookmaker")
        if not isinstance(book,str) or not book.endswith("_fr") or book=="_fr":
            invalid+=1;continue
        try:quoted=instant(obj.get("quote_at_utc"))
        except (ValueError,TypeError):invalid+=1;continue
        if quoted>start-CUT_OFF:
            invalid+=1;continue
        rule=obj.get("rule")
        if not isinstance(rule,str) or not rule or obj.get("market")!="h2h":
            invalid+=1;continue
        outcomes=obj.get("outcomes")
        if not isinstance(outcomes,dict) or not {"home","away"}<=set(outcomes):
            invalid+=1;continue
        keys=("home","draw","away") if "draw" in outcomes else ("home","away")
        if any(not price(outcomes[k]) for k in keys):
            invalid+=1;continue
        duplicate=("h2h",rule,book)
        if duplicate in seen:invalid+=1;continue
        seen.add(duplicate)
        overround=round(sum(1/float(outcomes[k]) for k in keys)-1,6)
        item={"market":"h2h","rule":rule,"bookmaker":book,
              "quote_at_utc":quoted.isoformat(),
              "rule_verified":obj.get("rule_verified") is True,
              "outcomes":{k:float(outcomes[k]) for k in keys},
              "book_overround_pct":round(overround*100,2),
              "selection_count":len(keys),"historical_not_live":True}
        raw.append(item)
        if item["rule_verified"]:
            comparables[("h2h",rule,keys)].append(item)
    for obj in totals:
        if not isinstance(obj,dict):invalid+=1;continue
        book=obj.get("bookmaker")
        if not isinstance(book,str) or not book.endswith("_fr") or book=="_fr" or obj.get("market")!="totals":
            invalid+=1;continue
        try:quoted=instant(obj.get("quote_at_utc"))
        except (ValueError,TypeError):invalid+=1;continue
        if quoted>start-CUT_OFF:invalid+=1;continue
        rule=obj.get("rule")
        if not isinstance(rule,str) or not rule or not isinstance(obj.get("lines"),list):
            invalid+=1;continue
        for obj_line in obj["lines"][:MAX_TOTAL_LINES]:
            line=obj_line.get("line")
            over=obj_line.get("over");under=obj_line.get("under")
            if (type(line) not in (int,float) or not math.isfinite(line)
                or not 0<float(line)<=100 or not price(over) or not price(under)):
                invalid+=1;continue
            key=("totals",rule,book,float(line))
            if key in seen:invalid+=1;continue
            seen.add(key)
            item={"market":"totals","rule":rule,"bookmaker":book,
                  "quote_at_utc":quoted.isoformat(),
                  "rule_verified":obj.get("rule_verified") is True,
                  "line":float(line),"outcomes":{"over":float(over),"under":float(under)},
                  "book_overround_pct":round(100*(1/float(over)+1/float(under)-1),2),
                  "historical_not_live":True}
            raw.append(item)
            if item["rule_verified"]:
                comparables[("totals",rule,float(line))].append(item)
    groups=[]
    for key,items in sorted(comparables.items(),key=lambda x:str(x[0])):
        outcome_names=("home","draw","away") if key[0]=="h2h" and len(key[2])==3 else (
            ("home","away") if key[0]=="h2h" else ("over","under"))
        if key[0]=="h2h" and key[2]!=outcome_names:
            # Different outcome universes are never pooled.
            continue
        best={}
        for outcome in outcome_names:
            matching=[(x["outcomes"][outcome],x) for x in items if outcome in x["outcomes"]]
            if matching:
                val,selected=max(matching,key=lambda v:(v[0],v[1]["quote_at_utc"]))
                best[outcome]={"price":val,"bookmaker":selected["bookmaker"],
                                "quote_at_utc":selected["quote_at_utc"]}
        groups.append({"market":key[0],"rule":key[1],
                       "line":key[2] if key[0]=="totals" else None,
                       "outcomes":list(outcome_names),"books_compared":len(items),
                       "best_observed_prices":best,
                       "no_arbitrage_or_ev_claim":True})
    raw.sort(key=lambda v:(v["market"],v["rule"],str(v.get("line","")),v["bookmaker"]))
    return {"observations":raw,"market_groups":groups,"invalid_quote_count":invalid,
            "verified_comparable_groups":len(groups),
            "source_note":"Historical FR bookmaker quotes only; market rules must match; no EV, no live availability"}

def compile_dossiers(center,history,ledger,asof):
    if asof.tzinfo is None:raise ValueError("Timestamp without timezone")
    asof=asof.astimezone(timezone.utc)
    if (center.get("status")!="experimental_revue_match_center" or
        center.get("real_bets_enabled") is not False or
        center.get("bookmaker_prices_are_live") is not False or
        center.get("validated_value_bets")!=0 or
        not isinstance(center.get("events"),list)):
        raise ValueError("Match source provenance unverified")
    timestamp=instant(center.get("generated_at_utc"))
    if timestamp>asof+timedelta(minutes=2):
        raise ValueError("Future Match Center snapshot")
    if (ledger.get("version")!="revue_multisport_pre_match_v1" or not isinstance(ledger.get("events"),list)):
        raise ValueError("Unsupported prospective ledger")
    hist,n_finals=history_index(history,asof)
    locked={}
    for row in ledger["events"]:
        if row.get("league")=="CFB":continue
        key=str(row.get("key"))
        if key in locked:raise ValueError("Duplicate original paper forecast key")
        locked[key]=row
    entries=[];seen=set()
    for row in center["events"]:
        league=row.get("league");eid=str(row.get("event_id",""))
        if (not isinstance(league,str) or not league or league=="CFB"
            or not eid.isdecimal()):
            # Specific exclusions (e.g. UFC ids include nonnumeric event IDs)
            # are reported rather than silently misrepresented.
            if league=="CFB":continue
            if not eid.isdecimal():
                # Stable UFC odds identifiers may contain a hyphen; a key is
                # safe if nonempty and no query fragments or URL separators.
                if not eid or len(eid)>100 or not all(c.isalnum() or c in "-_:" for c in eid):
                    raise ValueError("Invalid nonnumeric sports event ID")
        key=league+":"+eid
        if key in seen:raise ValueError("Duplicate match-center event ID")
        seen.add(key)
        start=instant(row["start_utc"])
        home,away=row.get("home"),row.get("away")
        if not isinstance(home,str) or not isinstance(away,str) or not home or not away or home==away:
            raise ValueError("Malformed match teams")
        selected=[]
        for model in row.get("research") or []:
            if not isinstance(model,dict):raise ValueError("Malformed research model")
            # Historical / indicative, not a pregame locked research forecast.
            selected.append({"id":model.get("id"),"label":model.get("label"),
                             "probabilities":model.get("probabilities",{}),
                             "source_generated_utc":model.get("source_generated_utc"),
                             "calibrated":model.get("calibrated") is True,
                             "is_verified_future_pre_game_output":False})
        paper=locked.get(key)
        locked_output=None
        if paper is not None:
            try:
                valid=(paper.get("league")==league and str(paper.get("event_id"))==eid
                       and paper.get("home")==home and paper.get("away")==away
                       and instant(paper.get("kickoff_utc"))==start
                       and instant(paper.get("locked_at_utc"))<=start-CUT_OFF
                       and paper.get("real_bet") is False and paper.get("staked_units")==0)
                # No future source feature may be introduced after the lock.
                for model in (paper.get("models") or {}).values():
                    if instant(model.get("source_generated_utc"))>instant(paper["locked_at_utc"]):
                        valid=False
            except (ValueError,TypeError,KeyError):
                valid=False
            if valid:
                locked_output={"status":paper.get("status"),"locked_at_utc":paper["locked_at_utc"],
                    "models":paper["models"],
                    "official_result_if_verified":paper.get("result") if paper.get("status")=="settled" else None,
                    "score_if_settled":paper.get("score") if paper.get("status")=="settled" else None,
                    "not_a_real_bet":True}
        markets=make_market_view(row,start)
        players=[]
        for athlete in row.get("player_profiles") or []:
            if athlete.get("lineup_status")=="confirmed":
                # This source has no independently confirmed starters.
                raise ValueError("Unexpected confirmed NHL lineup")
            players.append({"name":athlete.get("name"),"team":athlete.get("team"),
                            "games_current":athlete.get("season_games_current"),
                            "probabilities":athlete.get("probabilities"),
                            "lineup_confirmed":False,"research_only":True})
        entries.append({"key":key,"league":league,"event_id":eid,"sport":row.get("sport"),
            "home":home,"away":away,"start_utc":start.isoformat(),
            "source_match_center_at_utc":timestamp.isoformat(),
            "home_history":form_for(hist,league,home,asof,start),
            "away_history":form_for(hist,league,away,asof,start),
            "historical_odds":markets,"research_models":selected,
            "historical_player_profiles":players,
            "locked_forecast":locked_output,
            "no_real_betting":True,"exact_clairvoyance_source_equivalence":False})
    entries.sort(key=lambda x:(x["start_utc"],x["league"],x["event_id"]))
    return {"generated_at_utc":asof.isoformat(),
        "status":"source_audited_static_match_dossiers_not_live",
        "source_match_center_at_utc":timestamp.isoformat(),
        "source_history_as_of_utc":asof.isoformat(),
        "historical_data_not_point_in_time_forecasts":True,
        "real_bets_enabled":False,"original_clairvoyance_equivalence_verified":False,
        "bookmaker_prices_are_live":False,"validated_value_bets":0,
        "source":"Revue Match Center, stored ESPN finals and Revue frozen prospective ledger",
        "count":len(entries),"historical_finals_in_available_archive":n_finals,
        "with_observed_prices":sum(bool(x["historical_odds"]["observations"]) for x in entries),
        "with_comparable_markets":sum(bool(x["historical_odds"]["market_groups"]) for x in entries),
        "with_locked_forecasts":sum(x["locked_forecast"] is not None for x in entries),
        "with_descriptive_team_history":sum(
            x["home_history"]["games"]>0 or x["away_history"]["games"]>0 for x in entries),
        "games":entries,
        "disclaimer":"Source-observed odds are snapshots not live, uncalibrated research models do not justify bets, descriptive ESPN results are not historical pregame features; no original SQL or model predictions are claimed identical."}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--docs",default="docs");cli.add_argument("--output",default="docs/match-dossiers-latest.json")
    args=cli.parse_args();root=Path(args.docs)
    def read(n):return json.loads((root/n).read_text(encoding="utf-8"))
    doc=compile_dossiers(read("match-center-latest.json"),read("multisports-history.json"),
                         read("multisport-prospective-ledger.json"),datetime.now(timezone.utc))
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Verified match dossiers:",doc["count"],"market groups",doc["with_comparable_markets"],
          "historical team form",doc["with_descriptive_team_history"],
          "no external API calls or real bets.")

if __name__=="__main__":main()
