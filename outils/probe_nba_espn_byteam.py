#!/usr/bin/env python3
"""Read-only diagnostic for NBA ESPN regular-season advanced stats."""
import json
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from datetime import datetime,timezone

URL="https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byteam"

def main():
    for season in (2026,2027):
        params={"region":"us","lang":"en","contentorigin":"espn","season":season,"seasontype":2}
        url=URL+"?"+urlencode(params)
        try:
            with urlopen(Request(url,headers={"Accept":"application/json","User-Agent":"Revue-source-parity/1.0"}),timeout=23) as resp:
                d=json.load(resp)
            teams=d.get("teams") or []
            categories=d.get("categories") or []
            first=teams[0] if teams else {}
            print(json.dumps({"season":season,"requestedSeason":d.get("requestedSeason"),
                "teams":len(teams),"firstTeam":(first.get("team") or {}).get("abbreviation"),
                "categories":[{"name":x.get("name"),"sampleNames":(x.get("names") or [])[:10]} for x in categories[:9]],
                "firstTeamCategories":[{"name":x.get("name"),"splitId":x.get("splitId"),"len":len(x.get("values") or [])} for x in (first.get("categories") or [])[:9]],
                "generated_at_utc":datetime.now(timezone.utc).isoformat()
            },ensure_ascii=False))
        except Exception as e:
            print("NBA byteam",season,"UNAVAILABLE",type(e).__name__,str(e)[:130])
if __name__=="__main__":main()
