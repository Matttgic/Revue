"use strict";
/* Independent Revue read-only adapter from published reference hockey fixtures.
   Extracts factual schedules only, NEVER upstream scripts or American odds.
   Predictions use local, already source-tested Revue equations. */
const fs=require("node:fs"),path=require("node:path");
const {euroHockeyGame}=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_games.js");
const {euroEnsemble}=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_ensemble.js");
const LEAGUES=["shl","nla","extraliga"];
const ORIGIN="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/main/docs/";
const AHEAD=72*3600000,AGE=36*3600000,LEAD=20*60000;
const ok=(n,min,max)=>typeof n==="number"&&Number.isFinite(n)&&n>=min&&n<=max;
function time(s){
 if(typeof s!=="string")throw Error("Date absente");
 const x=s.replace(/^(\d{4}-\d\d-\d\d) (\d\d:\d\d) UTC$/,"$1T$2:00Z");
 if(!/(Z|[+-]\d\d:\d\d)$/.test(x)||!Number.isFinite(Date.parse(x)))throw Error("Date sans fuseau");
 return Date.parse(x);
}
function goodTeam(t){
 return t&&typeof t.name==="string"&&t.name.length>0&&t.name.length<110&&
  Number.isInteger(t.gp)&&ok(t.gp,3,90)&&ok(t.gf,0,800)&&ok(t.ga,0,800)&&
  (t.gm==null||ok(t.gm,0,15))&&
  (!t.prevSeason||(
    Number.isInteger(t.prevSeason.gp)&&ok(t.prevSeason.gp,0,90)&&
    ok(t.prevSeason.gf,0,800)&&ok(t.prevSeason.ga,0,800)&&
    (t.prevSeason.gm==null||ok(t.prevSeason.gm,0,15))
  ));
}
function build(sources,now=Date.now()){
 const report={status:"revue_euro_hockey_research_reference_observed",
  version:"revised_eu_hockey_1",generated_at_utc:new Date(now).toISOString(),
  source_repository:"Purple-Wraith/clairvoyance-backend",
  original_source_output_equivalence_verified:false,
  moneyline_bookmaker_odds:null,fr_bookmaker_odds_verified:false,
  calibrated:false,real_bets_enabled:false,ev_verified:false,
  horizon_hours:72,competitions:{},total_games:0,
  note:"Public reference game/standings facts and Revue independently checked same-input formulas. No copied upstream scripts, US bookmaker prices, or original database claims."};
 const finals={};
 for(const league of LEAGUES){
  const source=sources[league];const entry={league:league.toUpperCase(),status:"unavailable",
    games:[],source_generated_utc:null},seen=new Set();
  report.competitions[league]=entry;
  if(!source||!source.teams||!Array.isArray(source.games))continue;
  try{
   if(source.games.length>1200||Object.keys(source.teams).length>75)throw Error("bad source count");
   const ts=time(source.generated_at);entry.source_generated_utc=new Date(ts).toISOString();
   if(ts>now+120000||now-ts>AGE){entry.status="stale";continue;}
   const rows=[];
   for(const g of source.games){
    if(!g||typeof g.id!=="string"||!/^[-\w]{5,48}$/.test(g.id)||
       seen.has(g.id))throw Error("missing or duplicate event id");
    seen.add(g.id);
    if(!["pre","post"].includes(g.state)||!g.home||!g.away||g.home===g.away||
       !goodTeam(source.teams[g.home])||!goodTeam(source.teams[g.away]))continue;
    let start;try{start=time(g.date);}catch{continue;}
    rows.push({...g,start});
   }
   const past=rows.filter(g=>g.state==="post"&&g.start<now&&
     Number.isInteger(g.homeScore)&&Number.isInteger(g.awayScore)&&
     ok(g.homeScore,0,35)&&ok(g.awayScore,0,35));
   const model={teams:source.teams,games:past};
   for(const g of rows){
    if(g.state!=="pre"||g.start<now+LEAD||g.start>now+AHEAD)continue;
    const observedTotal=ok(g.ou,.5,15)?g.ou:null;
    const p=euroHockeyGame(g.home,g.away,observedTotal,{data:model});
    const q=euroEnsemble(league,g.home,g.away,observedTotal,null,{data:model});
    if(!p||!q||![p.hwP,p.awP,p.overP,q.p].every(x=>ok(x,0,1))||
       !ok(p.avgH,0,15)||!ok(p.avgA,0,15))continue;
    entry.games.push({
      key:league.toUpperCase()+":"+g.id,event_id:g.id,league:league.toUpperCase(),
      home:source.teams[g.home].name,away:source.teams[g.away].name,
      kickoff_utc:new Date(g.start).toISOString(),
      source_observed_at_utc:new Date(ts).toISOString(),
      home_gp:source.teams[g.home].gp,away_gp:source.teams[g.away].gp,
      poisson_home_win:Number(p.hwP.toFixed(5)),
      ensemble_home_win:Number(q.p.toFixed(5)),
      poisson_over:Number(p.overP.toFixed(5)),
      total_line:p.ouLine,expected_home_goals:Number(p.avgH.toFixed(3)),
      expected_away_goals:Number(p.avgA.toFixed(3)),
      calibrated:false,bet_recommended:false,fr_bookmaker_odds:null,
      source_parity_same_real_inputs_verified:false
    });
   }
   entry.games.sort((a,b)=>a.kickoff_utc.localeCompare(b.kickoff_utc)||a.event_id.localeCompare(b.event_id));
   finals[league]=past.map(g=>({
    key:league.toUpperCase()+":"+g.id,
    home:source.teams[g.home].name,away:source.teams[g.away].name,
    kickoff_utc:new Date(g.start).toISOString(),
    observed_at_utc:new Date(ts).toISOString(),
    home_score:g.homeScore,away_score:g.awayScore
   }));
   report.total_games+=entry.games.length;
   entry.status="ok";entry.source_finals_observed=past.length;
  }catch(e){entry.games=[];entry.status="failed";entry.error=String(e.message).slice(0,130);delete finals[league];}
 }
 return {report,finals};
}
function emptyLedger(){return{version:"euro_hockey_immutable_pre_match_v1",records:[]};}
function tracker(ledger,output,now=Date.now()){
 if(!ledger||ledger.version!=="euro_hockey_immutable_pre_match_v1"||
    !Array.isArray(ledger.records))throw Error("Invalid immutable ledger");
 const copy=JSON.parse(JSON.stringify(ledger)),keys=new Set();
 for(const rec of copy.records){
  if(keys.has(rec.key)||rec.real_bet!==false||rec.units!==0)throw Error("Unsafe prior record");
  keys.add(rec.key);
  if(rec.status!=="pending")continue;
  const league=rec.league.toLowerCase();
  if(output.report.competitions[league]?.status!=="ok")continue;
  const result=(output.finals[league]||[]).find(x=>x.key===rec.key);
  if(!result||result.home!==rec.home||result.away!==rec.away||
     result.kickoff_utc!==rec.kickoff_utc||
     time(rec.locked_at_utc)>time(rec.kickoff_utc)-LEAD||
     time(rec.source_generated_at_utc)>time(rec.locked_at_utc)||
     time(result.observed_at_utc)<=time(rec.kickoff_utc)||
     result.home_score===result.away_score)continue;
  if(!ok(rec.p_home,0,1))throw Error("Corrupt locked probability");
  const y=result.home_score>result.away_score?1:0;
  Object.assign(rec,{status:"settled",result:y,
   score:{home:result.home_score,away:result.away_score},
   result_source:"reference_feed_post_state_not_independent_official",
   result_observed_at_utc:result.observed_at_utc,
   brier:Number(((rec.p_home-y)**2).toFixed(6)),
   log_loss:Number((-Math.log(y?rec.p_home:1-rec.p_home)).toFixed(6))});
 }
 for(const league of LEAGUES){
  if(output.report.competitions[league]?.status!=="ok")continue;
  for(const g of output.report.competitions[league].games){
   if(keys.has(g.key)||time(g.kickoff_utc)-now<LEAD)continue;
   copy.records.push({
    key:g.key,league:g.league,event_id:g.event_id,home:g.home,away:g.away,
    kickoff_utc:g.kickoff_utc,locked_at_utc:new Date(now).toISOString(),
    source_generated_at_utc:g.source_observed_at_utc,
    p_home:g.ensemble_home_win,status:"pending",
    result:null,score:null,brier:null,log_loss:null,real_bet:false,units:0
   });
   keys.add(g.key);
  }
 }
 copy.records.sort((a,b)=>a.kickoff_utc.localeCompare(b.kickoff_utc)||a.key.localeCompare(b.key));
 return copy;
}
function performance(ledger,now=Date.now()){
 const leagues={};
 for(const l of LEAGUES){
  const recs=ledger.records.filter(r=>r.league===l.toUpperCase());
  const done=recs.filter(r=>r.status==="settled");
  leagues[l]={locked:recs.length,settled:done.length,
   mean_brier:done.length?Number((done.reduce((a,r)=>a+r.brier,0)/done.length).toFixed(6)):null,
   mean_log_loss:done.length?Number((done.reduce((a,r)=>a+r.log_loss,0)/done.length).toFixed(6)):null};
 }
 return{status:"independent_euro_hockey_pre_match_research",generated_at_utc:new Date(now).toISOString(),
  total_locked:ledger.records.length,total_settled:ledger.records.filter(r=>r.status==="settled").length,
  leagues,roi:null,real_bets:0,
  observed_post_state_is_not_independent_official_verification:true};
}
async function run(){
 const root=path.resolve(process.argv[2]||"docs");
 const sources={};
 for(const league of LEAGUES){
  try{
   const response=await fetch(ORIGIN+league+"_schedule.json",{signal:AbortSignal.timeout(15000)});
   if(!response.ok)throw Error("HTTP "+response.status);
   const txt=await response.text();
   if(txt.length>1800000)throw Error("Source too large");
   sources[league]=JSON.parse(txt);
  }catch(e){sources[league]=null;process.stderr.write(league+": "+String(e.message)+"\n");}
 }
 const current=Date.now(),output=build(sources,current),file=path.join(root,"euro-hockey-prospective-ledger.json");
 const previous=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,"utf8")):emptyLedger();
 const ledger=tracker(previous,output,current);
 fs.mkdirSync(root,{recursive:true});
 for(const [name,data] of [["euro-hockey-latest.json",output.report],
  ["euro-hockey-prospective-ledger.json",ledger],
  ["euro-hockey-prospective-performance.json",performance(ledger,current)]])
  fs.writeFileSync(path.join(root,name),JSON.stringify(data,null,2)+"\n");
 process.stdout.write("EU leagues: "+output.report.total_games+" future matches, "+
  ledger.records.length+" frozen research locks, "+
  ledger.records.filter(x=>x.status==="settled").length+" settled. No odds or bets.\n");
}
if(require.main===module)run().catch(e=>{process.stderr.write(String(e.stack)+"\n");process.exitCode=1;});
module.exports={time,build,tracker,emptyLedger,performance};
