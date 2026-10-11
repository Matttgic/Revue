#!/usr/bin/env python3
"""Metadata-only diagnostic of ESPN soccer match statistics; NOT an Opta API."""
import json
from urllib.request import Request,urlopen

URL="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=401879301"

def main():
    with urlopen(Request(URL,headers={"Accept":"application/json"}),timeout=20) as r:
        data=json.loads(r.read().decode("utf-8"))
    print("root_keys:",list(data))
    print("boxscore_keys:",list((data.get("boxscore") or {}).keys()))
    teams=(data.get("boxscore") or {}).get("teams") or []
    print("number_of_teams:",len(teams))
    for t in teams[:2]:
        stats=t.get("statistics") or []
        print("statistics:",[(x.get("name"),x.get("displayName")) for x in stats][:45])
        print("team_keys:",list((t.get("team") or {}).keys())[:25])
    print("header_keys:",list((data.get("header") or {}).keys()))
    print("has_xg_fields:",any("expect" in str(x).lower() or "xg"==str(x).lower() for t in teams for x in (t.get("statistics") or []) for x in [x.get("name"),x.get("displayName")]))
if __name__=="__main__":main()
