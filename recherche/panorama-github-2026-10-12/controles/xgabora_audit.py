import sys, json, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); from devig_lib import METHODS
df = pd.read_csv(sys.argv[1], low_memory=False); df["MatchDate"] = pd.to_datetime(df.MatchDate)
out = {"lignes": len(df), "periode": [str(df.MatchDate.min().date()), str(df.MatchDate.max().date())]}
# --- 1. Forme : recalcul à partir des matchs précédents (même table)
long = pd.concat([
  pd.DataFrame({"i": df.index, "d": df.MatchDate, "team": df.HomeTeam, "pts": df.FTResult.map({"H":3,"D":1,"A":0}), "side": "H"}),
  pd.DataFrame({"i": df.index, "d": df.MatchDate, "team": df.AwayTeam, "pts": df.FTResult.map({"A":3,"D":1,"H":0}), "side": "A"})]).sort_values(["team","d","i"])
g = long.groupby("team")["pts"]
long["prev3"] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=3).sum())
long["incl3"] = g.transform(lambda s: s.rolling(3, min_periods=3).sum())
h = long[long.side=="H"].set_index("i")
cmp = df[["Form3Home"]].join(h[["prev3","incl3"]]).dropna()
out["forme3_domicile"] = {"n_compares": len(cmp), "egal_3_matchs_precedents": float((cmp.Form3Home==cmp.prev3).mean()), "egal_fenetre_incluant_match": float((cmp.Form3Home==cmp.incl3).mean())}
# --- 2. Elo : quelle photo ClubElo est utilisée ?
elo = pd.read_csv(sys.argv[3]); elo["date"] = pd.to_datetime(elo.date)
s = df.sample(4000, random_state=1)[["MatchDate","HomeTeam","HomeElo"]].dropna()
m = s.merge(elo, left_on="HomeTeam", right_on="club")
m["exact"] = (m.elo - m.HomeElo).abs() < 0.006
hits = m[m.exact]; delta = (hits.MatchDate - hits.date).dt.days
out["elo_photo"] = {"echantillon": len(s), "matchs_avec_photo_identique": int(hits[["MatchDate","HomeTeam"]].drop_duplicates().shape[0]), "jours_entre_photo_et_match_min": int(delta.min()) if len(delta) else None, "part_photo_datee_jour_meme_ou_apres": float((delta<=0).mean()) if len(delta) else None, "quantiles_jours": [float(x) for x in delta.quantile([.05,.5,.95])] if len(delta) else None}
# --- 3. Colonnes de clusters : pouvoir prédictif comparé au marché
def auc(score, y):
    r = pd.Series(score).rank().values; y = np.asarray(y, bool); n1 = y.sum(); n0 = len(y)-n1
    return float((r[y].sum() - n1*(n1+1)/2) / (n1*n0))
c = df.dropna(subset=["C_VHD","C_VAD","OddHome","OddAway","HomeElo","AwayElo"])
yH = (c.FTResult=="H").values
out["auc_victoire_domicile"] = {"n": len(c), "marche_1/cote_dom": auc(1/c.OddHome.values, yH), "elo_diff": auc((c.HomeElo-c.AwayElo).values, yH), "cluster_C_VHD_moins_C_VAD": auc((c.C_VHD-c.C_VAD).values, yH)}
# --- 4. Retrait de marge : log-loss 1N2 et Over/Under 2,5
def evaluate(io, y, label):
    res = {}; base = None
    for k, f in METHODS.items():
        if k == "balanced_books" and io.shape[1] == 2: pass
        p = np.clip(f(io), 1e-12, 1); p = p / p.sum(1, keepdims=True)
        ll = -np.log(p[np.arange(len(y)), y])
        if base is None: base = ll
        d = ll - base
        res[k] = {"logloss": round(float(ll.mean()), 6), "brier": round(float(((p - np.eye(io.shape[1])[y])**2).sum(1).mean()), 6),
                  "diff_vs_multiplicatif": round(float(d.mean()), 6), "erreur_type_diff": round(float(d.std(ddof=1)/np.sqrt(len(d))), 6)}
    return {"n": int(len(y)), "marge_moyenne": round(float(io.sum(1).mean()-1), 5), "methodes": res}
x = df.dropna(subset=["OddHome","OddDraw","OddAway","FTResult"]); x = x[(x[["OddHome","OddDraw","OddAway"]]>1).all(1)]
io = 1/x[["OddHome","OddDraw","OddAway"]].values; ok = io.sum(1) > 1.0; x, io = x[ok], io[ok]
y = x.FTResult.map({"H":0,"D":1,"A":2}).values
out["devig_1n2_bet365"] = evaluate(io, y, "1n2")
per = {}
for lab, msk in {"2000-2009": x.MatchDate.dt.year<2010, "2010-2018": (x.MatchDate.dt.year>=2010)&(x.MatchDate.dt.year<2019), "2019-2026": x.MatchDate.dt.year>=2019}.items():
    per[lab] = {k: v["diff_vs_multiplicatif"] for k, v in evaluate(io[msk.values], y[msk.values], lab)["methodes"].items()}
    per[lab]["n"] = int(msk.sum())
out["devig_1n2_par_periode_diff_logloss"] = per
fav = io.max(1) > 1/1.35
out["devig_1n2_gros_favori_cote_<1.35"] = {k: v["diff_vs_multiplicatif"] for k, v in evaluate(io[fav], y[fav], "fav")["methodes"].items()} | {"n": int(fav.sum())}
u = df.dropna(subset=["Over25","Under25","FTHome","FTAway"]); u = u[(u[["Over25","Under25"]]>1).all(1)]
iou = 1/u[["Over25","Under25"]].values; ok = iou.sum(1) > 1.0; u, iou = u[ok], iou[ok]
yu = np.where(u.FTHome + u.FTAway > 2.5, 0, 1)
out["devig_over_under_2_5_bet365"] = evaluate(iou, yu, "ou")
# --- 5. "Meilleure cote" vs probabilité dé-margée Bet365 (illustration, non jouable)
mm = x.dropna(subset=["MaxHome","MaxDraw","MaxAway"]); iom = 1/mm[["OddHome","OddDraw","OddAway"]].values
pf = METHODS["shin"](iom); best = mm[["MaxHome","MaxDraw","MaxAway"]].values; ym = mm.FTResult.map({"H":0,"D":1,"A":2}).values
ev = pf * best - 1; res = {}
for thr in [0.0, 0.02, 0.05]:
    sel = ev > thr; r, c_ = np.nonzero(sel)
    pnl = np.where(ym[r]==c_, best[r, c_]-1, -1.0)
    res[f"EV>{thr}"] = {"paris": int(len(pnl)), "roi": round(float(pnl.mean()),4), "ic95": [round(float(pnl.mean()-1.96*pnl.std(ddof=1)/np.sqrt(len(pnl))),4), round(float(pnl.mean()+1.96*pnl.std(ddof=1)/np.sqrt(len(pnl))),4)]}
out["meilleure_cote_vs_shin_bet365_illustration"] = {"n_matchs": int(len(mm)), "resultats": res}
print(json.dumps(out, indent=1, ensure_ascii=False))
