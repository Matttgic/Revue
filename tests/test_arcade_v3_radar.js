"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {build,safeRadar,radarComparisons}=require("../docs/arcade-v3-data.js");
const load=x=>JSON.parse(fs.readFileSync(path.join(__dirname,"..","docs",x),"utf8"));
const M=load("match-center-latest.json");
const P=load("picks-center-latest.json");
const N=load("nhl-frontend-observed-latest.json");
const G=load("nhl-espn-goalies-latest.json");
const NOW=Math.max(...[M,P,N,G].map(x=>Date.parse(x.generated_at_utc)))+120000;
// Synthetic calendar fixture: unit tests must also run during league breaks.
const kick={league:"LIGUE1",sport:"football",event_id:"test-radar-fixture",
 home:"Test Home",away:"Test Away",start_utc:new Date(NOW+2*3600000).toISOString(),
 qualified_for_real_betting:false,recommendation:null,ev:null};
M.events.push(kick);
M.metrics.upcoming_matches=M.events.length;
const fakeMarket=(pHome,pDraw,pAway,league="LIGUE1")=>({
  market:"h2h",period_rule:"90min",
  quote_at:new Date(NOW-120000).toISOString(),
  outcomes:[
    {selection:"home",price:pHome},
    {selection:"draw",price:pDraw},
    {selection:"away",price:pAway}
  ],
});
function radar(){
return {
 version:"revue_pulsescore_six_hour_radar_v1",
 status:"observed",provider:"PulseScore",
 generated_at_utc:new Date(NOW-120000).toISOString(),
 source_model_generated_at_utc:new Date(NOW-25*60000).toISOString(),
 horizon_hours:6,request_cap:8,requests_used:5,
 market_prices_are_live:false,positive_ev_verified:false,
 model_is_calibrated:false,real_bets_enabled:false,
 new_paper_bets_created:false,existing_paper_ledger_modified:false,
 matches_observed:1,observations:[{
  league:kick.league,event_id:String(kick.event_id),
  home:kick.home,away:kick.away,start_utc:kick.start_utc,
  bookmakers:[
   {bookmaker:"betclic_fr",markets:[fakeMarket(1.95,3.4,4.2)]},
   {bookmaker:"winamax_fr",markets:[fakeMarket(2.10,3.5,4.0)]},
   {bookmaker:"pmu_fr",markets:[fakeMarket(2.0,3.2,4.1)]},
  ],
 }]
};
}
test("two or more comparable bookmakers create observed disparities, NEVER EV",()=>{
 const src=radar();
 assert.equal(safeRadar(src,NOW),true);
 const groups=radarComparisons(src,NOW);
 const item=groups.get(kick.league+":"+kick.event_id);
 assert.ok(item);
 assert.equal(item.compared.length,3);
 assert.equal(item.compared.find(x=>x.side==="home").topBook,"winamax_fr");
 assert.equal(item.compared.find(x=>x.side==="home").bookCount,3);
 assert.equal(item.compared.find(x=>x.side==="home").topPrice,2.1);
 assert.equal(item.compared.find(x=>x.side==="home").impliedValueVerified,false);
 const merged=build({matches:M,picks:P,nhl:N,goalies:G,radar:src},NOW);
 assert.equal(merged.sources.radar,"bounded_six_hour_observations");
 const event=merged.events.find(x=>x.key===kick.league+":"+kick.event_id);
 assert.ok(event);
 assert.equal(event.actionable,false);
 assert.equal(event.verdict,"AUCUN PARI RECOMMANDÉ");
 assert.equal(event.recentCrossBookPrices.length,3);
 assert.ok(event.why.some(x=>x.includes("PulseScore")));
});
test("incompatible lines do not create fake cross-book comparisons",()=>{
 const src=radar();
 src.observations[0].bookmakers=[
  {bookmaker:"betclic_fr",markets:[{
    market:"totals",period_rule:"90min",
    quote_at:new Date(NOW-120000).toISOString(),
    outcomes:[{selection:"over",line:2.5,price:1.90},
              {selection:"under",line:2.5,price:2.0}]
  }]},
  {bookmaker:"winamax_fr",markets:[{
    market:"totals",period_rule:"90min",
    quote_at:new Date(NOW-120000).toISOString(),
    outcomes:[{selection:"over",line:3.5,price:2.10},
              {selection:"under",line:3.5,price:1.7}]
  }]},
 ];
 assert.equal(radarComparisons(src,NOW).get(kick.league+":"+kick.event_id).compared.length,0);
});
test("stale, future, overbudget or fake live radar snapshots are rejected",()=>{
 for(const [field,bad] of [
  ["market_prices_are_live",true],["real_bets_enabled",true],
  ["positive_ev_verified",true],["new_paper_bets_created",true],
  ["existing_paper_ledger_modified",true],
  ["requests_used",9],["request_cap",101],["horizon_hours",24],
 ]){
  const r=radar();r[field]=bad;
  assert.equal(safeRadar(r,NOW),false,field);
 }
 const old=radar();old.generated_at_utc=new Date(NOW-5*3600000).toISOString();
 assert.equal(safeRadar(old,NOW),false);
 const futur=radar();futur.generated_at_utc="2030-01-01T00:00:00Z";
 assert.equal(safeRadar(futur,NOW),false);
});
test("mismatched fixture identity or kickoff, quote timestamp and one book do not compare",()=>{
 const mismatched=radar();
 mismatched.observations[0].home="Fake Host";
 const output=build({matches:M,picks:P,nhl:N,goalies:G,radar:mismatched},NOW);
 const row=output.events.find(x=>x.key===kick.league+":"+kick.event_id);
 assert.equal(row.recentCrossBookPrices.length,0);
 const stale=radar();
 stale.observations[0].bookmakers[0].markets[0].quote_at=
  new Date(NOW-3*3600000).toISOString();
 stale.observations[0].bookmakers[1].markets[0].quote_at=
  new Date(NOW-3*3600000).toISOString();
 assert.equal(radarComparisons(stale,NOW).get(kick.league+":"+kick.event_id).compared.length,0);
 const single=radar();single.observations[0].bookmakers.length=1;
 assert.equal(radarComparisons(single,NOW).get(kick.league+":"+kick.event_id).compared.length,0);
});
test("unverified NHL overtime market does not compare against another NHL market",()=>{
 const r=radar();
 r.observations[0].league="NHL";
 r.observations[0].bookmakers.forEach(b=>b.markets.forEach(m=>m.period_rule="overtime_rule_unverified"));
 assert.equal(radarComparisons(r,NOW).get("NHL:"+kick.event_id).compared.length,0);
});
