"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {build,paper,sourcePicks,sourceMatch,safeNhl}=require("../docs/arcade-v3-data.js");
const ROOT=path.join(__dirname,"..","docs");
const loaded=name=>JSON.parse(fs.readFileSync(path.join(ROOT,name),"utf8"));
const P=loaded("picks-center-latest.json");
const M=loaded("match-center-latest.json");
const N=loaded("nhl-frontend-observed-latest.json");
const T=Math.max(Date.parse(M.generated_at_utc),Date.parse(N.generated_at_utc),Date.parse(P.generated_at_utc))+120000;
const clone=x=>structuredClone(x);

test("real-source snapshot: safe research and verified fictional profit, not real advice",()=>{
 const m=build({picks:P,matches:M,nhl:N},T);
 assert.equal(m.version,"arcade_simple_source_gated_v1");
 assert.equal(m.noValidatedBets,true);
 assert.equal(m.hiddenCFB,true);
 assert.equal(m.sources.matches,"fresh");
 assert.equal(m.sources.research,"archived_paper_only");
 assert.equal(m.sources.nhl,"partial_research");
 assert.ok(m.events.length>0);
 assert.ok(m.paper.settled>0);
 assert.equal(m.paper.settled,P.paper_summary.settled);
 assert.equal(m.paper.won,P.paper_summary.wins);
 assert.equal(m.paper.lost,P.paper_summary.losses);
 assert.equal(m.paper.profit,P.paper_summary.paper_profit_units);
 assert.equal(m.paper.roi,P.paper_summary.paper_roi_percent);
 assert.equal(m.paper.pending,P.paper_summary.pending);
 assert.equal(m.paper.excluded,P.paper_summary.excluded);
 assert.ok(m.events.every(x=>x.actionable===false&&x.verdict==="AUCUN PARI RECOMMANDÉ"));
 assert.ok(m.events.every(x=>x.league!=="CFB"&&x.why.length>=2));
 assert.ok(m.events.every(x=>new Date(x.start).getTime()>T));
 assert.ok(m.events.every(x=>x.historicalQuotes.every(v=>typeof v.observedAt==="string")));
 assert.ok(m.events.every(x=>x.hockey===null||x.hockey.inputsComplete===false));
});
test("source changes never silently alter the built public output",()=>{
 const m=clone(M),p=clone(P),n=clone(N);
 const before=clone({m,p,n});
 build({picks:p,matches:m,nhl:n},T);
 assert.deepEqual({m,p,n},before);
});
test("reject stale and future calendar, preserve independently valid paper ledger",()=>{
 const date=T+24*3600*1000;
 const snapshot=build({picks:P,matches:M,nhl:N},date);
 assert.equal(snapshot.events.length,0);
 assert.equal(snapshot.sources.matches,"missing_or_stale");
 assert.ok(snapshot.paper);
 assert.equal(snapshot.paper.settled,P.paper_summary.settled);
 assert.equal(snapshot.sources.nhl,"partial_research");
});
test("reject forged real bets and live odds without showing fictional stats",()=>{
 const p=clone(P);p.real_bets_enabled=true;
 const result=build({picks:p,matches:M,nhl:N},T);
 assert.equal(result.paper,null);
 assert.equal(result.sources.research,"unverified");
 const m=clone(M);m.bookmaker_prices_are_live=true;
 const x=build({picks:P,matches:m,nhl:N},T);
 assert.equal(x.events.length,0);
 assert.equal(x.sources.matches,"missing_or_stale");
});
test("reject misleading ledger settlements and bad profit numbers",()=>{
 const p=clone(P);
 p.paper_records.find(r=>r.status==="won").paper_profit_units=999;
 assert.equal(paper(p),null);
 const q=clone(P);
 q.paper_records.find(r=>r.status==="pending").paper_profit_units=12;
 assert.equal(sourcePicks(q),false);
 const r=clone(P);
 r.paper_summary.total++;
 assert.equal(paper(r),null);
});
test("exclude CFB and any claimed actionable recommendation from matched fixtures",()=>{
 const m=clone(M);
 const orig=m.events[0];
 m.events.push({...orig,league:"CFB",event_id:"777888000"});
 m.events.push({...orig,league:"NHL",event_id:"777888001",ev:.12});
 m.metrics.upcoming_matches=m.events.length;
 const x=build({picks:P,matches:m,nhl:N},T);
 assert.ok(x.events.every(e=>e.league!=="CFB"&&e.id!=="777888001"));
});
test("incomplete or untrusted NHL model excluded while other sports stay visible",()=>{
 const n=clone(N);n.exact_original_frontend_predictions_verified=true;
 const report=build({picks:P,matches:M,nhl:n},T);
 assert.equal(report.sources.nhl,"missing_or_stale");
 assert.ok(report.events.some(e=>e.league!=="NHL"));
 assert.ok(report.events.every(e=>e.hockey===null));
 const wrong=clone(N);wrong.games_emitted++;
 assert.equal(safeNhl(wrong,T),false);
});
test("future source snapshots are rejected rather than surfaced as fresh",()=>{
 const m=clone(M);m.generated_at_utc="2032-01-01T00:00:00Z";
 assert.equal(sourceMatch(m,T),false);
 const n=clone(N);n.generated_at_utc="2032-01-01T00:00:00Z";
 assert.equal(safeNhl(n,T),false);
});
test("site never treats recorded historical prices as current odds",()=>{
 const s=build({picks:P,matches:M,nhl:N},T);
 for(const e of s.events){
  assert.equal(e.actionable,false);
  assert.ok(e.why.some(x=>x.includes("cote française actuelle")));
  for(const q of e.historicalQuotes){
   assert.ok(q.observedAt);
   assert.ok(q.quote>1);
  }
 }
});
