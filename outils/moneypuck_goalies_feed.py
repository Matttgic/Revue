#!/usr/bin/env python3
"""Derived MoneyPuck NHL goalie metrics from official non-commercial CSV downloads.

Source https://moneypuck.com/data.htm — attribution required.
Never claims a goalie is confirmed to start. Does not publish original CSVs.
"""
from __future__ import annotations
import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import io
import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from outils.moneypuck_feed import BASE, SOURCE_PAGE, USER_AGENT, season_year, season_label
from modeles.reproduction.clairvoyance_moneypuck_parser import numeric, integer


@dataclass(frozen=True)
class Download:
    body: str
    last_modified: str | None = None


def goalie_csv_url(year: int) -> str:
    if not 2008 <= year <= 2100:
        raise ValueError("Invalid season")
    return f"{BASE}/{year}/regular/goalies.csv"


def download_goalies(year: int) -> Download:
    request = Request(goalie_csv_url(year), headers={
        "User-Agent": USER_AGENT, "Accept": "text/csv"
    })
    with urlopen(request, timeout=25) as response:
        if response.status != 200:
            raise RuntimeError(f"MoneyPuck goalies HTTP {response.status}")
        blob = response.read(1_000_001)
        if len(blob) > 1_000_000:
            raise ValueError("MoneyPuck goalie CSV unexpectedly large")
        if "html" in response.headers.get("Content-Type", "").lower():
            raise ValueError("MoneyPuck returned HTML instead of CSV")
        return Download(blob.decode("utf-8-sig"), response.headers.get("Last-Modified"))


def derived_goalies(text: str, year: int) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    required = {"name", "team", "situation", "games_played",
                "icetime", "xGoals", "goals", "ongoal"}
    if not required.issubset(set(reader.fieldnames or ())):
        raise ValueError("MoneyPuck goalie column schema changed")
    players = {}
    for r in reader:
        if r.get("situation") != "all":
            continue
        team = str(r.get("team") or "").strip().upper()
        name = str(r.get("name") or "").strip()
        gp = integer(r.get("games_played"))
        ice_seconds = numeric(r.get("icetime"))
        xga,ga = numeric(r.get("xGoals")),numeric(r.get("goals"))
        on_goal = numeric(r.get("ongoal"))
        if (not 2 <= len(team) <= 4 or not team.isalpha() or
            len(name) < 3 or not gp or gp < 1 or
            ice_seconds is None or ice_seconds <= 0 or not math.isfinite(ice_seconds) or
            xga is None or ga is None or on_goal is None or
            not all(math.isfinite(x) and x >= 0 for x in (xga,ga,on_goal)) or
            on_goal < ga):
            continue
        gsax = round(xga - ga, 2)
        save = round((on_goal - ga) / on_goal, 4) if on_goal > 0 else None
        result = {"name":name, "team":team, "season":season_label(year),
                  "games_played":gp,"ice_hours":round(ice_seconds/3600,2),
                  "xg_against":round(xga,2),"goals_against":round(ga,2),
                  "gsax":gsax, "gsax_per_60":round(gsax*3600/ice_seconds,2),
                  "save_pct":save,"starter_status":"unknown"}
        key = (str(r.get("playerId") or name), team)
        players[key] = result
    return sorted(players.values(),key=lambda g:(-g["gsax"],-g["ice_hours"],g["name"]))


def create_snapshot(now: datetime, fetcher=download_goalies) -> dict:
    yr = season_year(now)
    seasons, statuses = {}, {}
    for y in (yr, yr-1):
        label=season_label(y)
        try:
            source=fetcher(y)
            records=derived_goalies(source.body,y)
            if not records:
                raise ValueError("No valid observed goalies")
            updated=None
            if source.last_modified:
                last=parsedate_to_datetime(source.last_modified)
                if last.tzinfo:updated=last.astimezone(timezone.utc).isoformat()
            seasons[label]=records
            statuses[label]={"status":"available","goalies":len(records),
                             "source_updated_utc":updated,
                             "download_url":goalie_csv_url(y)}
        except (HTTPError,URLError,OSError,TimeoutError,ValueError,
                UnicodeError,RuntimeError) as exc:
            seasons[label]=[]
            statuses[label]={"status":"unavailable","goalies":0,
                             "source_updated_utc":None,
                             "error_type":type(exc).__name__,
                             "download_url":goalie_csv_url(y)}
    if not any(seasons.values()):
        raise RuntimeError("No official MoneyPuck goalie dataset available")
    return {"generated_at_utc":now.astimezone(timezone.utc).isoformat(),
            "source":"MoneyPuck.com","source_page":SOURCE_PAGE,
            "usage":"personal non-commercial with source attribution",
            "current_season":season_label(yr),
            "is_live":False,"confirmed_starters":False,
            "statuses":statuses,"seasons":seasons,
            "disclaimer":"Goalie historical stats only. Starter unknown; no lineup verification."}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="docs/moneypuck-goalies-latest.json")
    args=parser.parse_args()
    report=create_snapshot(datetime.now(timezone.utc))
    file=Path(args.output);file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                    encoding="utf-8")
    print("MoneyPuck official goalie observations",
          {k:v["goalies"] for k,v in report["statuses"].items()})


if __name__=="__main__":
    main()
