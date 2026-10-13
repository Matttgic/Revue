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
test('incomplete samples, freshness and failed reads are data quality, never predictive certainty',()=>{
 const A=require('../docs/nhl-player-analytics.js'),now=Date.parse('2026-10-13T00:00:00Z');
 const rows=sample(games,'shots');
 const entry={status:'ok',season_collected_at:{2026:'2026-10-12T23:00:00Z'},diagnostics:[]};
 assert.equal(A.reliability(rows.slice(0,4),'shots',entry,2026,now).n,4);
 assert.equal(A.reliability(rows.slice(0,4),'shots',entry,2026,now).label,'Échantillon incomplet');
 assert.equal(A.reliability(rows,'shots',entry,2026,now).label,'Données bien couvertes');
 const missingRows=rows.map(g=>({...g,shots:null}));
 assert.equal(A.reliability(missingRows,'shots',entry,2026,now).n,0);
 assert.equal(A.reliability(rows,'shots',{...entry,season_collected_at:{2026:'2026-10-10T00:00:00Z'}},2026,now).label,'À actualiser');
 assert.equal(A.reliability(rows,'shots',{status:'partial'},2026,now).label,'Fraîcheur inconnue');
 assert.equal(A.reliability(rows,'shots',{...entry,diagnostics:[{season:2026,status:'unavailable'}]},2026,now).label,'Collecte partielle');
 assert.equal(A.reliability(rows,'shots',entry,2027,now).fresh,true);
 assert.equal(A.reliability(rows,'shots',{...entry,season_collected_at:{2026:'2026-10-14T00:00:00Z'}},2026,now).fresh,false);
});
test('quick name search ignores accents and case, no false matching of unknown names',()=>{
 const {searchPlayers}=require('../docs/nhl-player-analytics.js');
 const players=[{name:'Émile Test'},{name:'Autre Joueur'}];
 assert.deepEqual(searchPlayers(players,' EMILE '),[players[0]]);
 assert.equal(searchPlayers(players,'').length,2);
 assert.equal(searchPlayers(players,'absent').length,0);
});
test('duplicate identity representations count once and missing stats reduce actual denominator',()=>{
 const g={event_id:1,date:'2026-10-01T00:00:00Z',shots:3};
 assert.equal(sample([g,{...g,event_id:'1'}],'shots').length,1);
 const r=hitRate(sample([g,{event_id:'2',date:'2026-10-02T00:00:00Z',shots:null}],'shots'),'shots',2.5,20);
 assert.deepEqual(r,{n:1,hits:1,rate:1,missing:1});
});

test('manual decimal odds accept comma or dot and return only break-even, never EV',()=>{
 const {breakEvenOdds,ev}=require('../docs/nhl-player-analytics.js');
 assert.ok(Math.abs(breakEvenOdds('2,40')-1/2.4)<1e-12);
 assert.ok(Math.abs(breakEvenOdds('2.40')-1/2.4)<1e-12);
 assert.ok(Math.abs(breakEvenOdds(' 1,01 ')-1/1.01)<1e-12);
 for(const invalid of ['1','1,00','1,005','1001','2,40 euros','NaN','','-1','2 40',null,2.4]){
  assert.equal(breakEvenOdds(invalid),null);
 }
 assert.equal(ev,undefined);
});
