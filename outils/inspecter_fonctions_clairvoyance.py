#!/usr/bin/env python3
"""One-off READ-ONLY local inspector for a checked-out public JS app.

Only small bounded snippets are emitted to CI logs for developer analysis,
not published to Revue docs. Inspect the original, do not redistribute it.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

TARGETS={
    "nhlMC":7624,
    "nhlEns":7727,
    "nbaMC":13949,
    "nbaGetBayes":14004,
    "nbaEns":14028,
    "nflMC":10058,
    "_nflBayes":10158,
    "nflEns":10163,
    "_socXG":26784,
    "_socMarketBlend":27435,
    "_soccerMC":27466,
}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",required=True)
    ap.add_argument("--limit",type=int,default=4000)
    a=ap.parse_args()
    if not 50<=a.limit<=10000:raise ValueError("Bounded excerpts only")
    lines=Path(a.source).read_text(encoding="utf-8",errors="replace").splitlines()
    print("Reference frontend lines:",len(lines))
    for name,line in TARGETS.items():
        found=[]
        for i in range(max(0,line-4),min(len(lines),line+4)):
            if re.search(r"(?<![\w$])"+re.escape(name)+r"(?=\s*\(|\s*=)",lines[i]):
                found.append(i)
        if not found:
            print("NO DEFINITION",name,line)
            continue
        i=found[0]
        sample="\n".join(lines[i:min(len(lines),i+65)])[:a.limit]
        print("\n"+"="*50)
        print("FUNCTION",name,"START LINE",i+1,"excerpt chars",len(sample))
        print(sample)
        print("="*50)

if __name__=="__main__":main()
