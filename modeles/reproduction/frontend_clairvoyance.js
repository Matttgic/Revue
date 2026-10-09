"use strict";
/**
 * Behavioural reproductions of three named functions of Clairvoyance/docs/app.html.
 * Do not use this experimental file to create live picks.
 * Verified separately against ORIGINAL functions on the SAME synthetic inputs
 * by the GitHub Actions parity workflow.
 *
 * API injects dependencies for repeatability; it does not change formulas.
 */

function nbaGetBayes(abbr, { teams = {}, standings = {}, ratings = {}, ledger = [] } = {}) {
  const t = teams[abbr];
  const liveStand = standings[abbr];
  const tr = ratings[abbr];
  if (!t && !liveStand && !tr) return { m: .5 };
  let al, bl;
  if (tr && tr.priorWinPct != null) {
    al = 15 * tr.priorWinPct + (tr.current?.w || 0) + 1;
    bl = 15 * (1 - tr.priorWinPct) + (tr.current?.l || 0) + 1;
  } else {
    al = (t ? t.pw : parseInt(liveStand?.w) || 0) + 1;
    bl = (t ? t.pl : parseInt(liveStand?.l) || 0) + 1;
  }
  if (!(tr && tr.priorWinPct != null)) {
    for (const pick of ledger) {
      if (pick.outcome === "pending" || pick.sport !== "NBA" ||
          pick.hScore == null || pick.aScore == null) continue;
      const home = pick.hA === abbr, away = pick.awA === abbr;
      if (!home && !away) continue;
      const won = (home && pick.hScore > pick.aScore) ||
                  (away && pick.aScore > pick.hScore);
      if (won) al++;
      else bl++;
    }
  }
  return { m: al / (al + bl) };
}

function nflBayes(abbr, standings = {}) {
  const s = standings?.[abbr];
  const w = parseFloat(s?.wins) || 0;
  const l = parseFloat(s?.losses) || 0;
  return { m: (w + 1) / (w + l + 2), w, l };
}

function ml2decimal(line) {
  const parsed = parseFloat(line);
  return parsed > 0 ? parsed / 100 + 1 : 100 / Math.abs(parsed) + 1;
}

function footballCal(p, calibrator) {
  const adjusted = typeof calibrator === "function" ? calibrator(p, "SOC") : p;
  return Math.min(.96, Math.max(.02, adjusted));
}

function soccerMarketBlend(hP, dP, aP, hML, dML, aML,
                           weights = { model: .75, market: .25 }, calibrator) {
  if (hML == null || dML == null || aML == null) {
    return { hP: footballCal(hP, calibrator), dP: footballCal(dP, calibrator),
             aP: footballCal(aP, calibrator), blended: false };
  }
  const hd = ml2decimal(hML), dd = ml2decimal(dML), ad = ml2decimal(aML);
  if (!(hd > 1) || !(dd > 1) || !(ad > 1)) {
    return { hP: footballCal(hP, calibrator), dP: footballCal(dP, calibrator),
             aP: footballCal(aP, calibrator), blended: false };
  }
  const ih = 1 / hd, id = 1 / dd, ia = 1 / ad, over = ih + id + ia;
  if (!(over > 0)) {
    return { hP: footballCal(hP, calibrator), dP: footballCal(dP, calibrator),
             aP: footballCal(aP, calibrator), blended: false };
  }
  const mh = ih / over, md = id / over, ma = ia / over;
  const w = weights.market, mw = weights.model;
  const bh = mw * hP + w * mh, bd = mw * dP + w * md, ba = mw * aP + w * ma;
  const sum = bh + bd + ba || 1;
  return { hP: footballCal(bh / sum, calibrator),
           dP: footballCal(bd / sum, calibrator),
           aP: footballCal(ba / sum, calibrator),
           blended: true, marketH: mh, marketD: md, marketA: ma };
}

/**
 * Exact behavioural reconstruction of original _soccerMC (independent
 * Knuth-Poisson draws, no truncated analytic approximation). A deterministic
 * RNG can be injected ONLY for source-vs-replica parity tests; ordinary
 * evaluation uses Math.random like the original.
 */
function soccerMonteCarlo(hxg, axg, n, random = Math.random) {
  if (!n) n = 25000;
  hxg = (hxg != null && !isNaN(hxg) && hxg > 0) ? hxg : .9;
  axg = (axg != null && !isNaN(axg) && axg > 0) ? axg : .9;
  let hW = 0, draw = 0, aW = 0, hG = 0, aG = 0;
  let over25 = 0, over35 = 0, btts = 0;
  function poisson(lam) {
    const limit = Math.exp(-lam);
    let product = 1, k = 0;
    do { k++; product *= random(); } while (product > limit);
    return k - 1;
  }
  for (let i = 0; i < n; i++) {
    const h = poisson(hxg), a = poisson(axg);
    hG += h;
    aG += a;
    const goals = h + a;
    if (h > a) hW++;
    else if (h === a) draw++;
    else aW++;
    if (goals > 2.5) over25++;
    if (goals > 3.5) over35++;
    if (h > 0 && a > 0) btts++;
  }
  return { hWin:hW/n, draw:draw/n, aWin:aW/n, avgH:hG/n, avgA:aG/n,
           avgT:(hG+aG)/n, over25:over25/n, over35:over35/n,
           btts:btts/n, hxg, axg, n };
}

module.exports = { nbaGetBayes, nflBayes, soccerMarketBlend, soccerMonteCarlo,
                   ml2decimal, footballCal };
