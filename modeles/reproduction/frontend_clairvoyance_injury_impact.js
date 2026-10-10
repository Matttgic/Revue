"use strict";
/** Independent reconstruction of original computeInjuryImpact formula.
 * NHL delegation is injected: no claim that upstream NHL injury dataset
 * has been reproduced. Other sports require observed injury and roster data.
 */
function severity(status){
 const s=(status||"").toLowerCase();
 if(s.includes("out")||s.includes("-il")||s.includes(" ir")||s.includes("-day"))return 1;
 if(s.includes("doubtful"))return .75;
 if(s.includes("questionable"))return .30;
 return 0;
}
function weight(position,sport,tier){
 const pos=(position||"").toUpperCase();
 if(sport==="nba")return {PREMIUM:.070,OPTIMAL:.045,GOOD:.025}[tier]||.012;
 if(sport==="wnba")return {PREMIUM:.075,OPTIMAL:.048,GOOD:.026}[tier]||.012;
 if(sport==="mlb"){
  if(pos.includes("SP"))return .065;
  if(["C","SS","CF","3B"].includes(pos))return .030;
  if(["LF","RF","2B","1B","DH"].includes(pos))return .020;
  return .010;
 }
 if(["mls","cl","pl","liga","bl","ita"].includes(sport)){
  if(pos.includes("G"))return .055;
  if(pos.includes("F"))return .035;
  if(pos.includes("M"))return .028;
  if(pos.includes("D"))return .018;
  return .015;
 }
 if(sport==="nfl"){
  if(pos==="QB")return .090;
  if(["WR","RB","TE"].includes(pos))return .030;
  if(["LT","RT","C","LG","RG","OL"].includes(pos))return .022;
  if(["DE","DT","EDGE","LB"].includes(pos))return .020;
  if(["CB","S","DB"].includes(pos))return .018;
  return .012;
 }
 return .015;
}
function injuryImpact(abbr,sport,{
 injuries={},roster={},getRoster=()=>({}),
 nhlInjuries=()=>({any:false,players:[]})
}={}){
 if(String(sport).toLowerCase()==="nhl"){
  const adjustment=nhlInjuries(abbr);
  return {penalty:0,flag:adjustment.any,
   players:adjustment.players.map(x=>({
    name:x.name,pos:x.pos,status:x.status,pen:x.pct
   }))};
 }
 const list=injuries[sport.toLowerCase()]||[];
 if(!list.length)return {penalty:0,flag:false,players:[]};
 const profiles=roster||getRoster();
 const club=(abbr||"").toUpperCase();
 let total=0;
 const people=[];
 for(const person of list){
  const likelihood=severity(person.status);
  if(likelihood===0)continue;
  const key=(person.name||"").toLowerCase();
  let record=profiles[key];
  if(!record){
   const last=key.split(" ").pop();
   if(last&&last.length>3){
    const found=Object.entries(profiles).find(([name,detail])=>
       name.split(" ").pop()===last&&detail.sport===sport.toLowerCase());
    if(found)record=found[1];
   }
  }
  if(!record||(record.team||"").toUpperCase()!==club)continue;
  const impact=weight(person.pos,sport.toLowerCase(),record.rating)*likelihood;
  total+=impact;
  people.push({name:person.name,pos:person.pos||"?",status:person.status,
               pen:+(impact*100).toFixed(1)});
 }
 total=Math.min(.12,total);
 return {penalty:total,flag:total>.015,players:people};
}
module.exports={severity,weight,injuryImpact};
