"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path");
const {build,ownedSnapshot}=require("../docs/arcade-v3-data.js");
const get=n=>JSON.parse(fs.readFileSync(path.join(__dirname,"..","docs",n),"utf8"));
const M=get("match-center-latest.json"),P=get("picks-center-latest.json");
const N=get("nhl-frontend-observed-latest.json"),G=get("nhl-espn-goalies-latest.json");
const L=get("phase2-owned-ledger.json"),S=get("phase2-owned-performance.json");
const NOW=Math.max(...[M,P,N,G,S].map(x=>Date.parse(x.generated_at_utc)),
  Date.parse(L.updated_at_utc))+120000;
const copy=structuredClone;

test("actual 39+ independent frozen forecasts join exact match center fixtures",()=>{
 const o=ownedSnapshot(L,S,NOW);
 assert.equal(o.status,"prospective_independent_unvalidated");
 assert.equal(o.locked,Object.keys(L.events).length);
 assert.equal(o.settled,S.total_unique_matches_settled);
 assert.equal(o.elo,S.total_independent_elo_finals);
 assert.ok(o.locked>=39);
 assert.ok(o.since);
 const keys=new Set(M.events.map(x=>x.league+":"+x.event_id));
 assert.ok([...o.rows.keys()].every(k=>keys.has(k)));
 const result=build({matches:M,picks:P,nhl:N,goalies:G,
   ownedLedger:L,ownedPerformance:S},NOW);
 assert.equal(result.sources.own,"prospective_independent_unvalidated");
 assert.equal(result.ownedSummary.locked,L&&Object.keys(L.events).length);
 assert.equal(result.ownedSummary.settled,S.total_unique_matches_settled);
 assert.ok(result.events.length);
 const joined=result.events.filter(x=>x.owned);
 assert.ok(joined.length>0);
 assert.ok(joined.every(x=>x.modelCount>=x.owned.projections.length));
 assert.ok(joined.every(x=>x.actionable===false));
 assert.ok(joined.every(x=>x.owned.lockedAt<x.start));
 assert.ok(joined.every(x=>x.why.some(s=>s.includes("Revue phase 2"))));
 for(const e of joined)for(const m of e.owned.projections){
   assert.ok(m.probabilities.every(p=>p>0&&p<1));
   assert.ok(Math.abs(m.probabilities.reduce((a,b)=>a+b,0)-1)<.0001);
 }
});

test("joining the ledger never contaminates independent paper ROI",()=>{
 const inputs={matches:M,picks:P,nhl:N};
 const old=build(inputs,NOW);
 const current=build({...inputs,ownedLedger:L,ownedPerformance:S},NOW);
 assert.deepEqual(current.paper,old.paper);
 assert.equal(current.noValidatedBets,true);
 assert.equal(current.reason,old.reason);
 assert.ok(current.events.every(e=>e.verdict==="AUCUN PARI RECOMMANDÉ"));
});

test("all sources and locked models remain immutable by rendering",()=>{
 const cloned=copy({matches:M,picks:P,nhl:N,ownedLedger:L,ownedPerformance:S});
 const before=copy(cloned);
 build(cloned,NOW);
 assert.deepEqual(cloned,before);
});

test("missing, stale and future own history fail closed without erasing other sports",()=>{
 assert.equal(ownedSnapshot(null,S,NOW).status,"unavailable");
 const bad=copy(S);bad.generated_at_utc="2032-01-01T00:00:00Z";
 assert.equal(ownedSnapshot(L,bad,NOW).status,"unavailable");
 const stale=copy(S);stale.generated_at_utc=new Date(NOW-24*3600000).toISOString();
 assert.equal(ownedSnapshot(L,stale,NOW).status,"unavailable");
 const joined=build({matches:M,picks:P,nhl:N,ownedLedger:L,ownedPerformance:bad},NOW);
 assert.equal(joined.sources.own,"unavailable");
 assert.ok(joined.events.every(x=>x.owned===null));
 assert.ok(joined.events.length>0);
});

test("no fabricated independent history, SQL equivalence, ROI or live bookmaker market",()=>{
 for(const [field,v] of [
  ["real_bets_enabled",true],["odds_queried",true],["roi_computed",true],
  ["replayed_old_results",true],["models_calibrated",true],
  ["identical_original_clairvoyance_sql_history",true],
  ["bet_recommendations_verified",true]
 ]){
  const tampered=copy(S);tampered[field]=v;
  assert.equal(ownedSnapshot(L,tampered,NOW).status,"unavailable",field);
 }
});

test("reject edited or retroactively backfilled locked predictions",()=>{
 const key=Object.keys(L.events)[0];
 for(const mutate of [
  d=>{d.events[key].locked_at_utc=d.events[key].start_utc;},
  d=>{d.events[key].locked_at_utc="2026-01-01T00:00:00Z";},
  d=>{d.events[key].probabilities.baseline.probabilities[0]=1;},
  d=>{d.events[key].probabilities.baseline.published_at_utc="2030-01-01T00:00:00Z";},
  d=>{d.events[key].market="full_time_undefined";},
  d=>{d.events[key].real_bet=true;},
  d=>{d.events[key].status="settled";},
 ]){
  const bad=copy(L);mutate(bad);
  assert.equal(ownedSnapshot(bad,S,NOW).status,"unavailable");
 }
});

test("no invented confidence when event identities or kickoffs fail",()=>{
 const fake=copy(L);const key=Object.keys(fake.events)[0];
 fake.events[key].home="Unrelated Team";
 const joined=build({matches:M,picks:P,nhl:N,ownedLedger:fake,
   ownedPerformance:S},NOW);
 assert.equal(joined.sources.own,"prospective_independent_unvalidated");
 const e=joined.events.find(x=>x.key===key);
 assert.ok(e);
 assert.equal(e.owned,null);
 const another=copy(L);
 another.events[key].start_utc="2030-01-01T00:00:00Z";
 assert.equal(ownedSnapshot(another,S,NOW).status,"prospective_independent_unvalidated");
 const joined2=build({matches:M,picks:P,nhl:N,ownedLedger:another,
  ownedPerformance:S},NOW);
 assert.equal(joined2.events.find(x=>x.key===key).owned,null);
});

test("soccer markets 3-way and NFL/MLB/NBA 2-way remain distinct",()=>{
 const owned=ownedSnapshot(L,S,NOW);
 for(const x of owned.rows.values()){
  const expected=["PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"].includes(x.league)?3:2;
  assert.equal(x.projections[0].probabilities.length,expected);
  assert.equal(x.market,expected===3?"1X2_90min":"full_game_two_way");
 }
});

test("reject shadow model overclaim and inconsistent totals",()=>{
 const report=copy(S);report.total_unique_matches_locked+=1;
 assert.equal(ownedSnapshot(L,report,NOW).status,"unavailable");
 const report2=copy(S);const k=Object.keys(L.events)[0].split(":")[0];report2.per_league[k].locked+=1;
 assert.equal(ownedSnapshot(L,report2,NOW).status,"unavailable");
});
