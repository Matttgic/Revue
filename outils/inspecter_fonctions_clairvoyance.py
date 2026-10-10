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
    "liigaEns":12001,
    "nlaEns":12155,
    "extraligaEns":12275,
    "shlEns":13115,
    "_liigaBlendedRates":11931,
    "_nlaBlendedRates":12116,
    "_extraligaBlendedRates":12232,
    "_shlBlendedRates":13078,
    "_socFormFactorRaw":27219,
    "_socFormFactor":27230,
    "_socXGBlendCLDomestic":26831,
    "_socXGFromFBref":26670,
    "_socPoissonPmf":27508,
    "_socMarginDist":27509,
    "_socSpreadProb":27527,
    "_poissonOverProb":27392,
    "_socHomeAdv":26650,
    "_socTeamHomeAwaySplit":26650,
    "_blendLeagueOpta":26784,
    "_socXGRaw":26784,
    "_socXGBlendCLDomestic":26784,
    "_socXGFromFBref":26784,
    "_poisSampler":7600,
    "_hkRecentRates":12350,
    "_hkFormFactorRaw":12380,
    "_hkFormFactor":11920,
    "_hkBlendAlpha":3700,
    "_hkValidDec":3690,
    "HOCKEY_MKT_BLEND_ALPHA":3690,
    "HOCKEY_MKT_BLEND_FULL_GP":3690,
    "HOCKEY_MKT_BLEND_ALPHA_EARLY":3690,
    "_HK_MKT_OVERROUND_MIN":3690,
    "_HK_MKT_OVERROUND_MAX":3690,
    "_HK_MKT_PMIN":3690,
    "_HK_MKT_PMAX":3690,
    "_hkMarginCal":7600,
    "_nhlLiveCf":7600,
    "_nhlFormFactor":7600,
    "_hkBlendNhl":7600,
    "_hkPlLegsAt":7600,
    "_hkMktNoVig":7600,
    "_hkBlendCore":7600,
    "_NHL_LG_PP":7600,
    "_NHL_LG_PK":7600,
    "_NHL_LG_GA60":7600,
    "_boxMullerZ":10000,
    "_nflHFA":10000,
    "_nflInjAdj":10000,
    "_forceHalfLine":10000,
    "cfbWeatherImpact":10000,
    "_NFL_LG_TOTAL":10000,
    "_NFL_SIGMA_MARGIN":10000,
    "_NFL_SIGMA_TOTAL":10000,
    "NFL_INJ_TOTAL_SHARE":10000,
    "_socCal":27425,
    "ml2d":1600,
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
    ap.add_argument("--only",nargs="*",default=None)
    a=ap.parse_args()
    if not 50<=a.limit<=10000:raise ValueError("Bounded excerpts only")
    lines=Path(a.source).read_text(encoding="utf-8",errors="replace").splitlines()
    print("Reference frontend lines:",len(lines))
    for name,line in TARGETS.items():
        if a.only and name not in a.only:continue
        found=[]
        # Inspect a small local vicinity; helpers may sit far from MC code.
        near=range(max(0,line-10),min(len(lines),line+10))
        if name in ("_socFormFactorRaw","_socFormFactor","_socXGBlendCLDomestic","_socXGFromFBref","shlEns","_liigaBlendedRates","_nlaBlendedRates","_extraligaBlendedRates","_shlBlendedRates","_socPoissonPmf","_socMarginDist","_socSpreadProb","_poissonOverProb","_socHomeAdv","_socTeamHomeAwaySplit","_blendLeagueOpta","_socXGRaw","_socXGBlendCLDomestic","_socXGFromFBref","_poisSampler","_hkRecentRates","_hkFormFactorRaw","_hkFormFactor","_hkBlendAlpha","_hkValidDec","HOCKEY_MKT_BLEND_ALPHA","HOCKEY_MKT_BLEND_FULL_GP","HOCKEY_MKT_BLEND_ALPHA_EARLY","_HK_MKT_OVERROUND_MIN","_HK_MKT_OVERROUND_MAX","_HK_MKT_PMIN","_HK_MKT_PMAX","_hkMarginCal","_nhlLiveCf","_nhlFormFactor","_hkBlendNhl","_hkPlLegsAt","_hkMktNoVig","_hkBlendCore","_NHL_LG_PP","_NHL_LG_PK","_NHL_LG_GA60","_socCal","ml2d","_boxMullerZ","_nflHFA","_nflInjAdj","_forceHalfLine","cfbWeatherImpact","_NFL_LG_TOTAL","_NFL_SIGMA_MARGIN","_NFL_SIGMA_TOTAL","NFL_INJ_TOTAL_SHARE"):
            near=range(len(lines))
        for i in near:
            line_text=lines[i].strip()
            if any(line_text.startswith(pre+name+separator)
                   for pre in ("function ","const ","let ","var ")
                   for separator in ("(", "=")):
                found.append(i)
                break
        if not found:
            print("NO DEFINITION",name,line)
            continue
        i=found[0]
        sample="\n".join(lines[i:min(len(lines),i+170)])[:a.limit]
        print("\n"+"="*50)
        print("FUNCTION",name,"START LINE",i+1,"excerpt chars",len(sample))
        print(sample)
        print("="*50)

if __name__=="__main__":main()
