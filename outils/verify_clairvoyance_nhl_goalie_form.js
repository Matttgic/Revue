"use strict";
/** Direct outcome parity with original NHL goalie data patch and 5-game form. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const {applyGoalieStats,recentScoringFactor}=require("../modeles/reproduction/frontend_clairvoyance_nhl_goalie_form.js");
const clone=x=>JSON.parse(JSON.stringify(x));
function verifyNHLGoalieForm(source,compare) {
 let checks=0;
 const squads={
  BOS:{gf60:3.1,sv:.909,gsax:1.2},
  NYR:{gf60:2.9},
  CAR:{gf60:3.6,sv:null},
  FLA:{gf60:2.9,hdsv:.85},
 };
 const example=[
  {team:"BOS",name:"No shots",situation:"all",gp:27,shots:0,gsaa:100,hdSavePct:.99,savePct:.99},
  {team:"BOS",name:"BOS secondary",situation:"all",gp:20,shots:420,gsaa:7,hdSavePct:.91,savePct:.94},
  {team:"BOS",name:"BOS minor",situation:"all",gp:5,shots:100,gsaa:2,hdSavePct:.92},
  {team:"NYR",name:"NYR starter",situation:"all",gp:35,shots:620,gsaa:-4,hdSavePct:.86,savePct:.91},
  {team:"CAR",name:"CAR starter",situation:"all",gp:35,shots:450,gsaa:6,hdSavePct:.88,savePct:.93},
  {team:"FLA",name:"not all",situation:"5on5",gp:45,shots:999,gsaa:100},
  {team:"UNKNOWN",name:"unknown",situation:"all",gp:70,shots:800,gsaa:3}
 ];
 for(let i=0;i<95;i++){
  const goalies=clone(example).filter((_,j)=>i%4!==j%4||j===0);
  if(i%5===0)goalies.push({team:"FLA",situation:"all",name:"FLA keeper",gp:i,
    shots:290,savePct:.898,gsaa:null});
  if(i%7===0)goalies.push({team:"BOS",situation:"all",name:"BOS dual",gp:i,
    shots:220,gsaa:-2,savePct:.902});
  const originals=clone(squads);
  const mirror=clone(squads);
  const ctx=vm.createContext({NHL:originals,MONEYPUCK:{goalies}});
  vm.runInContext(sourceFunction(source,"_nhlApplyGoalieStats"),ctx,{timeout:600});
  ctx._nhlApplyGoalieStats();
  applyGoalieStats(mirror,goalies);
  compare("goalie NHL "+i,"frontend_nhl_goalie_update",originals,mirror);
  checks++;
 }
 for(let n=0;n<105;n++){
  const minGames=(n%4)+1;
  const config={minGames,windowSize:(n%7)+1,cap:.03+.01*(n%3),weight:.02+.005*(n%4)};
  const completed={BOS:Array.from({length:n%13},(_,i)=>({gf:(i+n%5)*.4+1}))};
  const base=n%9===0?null:n%10===0?NaN:(n%11===0?Infinity:2.25+(n%10)*.15);
  const env={
   NHL_FORM_MIN_GP:minGames,NHL_FORM_N:config.windowSize,
   NHL_FORM_CAP:config.cap,NHL_FORM_K:config.weight,
   _nhlCompletedByTeam:()=>completed
  };
  const ctx=vm.createContext(env);
  vm.runInContext(sourceFunction(source,"_nhlFormFactor"),ctx,{timeout:600});
  compare("form NHL "+n,"frontend_nhl_form",
    ctx._nhlFormFactor("BOS",base),
    recentScoringFactor("BOS",base,completed,config));
  checks++;
 }
 return checks;
}
module.exports={verifyNHLGoalieForm};
