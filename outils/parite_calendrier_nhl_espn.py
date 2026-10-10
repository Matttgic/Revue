#!/usr/bin/env python3
"""Reconcile factual ESPN and NHL official fixture identifiers, without copying picks.

Clairvoyance's public schedule uses ESPN event IDs; Revue's NHL API uses official
NHL game IDs. Strictly join home/away abbreviations and exact UTC puck drop.
Read source only inside ephemeral GitHub Actions checkout; publish minimal
derived *identifier concordance* (no odds, goalie status or source game data).
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess

from outils.match_center_revue import instant


def resolve_reference_ids(reference:dict, own:dict) -> tuple[list[dict],list[dict]]:
    if not isinstance(reference.get("games"),list) or not isinstance(own.get("games"),list):
        raise ValueError("Both source and Revue must contain NHL fixture arrays")
    indexed:dict[tuple,list[str]]={}
    official_ids:set[str]=set()
    for event in reference["games"]:
        try:
            ident=str(event["id"])
            if not ident.isdecimal() or not ident:
                continue
            key=(event["home"],event["away"],instant(event["date"]))
            indexed.setdefault(key,[]).append(ident)
        except (KeyError,ValueError,TypeError):
            continue
    matches,missing=[],[]
    for game in own["games"]:
        nhl_id=str(game.get("event_id"))
        if nhl_id in official_ids:
            raise ValueError("Duplicated official NHL game ID")
        try:
            nhl_id=str(game["event_id"])
            key=(game["home"],game["away"],instant(game["start_utc"]))
            if not nhl_id.isdecimal() or nhl_id in official_ids:
                raise ValueError("Duplicated/invalid official NHL game ID")
            official_ids.add(nhl_id)
            candidates=indexed.get(key,[])
            if len(candidates)!=1:
                missing.append({"nhl_game_id":nhl_id,"reason":"ambiguous_or_missing_ESPN_event_identity"})
                continue
            espn_id=candidates[0]
            matches.append({
                "nhl_game_id":nhl_id,
                "original_espn_id":espn_id,
                "home":game["home"],
                "away":game["away"],
                "start_utc":instant(game["start_utc"]).isoformat(),
            })
        except (KeyError,ValueError,TypeError):
            missing.append({"nhl_game_id":str(game.get("event_id")),"reason":"malformed_original_game"})
    if len({x["original_espn_id"] for x in matches})!=len(matches):
        raise ValueError("Multiple Revue NHL events correspond to one ESPN event")
    return matches,missing


def build(reference:dict,own:dict,source_sha:str,as_of:datetime) -> dict:
    if as_of.tzinfo is None or not source_sha:
        raise ValueError("Source commit and timezone are mandatory")
    generated=instant(own["generated_at_utc"])
    if generated>as_of:
        raise ValueError("Revue fixture snapshot generated in future")
    matches,missing=resolve_reference_ids(reference,own)
    if not matches:
        raise ValueError("No identical real fixtures; fail closed")
    return {
        "generated_at_utc":as_of.astimezone(timezone.utc).isoformat(),
        "status":"verified_fixture_identity_pairs",
        "reference_repository":"Purple-Wraith/clairvoyance-backend",
        "source_commit":source_sha,
        "revue_nhl_snapshot_generated_at_utc":generated.isoformat(),
        "matched":len(matches),
        "unmatched":len(missing),
        "mappings":matches,
        "unmatched_events":missing,
        "data_copied":"Only public factual cross-provider fixture IDs, home/away and UTC schedule",
        "not_copied":"Odds, injuries, projected/confirmed goalies, picks, statistical forecasts, proprietary assets",
        "actual_prediction_parity":"NOT_VERIFIED",
        "note":"Exact fixture identity does not prove equal original Elo, market or goalie inputs. Source calendar may be stale; refresh mappings with new sources.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",required=True)
    p.add_argument("--own",default="docs/nhl-clairvoyance-shadow-latest.json")
    p.add_argument("--output",default="docs/parite-nhl-espn-id-map.json")
    args=p.parse_args()
    source=Path(args.reference)
    ref=json.loads((source/"docs/nhl_schedule.json").read_text(encoding="utf-8"))
    own=json.loads(Path(args.own).read_text(encoding="utf-8"))
    sha=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    out=build(ref,own,sha,datetime.now(timezone.utc))
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("NHL cross-provider ID parity:",out["matched"],"matched,",out["unmatched"],"unmatched")


if __name__=="__main__":main()
