#!/usr/bin/env python3
"""One-time structure probe for ESPN NHL public stats. No personal credentials."""
import json
from urllib.request import Request,urlopen
from urllib.parse import urlencode

base="https://site.web.api.espn.com/apis/common/v3/sports/hockey/nhl/statistics/byathlete"
queries=[
    {"limit":50,"category":"skaters","season":"2026"},
    {"limit":50,"category":"skaters","season":"2027"},
]
for q in queries:
    url=base+"?"+urlencode(q)
    try:
        with urlopen(Request(url,headers={"Accept":"application/json"}),timeout=15) as r:
            data=json.loads(r.read().decode("utf-8"))
        print("Query",q,"ROOT",list(data)[:15])
        print("Categories:",[{"name":c.get("name"),"labels":(c.get("labels") or [])[:20],"keys":list(c)} for c in (data.get("categories") or [])[:3]])
        athletes=data.get("athletes") or []
        print("Athletes",len(athletes),"ATHLETE_KEYS",list((athletes[0] or {}).keys()) if athletes else [])
        if athletes:
            print("ATHLETE_DATA",json.dumps(athletes[0],ensure_ascii=False)[-3200:])
            print("CATEGORY_NAMES",[(c.get("name"),(c.get("names") or [])[:20]) for c in data.get("categories",[])])
    except Exception as e:
        print("FAILED",q,type(e).__name__,str(e)[:150])
