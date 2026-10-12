"""Méthodes de retrait de marge vectorisées (réécriture indépendante, formules publiques)."""
import numpy as np
def bisect_rows(g, lo, hi, nrows, it=90):
    """Trouve x par ligne tel que g(x) = 0, g croissante ou décroissante (signe testé)."""
    a = np.full(nrows, float(lo)); b = np.full(nrows, float(hi))
    ga = g(a)
    for _ in range(it):
        m = (a + b) / 2; gm = g(m)
        same = np.sign(gm) == np.sign(ga)
        a = np.where(same, m, a); ga = np.where(same, gm, ga); b = np.where(same, b, m)
    return (a + b) / 2
def basic(io): return io / io.sum(1, keepdims=True)
def additive(io):
    n = io.shape[1]; return io - (io.sum(1, keepdims=True) - 1) / n
def wpo(io):
    n = io.shape[1]; o = 1 / io; M = io.sum(1, keepdims=True) - 1
    return 1 / (n * o / (n - M * o))
def power(io):
    k = bisect_rows(lambda k: (io ** k[:, None]).sum(1) - 1, 1.0, 3.0, io.shape[0])
    return io ** k[:, None]
def odds_ratio(io):
    f = lambda c: (io / (c[:, None] + io - c[:, None] * io)).sum(1) - 1
    c = bisect_rows(f, 1.0, 5.0, io.shape[0]); return io / (c[:, None] + io - c[:, None] * io)
def shin(io):
    B = io.sum(1, keepdims=True)
    p = lambda z: (np.sqrt(z[:, None] ** 2 + 4 * (1 - z[:, None]) * io ** 2 / B) - z[:, None]) / (2 * (1 - z[:, None]))
    z = bisect_rows(lambda z: p(z).sum(1) - 1, 0.0, 0.4, io.shape[0]); return p(z)
def goto(io):
    se = np.sqrt(1 - io); z = (io.sum(1, keepdims=True) - 1) / se.sum(1, keepdims=True)
    return io - z * se
def balanced_books(io):
    n = io.shape[1]; z = (io.sum(1, keepdims=True) - 1) / (n - 1); return (io - z) / (1 - z)
METHODS = {"multiplicative": basic, "additive": additive, "wpo": wpo, "power": power,
           "odds_ratio": odds_ratio, "shin": shin, "goto": goto, "balanced_books": balanced_books}
