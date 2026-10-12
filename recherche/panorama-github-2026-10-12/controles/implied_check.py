import math, json
import numpy as np
def brentq(f,a,b,xtol=1e-15):
    fa=f(a)
    for _ in range(200):
        m=(a+b)/2; fm=f(m)
        if (fm>0)==(fa>0): a,fa=m,fm
        else: b=m
    return (a+b)/2
EPS4 = np.finfo(float).eps ** 0.25
def shin_func(z, io):
    B = io.sum(); return (np.sqrt(z*z + 4*(1-z)*io**2/B) - z) / (2*(1-z))
def shin_js_R(odds, maxit=1000):
    """Port fidèle de la boucle R 'js' (y compris l'ordre break/assignation)."""
    io = 1/np.asarray(odds, float); B = io.sum(); n = len(io)
    z = 0.0; zstore = 0.0; probs = None
    for jj in range(1, maxit+1):
        zprev = z
        with np.errstate(divide='ignore', invalid='ignore'):
            num = np.sqrt(zprev**2 + 4*(1-zprev)*io**2/B).sum() - 2
            z = float(np.float64(num) / np.float64(n-2))  # division R : x/0 -> Inf ou NaN
        d = abs(z - zprev)
        if math.isnan(d):
            return {"erreur_R": "missing value where TRUE/FALSE needed", "iteration": jj}
        if d <= EPS4: break
        zstore = z; probs = shin_func(z, io)
    return {"z": zstore, "probs": None if probs is None else (probs/probs.sum()).tolist(), "iterations": jj}
def shin_exact(odds):
    io = 1/np.asarray(odds, float)
    z = brentq(lambda z: shin_func(z, io).sum() - 1, 0, 0.5, xtol=1e-15)
    return {"z": z, "probs": shin_func(z, io).tolist()}
out = {}
for name, o in {"1N2 [4.20,3.70,1.95]": [4.20,3.70,1.95], "1N2 [1.19,7.0,14.0]": [1.19,7.0,14.0], "6 issues test my_odds2": list(1/np.array([0.870,0.2,0.1,0.05,0.02,0.01]))}.items():
    js, ex = shin_js_R(o), shin_exact(o)
    out[name] = {"js_R": js, "exact": ex, "ecart_max_proba": float(np.max(np.abs(np.array(js["probs"]) - np.array(ex["probs"])))), "ecart_z": js["z"] - ex["z"]}
out["2 issues [1.90,1.90]"] = {"js_R": shin_js_R([1.90,1.90]), "exact": shin_exact([1.90,1.90])}
out["2 issues [1.25,4.00]"] = {"js_R": shin_js_R([1.25,4.00]), "exact": shin_exact([1.25,4.00])}
# marge nulle : la boucle s'arrête à l'itération 1 avant d'avoir rempli probs
out["3 issues sans marge [2,4,4]"] = shin_js_R([2,4,4])
# goto/ooepc : zvalues écrase par probs
io = 1/np.array([4.20,3.70,1.95]); se = np.sqrt(1-io); zval = (io.sum()-1)/se.sum()
out["goto zvalues attendu (scalaire)"] = float(zval)
out["goto zvalues renvoye par le code (= probs)"] = (io - zval*se).tolist()
print(json.dumps(out, indent=1, default=float))
