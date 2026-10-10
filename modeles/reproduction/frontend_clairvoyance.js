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

/** Identical NBA Elo win-probability transform from the original frontend.
 * No new strength ratings, market assumptions or extra home advantage.
 */
function nbaEloWinProbability(eloHome,eloAway) {
  return 1/(1+Math.pow(10,(eloAway-eloHome)/400));
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

/**
 * Faithful formula of original nbaMC, including fallback order, points per
 * possession, HCA as a margin shift, separate normal score draws, and
 * 50.3/49.7 split of simulated ties. No new predictive coefficients.
 */
function nbaMonteCarlo(homeAbbr, awayAbbr, n = 25000, ouLine = 220.5,
                       {teamAdv = {}, priorRatings = {}, staticBBref = {},
                        teams = {}, random = Math.random} = {}) {
  const liveAdv = teamAdv || {};
  const h = staticBBref[homeAbbr], aw = staticBBref[awayAbbr];
  function priorAdv(abbr) {
    const pr = priorRatings?.[abbr]?.prior;
    return pr && pr.ortg != null && pr.drtg != null
      ? {ortg: pr.ortg, drtg: pr.drtg, pace: pr.pace} : undefined;
  }
  const hLive = liveAdv[homeAbbr] || priorAdv(homeAbbr);
  const aLive = liveAdv[awayAbbr] || priorAdv(awayAbbr);
  const ht = teams[homeAbbr], awt = teams[awayAbbr];
  if (!ht && !awt && !hLive && !aLive) return null;

  const LG_ORTG = 114.5, LG_DRTG = 114.5, LG_PACE = 99.0, LG_TS = .570;
  const hOrtg = hLive?.ortg ?? (h ? h.p100.ortg : LG_ORTG);
  const hDrtg = hLive?.drtg ?? (h ? h.p100.drtg : LG_DRTG);
  const aOrtg = aLive?.ortg ?? (aw ? aw.p100.ortg : LG_ORTG);
  const aDrtg = aLive?.drtg ?? (aw ? aw.p100.drtg : LG_DRTG);
  const pace = ((hLive?.pace ?? (h ? h.p100.pace : LG_PACE)) +
                (aLive?.pace ?? (aw ? aw.p100.pace : LG_PACE))) / 2;
  const advAll = Object.values(liveAdv).filter(t => t && t.ortg != null && t.drtg != null);
  const lgDrtg = advAll.length >= 10
    ? advAll.reduce((total,t) => total + t.drtg,0) / advAll.length
    : 115.7;
  const poss = pace / 100, HCA = 2.9;
  const hProj = hOrtg * (aDrtg / lgDrtg) * poss + HCA / 2;
  const aProj = aOrtg * (hDrtg / lgDrtg) * poss - HCA / 2;
  const hTS = hLive?.ts_pct ?? (h ? h.p100.ts_pct : LG_TS);
  const aTS = aLive?.ts_pct ?? (aw ? aw.p100.ts_pct : LG_TS);
  const hSD = Math.max(8,18-(hTS-.56)*40);
  const aSD = Math.max(8,18-(aTS-.56)*40);
  let hw=0,aw2=0,hT=0,aT=0,ts=0,ov=0;
  for (let i=0;i<n;i++) {
    const u1=random()||1e-10,u2=random();
    const z1=Math.sqrt(-2*Math.log(u1))*Math.cos(2*Math.PI*u2);
    const z2=Math.sqrt(-2*Math.log(random()||1e-10))*Math.cos(2*Math.PI*random());
    const hs=Math.max(70,Math.round(hProj+z1*hSD));
    const as=Math.max(70,Math.round(aProj+z2*aSD));
    hT+=hs;aT+=as;
    if(hs>as)hw++;else if(as>hs)aw2++;else ts++;
    if(hs+as>ouLine)ov++;
  }
  hw+=Math.round(ts*.503);aw2+=Math.round(ts*.497);
  return { hwP:hw/n,avgH:+(hT/n).toFixed(1),avgA:+(aT/n).toFixed(1),
           avgT:+((hT+aT)/n).toFixed(1),spread:+((hT-aT)/n).toFixed(1),
           overP:ov/n,underP:1-ov/n };
}

/**
 * Reproduction of nflMC's numerical core with injected injury and weather
 * sources. Dependency injection is mandatory for source-conditional parity:
 * accurate current injuries are NOT available from these test fixtures.
 */
function nflWeatherImpact(wx) {
  if (!wx) return {totalAdj:0,label:""};
  let totalAdj=0;
  const notes=[];
  const wind=wx.wind||0, precip=wx.precip||0, temp=wx.temp!=null?wx.temp:65, snow=wx.snow||0;
  if(wind>=20){totalAdj-=2.5;notes.push(wind+"mph wind");}
  else if(wind>=12){totalAdj-=1.0;notes.push(wind+"mph wind");}
  if(snow>=.3){totalAdj-=6.5;notes.push('heavy snow ('+snow+'"/hr)');}
  else if(snow>0){totalAdj-=1.2;notes.push('snow ('+snow+'"/hr)');}
  if(precip>=70){totalAdj-=1.5;notes.push("high rain risk");}
  else if(precip>=40){totalAdj-=.5;notes.push("rain possible");}
  if(temp<25){totalAdj-=1.5;notes.push("hard freeze");}
  else if(temp<40){totalAdj-=.7;notes.push("cold");}
  totalAdj=Math.max(-6.5,Math.min(1,totalAdj));
  return {totalAdj:+totalAdj.toFixed(2),label:notes.join(" · ")};
}

function nflHalfLine(value) {
  const rounded=Math.round(parseFloat(value)*2)/2;
  return (Number.isInteger(rounded)?rounded+.5:rounded).toFixed(1);
}
function nflBoxMuller(random) {
  const u1=random()||1e-10,u2=random();
  return Math.sqrt(-2*Math.log(u1))*Math.cos(2*Math.PI*u2);
}
const NO_NFL_INJURY = () => ({pts:0,players:[],any:false});
function nflMonteCarlo(homeAbbr, awayAbbr, n, ouLine, game,
                       { data = null, hfa = 1.8, injury = NO_NFL_INJURY,
                         weather = {}, weatherImpact = nflWeatherImpact,
                         random = Math.random, marginSigma = 13.5,
                         totalSigma = 10.0, lgTotal = 44,
                         injuryTotalShare = .5 } = {}) {
  const D=data;
  if (!D) return null;
  const hs=D.standings[homeAbbr],as=D.standings[awayAbbr];
  const num = v => {const x=parseFloat(v);return isNaN(x)?null:x;};
  const hg=(num(hs?.wins)??0)+(num(hs?.losses)??0)+(num(hs?.ties)??0);
  const ag=(num(as?.wins)??0)+(num(as?.losses)??0)+(num(as?.ties)??0);
  const hdiff=(hs&&hg>0)?num(hs.differential)/hg:null;
  const adiff=(as&&ag>0)?num(as.differential)/ag:null;
  const hasDiff=hdiff!=null&&adiff!=null;
  const marketMargin=(game&&game.spread!=null)?-parseFloat(game.spread):null;
  if(!hasDiff&&marketMargin==null)return null;
  const hOff=D.stats[homeAbbr]?.offense||{},aOff=D.stats[awayAbbr]?.offense||{};
  const hDef=D.stats[homeAbbr]?.defenseAllowed||{},aDef=D.stats[awayAbbr]?.defenseAllowed||{};
  let yards=0;
  const hy=(num(hOff.netPassingYardsPerGame)??0)+(num(hOff.rushingYardsPerGame)??0);
  const aDY=(num(aDef.yardsPerGame)??0);
  const ay=(num(aOff.netPassingYardsPerGame)??0)+(num(aOff.rushingYardsPerGame)??0);
  const hDY=(num(hDef.yardsPerGame)??0);
  if(hy&&aDY&&ay&&hDY){
    const he=hy-aDY,ae=ay-hDY;
    yards=Math.max(-3,Math.min(3,(he-ae)/16));
  }
  let takeaways=0;
  const ht=num(hDef.totalTakeaways),at=num(aDef.totalTakeaways);
  if(ht!=null&&at!=null)takeaways=Math.max(-1.5,Math.min(1.5,(ht-at)*.15));
  const homeBonus=game?.neutralSite?0:hfa;
  const injH=injury(homeAbbr,game),injA=injury(awayAbbr,game);
  const injMargin=hasDiff?(injA.pts-injH.pts):0;
  const margin0=hasDiff?((hdiff-adiff)+homeBonus+yards+takeaways+injMargin):
    (marketMargin+yards+takeaways);
  const hPts=num(hOff.totalPointsPerGame),aPts=num(aOff.totalPointsPerGame);
  const hAllowed=num(hDef.totalPointsPerGame),aAllowed=num(aDef.totalPointsPerGame);
  let baseTotal;
  if(hPts!=null&&aPts!=null&&hAllowed!=null&&aAllowed!=null){
    const he=(hPts+aAllowed)/2,ae=(aPts+hAllowed)/2;
    baseTotal=he+ae;
  }else baseTotal=lgTotal;
  const injTotal=-(injH.pts+injA.pts)*injuryTotalShare;
  baseTotal+=injTotal;
  const wxKey=game&&(game.id||(game.city+game.date));
  const wx=wxKey?weather[wxKey]:null;
  const impact=wx?weatherImpact(wx):{totalAdj:0,label:""};
  baseTotal=Math.max(20,baseTotal+impact.totalAdj);
  const finalOU=ouLine!=null?parseFloat(ouLine):parseFloat(nflHalfLine(baseTotal));
  n=n||15000;
  let hw=0,ov=0,marginSum=0,totalSum=0,hScoreSum=0,aScoreSum=0;
  for(let i=0;i<n;i++){
    const margin=margin0+nflBoxMuller(random)*marginSigma;
    const total=Math.max(20,baseTotal+nflBoxMuller(random)*totalSigma);
    marginSum+=margin;totalSum+=total;
    if(margin>0)hw++;
    if(total>finalOU)ov++;
    hScoreSum+=Math.max(0,(total+margin)/2);
    aScoreSum+=Math.max(0,(total-margin)/2);
  }
  const avgMargin=marginSum/n,avgTotal=totalSum/n;
  return {
    hwP:hw/n,avgMargin:+avgMargin.toFixed(1),avgTotal:+avgTotal.toFixed(1),
    avgH:+(hScoreSum/n).toFixed(1),avgA:+(aScoreSum/n).toFixed(1),
    overP:ov/n,underP:1-ov/n,ouLine:+finalOU.toFixed(1),n,
    wx,wxImpact:impact,hasDiff,marketMargin,
    margin0:+margin0.toFixed(2),baseTotal:+baseTotal.toFixed(2),
    inj:{h:injH,a:injA,margin:injMargin,total:injTotal,marginApplied:hasDiff},
  };
}

/** Exact nflEns weighting and calibration; uses the original MC formula. */
function nflEnsemble(homeAbbr,awayAbbr,ouLine,game,
                     {data=null,weights={mc:.75,bay:.25},calibrator,...opts}={}){
  const mc=nflMonteCarlo(homeAbbr,awayAbbr,25000,ouLine,game,{data,...opts});
  if(!mc)return{p:.5,mc:.5,bay:.5,mcD:null};
  const standings=data?.standings||{};
  const hp=nflBayes(homeAbbr,standings),ap=nflBayes(awayAbbr,standings);
  const bayP=Math.min(.92,Math.max(.08,hp.m/(hp.m+ap.m)+.015));
  const w=weights||{mc:.75,bay:.25};
  let p=mc.hwP*w.mc+bayP*w.bay;
  p=Math.min(.92,Math.max(.08,p));
  p=typeof calibrator==="function"?calibrator(p,"NFL"):p;
  return{p,mc:mc.hwP,bay:bayP,mcD:mc};
}

/**
 * Source-equivalent NBA ensemble formula: corrected adaptive weights,
 * 2.8-point home-court probability shift, 25% market blend, injury penalties,
 * and the strict 6.5-percentage-point no-vig market guardrail.
 * Dependency inputs are injected for direct original-vs-replica parity.
 */
function nbaEnsemble(homeAbbr,awayAbbr,espnGame,
                     {teamAdv={},priorRatings={},staticBBref={},teams={},
                      standings={},ledger=[],elo={},weights={mc:.50,bay:.20,elo:.30},
                      injuries={},calibrator=p=>p,random=Math.random}={}){
  const nbaOUL=parseFloat(espnGame?.ou||espnGame?.overUnder||220.5);
  const mc=nbaMonteCarlo(homeAbbr,awayAbbr,25000,nbaOUL,{
    teamAdv,priorRatings,staticBBref,teams,random
  });
  if(!mc)return{p:.5,mc:.5,bay:.5,elo:.5,mcD:null};
  const hfa=.028;
  const hBay=nbaGetBayes(homeAbbr,{teams,standings,ratings:priorRatings,ledger}).m;
  const aBay=nbaGetBayes(awayAbbr,{teams,standings,ratings:priorRatings,ledger}).m;
  const bay=Math.min(.90,Math.max(.10,hBay/(hBay+aBay)+hfa));
  const eloHome=elo[homeAbbr]||1550,eloAway=elo[awayAbbr]||1550;
  const eloP=Math.min(.90,Math.max(.10,
    1/(1+Math.pow(10,(eloAway-eloHome)/400))+hfa));
  const w=weights||{mc:.50,bay:.20,elo:.30};
  let p=Math.min(.90,Math.max(.10,
    (mc.hwP*(.45/.50)*w.mc+bay*(.30/.20)*w.bay+eloP*(.25/.30)*w.elo)));
  if(espnGame?.hL){
    const line=ml2decimal(espnGame.hL);
    const implied=Math.min(.88,Math.max(.12,1/line));
    p=p*.75+implied*.25;
  }
  p=calibrator(p,"NBA");
  const injH=injuries[homeAbbr]||{penalty:0},injA=injuries[awayAbbr]||{penalty:0};
  p=Math.min(.90,Math.max(.10,p-injH.penalty+injA.penalty));
  let mkt=null,capped=false;
  if(espnGame?.hL){
    const ih=1/ml2decimal(espnGame.hL);
    const ia=espnGame?.aL?1/ml2decimal(espnGame.aL):null;
    mkt=ia!=null?ih/(ih+ia):ih/1.045;
    const lo=Math.max(.10,mkt-.065),hi=Math.min(.90,mkt+.065);
    const pc=Math.min(hi,Math.max(lo,p));
    if(pc!==p){capped=true;p=pc;}
  }
  return{p,mc:mc.hwP,bay,elo:eloP,mcD:mc,injH,injA,mkt,capped};
}

module.exports = { nbaGetBayes, nbaEloWinProbability, nflBayes, soccerMarketBlend, soccerMonteCarlo,
                   nbaMonteCarlo, nbaEnsemble, nflWeatherImpact, nflMonteCarlo,
                   nflEnsemble, ml2decimal, footballCal };
