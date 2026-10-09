"use strict";
/**
 * Independent, data-injected behaviour of the source's _socXG pipeline.
 * Reference: Clairvoyance docs/app.html: _socXG/_socXGRaw, _socXGFromFBref,
 * CL domestic weighting, Opta 50/50 averaging and team-venue splits.
 * NO FBref/Opta proprietary data is bundled or fetched. Source parity is
 * checked in CI against the original functions on synthetic inputs.
 */
const OPTA_LEAGUES=["pl","liga","ita","bl","mls","cl"];
const DOMESTIC_LEAGUES=["pl","liga","bl","ita"];

function findTeam(rows,name) {
  if(!rows||!name)return undefined;
  const k=name.toLowerCase().trim();
  for(const candidate of rows){
    const team=String(candidate?.team||"").toLowerCase();
    if(team===k||k.indexOf(team)>=0||team.indexOf(k)>=0)return candidate;
  }
  return undefined;
}
function soccerXG(name,leagueKey,context={}){
  if(!name)return null;
  const fb=context.fbref,staticTeams=context.staticXG||{},
        opta=context.opta||{},mlsOpta=context.mlsOpta,
        homeAdv=context.homeAdv||{default:0};
  const advFor=league=>homeAdv[league]!=null?homeAdv[league]:homeAdv.default;
  const teamSplit=t=>{
    const h=t?.homeSplit,a=t?.awaySplit;
    return(!h||!a||h.games<3||a.games<3)?null:
      {homeGf:h.gf,homeGa:h.ga,awayGf:a.gf,awayGa:a.ga};
  };
  function fromFBref(name,league){
    if(!fb||!name)return null;
    const k=name.toLowerCase().trim();
    const leagues=league?[league]:Object.keys(fb);
    for(const lg of leagues){
      const teams=fb[lg]?.teams;
      if(!teams)continue;
      for(const nameKey of Object.keys(teams)){
        const key=nameKey.toLowerCase();
        if(key!==k&&!key.includes(k)&&!k.includes(key))continue;
        const t=teams[nameKey],mp=t.mp||34,adv=advFor(league),split=teamSplit(t);
        const hxg=split?split.homeGf:t.xg/mp*(1+adv),
              hxga=split?split.homeGa:t.xga/mp*(1-adv),
              axg=split?split.awayGf:t.xg/mp*(1-adv),
              axga=split?split.awayGa:t.xga/mp*(1+adv);
        return {xg:t.xg/mp,xga:t.xga/mp,hxg,hxga,axg,axga,
          gf:t.gf/mp,ga:t.ga/mp,mp,poss:t.poss,xag:t.xag,
          shotsPg:t.shots_pg,sotPg:t.sot_pg,
          recentForm:t.recentForm,homeSplit:t.homeSplit,
          awaySplit:t.awaySplit,matchLog:t.matchLog,
          gamesPlayedThisSeason:t.gamesPlayedThisSeason,
          homeSplitUsed:!!split,src:"fbref"};
      }
    }
    return null;
  }
  function championsLeague(name){
    const cl=fromFBref(name,"cl");
    let domKey=null;
    for(const lg of DOMESTIC_LEAGUES){
      if(fromFBref(name,lg)){domKey=lg;break}
    }
    if(!cl&&!domKey)return null;
    if(!domKey)return cl;
    const domestic=fromFBref(name,domKey);
    if(!cl)return domestic;
    const games=cl.gamesPlayedThisSeason||0;
    const wCL=.35*Math.min(games,3)/3,wDom=1-wCL;
    const blend=(a,b)=>a==null||b==null?(a==null?b:a):a*wCL+b*wDom;
    return {
      xg:blend(cl.xg,domestic.xg),xga:blend(cl.xga,domestic.xga),
      hxg:blend(cl.hxg,domestic.hxg),hxga:blend(cl.hxga,domestic.hxga),
      axg:blend(cl.axg,domestic.axg),axga:blend(cl.axga,domestic.axga),
      gf:domestic.gf,ga:domestic.ga,mp:domestic.mp,
      poss:domestic.poss,xag:domestic.xag,
      shotsPg:domestic.shotsPg,sotPg:domestic.sotPg,
      recentForm:domestic.recentForm,
      homeSplit:domestic.homeSplit,awaySplit:domestic.awaySplit,
      matchLog:domestic.matchLog,homeSplitUsed:domestic.homeSplitUsed,
      src:"cl+"+domKey+"-blend(w_cl="+wCL.toFixed(2)+")"
    };
  }
  function raw(name,league){
    if(!name)return null;
    const live=league==="cl"?championsLeague(name):fromFBref(name,league);
    if(live)return live;
    const key=name.toLowerCase().trim();
    if(staticTeams[key])return staticTeams[key];
    const keys=Object.keys(staticTeams);
    for(const k of keys)if(key.includes(k)||k.includes(key))return staticTeams[k];
    const firstWord=key.split(" ")[0];
    for(const k of keys)if(k.includes(firstWord))return staticTeams[k];
    return null;
  }
  function optaBase(name,league){
    let data=opta[league];
    if(!data&&league==="mls")data=mlsOpta;
    if(!data||!name)return null;
    const att=findTeam(data.attacking,name),
          def=findTeam(data.defending,name);
    if(!att||!def||!att.played)return null;
    return{xg:att.xg/att.played,xga:def.xg_against/att.played};
  }
  function blended(name,base,league){
    if(!base)return base;
    const latest=optaBase(name,league);
    if(!latest)return base;
    const xg=(base.xg+latest.xg)/2,
          xga=(base.xga+latest.xga)/2,
          adv=advFor(league);
    const hRatio=base.xg?base.hxg/base.xg:1+adv,
          hgaRatio=base.xga?base.hxga/base.xga:1-adv,
          aRatio=base.xg?base.axg/base.xg:1-adv,
          agaRatio=base.xga?base.axga/base.xga:1+adv;
    return{xg,xga,
      hxg:+(xg*hRatio).toFixed(3),
      hxga:+(xga*hgaRatio).toFixed(3),
      axg:+(xg*aRatio).toFixed(3),
      axga:+(xga*agaRatio).toFixed(3),
      gf:base.gf,ga:base.ga,mp:base.mp,
      poss:base.poss,xag:base.xag,
      shotsPg:base.shotsPg,sotPg:base.sotPg,
      recentForm:base.recentForm,
      homeSplit:base.homeSplit,awaySplit:base.awaySplit,
      matchLog:base.matchLog,homeSplitUsed:base.homeSplitUsed,
      src:(base.src||"")+"+opta-blend"};
  }
  let output=raw(name,leagueKey);
  if(OPTA_LEAGUES.includes(leagueKey))output=blended(name,output,leagueKey);
  return output;
}

module.exports={soccerXG};
