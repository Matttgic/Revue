#!/usr/bin/env python3
"""Read-only NHL published GOALIE observation comparison against public Clairvoyance.

Source docs/nhl_schedule.json (ESPN game ids), Revue ESPN goalie observations
(official NHL game ids). Join with both team codes and UTC kickoff, not IDs.
Names and projected/confirmed statuses are separate observations: a later
confirmation is not a source mismatch or proof the goalie actually started.

Neither reference schedule nor copyrighted source artifacts are redistributed.
"""
from __future__ import annotations
import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import urlopen,Request

URL="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/main/docs/nhl_schedule.json"
VERSION="revue_nhl_public_espn_goalie_parity_v1"
MAX_SNAPSHOT_AGE=timedelta(hours=24)
MATCH_TIME=timedelta(minutes=10)


def utc(value):
    if not isinstance(value,str):raise ValueError("Missing timestamp")
    if value.endswith(" UTC"):
        val=datetime.strptime(value,"%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
    else:
        val=datetime.fromisoformat(value.replace("Z","+00:00"))
    if val.tzinfo is None:raise ValueError("Naive timestamp")
    return val.astimezone(timezone.utc)


def name_key(value):
    if not isinstance(value,str):return ""
    decomposed=unicodedata.normalize("NFKD",value)
    return re.sub(r"[^a-z]","", "".join(c for c in decomposed if not unicodedata.combining(c)).lower())


def compare(reference:dict,observed:dict,now:datetime)->dict:
    if now.tzinfo is None:raise ValueError("Aware comparison time required")
    now=now.astimezone(timezone.utc)
    src_time=utc(reference["generated_at"])
    dst_time=utc(observed["generated_at_utc"])
    if any(t>now+timedelta(minutes=2) or now-t>MAX_SNAPSHOT_AGE
           for t in (src_time,dst_time)):
        raise ValueError("Published goalie snapshots are stale or future dated")
    if (observed.get("status")!="espn_probable_goalies_observed_not_part_of_model"
        or observed.get("source")!="ESPN NHL scoreboard, separate from official NHL IDs"
        or observed.get("real_bets_enabled") is not False
        or observed.get("used_in_prediction_model") is not False
        or not isinstance(observed.get("rows"),list)
        or not isinstance(reference.get("games"),list)):
        raise ValueError("Unsupported goalie report provenance")
    if len(reference["games"])<100:
        raise ValueError("Reference schedule incomplete")
    reference_index={}
    reference_duplicates=set()
    for game in reference["games"]:
        try:
            start=utc(game["date"])
            home,away=game["home"],game["away"]
            if not all(isinstance(x,str) and 2<=len(x)<=4 for x in (home,away)):
                continue
            key=(home,away)
            reference_index.setdefault(key,[]).append((start,game))
        except (KeyError,TypeError,ValueError):
            continue
    seen=set()
    diagnostics=Counter()
    rows=[]
    for actual in observed["rows"]:
        if not isinstance(actual,dict):continue
        game_id=str(actual.get("event_id") or "")
        if game_id in seen:
            raise ValueError("Duplicate Revue official NHL game IDs")
        seen.add(game_id)
        try:
            start=utc(actual["start_utc"])
            observed_at=utc(actual["observed_at_utc"])
            if observed_at>dst_time+timedelta(minutes=2):
                raise ValueError("Future goalie status date after published snapshot")
            home,away=actual["home"],actual["away"]
        except (KeyError,ValueError,TypeError):
            diagnostics["invalid_revue_observation"]+=1
            continue
        eligible=[g for when,g in reference_index.get((home,away),[])
                  if abs(when-start)<=MATCH_TIME]
        if len(eligible)!=1:
            diagnostics["missing_or_ambiguous_fixture"]+=1
            continue
        orig=eligible[0]
        keep={"event_id":game_id,"home":home,"away":away,
              "kickoff_utc":start.isoformat(),
              "reference_espn_event_id":str(orig.get("id") or ""),
              "source_goalie_at_utc":None,"revue_goalie_at_utc":observed_at.isoformat(),
              "sides":{}}
        goalie=orig.get("goalies")
        source_at=None
        if isinstance(goalie,dict) and goalie.get("at"):
            source_at=utc(goalie["at"])
            if source_at>src_time+timedelta(minutes=2):
                diagnostics["reference_source_time_invalid"]+=1
                continue
            keep["source_goalie_at_utc"]=source_at.isoformat()
        for side in ("home","away"):
            a=actual.get(side+"_goalie")
            b=goalie.get(side) if isinstance(goalie,dict) else None
            valid_a=a if isinstance(a,dict) and a.get("status") in ("confirmed","projected") else None
            valid_b=b if isinstance(b,dict) and b.get("status") in ("confirmed","projected") else None
            if not valid_a or not valid_b:
                diagnostics["side_missing_either_source"]+=1
                keep["sides"][side]={"status":"missing_either_source"}
                continue
            if not name_key(valid_a.get("name")) or not name_key(valid_b.get("name")):
                diagnostics["side_name_unusable"]+=1
                keep["sides"][side]={"status":"unusable_name"}
                continue
            name_equal=name_key(valid_a["name"])==name_key(valid_b["name"])
            status_equal=valid_a["status"]==valid_b["status"]
            diagnostics["comparable_goalie_sides"]+=1
            if name_equal:diagnostics["equal_names"]+=1
            if status_equal:diagnostics["equal_statuses"]+=1
            if not status_equal:
                diagnostics["status_changes_different_observation_times"]+=1
            if not name_equal:diagnostics["different_names"]+=1
            keep["sides"][side]={
                "name_equal":name_equal,"status_equal":status_equal,
                "source_status":valid_b["status"],"revue_status":valid_a["status"],
                "observation_times_equivalent":bool(source_at and source_at==observed_at),
                "status_disagreement_is_not_proof_of_bad_prediction":True,
            }
        diagnostics["matched_unique_fixture"]+=1
        rows.append(keep)
    return {
        "version":VERSION,"generated_at_utc":now.isoformat(),
        "status":"public_goalie_observation_comparison_not_prediction_parity",
        "source_repo":"Purple-Wraith/clairvoyance-backend",
        "reference_public_path":"docs/nhl_schedule.json",
        "original_snapshot_at_utc":src_time.isoformat(),
        "revue_snapshot_at_utc":dst_time.isoformat(),
        "reference_nhl_schedule_games":len(reference["games"]),
        "revue_espn_observed_games":len(observed["rows"]),
        "matched_unique_games":diagnostics["matched_unique_fixture"],
        "comparable_goalie_sides":diagnostics["comparable_goalie_sides"],
        "matching_names":diagnostics["equal_names"],
        "matching_statuses":diagnostics["equal_statuses"],
        "different_statuses":diagnostics["comparable_goalie_sides"]-diagnostics["equal_statuses"],
        "different_names":diagnostics["different_names"],
        "unmatched_games":len(observed["rows"])-len(rows),
        "not_a_verified_same_time_goalie_state":True,
        "goalies_verified_to_have_played":False,
        "original_sql_goalie_rows_verified":False,
        "original_prediction_parity_verified":False,
        "no_real_bets":True,
        "diagnostics":dict(diagnostics),
        "matches":rows,
        "note":"Same public ESPN observations may have different statuses when source snapshots are taken at different times. Even 100% matching names is not an original SQL goalie-stat or prediction match.",
    }


def download():
    req=Request(URL,headers={"Accept":"application/json","User-Agent":"RevueSourceComparison/1.0"})
    with urlopen(req,timeout=22) as res:
        data=res.read(4_000_001)
    if len(data)>4_000_000:raise ValueError("Reference snapshot too large")
    return json.loads(data.decode("utf8"))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--docs",default="docs")
    args=parser.parse_args()
    root=Path(args.docs)
    reference=download()
    data=json.loads((root/"nhl-espn-goalies-latest.json").read_text("utf8"))
    result=compare(reference,data,datetime.now(timezone.utc))
    (root/"parite-nhl-gardiens-publics.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print("Source goalie public comparison:",result["matched_unique_games"],"games,",
          result["matching_names"],"/",result["comparable_goalie_sides"],"names,",
          result["matching_statuses"],"statuses; NOT SQL or actual starter parity.")


if __name__=="__main__":
    main()
