"""Independent MLB Elo replay on verified ESPN final scores kept by Revue.

Clairvoyance's public Elo step uses base 1500, K=32 and two-sided update
without home advantage. This reconstructs the same *rule* on Revue results.
Original SQL starting ratings and its full historical games remain unknown,
so the resulting ratings are NOT alleged to equal Clairvoyance's DB values.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

from api_revue.fixtures import SourceUnavailable,timestamp

K_FACTOR=32.0
DEFAULT_RATING=1500.0
MAX_TEAM_RATING=3000.0


def expected_score(a:float,b:float)->float:
    return 1/(1+10**((b-a)/400))


def update_winner_loser(winner:float,loser:float)->tuple[float,float]:
    return (
        round(winner+K_FACTOR*(1-expected_score(winner,loser)),2),
        round(loser+K_FACTOR*(0-expected_score(loser,winner)),2),
    )


def replay_mlb_elo(history:dict,as_of:datetime)->dict:
    if as_of.tzinfo is None:
        raise ValueError("Elo cutoff time must include timezone")
    as_of=as_of.astimezone(timezone.utc)
    if not isinstance(history,dict) or history.get("version") not in (1, "1", "multisports_history_v1"):
        # Do not assume a new schema's event integrity and status rules.
        raise SourceUnavailable("Unknown historical ESPN data schema")
    leagues=history.get("leagues")
    if not isinstance(leagues,dict) or not isinstance(leagues.get("MLB"),dict):
        raise SourceUnavailable("No verified ESPN MLB history")
    events=leagues["MLB"].get("events")
    if not isinstance(events,list):
        raise SourceUnavailable("Missing ESPN MLB event list")
    eligible=[]
    seen=set()
    for event in events:
        if not isinstance(event,dict):
            raise SourceUnavailable("Malformed MLB history event")
        ident=str(event.get("id"))
        if not ident.isdecimal() or ident in seen:
            raise SourceUnavailable("Malformed or repeated ESPN MLB event ID")
        seen.add(ident)
        try:
            kickoff=timestamp(event["start"])
        except (KeyError,TypeError,ValueError) as exc:
            raise SourceUnavailable("Bad ESPN MLB fixture kickoff") from exc
        if event.get("league")!="MLB" or not isinstance(event.get("home"),str) or not isinstance(event.get("away"),str):
            raise SourceUnavailable("Wrong-league or missing team identity")
        if event["home"]==event["away"]:
            raise SourceUnavailable("Same MLB team on both sides")
        if event.get("complete") is not True or kickoff>=as_of:
            continue
        hs,aws=event.get("home_score"),event.get("away_score")
        # ESPN history normalizes integral scores to JSON floats (e.g. 3.0).
        # Accept only nonnegative finite whole values, never fractional goals.
        if (type(hs) not in (int,float) or type(aws) not in (int,float) or
            not math.isfinite(hs) or not math.isfinite(aws) or
            not 0<=hs<=100 or not 0<=aws<=100 or
            not float(hs).is_integer() or not float(aws).is_integer()):
            raise SourceUnavailable("Malformed official final MLB score")
        if hs==aws:
            # MLB has no tied final scores under normal rules. Exclude rather
            # than pretend a win for either side.
            continue
        eligible.append((kickoff,ident,event))
    eligible.sort(key=lambda item:(item[0],int(item[1])))
    if len(eligible)<20:
        raise SourceUnavailable("Insufficient completed MLB games for an Elo replay")

    ratings={}
    games_played={}
    last_game={}
    trace=[]
    for kickoff,ident,event in eligible:
        home,away=event["home"],event["away"]
        hr=ratings.get(home,DEFAULT_RATING)
        ar=ratings.get(away,DEFAULT_RATING)
        if event["home_score"]>event["away_score"]:
            after_home,after_away=update_winner_loser(hr,ar)
        else:
            after_away,after_home=update_winner_loser(ar,hr)
        for team,value in ((home,after_home),(away,after_away)):
            if not math.isfinite(value) or not 0<value<MAX_TEAM_RATING:
                raise SourceUnavailable("Invalid Elo rating update")
            ratings[team]=value
            games_played[team]=games_played.get(team,0)+1
            last_game[team]=kickoff.date().isoformat()
        trace.append({"espn_id":ident,"kickoff_utc":kickoff.isoformat(),
                      "home":home,"away":away,
                      "before_home_elo":hr,"before_away_elo":ar,
                      "after_home_elo":after_home,"after_away_elo":after_away})
    values=[
        {"team":team,"rating":rating,
         "games_played":games_played[team],"last_game_date":last_game[team]}
        for team,rating in ratings.items()
    ]
    values.sort(key=lambda r:(-r["rating"],r["team"]))
    return {
        "status":"recomputed_from_revue_verified_espn_finals_not_original_db",
        "sport":"mlb","cutoff_utc":as_of.isoformat(),
        "initial_rating":DEFAULT_RATING,"k_factor":K_FACTOR,
        "completed_espn_games":len(trace),"teams_count":len(values),
        "rows":values,"trace":trace,
        "original_clairvoyance_sql_ratings_equal":False,
        "note":"Matches original Elo arithmetic only. Limited Revue ESPN history and unknown original starting DB mean absolute Elo/predictions cannot be called identical.",
    }


def mlb_elo_from_file(root:Path,as_of:datetime)->dict:
    try:
        data=json.loads((root/"multisports-history.json").read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        raise SourceUnavailable("Revue ESPN historical scores not accessible") from exc
    return replay_mlb_elo(data,as_of)
