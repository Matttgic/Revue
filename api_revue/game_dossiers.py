"""Read-only HTTP access to independently validated static Revue match dossiers.

No upstream sports calls, private SQL or artificial betting recommendations.
A stale or malformed dossier snapshot fails closed with 503.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
from api_revue.fixtures import SourceUnavailable,timestamp
MAX_AGE=timedelta(hours=12)

def dossier_snapshot(root:Path,now:datetime)->dict:
    try:
        d=json.loads((root/"match-dossiers-latest.json").read_text(encoding="utf-8"))
        if (not isinstance(d,dict) or d.get("status")!="source_audited_static_match_dossiers_not_live" or
            d.get("original_clairvoyance_equivalence_verified") is not False or
            d.get("historical_data_not_point_in_time_forecasts") is not True or
            d.get("real_bets_enabled") is not False or
            d.get("bookmaker_prices_are_live") is not False or
            d.get("validated_value_bets")!=0 or
            not isinstance(d.get("games"),list) or
            d.get("count")!=len(d["games"])):
            raise ValueError("Invalid Revue game report provenance")
        t=timestamp(d["generated_at_utc"]);now=now.astimezone(timezone.utc)
        if t>now+timedelta(minutes=2) or now-t>MAX_AGE:
            raise ValueError("Stale or future report")
        seen=set()
        for g in d["games"]:
            if g.get("league")=="CFB" or g.get("no_real_betting") is not True:
                raise ValueError("Unsupported betting or CFB record")
            key=str(g.get("league"))+":"+str(g.get("event_id"))
            if key in seen or key!=g.get("key"):
                raise ValueError("Duplicate/corrupt game key")
            seen.add(key)
        return d
    except (OSError,ValueError,TypeError,AttributeError,KeyError) as exc:
        raise SourceUnavailable("Revue match dossier snapshot missing, stale or untrusted") from exc

def list_dossiers(root:Path,now:datetime,league:str|None,query:str|None,
                  only_priced:bool,limit:int,offset:int)->dict:
    d=dossier_snapshot(root,now)
    games=[g for g in d["games"]
           if (not league or g["league"].casefold()==league.casefold())
           and (not query or query.casefold() in
                (" ".join((g["home"],g["away"],g["league"],g["event_id"]))).casefold())
           and (not only_priced or bool(g["historical_odds"]["observations"]))]
    return {"source":"Revue archived dossiers, not original source SQL",
            "generated_at_utc":d["generated_at_utc"],
            "source_observed_utc":d["source_match_center_at_utc"],
            "not_live":True,"no_real_bets":True,"original_parity_verified":False,
            "total":len(games),"offset":offset,"limit":limit,
            "items":[{"key":g["key"],"league":g["league"],"event_id":g["event_id"],
                      "home":g["home"],"away":g["away"],"start_utc":g["start_utc"],
                      "observed_price_count":len(g["historical_odds"]["observations"]),
                      "models":len(g["research_models"]),
                      "has_frozen_forecast":g["locked_forecast"] is not None,
                      "home_recent_games":g["home_history"]["games"],
                      "away_recent_games":g["away_history"]["games"]}
                     for g in games[offset:offset+limit]]}

def dossier_detail(root:Path,now:datetime,league:str,event_id:str)->dict|None:
    d=dossier_snapshot(root,now)
    return next((g for g in d["games"] if
                 g["league"]==league and g["event_id"]==event_id),None)
