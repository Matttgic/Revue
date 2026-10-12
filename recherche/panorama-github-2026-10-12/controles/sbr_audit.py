import sys, json, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); from devig_lib import METHODS
def am2dec(a):
    a = np.asarray(a, float); return np.where(a > 0, 1 + a/100, np.where(a < 0, 1 + 100/np.abs(a), np.nan))
out = {}
for sport in ["nhl", "nba", "nfl", "mlb"]:
    d = pd.DataFrame(json.load(open(f"{sys.argv[1]}/{sport}.json")))
    r = {"lignes": len(d), "saisons": [int(d.season.min()), int(d.season.max())]}
    r["doublons_date_equipes"] = int(d.duplicated(["date","home_team","away_team"]).sum())
    hf = pd.to_numeric(d.home_final, errors="coerce"); af = pd.to_numeric(d.away_final, errors="coerce")
    whens = [w for w in ["open", "close"] if f"home_{w}_ml" in d]
    r["colonnes_ml_disponibles"] = whens
    for when in whens:
        h = am2dec(pd.to_numeric(d[f"home_{when}_ml"], errors="coerce")); a = am2dec(pd.to_numeric(d[f"away_{when}_ml"], errors="coerce"))
        s = 1/h + 1/a; ok = np.isfinite(s)
        r[f"{when}_ml"] = {"manquantes_ou_nulles": float(1 - ok.mean()), "somme_implicite_<1": float((s[ok] < 1).mean()), "somme_implicite_>1.10": float((s[ok] > 1.10).mean()), "marge_mediane": round(float(np.median(s[ok]) - 1), 4)}
    # log-loss clôture vs ouverture, méthodes de dé-margination (2 issues)
    res = {}
    for when in ["open", "close"]:
        if when not in whens: res[when] = (np.full(len(d), 2.0), np.full(len(d), 2.0)); continue
        h = am2dec(pd.to_numeric(d[f"home_{when}_ml"], errors="coerce")); a = am2dec(pd.to_numeric(d[f"away_{when}_ml"], errors="coerce"))
        res[when] = (h, a)
    ho, ao = res["open"]; hc, ac = res["close"]
    m = np.isfinite(ho) & np.isfinite(ao) & np.isfinite(hc) & np.isfinite(ac) & np.isfinite(hf) & np.isfinite(af) & (hf != af)
    m &= (1/ho + 1/ao >= 1) & (1/hc + 1/ac > 1) & (1/hc + 1/ac < 1.15) & (1/ho + 1/ao < 1.15)
    y = np.where(hf[m] > af[m], 0, 1)
    ll = {}
    for when, (h, a) in {k: v for k, v in {"open": (ho, ao), "close": (hc, ac)}.items() if k in whens}.items():
        io = np.c_[1/h[m], 1/a[m]]
        base = None
        for k in ["multiplicative", "additive", "power", "shin", "odds_ratio"]:
            p = METHODS[k](io); p = np.clip(p / p.sum(1, keepdims=True), 1e-12, 1)
            l = -np.log(p[np.arange(len(y)), y]); base = l if base is None else base
            ll[f"{when}_{k}"] = {"logloss": round(float(l.mean()), 5), "diff_vs_mult": round(float((l-base).mean()), 6), "se": round(float((l-base).std(ddof=1)/np.sqrt(len(l))), 6)}
    # biais favori-outsider à la clôture (multiplicatif)
    io = np.c_[1/hc[m], 1/ac[m]]; p = io / io.sum(1, keepdims=True); ph = p[:,0]; yh = (y == 0).astype(float)
    bins = pd.cut(ph, [0, .3, .4, .5, .6, .7, 1]); cal = pd.DataFrame({"b": bins, "p": ph, "y": yh}).groupby("b", observed=True).agg(n=("y","size"), p_moy=("p","mean"), freq=("y","mean")).round(4)
    r["n_matchs_evalues_hors_nuls"] = int(m.sum()); r["logloss"] = ll; r["calibration_cloture_domicile"] = {str(k): v for k, v in cal.to_dict("index").items()}
    out[sport] = r
print(json.dumps(out, indent=1, ensure_ascii=False))
