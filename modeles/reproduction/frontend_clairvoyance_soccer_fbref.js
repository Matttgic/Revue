"use strict";
/**
 * Original Clairvoyance formulas faithfully reconstructed:
 * _socXGFromFBref and _socXGBlendCLDomestic.
 *
 * Caller injects actual league home advantage + CL blending parameters.
 * No Opta files or unpublished source used. Tested against the original
 * functions with exact output comparisons in CI.
 */
function homeAway(row){
 const home=row?.homeSplit,away=row?.awaySplit;
 if(!home||!away||home.games<3||away.games<3)return null;
 return {homeGf:home.gf,homeGa:home.ga,awayGf:away.gf,awayGa:away.ga};
}
function fbrefXg(name,key,leagues,homeAdvantages){
 if(!leagues||!name)return null;
 const lowered=name.toLowerCase().trim();
 const keys=key?[key]:Object.keys(leagues);
 for(const league of keys){
  const teams=leagues[league]?.teams;
  if(!teams)continue;
  for(const candidate of Object.keys(teams)){
   const ck=candidate.toLowerCase();
   if(ck===lowered||ck.includes(lowered)||lowered.includes(ck)){
    const stats=teams[candidate];
    const games=stats.mp||34;
    const adv=homeAdvantages[key]??homeAdvantages.default;
    const split=homeAway(stats);
    return {
      xg:stats.xg/games,
      xga:stats.xga/games,
      hxg:split?split.homeGf:stats.xg/games*(1+adv),
      hxga:split?split.homeGa:stats.xga/games*(1-adv),
      axg:split?split.awayGf:stats.xg/games*(1-adv),
      axga:split?split.awayGa:stats.xga/games*(1+adv),
      gf:stats.gf/games,ga:stats.ga/games,mp:games,
      poss:stats.poss,xag:stats.xag,shotsPg:stats.shots_pg,
      sotPg:stats.sot_pg,recentForm:stats.recentForm,
      homeSplit:stats.homeSplit,awaySplit:stats.awaySplit,
      matchLog:stats.matchLog,gamesPlayedThisSeason:stats.gamesPlayedThisSeason,
      homeSplitUsed:!!split,src:"fbref"
    };
   }
  }
 }
 return null;
}
function championsContext(name,leagues,homeAdvantages,params){
 let dom=null;
 for(const league of params.domesticLeagues){
  if(fbrefXg(name,league,leagues,homeAdvantages)){dom=league;break;}
 }
 if(!dom)return null;
 const cl=fbrefXg(name,"cl",leagues,homeAdvantages);
 const games=(cl&&cl.gamesPlayedThisSeason)||0;
 const share=params.weightMax*Math.min(games,params.rampGames)/params.rampGames;
 return {domKey:dom,wCL:share,wDom:1-share};
}
function clDomesticXg(name,leagues,homeAdvantages,params){
 const champions=fbrefXg(name,"cl",leagues,homeAdvantages);
 const ctx=championsContext(name,leagues,homeAdvantages,params);
 if(!champions&&!ctx)return null;
 if(!ctx)return champions;
 const domestic=fbrefXg(name,ctx.domKey,leagues,homeAdvantages);
 if(!champions)return domestic;
 const blended=(a,b)=>a==null||b==null?(a==null?b:a):a*ctx.wCL+b*ctx.wDom;
 return {
  xg:blended(champions.xg,domestic.xg),
  xga:blended(champions.xga,domestic.xga),
  hxg:blended(champions.hxg,domestic.hxg),
  hxga:blended(champions.hxga,domestic.hxga),
  axg:blended(champions.axg,domestic.axg),
  axga:blended(champions.axga,domestic.axga),
  gf:domestic.gf,ga:domestic.ga,mp:domestic.mp,
  poss:domestic.poss,xag:domestic.xag,shotsPg:domestic.shotsPg,
  sotPg:domestic.sotPg,recentForm:domestic.recentForm,
  homeSplit:domestic.homeSplit,awaySplit:domestic.awaySplit,
  matchLog:domestic.matchLog,homeSplitUsed:domestic.homeSplitUsed,
  src:"cl+"+ctx.domKey+"-blend(w_cl="+ctx.wCL.toFixed(2)+")"
 };
}
module.exports={homeAway,fbrefXg,championsContext,clDomesticXg};
