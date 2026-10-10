"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {build,tracker,emptyLedger,performance,time}=require("../outils/euro_hockey_reference_feed.js");
const NOW=Date.UTC(2026,9,10,12);
const iso=hours=>new Date(NOW+hours*3600000).toISOString();
function fixture(){
 return{
  generated_at:"2026-10-10 11:15 UTC",season:"2026-2027",
  teams:{
   A:{name:"Alpha",gp:8,w:4,gf:25,ga:24,gm:6,prevSeason:{gp:52,gf:165,ga:155,gm:6}},
   B:{name:"Beta",gp:9,w:5,gf:21,ga:27,gm:5.9,prevSeason:{gp:52,gf:158,ga:178,gm:6.5}}
  },games:[
   {id:"future-1234",home:"A",away:"B",date:iso(5),state:"pre",ou:5.5,
    odds:{ml:{home:2.4,away:1.6},bk:["bet365.us"]}},
   {id:"final-1234",home:"A",away:"B",date:iso(-50),state:"post",homeScore:5,awayScore:1},
   {id:"final-1235",home:"B",away:"A",date:iso(-34),state:"post",homeScore:4,awayScore:2},
   {id:"final-1236",home:"A",away:"B",date:iso(-20),state:"post",homeScore:3,awayScore:2},
   {id:"later-1234",home:"B",away:"A",date:iso(84),state:"pre"},
   {id:"not-final",home:"B",away:"A",date:iso(-2),state:"pre",homeScore:4,awayScore:0}
  ]};
}
function triple(){return {shl:fixture(),nla:fixture(),extraliga:fixture()};}
test("three reference leagues have genuinely constructed non-staked local Poisson and ensemble projections",()=>{
 const d=build(triple(),NOW).report;
 assert.equal(d.total_games,3);
 assert.equal(d.real_bets_enabled,false);
 assert.equal(d.fr_bookmaker_odds_verified,false);
 assert.equal(d.original_source_output_equivalence_verified,false);
 for(const [lg,row] of Object.entries(d.competitions)){
  assert.equal(row.games.length,1);
  assert.equal(row.games[0].league,lg.toUpperCase());
  assert.ok(row.games[0].ensemble_home_win>0&&row.games[0].ensemble_home_win<1);
  assert.ok(row.games[0].poisson_home_win>0&&row.games[0].poisson_home_win<1);
  assert.equal(row.games[0].fr_bookmaker_odds,null);
  assert.equal(row.games[0].source_parity_same_real_inputs_verified,false);
 }
});
test("stale feeds and duplicate IDs fail closed",()=>{
 const x=triple();x.shl.generated_at="2026-10-07 11:15 UTC";
 let r=build(x,NOW);
 assert.equal(r.report.competitions.shl.status,"stale");
 assert.equal(r.report.total_games,2);
 x.shl=fixture();x.nla.games.push({...x.nla.games[0]});
 r=build(x,NOW);
 assert.equal(r.report.competitions.nla.status,"failed");
 assert.equal(r.report.total_games,2);
});
test("frozen pending forecasts cannot be revised after the fixture's stats change",()=>{
 const x=triple(),out=build(x,NOW),journal=tracker(emptyLedger(),out,NOW);
 assert.equal(journal.records.length,3);
 assert.ok(journal.records.every(x=>x.status==="pending"&&x.units===0&&x.real_bet===false));
 x.shl.teams.A.gf=500;
 const updated=tracker(journal,build(x,NOW+3600000),NOW+3600000);
 assert.equal(updated.records.length,3);
 assert.equal(updated.records.find(x=>x.league==="SHL").p_home,
              journal.records.find(x=>x.league==="SHL").p_home);
});
test("result settlement requires matching identity, time and post-state",()=>{
 const x=triple(),first=tracker(emptyLedger(),build(x,NOW),NOW);
 x.nla.generated_at="2026-10-10 19:30 UTC";
 x.nla.games[0]={...x.nla.games[0],state:"post",homeScore:4,awayScore:2};
 const later=NOW+8*3600000;
 const done=tracker(first,build(x,later),later);
 const r=done.records.find(x=>x.league==="NLA");
 assert.equal(r.status,"settled");assert.equal(r.result,1);
 assert.equal(r.result_source,"reference_feed_post_state_not_independent_official");
 assert.ok(r.brier>=0&&r.log_loss>=0);
 assert.equal(performance(done,later).roi,null);
 const falsified=triple();falsified.nla.generated_at=x.nla.generated_at;
 falsified.nla.games[0]={...x.nla.games[0],away:"UNKNOWN"};
 const prevented=tracker(first,build(falsified,later),later);
 assert.equal(prevented.records.find(x=>x.league==="NLA").status,"pending");
});
test("a late lock is not backdated into a scored success",()=>{
 const x=triple(),first=tracker(emptyLedger(),build(x,NOW),NOW);
 first.records.find(x=>x.league==="SHL").locked_at_utc=iso(5.1);
 x.shl.generated_at="2026-10-10 19:30 UTC";
 x.shl.games[0]={...x.shl.games[0],state:"post",homeScore:4,awayScore:2};
 const out=tracker(first,build(x,NOW+8*3600000),NOW+8*3600000);
 assert.equal(out.records.find(x=>x.league==="SHL").status,"pending");
});
test("old journal never accepts real bets or duplicate locks",()=>{
 const out=build(triple(),NOW),j=tracker(emptyLedger(),out,NOW);
 j.records[0].real_bet=true;
 assert.throws(()=>tracker(j,out,NOW),/Unsafe prior/);
 j.records[0].real_bet=false;j.records.push({...j.records[0]});
 assert.throws(()=>tracker(j,out,NOW),/Unsafe prior/);
});
test("timezone must be explicit",()=>{
 assert.equal(time("2026-10-10 11:15 UTC"),Date.parse("2026-10-10T11:15:00Z"));
 assert.throws(()=>time("2026-10-10T11:15:00"));
});
