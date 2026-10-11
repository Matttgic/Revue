#!/usr/bin/env python3
"""Read-only diagnostic: ESPN previous NBA season team standings metadata."""
import json
from urllib.request import Request,urlopen

URL="https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?season=2026"
def main():
    with urlopen(Request(URL,headers={"Accept":"application/json"}),timeout=24) as f:
        data=json.load(f)
    if not isinstance(data,dict):raise ValueError("Non-dict ESPN response")
    children=data.get("children") or []
    entries=[]
    def walk(block):
        for e in (block.get("standings") or {}).get("entries") or []:
            if isinstance(e,dict):entries.append(e)
        for part in block.get("children") or []:
            if isinstance(part,dict):walk(part)
    walk(data)
    out={"roots":list(data)[:25],"children":len(children),
         "entry_count":len(entries),
         "first3":[{"team":e.get("team"),
                    "stats":[{"name":v.get("name"),"value":v.get("value"),"displayValue":v.get("displayValue")}
                             for v in (e.get("stats") or [])[:16]]}
                   for e in entries[:3]]}
    print(json.dumps(out,ensure_ascii=False))
    if not entries:raise ValueError("No standings entries")
if __name__=="__main__":main()
