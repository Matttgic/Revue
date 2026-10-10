"use strict";
/** Behaviour parity with original computeInjuryImpact, all supported major sports except CFB. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const {injuryImpact}=require("../modeles/reproduction/frontend_clairvoyance_injury_impact.js");
function verifyInjuryImpact(source,compare){
 const profiles={
  "peter franchise":{sport:"nba",team:"BOS",rating:"PREMIUM"},
  "alex smith":{sport:"nba",team:"BOS",rating:"GOOD"},
  "tony spiller":{sport:"nfl",team:"BOS",rating:"PREMIUM"},
  "qb starter":{sport:"nfl",team:"BOS",rating:"GOOD"},
  "daniel reserve":{sport:"mlb",team:"BOS",rating:"GOOD"},
  "marcus ball":{sport:"pl",team:"BOS",rating:"GOOD"},
  "team scorer":{sport:"wnba",team:"BOS",rating:"OPTIMAL"},
 };
 const people=[
  {name:"Peter Franchise",status:"Out",pos:"PG",team:"BOS"},
  {name:"Alex Smith",status:"Questionable",pos:"SG",team:"BOS"},
  {name:"Tony Spiller",status:"Doubtful",pos:"RB",team:"BOS"},
  {name:"QB Starter",status:"Out",pos:"QB",team:"BOS"},
  {name:"Daniel Reserve",status:"10-day IL",pos:"SP",team:"BOS"},
  {name:"Marcus Ball",status:"Out",pos:"F",team:"BOS"},
  {name:"Team Scorer",status:"Out",pos:"G",team:"BOS"},
  {name:"Nobody",status:"Out",pos:"F",team:"BOS"},
  {name:"Peter Franchise",status:"Active",pos:"PG",team:"BOS"},
  {name:"Peter Franchise",status:"Probable",pos:"PG",team:"BOS"}
 ];
 const condition=["Out","Doubtful","Questionable","Active","day-to-day","IL","Probable"];
 const positions=["QB","PG","SG","SP","C","D","RB","WR","G","F"];
 let n=0;
 for(const sp of ["nba","wnba","mlb","nfl","pl","liga","bl","ita","mls","cl","nhl"]){
  for(let iter=0;iter<33;iter++){
   const full=iter%5===0?[]:people.filter((_,j)=>j%4!==(iter%4)).map((x,j)=>({
      ...x,status:iter%7===0?condition[(j+iter)%condition.length]:x.status,
      pos:iter%6===0?positions[(j+iter)%positions.length]:x.pos,
   }));
   const list=Array.from({length:sp==="nhl"?0:full.length},(_,j)=>full[j]);
   const injury={ [sp]:list };
   const goalieMock=()=>({any:true,players:[{name:"Goalie",pos:"G",status:"Out",pct:0}]});
   const env={
    window:{__CV_DATA:{injuries:injury},_injRoster:profiles},
    buildInjuryRoster:()=>profiles,
    _nhlInjAdj:goalieMock,
   };
   const ctx=vm.createContext(env);
   vm.runInContext(sourceFunction(source,"computeInjuryImpact"),ctx,{timeout:700});
   const abbr=iter%8===0?"NYR":"BOS";
   compare("impact "+sp+" "+iter,"frontend_nhl_injuries",
      ctx.computeInjuryImpact(abbr,sp),
      injuryImpact(abbr,sp,{injuries:injury,roster:profiles,nhlInjuries:goalieMock}));
   n++;
  }
 }
 return n;
}
module.exports={verifyInjuryImpact};
