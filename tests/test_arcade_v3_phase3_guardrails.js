"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path");
const {build,originalResearch,radarComparisons,prioritizeForReview}=
 require("../docs/arcade-v3-data.js");
const get=x=>JSON.parse(fs.readFileSync(path.join(__dirname,"..","docs",x),"utf8"));
const M=get("match-center-latest.json"),P=get("picks-center-latest.json");
const NOW=Math.max(Date.parse(M.generated_at_utc),Date.parse(P.generated_at_utc))+120000;
const kick=M.events.find(x=>x.league==="LIGUE1"&&Date.parse(x.start_utc)>NOW+30*60000)
 ||M.events.find(x=>x.league==="LALIGA"&&Date.parse(x.start_utc)>NOW+30*60000)
 ||M.events.find(x=>Date.parse(x.start_utc)>NOW+30*60000);
if(!kick)throw Error("No future fixture in snapshot");
function picks(){
 const doc=structuredClone(P);
 doc.research_selections=[{...P.research_selections[0],
  league:kick.league,event_id:String(kick.event_id),home:kick.home,away:kick.away,
  start_utc:kick.start_utc,real_bet:false,model_is_calibrated:false,
  qualified_positive_ev:false,available_as_real_market:false,
  best_observed_price:{bookmaker:"betclic_fr",decimal_odds:2.1,
    quote_at_utc:new Date(NOW-60000).toISOString()}}];
 doc.unique_research_selections=1;
 return doc;
}
test("history prices join only on league, ID, teams and EXACT start",()=>{
 const p=picks(),key=kick.league+":"+kick.event_id;
 assert.equal(originalResearch(p,NOW).get(key).length,1);
 assert.equal(build({matches:M,picks:p},NOW).events.find(e=>e.key===key).historicalQuotes.length,1);
 for(const f of ["home","away","start_utc"]){
  const forged=structuredClone(p);
  forged.research_selections[0][f]=f==="start_utc"?
   new Date(Date.parse(kick.start_utc)+3600000).toISOString():"Different team";
  assert.equal(build({matches:M,picks:forged},NOW).events.find(e=>e.key===key).historicalQuotes.length,0,f);
 }
});
function radar(rules,league){
 const when=new Date(NOW-60000).toISOString();
 return {version:"revue_pulsescore_six_hour_radar_v1",
  status:"observed",provider:"PulseScore",generated_at_utc:when,
  source_model_generated_at_utc:when,horizon_hours:6,request_cap:8,requests_used:2,
  market_prices_are_live:false,positive_ev_verified:false,model_is_calibrated:false,
  real_bets_enabled:false,new_paper_bets_created:false,
  existing_paper_ledger_modified:false,matches_observed:1,
  observations:[{league,event_id:String(kick.event_id),home:kick.home,away:kick.away,
   start_utc:kick.start_utc,bookmakers:rules.map(([book,rule],i)=>({
    bookmaker:book,markets:[{market:"h2h",period_rule:rule,
     quote_at:when,outcomes:[{selection:"home",price:i?2.2:2.1}]}]
   }))}]};
}
test("different settlement periods do not produce apparent cross-book edges",()=>{
 const k="OTHER:"+kick.event_id;
 const bad=radar([["betclic_fr","90min"],["winamax_fr","full_game"]],"OTHER");
 assert.equal(radarComparisons(bad,NOW).get(k).compared.length,0);
 const good=radar([["betclic_fr","90min"],["winamax_fr","90min"]],"OTHER");
 const c=radarComparisons(good,NOW).get(k).compared;
 assert.equal(c.length,1);assert.equal(c[0].periodRule,"90min");
 assert.equal(c[0].impliedValueVerified,false);
});
test("soccer markets need the explicitly comparable 90-minute period",()=>{
 const k="LIGUE1:"+kick.event_id;
 assert.equal(radarComparisons(radar([["betclic_fr","full_game"],["winamax_fr","full_game"]],"LIGUE1"),NOW).get(k).compared.length,0);
 assert.equal(radarComparisons(radar([["betclic_fr","90min"],["winamax_fr","90min"]],"LIGUE1"),NOW).get(k).compared.length,1);
});
test("source coverage ranking never edits matches nor implies a bet",()=>{
 const a=[{key:"soon",start:new Date(NOW+3600000).toISOString()},
  {key:"locked",start:new Date(NOW+7200000).toISOString(),owned:{}},
  {key:"quoted",start:new Date(NOW+5400000).toISOString(),recentCrossBookPrices:[{}]}];
 const before=structuredClone(a);
 assert.deepEqual(prioritizeForReview(a).map(x=>x.key),["locked","quoted","soon"]);
 assert.deepEqual(a,before);
});
