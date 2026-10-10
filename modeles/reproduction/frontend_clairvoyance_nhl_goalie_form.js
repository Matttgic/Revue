"use strict";
/**
 * Faithful reconstruction of original _nhlApplyGoalieStats and _nhlFormFactor.
 * Source: Purple-Wraith/clairvoyance-backend/docs/app.html.
 *
 * 'starter' here means highest games played, NEVER confirmed on the night.
 */
function applyGoalieStats(teams,goalies) {
 const leaders={};
 for(const keeper of (goalies||[]).filter(x=>x.situation==="all")){
  const old=leaders[keeper.team];
  if(!old||(keeper.gp||0)>(old.gp||0))leaders[keeper.team]=keeper;
 }
 for(const [abbr,g] of Object.entries(leaders)){
  const team=teams[abbr];
  if(!team||!g.shots)continue;
  if(g.gsaa!=null)team.gsax=g.gsaa;
  if(g.hdSavePct!=null)team.hdsv=g.hdSavePct;
  if(g.savePct!=null&&team.sv==null)team.sv=g.savePct;
  team._liveGoalieStarter=g.name;
 }
 return teams;
}
function recentScoringFactor(team,goalsPerGame,completedByTeam,
                             {minGames,windowSize,cap,weight}) {
 const neutral={mult:1,delta:null,n:0,gfL:null};
 try{
  const games=completedByTeam?.[team];
  if(!games||games.length<minGames||goalsPerGame==null||
     !Number.isFinite(Number(goalsPerGame)))return neutral;
  const subset=games.slice(0,windowSize);
  const mean=subset.reduce((sum,x)=>sum+x.gf,0)/subset.length;
  const delta=mean-goalsPerGame;
  const factor=1+Math.max(-cap,Math.min(cap,delta*weight));
  return {mult:Number.isFinite(factor)?factor:1,delta,n:subset.length,gfL:mean};
 }catch(_){return neutral}
}
module.exports={applyGoalieStats,recentScoringFactor};
