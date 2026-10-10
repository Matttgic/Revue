"use strict";
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const {modelLineForProp}=require("../modeles/reproduction/frontend_clairvoyance_player_line.js");
function verifyPlayerLine(source,compare){
 const norms={"Points":"pts","Rebounds":"reb","Assists":"ast",
              "PRA":"pra","Goals":"goal","Shots":"shot","Other":"other"};
 const norm=label=>norms[label]||"other";
 const factors={"BOS":{factor:0},"NYK":{factor:.1},"ATL":{factor:-.18},
                "GS":{factor:.4},"BLOCK":{factor:-1},"UNKNOWN":{factor:0}};
 const opponent=(sport,opp)=>factors[opp]||{factor:0};
 const halfLine=n=>(Math.floor(n)+.5).toFixed(1);
 const caches={
  nba:{"anthony edwards":{ppg:26.5,rpg:5.4,apg:3.1},
       "zero scorer":{ppg:0,rpg:2.1,apg:1.1}},
  wnba:{"star":{ppg:20,rpg:7.5,apg:4}},
  nhl:{"skater":{gpg:.45,shpg:3.1}, "faint":{gpg:0,shpg:1.7}},
 };
 let n=0;
 for(const sport of ["nba","wnba","nhl","mlb","NBA"]){
  for(const player of ["Anthony Edwards","zero scorer","star","skater","faint","unknown",null]){
   for(const stat of ["Points","Rebounds","Assists","PRA","Goals","Shots","Other"]){
    for(const opp of [null,"BOS","NYK","ATL","GS","BLOCK"]){
     const env={
       _nbaStatsCache:caches.nba,
       _wnbaStatsCache:caches.wnba,
       _nhlStatsCache:caches.nhl,
       _propStatNorm:norm,_propOppDefFactor:opponent,_forceHalfLine:halfLine
     };
     const ctx=vm.createContext(env);
     vm.runInContext(sourceFunction(source,"_modelLineForProp"),ctx,{timeout:700});
     compare("player line "+sport+" "+player+" "+stat+" "+opp,
         "frontend_nba_prop_line",
         ctx._modelLineForProp(sport,player,stat,opp),
         modelLineForProp(sport,player,stat,opp,{
           caches,normalize:norm,defFactor:opponent,halfLine
         }));
     n++;
    }
   }
  }
 }
 return n;
}
module.exports={verifyPlayerLine};
