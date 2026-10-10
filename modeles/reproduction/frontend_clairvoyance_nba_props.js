"use strict";
/** Reproduction of source _generateNBAProps numerical decision pipeline.
 * Description fields are independently worded; tests compare exact numeric
 * and selection outcomes, not copyrighted prose from the original UI.
 * The underlying propMC function is an injected, separately testable
 * dependency: without real player stats it creates no selections.
 */
function nbaProps(games,stats,{
 defense=()=>({factor:0,note:true}),
 halfLine=value=>Math.floor(value)+.5,
 monteCarlo=()=>({overP:.5}),
 classify=()=> "SKIP",
 explain=object=>object,
}={}){
 if(!stats)return[];
 const result=[];
 const players=Object.values(stats);
 const odds=prob=>prob>=.5?
   Math.round(-prob/(1-prob)*100):Math.round((1-prob)/prob*100);
 for(const game of games||[]){
  const home=game.h||game.hA||game.home;
  const away=game.a||game.awA||game.away;
  if(!home||!away||game.seasonType===1||game.preseason===true)continue;
  const eligible=players.filter(player=>{
    if(player.status&&/^out/i.test(player.status))return false;
    return (player.team===home||player.team===away)&&player.gp>=10;
  }).sort((a,b)=>b.ppg-a.ppg).slice(0,6);
  const known=new Set();
  for(const athlete of eligible){
   const opponent=athlete.team===home?away:home;
   const opponentInfo=defense("NBA",opponent);
   const modifier=opponentInfo.factor;
   function evaluate(field,minAverage,cv){
    const id=athlete.name+"_"+field;
    if(known.has(id))return;
    const average=athlete[field];
    if(average==null||average<minAverage)return;
    known.add(id);
    const line=parseFloat(halfLine(average));
    const recent=athlete.last5&&({
      ppg:athlete.last5.ppg,
      rpg:athlete.last5.rpg,
      apg:athlete.last5.apg
    })[field];
    const validForm=recent!=null&&athlete.last5.n>=3;
    const expectation=validForm?average*.75+recent*.25:average;
    const adjusted=Math.max(.1,expectation*(1+modifier));
    const deviation=athlete.stdev&&({
      ppg:athlete.stdev.pts,
      rpg:athlete.stdev.reb,
      apg:athlete.stdev.ast
    })[field];
    const sigma=Math.max(minAverage*.3,
       deviation!=null&&deviation>0?deviation:average*cv);
    const probability=monteCarlo(adjusted,sigma,line,5000).overP;
    const over=adjusted>=line;
    const conf=(over?probability:1-probability)*100;
    const grade=(Math.abs(modifier)<.01&&Math.abs(conf-50)<4)
       ?"SKIP":classify(conf);
    const american=odds(over?probability:1-probability);
    const stat=field==="ppg"?"PTS":field==="rpg"?"REB":field==="apg"?"AST":field.toUpperCase();
    const record={
      player:athlete.name,team:athlete.team,opp:opponent,
      hA:home,awA:away,stat:field,statAbbr:stat,line,
      over,ml:american>0?"+"+american:""+american,prob:conf/100,
      grade,hitRate:Math.round(conf)+"%",
      adjustor:+(adjusted-average).toFixed(1),
      mu:+adjusted.toFixed(2),sigma:+sigma.toFixed(2),
      base:+average.toFixed(1),
      form:validForm?+recent.toFixed(1):null,
      basis:"Revue source parity: observed season mean and variance, 25% recent form, matchup-adjusted projection. No bookmaker edge inferred."
    };
    result.push(explain(record));
   }
   evaluate("ppg",12,.38);
   evaluate("rpg",6,.45);
   evaluate("apg",5,.50);
  }
 }
 return result.sort((a,b)=>b.prob-a.prob);
}
function nhlPropsLive(){
 return [];
}
module.exports={nbaProps,nhlPropsLive};
