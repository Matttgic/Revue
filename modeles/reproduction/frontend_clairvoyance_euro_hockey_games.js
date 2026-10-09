"use strict";
/**
 * Independently reconstructed European hockey match probabilities.
 * Same public Clairvoyance model equations for Liiga, NLA, Extraliga, SHL:
 * actual season/preseason rate blend, last-five goal form, independent
 * Poisson convolution and 50/50 resolution of regulation draws.
 *
 * No original JS source or copyrighted sports data included.
 * Matches require caller-provided, verified source inputs; this is NOT
 * connected to Revue's betting engine or auto-selections.
 */
const {previousSeasonRates}=require("./frontend_clairvoyance_euro_hockey.js");
const {poissonMass,marginDistribution,asianHomeCover}=
  require("./frontend_clairvoyance_soccer_analytic.js");
const LOGIT_SHIFT=.18;

function recentRates(teamId,allGames,count=5){
  const selected=(allGames||[]).filter(g=>g.state==="post" &&
    g.homeScore!=null&&g.awayScore!=null &&
    (g.home===teamId||g.away===teamId));
  selected.sort((a,b)=>new Date(b.date)-new Date(a.date));
  const n=count||5;
  const slice=selected.slice(0,n);
  if(slice.length<3)return null;
  let attack=0,conceded=0;
  for(const g of slice){
    const isHome=g.home===teamId;
    attack+=isHome?g.homeScore:g.awayScore;
    conceded+=isHome?g.awayScore:g.homeScore;
  }
  return {games:slice.length,gf:attack/slice.length,ga:conceded/slice.length};
}
function recentFormDelta(teamId,allGames,base){
  const last=recentRates(teamId,allGames,5);
  if(!last)return null;
  return (last.gf-last.ga)-((base.gf||0)-(base.ga||0));
}
function lastFiveForm(teamId,allGames,base){
  const delta=recentFormDelta(teamId,allGames,base);
  if(delta==null)return 1;
  return 1+Math.max(-.06,Math.min(.06,delta*.05));
}
function clampMargin(p){
  if(!(p>0&&p<1))return p;
  const shifted=Math.log(p/(1-p))+LOGIT_SHIFT;
  return 1/(1+Math.exp(-shifted));
}
function marketHalfGoalLine(value){
  const half=Math.round(parseFloat(value)*2)/2;
  return (Number.isInteger(half)?half+.5:half).toFixed(1);
}

/**
 * @param {string} homeId
 * @param {string} awayId
 * @param {number|string|undefined} marketTotal
 * @param {object} options - {data:{teams,games},formFactor?}
 * The caller can inject a preverified last-five helper; the defaults
 * in this module remain neutral until a full upstream data check passes.
 */
function euroHockeyGame(homeId,awayId,marketTotal,options={}){
  const source=options.data;
  if(!source)return null;
  const h=source.teams[homeId], a=source.teams[awayId];
  if(!h||!a)return null;
  const hRates=previousSeasonRates(h);
  const aRates=previousSeasonRates(a);
  const form=options.formFactor||lastFiveForm;
  const hFactor=form(homeId,source.games,hRates);
  const aFactor=form(awayId,source.games,aRates);
  const homeIce=.055;
  const homeLambda=Math.max(.4,((hRates.gf*hFactor+aRates.ga)/2)*(1+homeIce));
  const awayLambda=Math.max(.4,((aRates.gf*aFactor+hRates.ga)/2)*(1-homeIce*.5));
  const differences=marginDistribution(homeLambda,awayLambda);
  let hWins=0,aWins=0,overtime=0;
  Object.keys(differences).forEach(key=>{
    const margin=parseFloat(key);
    if(margin>0)hWins+=differences[key];
    else if(margin<0)aWins+=differences[key];
    else overtime+=differences[key];
  });
  hWins+=overtime/2;
  aWins+=overtime/2;
  const total=marketTotal!=null
    ?parseFloat(marketTotal)
    :parseFloat(marketHalfGoalLine((hRates.gm+aRates.gm)/2));
  const totalExpected=homeLambda+awayLambda;
  let under=0;
  for(let k=0;k<=Math.floor(total);k++)under+=poissonMass(totalExpected,k);
  const over=1-under;
  const homeTwo=clampMargin(asianHomeCover(homeLambda,awayLambda,-1.5));
  const awayTwo=clampMargin(asianHomeCover(awayLambda,homeLambda,-1.5));
  return {
    hwP:hWins,awP:aWins,
    avgH:homeLambda,avgA:awayLambda,avgT:totalExpected,
    overP:over,otP:overtime,ouLine:total,
    rl15:homeTwo,rl15A:awayTwo,rlN:1-homeTwo
  };
}
function liigaMatch(home,away,ou,opts){return euroHockeyGame(home,away,ou,opts);}
function swissMatch(home,away,ou,opts){return euroHockeyGame(home,away,ou,opts);}
function czechMatch(home,away,ou,opts){return euroHockeyGame(home,away,ou,opts);}
function shlMatch(home,away,ou,opts){return euroHockeyGame(home,away,ou,opts);}
module.exports={euroHockeyGame,liigaMatch,swissMatch,czechMatch,shlMatch,
  clampMargin,marketHalfGoalLine,recentRates,recentFormDelta,lastFiveForm};
