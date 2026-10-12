import sys, json, numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1], usecols=["MatchDate","HomeTeam","HomeElo","FTResult"]); df["MatchDate"]=pd.to_datetime(df.MatchDate)
elo = pd.read_csv(sys.argv[2]); elo["date"]=pd.to_datetime(elo.date)
df = df.dropna(subset=["HomeElo"]).reset_index(drop=True)
e = elo.rename(columns={"club":"HomeTeam"}).sort_values("date")
d = df.sort_values("MatchDate")
prev = pd.merge_asof(d, e[["date","HomeTeam","elo"]].rename(columns={"date":"d_prev","elo":"elo_prev"}), left_on="MatchDate", right_on="d_prev", by="HomeTeam", direction="backward", allow_exact_matches=False)
nxt = pd.merge_asof(d, e[["date","HomeTeam","elo"]].rename(columns={"date":"d_next","elo":"elo_next"}), left_on="MatchDate", right_on="d_next", by="HomeTeam", direction="forward", allow_exact_matches=True)
m = prev.join(nxt[["d_next","elo_next"]])
m["eq_prev"] = (m.HomeElo-m.elo_prev).abs()<0.006; m["eq_next"]=(m.HomeElo-m.elo_next).abs()<0.006
m["amb"] = m.eq_prev & m.eq_next
m["year"]=m.MatchDate.dt.year
out = {"n": len(m), "egal_photo_strictement_anterieure": float(m.eq_prev.mean()), "egal_photo_du_jour_ou_posterieure": float(m.eq_next.mean()), "egal_aux_deux_(Elo_inchange)": float(m.amb.mean()), "aucune_des_deux": float((~m.eq_prev & ~m.eq_next).mean())}
only_next = m[m.eq_next & ~m.eq_prev]
out["uniquement_photo_posterieure"] = {"n": len(only_next), "part": len(only_next)/len(m), "jours_apres_match_quantiles": [float(x) for x in (only_next.d_next-only_next.MatchDate).dt.days.quantile([.1,.5,.9])], "par_annee": only_next.year.value_counts().sort_index().to_dict()}
# Effet : la photo postérieure contient-elle le résultat ? comparer écart (next - prev) selon résultat domicile
z = m.dropna(subset=["elo_prev","elo_next"]); z = z[z.eq_next & ~z.eq_prev]
out["variation_elo_photo_post_moins_ant_selon_resultat"] = z.assign(dv=z.elo_next-z.elo_prev).groupby("FTResult").dv.mean().round(2).to_dict()
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
