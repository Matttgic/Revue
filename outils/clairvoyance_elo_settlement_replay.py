#!/usr/bin/env python3
"""Audit and *independent* Elo reconstruction matching Clairvoyance settlement rules.

Clairvoyance app/services/settlement.py calls its Elo updater only after a
PENDING moneyline pick is settled. A replay of EVERY NHL final, or a team power
rating from standings, cannot replicate that private SQL state.

This script replays only qualified, already-settled Revue paper moneylines for
NHL/MLB as a non-production DIAGNOSTIC, not Clairvoyance's private pick ledger.
It never changes the locked paper records or publishes betting predictions.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path

from outils.revue_engine_v2 import timestamp, verified_pre_match

SOURCE_DEFAULT = 1500.0
SOURCE_K = 32.0
REF = "Purple-Wraith/clairvoyance-backend:app/services/settlement.py + app/services/elo.py"
VERSION = "revue_elo_settlement_only_source_semantics_v1"
ALLOWED = {"NHL", "MLB"}
MIN_POST_GAME = timedelta(minutes=45)


def _time(x):
    try:
        return timestamp(x)
    except (ValueError, TypeError):
        return None


def eligible(row: dict, now: datetime) -> tuple[bool, str]:
    if not isinstance(row,dict):
        return False, "malformed"
    if row.get("league") not in ALLOWED:
        return False, "not_nhl_or_mlb"
    if row.get("market") != "h2h":
        return False, "not_moneyline"
    if row.get("status") not in ("won","lost"):
        return False, "not_verified_settled_moneyline"
    if row.get("market_rule_verified") is not True or not verified_pre_match(row):
        return False, "pregame_or_market_rule_unverified"
    if row.get("side") not in ("home","away"):
        return False, "not_two_way_moneyline"
    if row.get("settlement_source") not in (
        "ESPN observed final, league and fixture identity verified",
        "NHL official final"):
        return False, "official_score_provenance_unknown"
    if not isinstance(row.get("event_id"),(int,str)) or not str(row["event_id"]).isdigit():
        return False, "invalid_fixture_id"
    home,away=row.get("home"),row.get("away")
    if (not isinstance(home,str) or not isinstance(away,str) or
        home==away or not home or not away):
        return False, "invalid_teams"
    start,settle=_time(row.get("start_utc")),_time(row.get("settled_at"))
    if start is None or settle is None or settle<start+MIN_POST_GAME or settle>now:
        return False, "invalid_score_chronology"
    scored=row.get("score")
    if not isinstance(scored,dict):
        return False, "no_verified_final_score"
    x,y=scored.get("home"),scored.get("away")
    if (type(x) not in (int,float) or type(y) not in (int,float)
        or not math.isfinite(x) or not math.isfinite(y)
        or x<0 or y<0 or x!=int(x) or y!=int(y) or x==y
        or x>100 or y>100):
        return False, "invalid_score"
    selected_home=row["side"]=="home"
    selected_won=(x>y) if selected_home else (y>x)
    if (row["status"]=="won")!=selected_won:
        return False, "recorded_result_conflicts_score"
    return True, "qualified_settled_moneyline"


def update_pair(winner:float,loser:float)->tuple[float,float]:
    """Same per-settlement Elo algorithm as public source (checked on CI).

    No home bonus applies at settlement. Rounding to cents per update matters.
    """
    for x in (winner,loser):
        if type(x) not in (int,float) or not math.isfinite(x):
            raise ValueError("Invalid Elo")
    exp=1/(1+10**((loser-winner)/400))
    return (round(winner+SOURCE_K*(1-exp),2),
            round(loser-SOURCE_K*exp,2))


def reconstruct(ledger:dict,now:datetime)->dict:
    if now.tzinfo is None:
        raise ValueError("Timezone aware cutoff required")
    now=now.astimezone(timezone.utc)
    if ledger.get("version")!=1 or not isinstance(ledger.get("bets"),list):
        raise ValueError("Untrusted paper ledger schema")
    used=[]
    skipped=Counter()
    ids=set()
    for bet in ledger["bets"]:
        good,why=eligible(bet,now)
        if not good:
            skipped[why]+=1
            continue
        ident=bet.get("id")
        if not isinstance(ident,str) or ident in ids:
            raise ValueError("Duplicate or missing settled paper identifier")
        ids.add(ident)
        used.append(bet)
    # The original SQL settlement ordering is unavailable. Sorting by
    # settlement timestamp is a deterministic *Revue* replay, not SQL parity.
    used.sort(key=lambda x:(_time(x["settled_at"]),str(x["id"])))
    elo=defaultdict(lambda:SOURCE_DEFAULT)
    counts=Counter()
    events=Counter()
    history=[]
    for b in used:
        sport=b["league"]
        score=b["score"]
        winner=b["home"] if score["home"]>score["away"] else b["away"]
        loser=b["away"] if winner==b["home"] else b["home"]
        wkey,lkey=(sport,winner),(sport,loser)
        oldw,oldl=elo[wkey],elo[lkey]
        w,l=update_pair(oldw,oldl)
        elo[wkey],elo[lkey]=w,l
        counts[wkey]+=1;counts[lkey]+=1
        eid=(sport,str(b["event_id"]))
        events[eid]+=1
        history.append({
            "league":sport,"event_id":str(b["event_id"]),
            "paper_lock_id":b["id"],"settled_at_utc":_time(b["settled_at"]).isoformat(),
            "winner":winner,"loser":loser,
            "winner_rating_before":oldw,"loser_rating_before":oldl,
            "winner_rating_after":w,"loser_rating_after":l,
            "verified_official_score":True,
            "identical_original_sql_rating":False,
        })
    by_sport={}
    for sport in sorted(ALLOWED):
        by_sport[sport]={
            "settled_paper_moneyline_updates":sum(b["league"]==sport for b in used),
            "teams_with_updates":sum(s==sport for s,_ in elo),
            "ratings":{
                team:{"rating":rating,"qualified_settlements":counts[(sport,team)]}
                for (s,team),rating in sorted(elo.items()) if s==sport
            }
        }
    duplicated=[f"{lg}:{eid}" for (lg,eid),num in events.items() if num>1]
    return {
        "version":VERSION,"generated_at_utc":now.isoformat(),
        "reference":REF,
        "reference_initial_elo":SOURCE_DEFAULT,
        "reference_k_factor":SOURCE_K,
        "updates_only_on_settled_moneyline_picks":True,
        "updates_every_completed_nhl_game":False,
        "zero_home_bonus_during_elo_update":True,
        "reproduced_math_not_original_elo_database":True,
        "original_sql_elo_values_available":False,
        "identical_original_settled_pick_history_verified":False,
        "original_sql_ordering_verified":False,
        "source_backend_model_is_published_public_best_bet_model_verified":False,
        "real_bets_enabled":False,
        "paper_ledger_modified":False,
        "no_backfilled_picks":True,
        "eligible_revue_settled_moneyline_updates":len(used),
        "duplicate_event_updates":duplicated,
        "rejected_entries":dict(skipped),
        "by_sport":by_sport,
        "update_audit":history,
        "status":"source_elo_update_math_verified_private_state_unknown",
        "note":"Clairvoyance SQL updates Elo after each settled moneyline PICK, not every game. Revue's separately sourced settled-paper subset cannot recover source SQL: original picks, settlement order, starting SQL values and DB history are unknown. Zero verified Revue NHL updates is an honest empty simulation, not default Elo proof.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args=parser.parse_args()
    root=Path(args.docs)
    bets=json.loads((root/"engine-v2-ledger.json").read_text("utf8"))
    outcome=reconstruct(bets,datetime.now(timezone.utc))
    (root/"clairvoyance-elo-source-audit.json").write_text(
        json.dumps(outcome,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
        encoding="utf8")
    print("Source-style Elo settlement:",outcome["eligible_revue_settled_moneyline_updates"],
          "verified Revue updates, SQL identity UNVERIFIED; no fake bets.")


if __name__=="__main__":
    main()
