'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {sample,hitRate,poisson}=require('../docs/nhl-player-analytics.js');
// Synthetic fixtures for arithmetic only; never published as player data.
const games=Array.from({length:22},(_,i)=>({event_id:String(i),date:`2026-01-${String(i+1).padStart(2,'0')}T00:00:00Z`,season:2026,shots:i%4,home:i%2===0,opponent:i%2?'BOS':'ANA'}));
test('chronology, context, uniqueness and no input mutation',()=>{
 const rows=sample([...games,games[21]],'shots',{venue:'home',opponent:'ANA',season:'2026'});
 assert.equal(rows.length,11);assert.equal(rows[0].event_id,'20');assert.equal(games[0].event_id,'0');
 assert.equal(sample(games,'shots',{season:'2027'}).length,0);
 assert.equal(sample([{...games[0],home:null}],'shots',{venue:'away'}).length,0);
});
test('L5 L10 L20 use actual denominator and strict Over',()=>{
 const rows=sample(games,'shots');
 assert.deepEqual(hitRate(rows,'shots',2.5,5),{n:5,hits:1,rate:.2,missing:0});
 assert.equal(hitRate(rows,'shots',2.5,10).n,10);
 assert.equal(hitRate(rows,'shots',2.5,20).n,20);
 assert.equal(hitRate(rows.slice(0,2),'shots',2.5,20).n,2);
});
test('missing is not zero and does not backfill older appearances',()=>{
 const rows=sample(games,'shots');rows[0]={...rows[0],shots:null};rows[1]={...rows[1],shots:'3'};
 const r=hitRate(rows,'shots',2.5,5);assert.equal(r.n,3);assert.equal(r.missing,2);
 assert.equal(hitRate([{shots:0}],'shots',.5,5).rate,0);
 assert.equal(hitRate([{shots:null}],'shots',.5,5).rate,null);
 assert.equal(hitRate([],'shots',.5,5).rate,null);
 assert.equal(hitRate(rows,'shots',NaN,5).rate,null);
});
test('probability is a separate Poisson calculation and no EV exported',()=>{
 assert.ok(Math.abs(poisson(1,.5)-(1-Math.exp(-1)))<1e-12);
 assert.equal(poisson(null,.5),null);assert.equal(poisson(-1,.5),null);assert.equal(poisson(1,1),null);
 assert.equal(require('../docs/nhl-player-analytics.js').ev,undefined);
});
