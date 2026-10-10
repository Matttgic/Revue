"""Immutable independent pre-match individual sports research tracker.

Supported sources:
- ESPN individual ATP, WTA and UFC: explicit completed winner flags only.
- Official liiga.fi v2 completed records (never a merely observed score).
No odds, betting recommendations, cash returns or retrospectively generated
predictions. A matchup must be observed >=20min before its scheduled start.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
import argparse,json,math

VERSION="revue_individual_pre_match_v1"
MIN_BEFORE=timedelta(minutes=20)
LEAGUES={"ATP","WTA","UFC","LIIGA"}
MIN_GAMES={"ATP":6,"WTA":6,"UFC":0,"LIIGA":4}
SOURCE_WINDOW=timedelta(hours=26)

def at(x):
    if not isinstance(x,str):raise ValueError("Missing timestamp")
    t=datetime.fromisoformat(x.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("Naive timestamp")
    return t.astimezone(timezone.utc)

def score(x):
    return type(x) is int and 0<=x<=99

def valid_probability(x):
    return type(x) in (int,float) and math.isfinite(x) and .001<x<.999

def participant(v):
    if not isinstance(v,str) or not v.strip() or len(v)>125:return False
    u=" ".join(v.upper().split())
    return u not in {"TBD","TBA","TO BE DETERMINED","QUALIFIER","BYE","UNKNOWN","TBC"} and not u.startswith(("WINNER OF ","LOSER OF ","QUALIFIER "))

def base():
    return {"version":VERSION,"events":[]}

def lock(ledger,source,now):
    if now.tzinfo is None:raise ValueError("Timezone aware clock required")
    now=now.astimezone(timezone.utc)
    if ledger is None:ledger=base()
    if ledger.get("version")!=VERSION or not isinstance(ledger.get("events"),list):
        raise ValueError("Unsupported prospective tracker")
    old={r["key"]:r for r in ledger["events"]}
    if len(old)!=len(ledger["events"]):raise ValueError("Duplicate original forecast key")
    if source.get("status")!="prototype_non_calibre":
        return ledger
    generated=at(source["generated_at_utc"])
    if not generated<=now or now-generated>SOURCE_WINDOW:
        return ledger
    for league,item in (source.get("competitions") or {}).items():
        if league not in LEAGUES or item.get("status") not in ("ok","partial"):
            continue
        for game in item.get("games") or []:
            try:
                key=f"{league}:{game['event_id']}"
                if key in old:continue
                if not str(game["event_id"]).strip():continue
                kickoff=at(game["start_utc"])
                if not now<=kickoff-MIN_BEFORE or not generated<=now:
                    continue
                home,away=game["home"],game["away"]
                if not participant(home) or not participant(away) or home.casefold()==away.casefold():
                    continue
                if game.get("status")!="prototype_non_calibre":continue
                p=game["probabilities"]
                if not isinstance(p,dict) or not (
                    valid_probability(p.get("home_win")) and
                    valid_probability(p.get("away_win")) and
                    abs(p["home_win"]+p["away_win"]-1)<.012):
                    continue
                training=game.get("training_games") or {}
                if not all(type(training.get(k)) is int and training[k]>=MIN_GAMES[league]
                           for k in ("home","away")):
                    continue
                if league=="UFC" and game.get("model") not in (
                    "elo_individuel","baseline_carriere_fiable_seulement_si_verifiee"):
                    continue
                old[key]={
                    "key":key,"league":league,"event_id":str(game["event_id"]),
                    "home":home,"away":away,"kickoff_utc":kickoff.isoformat(),
                    "source_generated_utc":generated.isoformat(),
                    "locked_at_utc":now.isoformat(),
                    "model":"revue_individual_elo" if league!="LIIGA" else "revue_liiga_elo_poisson",
                    "p_home":float(p["home_win"]),"training_games":training,
                    "status":"pending","result":None,"source_result":None,
                    "observed_result_at_utc":None,"brier":None,"log_loss":None,
                    "real_bet":False,"stake_units":0,
                }
            except (ValueError,KeyError,TypeError):
                continue
    return {"version":VERSION,"events":sorted(old.values(),
            key=lambda r:(r["kickoff_utc"],r["key"]))}

def source_results(individual,archive,now):
    """Result extraction, without synthesizing winner from scorelines."""
    try:
        obs=at(individual["generated_at_utc"])
        if (not now-SOURCE_WINDOW<=obs<=now or
            individual.get("status")!="prototype_non_calibre" or
            archive.get("LIIGA",{}) and
            archive["LIIGA"].get("source")!="liiga.fi public API v2"):
            return {}
    except (KeyError,ValueError,TypeError,AttributeError):return {}
    out={}
    for league in ("ATP","WTA","UFC"):
        if (individual.get("competitions",{}).get(league,{}).get("status")
            not in ("ok","partial")):continue
        for event in archive.get(league,{}).get("events",[]):
            try:
                start=at(event["starts"])
                if (event.get("finished") is not True or
                    start>=obs or start>=now or
                    event.get("league")!=league or
                    not participant(event.get("player1")) or
                    not participant(event.get("player2")) or
                    event["player1"]==event["player2"] or
                    event.get("winner_id") not in (
                        event.get("player1_id"),event.get("player2_id"))):
                    continue
                value=1 if event["winner_id"]==event["player1_id"] else 0
                key=f"{league}:{event['id']}"
                if key in out:raise ValueError("Duplicate ESPN result ID")
                out[key]={"league":league,"event_id":str(event["id"]),
                          "home":event["player1"],"away":event["player2"],
                          "kickoff_utc":start.isoformat(),"result":value,
                          "result_info":{"winner":event["player1"] if value else event["player2"],
                                         "source":"ESPN completed winner flag"},
                          "observed_at_utc":obs.isoformat()}
            except (KeyError,TypeError,ValueError):continue
    liiga=archive.get("LIIGA") or {}
    try:
        liiga_time=at(liiga["observed_at_utc"])
    except (KeyError,TypeError,ValueError):liiga_time=None
    if (liiga_time and now-SOURCE_WINDOW<=liiga_time<=now and
        individual.get("competitions",{}).get("LIIGA",{}).get("status") in ("ok","partial") and
        liiga_time<=obs+timedelta(minutes=5)):
        for event in liiga.get("events",[]):
            try:
                start=at(event["starts"]);home_goals=event["home_goals"];away_goals=event["away_goals"]
                if (event.get("finished") is not True or start>=liiga_time or
                    not score(home_goals) or not score(away_goals) or
                    home_goals==away_goals or
                    not participant(event["home"]) or not participant(event["away"])):
                    continue
                eid=str(event["id"])
                key="LIIGA:"+eid
                if key in out:raise ValueError("Duplicate Liiga result")
                out[key]={"league":"LIIGA","event_id":eid,
                          "home":event["home"],"away":event["away"],
                          "kickoff_utc":start.isoformat(),
                          "result":int(home_goals>away_goals),
                          "result_info":{"score":{"home":home_goals,"away":away_goals},
                                         "shootout":event.get("shootout") is True,
                                         "source":"liiga.fi API v2 ended flag"},
                          "observed_at_utc":liiga_time.isoformat()}
            except (ValueError,KeyError,TypeError):continue
    return out

def settle(ledger,individual,archive,now):
    if ledger.get("version")!=VERSION or not isinstance(ledger.get("events"),list):
        raise ValueError("Unknown tracker version")
    frozen=json.loads(json.dumps(ledger))
    verified=source_results(individual,archive,now)
    for row in frozen["events"]:
        if row.get("status")!="pending":continue
        official=verified.get(row["key"])
        if not official:continue
        try:
            if (official["league"]!=row["league"] or
                official["event_id"]!=row["event_id"] or
                official["home"].casefold()!=row["home"].casefold() or
                official["away"].casefold()!=row["away"].casefold() or
                at(official["kickoff_utc"])!=at(row["kickoff_utc"]) or
                not at(row["locked_at_utc"])<=at(row["kickoff_utc"])-MIN_BEFORE or
                not at(row["source_generated_utc"])<=at(row["locked_at_utc"]) or
                not at(row["kickoff_utc"])<at(official["observed_at_utc"])<=now or
                row["real_bet"] is not False or row["stake_units"]!=0):
                continue
            p=row["p_home"];y=official["result"]
            if not valid_probability(p) or type(y) is not int or y not in (0,1):
                raise ValueError("Corrupt forecast or official result")
            row.update({"status":"settled","result":y,
                        "source_result":official["result_info"],
                        "observed_result_at_utc":official["observed_at_utc"],
                        "brier":round((p-y)**2,6),
                        "log_loss":round(-math.log(p if y else 1-p),6)})
        except (ValueError,KeyError,TypeError):
            continue
    return frozen

def performance(ledger,now):
    if ledger.get("version")!=VERSION:raise ValueError("Bad ledger version")
    rows=ledger["events"];summaries={}
    for league in sorted(LEAGUES):
        group=[x for x in rows if x["league"]==league]
        settled=[x for x in group if x["status"]=="settled"]
        summaries[league]={
            "locked":len(group),"pending":len(group)-len(settled),
            "settled":len(settled),
            "mean_brier":round(sum(x["brier"] for x in settled)/len(settled),6) if settled else None,
            "mean_log_loss":round(sum(x["log_loss"] for x in settled)/len(settled),6) if settled else None,
            "research_only":True,"profit_units":None,"roi":None,
        }
    return {"generated_at_utc":now.astimezone(timezone.utc).isoformat(),
            "status":"independent_individual_prospective_unscaled_research",
            "version":VERSION,"total_locked":len(rows),
            "pending":sum(x["status"]=="pending" for x in rows),
            "settled":sum(x["status"]=="settled" for x in rows),
            "leagues":summaries,"real_bets":0,"roi":None,
            "source_note":"ESPN explicit winner flags, Liiga official ended finals. At least 20 minutes before start to lock. No prices. No retroactive model feature backfill.",
            "note":"No calibration proven, no profitability claimed; compare Brier only on common events and adequate samples."}

def main():
    p=argparse.ArgumentParser();p.add_argument("--docs",default="docs");args=p.parse_args()
    root=Path(args.docs)
    def read(name,fallback=None):
        try:return json.loads((root/name).read_text(encoding="utf-8"))
        except (OSError,ValueError):return fallback
    source=read("individual-latest.json",{})
    archive=read("individual-history.json",{})
    ledger=read("individual-prospective-ledger.json",base())
    now=datetime.now(timezone.utc)
    next_ledger=settle(lock(ledger,source,now),source,archive,now)
    metrics=performance(next_ledger,now)
    for name,obj in [("individual-prospective-ledger.json",next_ledger),
                     ("individual-prospective-performance.json",metrics)]:
        (root/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("Individual prospective: ",metrics["total_locked"],"locked,",
          metrics["settled"],"settled, 0 real bets.")

if __name__=="__main__":main()
