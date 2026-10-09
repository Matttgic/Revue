"use strict";
/**
 * Independent parity-focused reconstruction of the four source European
 * hockey *ensemble* formulas (not a new statistical strategy).
 *
 * Caller MUST provide validated market and calibration adapters where
 * available. Missing odds leave the original unblended model probability.
 * The adapter behaviour is verified via same-input test doubles until
 * actual providers are reconstructed. No bets are made.
 */
const {euroHockeyGame}=require("./frontend_clairvoyance_euro_hockey_games.js");

function majorMargin(teamId,games){
  const finals=(games||[]).filter(game=>game.state==="post" &&
    game.homeScore!=null && game.awayScore!=null &&
    (game.home===teamId||game.away===teamId));
  if(!finals.length)return null;
  let big=0;
  for(const g of finals){
    const margin=(g.home===teamId ? g.homeScore-g.awayScore :
                                     g.awayScore-g.homeScore);
    if(margin>=2)big++;
  }
  return {big,n:finals.length};
}
function squash(p,low=.05,high=.95){
  return Math.min(high,Math.max(low,p));
}
function euroEnsemble(league,homeId,awayId,marketTotal,game,opts={}){
  const mc=euroHockeyGame(homeId,awayId,marketTotal,{data:opts.data});
  if(!mc)return {p:.5};
  const data=opts.data;
  const h=data.teams[homeId], a=data.teams[awayId];
  const winRate=team=>{
    if(!team)return .5;
    return ((team.w||0)+1)/((team.gp||0)+2);
  };
  const ph=winRate(h),pa=winRate(a);
  const bayD=ph*(1-pa)+pa*(1-ph);
  const share=bayD?ph*(1-pa)/bayD:.5;
  const coefficients=opts.weights || {mc:.7,bay:.2,elo:.1};
  const posteriorShare=(coefficients.bay||0)+(coefficients.elo||0);
  const calibrate=opts.calibrate||((p)=>p);
  const score=squash(mc.hwP*(coefficients.mc??.7)+share*posteriorShare);
  const pModel=calibrate(score,league.toUpperCase());
  const played=Math.min((h&&h.gp)||0,(a&&a.gp)||0);
  const lineMoney=(opts.moneylineBlend||(()=>null))(pModel,game,played);
  const p=lineMoney?lineMoney.p:pModel;
  const favorite=p>=.5?homeId:awayId;
  const opponent=p>=.5?awayId:homeId;
  const empirical=x=>x?(x.big+1)/(x.n+2):.5;
  const favored=empirical(majorMargin(favorite,data.games));
  const underdog=empirical(majorMargin(opponent,data.games));
  const denominator=favored*(1-underdog)+underdog*(1-favored);
  const marginEstimate=denominator?favored*(1-underdog)/denominator:.5;
  const winByTwo=p>=.5?mc.rl15:mc.rl15A;
  let covered=squash(.9*winByTwo+.1*marginEstimate);
  const adjust=opts.adjustByMarketType;
  if(typeof adjust==="function"){
    const changed=adjust(covered,"SPREAD",league.toUpperCase());
    if(changed>0&&changed<1)covered=changed;
  }
  const lineSpread=(opts.spreadBlend||(()=>null))(covered,game,p>=.5,played);
  if(lineSpread)covered=lineSpread.p;
  const lineOver=(opts.totalBlend||(()=>null))(mc.overP,game,mc.ouLine,played);
  return {
    p,pModel,mcD:mc,
    mc:coefficients.mc??.7,
    bay:posteriorShare,elo:0,
    favCoverP:covered,dogCoverP:1-covered,
    ouP:lineOver?lineOver.p:mc.overP,
    mkt:{ml:lineMoney,pl:lineSpread,ou:lineOver}
  };
}
function liigaEnsemble(home,away,total,game,opts){return euroEnsemble("liiga",home,away,total,game,opts);}
function swissEnsemble(home,away,total,game,opts){return euroEnsemble("nla",home,away,total,game,opts);}
function czechEnsemble(home,away,total,game,opts){return euroEnsemble("extraliga",home,away,total,game,opts);}
function shlEnsemble(home,away,total,game,opts){return euroEnsemble("shl",home,away,total,game,opts);}
module.exports={euroEnsemble,liigaEnsemble,swissEnsemble,czechEnsemble,
 shlEnsemble,majorMargin};
