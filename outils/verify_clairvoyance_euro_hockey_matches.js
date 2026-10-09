"use strict";
/**
 * Source-vs-replica verification of Clairvoyance's entire 4 EU hockey MC
 * match calculations. Exercises original source functions and helpers
 * inside an ephemeral Node VM; no third-party source is bundled with Revue.
 */
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_games.js");
const spec=[
  ["liigaMC","_liigaBlendedRates","_LIIGA_DATA","frontend_liiga_mc","liigaMatch"],
  ["nlaMC","_nlaBlendedRates","_NLA_DATA","frontend_nla_mc","swissMatch"],
  ["extraligaMC","_extraligaBlendedRates","_EXTRALIGA_DATA","frontend_extraliga_mc","czechMatch"],
  ["shlMC","_shlBlendedRates","_SHL_DATA","frontend_shl_mc","shlMatch"],
];
const helpers=[
  "_hkRecentRates","_hkFormFactorRaw","_hkFormFactor",
  "_socPoissonPmf","_socMarginDist","_socSpreadProb",
  "_forceHalfLine","_hkMarginCal"
];

function sourceFunction(source,name){
  if(!/^[_a-zA-Z][_a-zA-Z0-9]*$/.test(name))throw Error("Unexpected reference identifier");
  const m=new RegExp("^function\\s+"+name+"\\s*\\(","m").exec(source);
  if(!m)throw Error("Missing source code function "+name);
  const e=source.indexOf("\n}",m.index);
  if(e<0)throw Error("Unterminated original function "+name);
  const part=source.slice(m.index,e+2);
  if(part.length<60||part.length>16000)throw Error("Invalid source function size "+name);
  return part;
}
function scoredGames(){
  const out=[];
  for(let i=0;i<8;i++){
    out.push({
      date:new Date(Date.UTC(2026,9,1+i)).toISOString(),
      home:i%2?"AWAY":"HOME",away:i%2?"HOME":"AWAY",
      homeScore:[4,1,2,4,6,3,0,2][i],
      awayScore:[2,4,3,1,2,4,1,3][i],
      state:"post"
    });
  }
  out.push({date:"2026-10-09",home:"HOME",away:"AWAY",state:"pre"});
  out.push({date:"2026-10-03",home:"HOME",away:"AWAY",state:"post",homeScore:3});
  return out;
}
function fixtureCases(){
  const complete={
    HOME:{gp:10,gf:38,ga:22,gm:6.0,prevSeason:{gp:52,gf:165,ga:147,gm:6.1}},
    AWAY:{gp:7,gf:17,ga:28,gm:5.5,prevSeason:{gp:55,gf:144,ga:175,gm:5.7}}
  };
  const cases=[
    {label:"no data",data:null},
    {label:"missing teams",data:{teams:{},games:[]}},
    {label:"no games data",data:{teams:complete,games:[]}},
    {label:"three or more finals",data:{teams:complete,games:scoredGames()}},
    {label:"alternate total 6.5",data:{teams:complete,games:scoredGames()},ou:6.5},
    {label:"alternate total 4.5",data:{teams:complete,games:scoredGames()},ou:4.5},
    {label:"total whole number 6",data:{teams:complete,games:scoredGames()},ou:6},
    {label:"no previous",data:{teams:{
        HOME:{gp:4,gf:9,ga:10,gm:4.4},AWAY:{gp:5,gf:20,ga:16,gm:7.1}
      },games:scoredGames()}},
    {label:"no current",data:{teams:{
        HOME:{gp:0,prevSeason:{gp:60,gf:162,ga:151,gm:5.95}},
        AWAY:{gp:0,prevSeason:{gp:55,gf:185,ga:170,gm:6.55}}
      },games:[]}},
    {label:"fully current",data:{teams:{
        HOME:{gp:25,gf:80,ga:62,gm:5.6,prevSeason:{gp:50,gf:180,ga:160,gm:6}},
        AWAY:{gp:22,gf:52,ga:82,gm:5.9,prevSeason:{gp:50,gf:175,ga:150,gm:6.4}}
      },games:scoredGames()}},
    {label:"nonuniform schedule",data:{teams:complete,games:scoredGames().reverse()},ou:7.5},
    {label:"zero goal sample",data:{teams:{
        HOME:{gp:5,gf:0,ga:16,gm:3.2,prevSeason:{gp:50,gf:122,ga:190,gm:6.5}},
        AWAY:{gp:5,gf:15,ga:2,gm:3.3,prevSeason:{gp:50,gf:171,ga:112,gm:5.6}}
      },games:scoredGames()}},
    {label:"goals per game absent",data:{teams:{
        HOME:{gp:8,gf:21,ga:18,prevSeason:{gp:50,gf:155,ga:150}},
        AWAY:{gp:8,gf:18,ga:26,prevSeason:{gp:50,gf:150,ga:177}}
      },games:scoredGames()},ou:null},
    {label:"large market total",data:{teams:complete,games:scoredGames()},ou:"8.5"}
  ];
  return cases;
}

function verifyEuroHockeyMatches(source,compare){
  let count=0;
  for(const [model,blend,variable,label,ours] of spec){
    for(const c of fixtureCases()){
      const env={HOCKEY_PL_MARGIN_LOGIT_SHIFT:.18};
      env[variable]=c.data;
      const ctx=vm.createContext(env);
      for(const fn of [blend,...helpers,model])
        vm.runInContext(sourceFunction(source,fn),ctx,{timeout:900});
      const expected=ctx[model]("HOME","AWAY",c.ou);
      const actual=own[ours]("HOME","AWAY",c.ou,{data:c.data});
      compare(label+" / "+c.label,label,expected,actual);
      count++;
    }
  }
  return count;
}
module.exports={verifyEuroHockeyMatches,sourceFunction,fixtureCases};
