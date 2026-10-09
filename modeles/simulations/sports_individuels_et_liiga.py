#!/usr/bin/env python3
"""Research adapters: tennis, MMA and Finnish Liiga — independently authored.

Scoreboard data is collected from public ESPN site endpoints for tennis/MMA
and official liiga.fi v2 for hockey. Predictions only after sufficient,
completed PRIOR results. NO price quotes, bankroll advice or calibrated EV.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
ESPN = "https://site.api.espn.com/apis/site/v2/sports"
LIIGA = "https://www.liiga.fi/api/v2/games?tournament=runkosarja&season={season}"
SOURCES = {
    "ATP": f"{ESPN}/tennis/atp/scoreboard",
    "WTA": f"{ESPN}/tennis/wta/scoreboard",
    "TENNIS": f"{ESPN}/tennis/all/scoreboard",
    "UFC": f"{ESPN}/mma/ufc/scoreboard",
}
# ATP and WTA are tried individually, then ALL only to catalog unclassified matches.
HISTORY_DAYS = {"ATP": 21, "WTA": 21, "TENNIS": 4, "UFC": 50}
MIN_MATCHES = {"ATP": 6, "WTA": 6, "TENNIS": 6, "UFC": 3, "LIIGA": 4}


@dataclass(frozen=True)
class Match:
    id: str
    league: str
    starts: datetime
    player1_id: str
    player2_id: str
    player1: str
    player2: str
    finished: bool
    winner_id: str | None


def dt_utc(raw) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        val = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return val.astimezone(timezone.utc) if val.tzinfo else None
    except ValueError:
        return None


def _completed(comp: dict, parent: dict) -> bool:
    for obj in (comp, parent):
        status = obj.get("status") or {}
        if (status.get("type") or {}).get("completed") is True:
            return True
    return False


def parse_espn_scoreboard(data: dict, league: str) -> list[Match]:
    """Flatten events, competition cards and groupings (tennis uses groups).

    Only 2 individual competitors. We never infer a winning player from
    scoreline text or a country without the provider's explicit winner flag.
    """
    seen: dict[str, Match] = {}
    for event in data.get("events") or []:
        if not isinstance(event, dict):
            continue
        # Competition in individual sports can be within tournament groupings.
        groups = event.get("groupings") or []
        competitions = list(event.get("competitions") or [])
        for group in groups:
            competitions.extend(group.get("competitions") or [])
        if event.get("competitors") and not competitions:
            competitions.append(event)
        for idx, comp in enumerate(competitions):
            if not isinstance(comp, dict):
                continue
            if comp.get("type", {}).get("abbreviation", "") == "DBL":
                continue
            members = comp.get("competitors") or []
            if len(members) != 2:
                continue
            players = []
            for member in members:
                athlete = member.get("athlete") or member.get("team") or {}
                aid = athlete.get("id") or member.get("id")
                name = athlete.get("displayName") or athlete.get("fullName") or athlete.get("shortName")
                if not aid or not name:
                    break
                # Some tennis tournaments publish doubles as pair names; exclude.
                if " / " in str(name) or " & " in str(name):
                    break
                players.append((str(aid), str(name), member.get("winner") is True))
            if len(players) != 2 or players[0][0] == players[1][0]:
                continue
            start = dt_utc(comp.get("date")) or dt_utc(event.get("date"))
            if start is None:
                continue
            finished = _completed(comp, event)
            wins = [p for p in players if p[2]]
            winner = wins[0][0] if finished and len(wins) == 1 else None
            # A finished competition with no winner is not a usable training label.
            mid = str(comp.get("id") or f"{event.get('id','')}:{idx}")
            if not mid or mid == ":0":
                continue
            key = f"{league}:{mid}"
            seen[key] = Match(
                id=key, league=league, starts=start,
                player1_id=players[0][0], player2_id=players[1][0],
                player1=players[0][1], player2=players[1][1],
                finished=finished, winner_id=winner,
            )
    return list(seen.values())


def _get_json(url: str, timeout=14):
    request = Request(url, headers={"Accept": "application/json"})
    err = None
    for attempt in range(2):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            err = exc
            if attempt == 0:
                time.sleep(.35)
    raise RuntimeError(f"{type(err).__name__}: {str(err)[:130]}")


def individual_elo(matches: list[Match], now: datetime, days=3) -> list[dict]:
    """Chronological one-result-per-fight/match Elo; no fake match with no stats."""
    ratings = defaultdict(lambda: 1500.0)
    appearances = defaultdict(int)
    games: dict[str, Match] = {}
    for match in matches:
        prev = games.get(match.id)
        if prev is None or (match.finished and not prev.finished):
            games[match.id] = match
    complete = sorted((m for m in games.values()
                       if m.finished and m.winner_id in (m.player1_id, m.player2_id)
                       and m.starts < now), key=lambda m: (m.starts, m.id))
    for m in complete:
        a, b = ratings[m.player1_id], ratings[m.player2_id]
        exp = 1 / (1 + 10**((b-a)/400))
        obs = 1 if m.winner_id == m.player1_id else 0
        ratings[m.player1_id] += 26 * (obs - exp)
        ratings[m.player2_id] -= 26 * (obs - exp)
        appearances[m.player1_id] += 1
        appearances[m.player2_id] += 1
    today = now.astimezone(PARIS).date()
    output = []
    for m in sorted(games.values(), key=lambda x: (x.starts, x.id)):
        if m.finished or m.starts <= now:
            continue
        if not today <= m.starts.astimezone(PARIS).date() < today + timedelta(days=days):
            continue
        n1, n2 = appearances[m.player1_id], appearances[m.player2_id]
        threshold = MIN_MATCHES[m.league]
        probability = None
        if n1 >= threshold and n2 >= threshold:
            # Need enough observed results to estimate a two-way Elo.
            probability = 1 / (1 + 10**((ratings[m.player2_id]-ratings[m.player1_id])/400))
        output.append({
            "event_id": m.id, "home": m.player1, "away": m.player2,
            "start_utc": m.starts.isoformat(),
            "status": "prototype_non_calibre" if probability is not None else "historique_insuffisant",
            "probabilities": ({"home_win": round(probability, 4),
                              "away_win": round(1-probability, 4)}
                              if probability is not None else None),
            "training_games": {"home": n1, "away": n2},
            "odds": None,
        })
    return output


def parse_liiga(data, now: datetime) -> list[dict]:
    if not isinstance(data, list):
        raise ValueError("Liiga expected a list of games")
    events = []
    for row in data:
        if not isinstance(row, dict):
            continue
        start = dt_utc(row.get("start"))
        home, away = row.get("homeTeam") or {}, row.get("awayTeam") or {}
        if not start or not row.get("id"):
            continue
        hid = home.get("teamId") or home.get("id") or home.get("teamName")
        aid = away.get("teamId") or away.get("id") or away.get("teamName")
        hname, aname = home.get("teamName"), away.get("teamName")
        if not all((hid, aid, hname, aname)) or str(hid)==str(aid):
            continue
        hs, ans = home.get("goals"), away.get("goals")
        finished = row.get("ended") is True
        if finished and (not isinstance(hs, int) or not isinstance(ans, int)):
            finished = False
        events.append({
            "id": str(row["id"]), "start": start, "hid": str(hid),
            "aid": str(aid), "home": str(hname), "away": str(aname),
            "finished": finished, "hgoals": hs if finished else None,
            "agoals": ans if finished else None,
            "shootout": "WINNING_SHOT" in str(row.get("finishedType") or "").upper(),
        })
    return events


def predict_liiga(events: list[dict], now: datetime, days=3) -> list[dict]:
    try:
        from .nhl_independant import _distribution, _over
    except ImportError:
        from nhl_independant import _distribution, _over
    unique = {}
    for e in events:
        if e["id"] not in unique or (e["finished"] and not unique[e["id"]]["finished"]):
            unique[e["id"]] = e
    trained = sorted((e for e in unique.values() if e["finished"] and e["start"] < now),
                     key=lambda e: (e["start"], e["id"]))
    stats = defaultdict(lambda: [0., 0., 0])
    ratings = defaultdict(lambda: 1500.)
    total_goals = 0.
    for e in trained:
        gh, ga = e["hgoals"], e["agoals"]
        # Shootout winner goal does not belong to an O/U goals model.
        th, ta = gh, ga
        if e["shootout"] and abs(gh-ga)==1:
            if gh>ga: th-=1
            else: ta-=1
        total_goals += th + ta
        a,b = ratings[e["hid"]], ratings[e["aid"]]
        expected = 1/(1+10**((b-a-32)/400))
        actual = 1 if gh>ga else 0 if gh<ga else .5
        delta = 20*(actual-expected)
        ratings[e["hid"]] += delta; ratings[e["aid"]] -= delta
        for team,gf,ga in ((e["hid"],th,ta),(e["aid"],ta,th)):
            stats[team][0]+=gf;stats[team][1]+=ga;stats[team][2]+=1
    base = total_goals/(2*len(trained)) if trained else 2.75
    base = max(1.8,min(base,3.8))
    today = now.astimezone(PARIS).date()
    out=[]
    for e in sorted(unique.values(), key=lambda x:(x["start"],x["id"])):
        if e["finished"] or e["start"]<=now or not today<=e["start"].astimezone(PARIS).date()<today+timedelta(days=days):
            continue
        nh,na=stats[e["hid"]][2],stats[e["aid"]][2]
        probs,expected=None,None
        if nh>=MIN_MATCHES["LIIGA"] and na>=MIN_MATCHES["LIIGA"]:
            def rate(team):
                gf,ga,n=stats[team]
                return ((gf+12*base)/(n+12),(ga+12*base)/(n+12))
            gf_h,ga_h=rate(e["hid"]);gf_a,ga_a=rate(e["aid"])
            lamh=max(.6,min(6.,gf_h*ga_a/base*1.05))
            lama=max(.6,min(6.,gf_a*ga_h/base*.95))
            pre,draw=_distribution(lamh,lama)
            home_elo=1/(1+10**((ratings[e["aid"]]-ratings[e["hid"]]-32)/400))
            hw=.5*(pre+draw*home_elo)+.5*home_elo
            probs={
                "home_win":round(hw,4),"away_win":round(1-hw,4),
                "over_4_5":round(_over(lamh+lama,4.5),4),
                "over_5_5":round(_over(lamh+lama,5.5),4),
            }
            expected={"home":round(lamh,2),"away":round(lama,2)}
        out.append({
            "event_id":e["id"],"home":e["home"],"away":e["away"],
            "start_utc":e["start"].isoformat(),
            "status":"prototype_non_calibre" if probs else "historique_insuffisant",
            "probabilities":probs,
            "expected_score":expected,"odds":None,
            "training_games":{"home":nh,"away":na}
        })
    return out


def dump_match(m: Match) -> dict:
    d=vars(m).copy();d["starts"]=m.starts.isoformat();return d


def load_match(row: dict) -> Match:
    values=dict(row)
    values["starts"]=dt_utc(values["starts"])
    if not values["starts"]:
        raise ValueError("bad date")
    return Match(**values)


def _fetch_individual(league: str, now: datetime, days: int,
                      prev: dict | None) -> tuple[list[Match],dict,dict]:
    back = HISTORY_DAYS[league]
    begin=now.astimezone(PARIS).date()-timedelta(days=back)
    end=now.astimezone(PARIS).date()+timedelta(days=days)
    saved=prev if isinstance(prev,dict) else {}
    dates=set(saved.get("days_ok") or [])
    matches={}
    for item in saved.get("events") or []:
        try:
            m=load_match(item)
            if m.league==league and begin-timedelta(days=1)<=m.starts.astimezone(PARIS).date()<=end+timedelta(days=1):
                matches[m.id]=m
        except (ValueError,KeyError,TypeError):
            pass
    requests=0;fails=[]
    for i in range((end-begin).days+1):
        day=begin+timedelta(days=i)
        key=day.isoformat()
        if day<now.astimezone(PARIS).date()-timedelta(days=2) and key in dates:
            continue
        stamp=day.strftime("%Y%m%d")
        try:
            data=_get_json(SOURCES[league]+"?dates="+stamp)
            if not isinstance(data,dict) or not isinstance(data.get("events"),list):
                raise RuntimeError("events missing")
            requests+=1;dates.add(key)
            for m in parse_espn_scoreboard(data,league):
                if abs((m.starts.astimezone(PARIS).date()-day).days)<=1:
                    if m.id not in matches or (m.finished and not matches[m.id].finished):
                        matches[m.id]=m
        except RuntimeError as err:
            fails.append(key+":"+str(err)[:75])
    dates={d for d in dates if begin.isoformat()<=d<=end.isoformat()}
    result=sorted(matches.values(),key=lambda x:(x.starts,x.id))
    coverage=len(dates)
    status="ok" if coverage==(end-begin).days+1 else "partial" if coverage else "failed"
    return result,{"status":status,"dates_ok":coverage,"dates_total":(end-begin).days+1,
                   "requests_now":requests,"errors":fails[:4],"matches":len(result)},{
        "days_ok":sorted(dates),"events":[dump_match(m) for m in result],
    }


def run(days: int, now: datetime, cache: dict | None=None) -> tuple[dict,dict]:
    if days not in range(1,8):
        raise ValueError("days 1..7")
    cache=cache or {}
    updated={}
    competitions={}
    for lg,label,sport in [
        ("ATP","ATP","Tennis"),("WTA","WTA","Tennis"),
        ("UFC","UFC","MMA"),
    ]:
        matches,diag,state=_fetch_individual(lg,now,days,cache.get(lg))
        competitions[lg]={"name":label,"sport":sport,"model":"Elo individuel (expérimental)",
                          "status":diag["status"],"games":individual_elo(matches,now,days),
                          "diagnostics":diag}
        updated[lg]=state
    # Tennis all is for coverage audit, not merge into ATP/WTA without a reliable
    # gender/tournament classification. Fallback cannot silently relabel.
    matches,diag,state=_fetch_individual("TENNIS",now,days,cache.get("TENNIS"))
    competitions["TENNIS"]={"name":"Tennis (circuit non confirmé)","sport":"Tennis",
        "model":"Aucune attribution de circuit","status":diag["status"],
        "games":[{"event_id":m.id,"home":m.player1,"away":m.player2,
            "start_utc":m.starts.isoformat(),"status":"circuit_non_identifie",
            "probabilities":None,"odds":None} for m in matches
            if not m.finished and m.starts>now and now.astimezone(PARIS).date()<=m.starts.astimezone(PARIS).date()<now.astimezone(PARIS).date()+timedelta(days=days)],
        "diagnostics":diag}
    updated["TENNIS"]=state
    # Liiga one bulk request for this season, supported by previous source verification.
    season=now.astimezone(PARIS).year+1 if now.astimezone(PARIS).month>=8 else now.astimezone(PARIS).year
    try:
        data=_get_json(LIIGA.format(season=season),timeout=24)
        events=parse_liiga(data,now)
        games=predict_liiga(events,now,days)
        competitions["LIIGA"]={"name":"Liiga Finlande","sport":"Hockey",
           "model":"Elo + buts lissés / Poisson",
           "status":"ok","games":games,
           "diagnostics":{"source":"liiga.fi API v2","total_games":len(events),"season":season}}
    except (RuntimeError,ValueError) as err:
        competitions["LIIGA"]={"name":"Liiga Finlande","sport":"Hockey",
           "model":"Elo + Poisson","status":"failed","games":[],
           "diagnostics":{"error":str(err)[:150],"season":season}}
    report={
        "generated_at_utc":now.astimezone(timezone.utc).isoformat(),
        "days":days,"status":"prototype_non_calibre",
        "disclaimer":"Aucun prix bookmaker. Elo individuel limité par historique du flux. Ni UTR ni classement, aucun pari conseillé.",
        "competitions":competitions,
    }
    return report,updated


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--days",type=int,default=3)
    p.add_argument("--output",default="docs/individual-latest.json")
    p.add_argument("--history-file",default="docs/individual-history.json")
    a=p.parse_args()
    f=Path(a.history_file)
    try:
        cache=json.loads(f.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        cache={}
    report,hist=run(a.days,datetime.now(timezone.utc),cache)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(hist,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    for k,v in report["competitions"].items():
        print(f"{k}: {v['status']} | {len(v['games'])} futurs, {sum(g.get('probabilities') is not None for g in v['games'])} probabilités")
    return 0 if any(v["status"] in ("ok","partial") for v in report["competitions"].values()) else 2


if __name__=="__main__":
    sys.exit(main())
