"use strict";
const {test}=require("node:test"),assert=require("node:assert/strict");
const {reconcile}=require("../outils/reconcile_reference_fixtures.js");
const now=Date.parse("2026-10-10T18:00:00Z");
function input(){
 const o={generated:"2026-10-10T17:00:00Z",nhl:{today:[{id:12,home:"BOS",away:"PHI",date:"2026-10-10T22:00Z",homeML:-150}],tomorrow:[]},
 nba:{today:[],tomorrow:[{id:"24",home:"TOR",away:"LAC",date:"2026-10-11T21:00Z"}]},
 mlb:{today:[],tomorrow:[]}};
 const r={generated_at_utc:"2026-10-10T17:01:00Z",events:[
 {league:"NHL",event_id:"12",home:"BOS",away:"PHI",start_utc:"2026-10-10T22:00:00Z"},
 {league:"NBA",event_id:"24",home:"TOR",away:"LAC",start_utc:"2026-10-11T21:00:00Z"}]};
 return[o,r];
}
test("independent factual fixtures strict id teams and time",()=>{
 const d=reconcile(...input(),now);assert.equal(d.exact_fixture_matches,2);
 assert.equal(d.model_probability_parity_proven,0);
 assert.equal(d.bookmaker_prices_included,false);
 assert.equal(d.leagues.MLB.matched_exact_fixture,0);
});
test("mismatches never count as model or schedule equality",()=>{
 const x=input();x[1].events[0].home="NYR";
 const d=reconcile(...x,now);assert.equal(d.leagues.NHL.identity_disagreements,1);
 assert.equal(d.exact_fixture_matches,1);
});
test("stale, future, duplicate and malformed sources are explicit",()=>{
 const x=input();x[0].generated="2026-10-01T17:00:00Z";assert.equal(reconcile(...x,now).stale,true);
 const y=input();y[0].generated="2026-10-11T17:00:00Z";assert.throws(()=>reconcile(...y,now),/Future/);
 const z=input();z[1].events.push({...z[1].events[0]});assert.throws(()=>reconcile(...z,now),/Duplicate/);
});