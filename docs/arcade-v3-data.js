/* REVUE ARCADE V3 · pure, defensive view model.
 * Independent timestamped sources, no live bookmaker odds, no betting advice.
 * This file deliberately has no DOM dependency so CI can test its behavior. */
"use strict";
(function(root,factory){
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  else root.RevueArcadeV3=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
const DAY=86400000;
const ms=v=>{const t=Date.parse(v);return Number.isFinite(t)?t:null;};
const finite=(v,min=-Infinity,max=Infinity)=>typeof v==="number"&&Number.isFinite(v)&&v>=min&&v<=max;
const age=(iso,now,maxH)=>{const t=ms(iso);return t!==null&&t<=now+120000&&now-t<=maxH*3600000;};
const future=(iso,now)=>{const t=ms(iso);return t!==null&&t>=now+20*60000;};
const statuses=new Set(["won","lost","push","pending","unverified"]);
function sourceMatch(doc,now){
  return !!(doc?.status==="experimental_revue_match_center"&&
    doc.bookmaker_prices_are_live===false&&doc.real_bets_enabled===false&&
    doc.validated_value_bets===0&&Array.isArray(doc.events)&&
    doc.metrics?.upcoming_matches===doc.events.length&&
    age(doc.generated_at_utc,now,12));
}
function sourcePicks(doc){
  return !!(doc?.status==="revue_independent_picks_hub_static_research_paper_only"&&
    doc.research_model_calibrated===false&&doc.verified_real_ev===false&&
    doc.live_bookmaker_prices===false&&doc.real_bets_enabled===false&&
    doc.original_clairvoyance_sql_parity===false&&
    Array.isArray(doc.paper_records)&&Array.isArray(doc.research_selections)&&
    doc.unique_research_selections===doc.research_selections.length&&
    doc.paper_summary?.total===doc.paper_records.length&&
    doc.paper_records.every(r=>r.real_bet===false&&statuses.has(r.status)&&
      finite(r.paper_stake_units,0,100000)&&
      (["won","lost","push"].includes(r.status)?
         r.verified_pregame===true&&finite(r.paper_profit_units,-1e7,1e7):
         r.paper_profit_units===null)));
}
function paper(doc){
  if(!sourcePicks(doc))return null;
  const r=doc.paper_records,s=doc.paper_summary,settled=r.filter(x=>["won","lost","push"].includes(x.status));
  const stake=settled.reduce((v,x)=>v+x.paper_stake_units,0);
  const profit=settled.reduce((v,x)=>v+x.paper_profit_units,0);
  const wins=settled.filter(x=>x.status==="won").length;
  const losses=settled.filter(x=>x.status==="lost").length;
  const pushes=settled.filter(x=>x.status==="push").length;
  const pending=r.filter(x=>x.status==="pending").length;
  const excluded=r.filter(x=>x.status==="unverified").length;
  if(s.settled!==settled.length||s.wins!==wins||s.losses!==losses||
     s.pushes!==pushes||s.pending!==pending||s.excluded!==excluded||
     Math.abs(profit-s.paper_profit_units)>.011||
     Math.abs(stake-s.settled_stake_units)>.011) return null;
  return {
    settled:settled.length,won:wins,lost:losses,push:pushes,pending,excluded,
    profit:Math.round(profit*100)/100,stake:Math.round(stake*100)/100,
    roi:stake>0?Math.round(profit/stake*10000)/100:null,
    winrate:settled.length?Math.round(wins/settled.length*1000)/10:null,
    records:[...r].filter(x=>x.league!=="CFB").sort((a,b)=>(ms(b.start_utc)||0)-(ms(a.start_utc)||0)),
    observedAt:doc.source_ledger_generated_at_utc,
  };
}
function safeNhl(doc,now){
  return !!(doc?.version==="revue_nhl_frontend_observed_v1"&&
   doc.status==="prospective_research_partial_input_frontend_not_parity"&&
   doc.exact_original_frontend_predictions_verified===false&&
   doc.odds_and_value_bets_enabled===false&&doc.real_bets_enabled===false&&
   doc.paper_bets_auto_created===false&&doc.updated_frozen_ledgers===false&&
   Array.isArray(doc.games)&&doc.games_emitted===doc.games.length&&
   age(doc.generated_at_utc,now,48));
}
function originalResearch(doc,now){
 if(!sourcePicks(doc)||!age(doc.source_engine_generated_at_utc,now,6))return new Map();
 const m=new Map();
 for(const r of doc.research_selections){
  if(r.league==="CFB"||!future(r.start_utc,now)||
    r.real_bet!==false||r.model_is_calibrated!==false||
    r.qualified_positive_ev!==false||r.available_as_real_market!==false)
   continue;
  const quote=r.best_observed_price;
  if(!quote||!finite(quote.decimal_odds,1.01,10000)||
     !age(quote.quote_at_utc,now,6)||
     (ms(quote.quote_at_utc)||Infinity)>(ms(r.start_utc)||0)-20*60000)
     continue;
  const k=r.league+":"+r.event_id;
  if(!m.has(k))m.set(k,[]);
  m.get(k).push({market:r.market,side:r.side,line:r.line,
    selection:r.selection_label,quote:quote.decimal_odds,
    bookmaker:quote.bookmaker,observedAt:quote.quote_at_utc});
 }
 return m;
}
function sourceModels(event){
 return Array.isArray(event.research)?event.research
  .filter(m=>m&&m.calibrated===false&&m.probabilities&&typeof m.probabilities==="object")
  .map(m=>({name:String(m.label||m.id||"Modèle expérimental"),
    probabilities:Object.fromEntries(Object.entries(m.probabilities)
      .filter(([k,v])=>finite(v,0,1)).slice(0,7))})).slice(0,3):[];
}
function build(sources,now){
 const gamesOk=sourceMatch(sources.matches,now);
 const picksOk=sourcePicks(sources.picks);
 const nhlOk=safeNhl(sources.nhl,now);
 const journal=paper(sources.picks);
 const quotes=originalResearch(sources.picks,now);
 const hockey=new Map(nhlOk?sources.nhl.games.filter(g=>future(g.start_utc,now)&&
   g.source_equivalent_predictions===false&&g.bookmaker_quotes_available===false&&
   g.starting_goalies_verified===false&&g.injuries_verified===false&&
   finite(g.research?.ensemble_home,0,1)&&finite(g.research?.monte_carlo_home,0,1))
   .map(g=>[String(g.event_id),g]):[]);
 const events=[];
 if(gamesOk)for(const g of sources.matches.events){
  if(g.league==="CFB"||!future(g.start_utc,now)||
     g.qualified_for_real_betting!==false||g.recommendation!==null||g.ev!==null||
     !g.event_id||!g.league||!g.home||!g.away)continue;
  const key=g.league+":"+g.event_id;
  const h=g.league==="NHL"?hockey.get(String(g.event_id)):null;
  if(h&&(h.home!==g.home||h.away!==g.away||ms(h.start_utc)!==ms(g.start_utc)))continue;
  const q=quotes.get(key)||[];
  const srcModels=sourceModels(g);
  const why=[
    "Aucune cote française actuelle confirmée pour une comparaison EV.",
    "Aucun modèle calibré et validé pour recommander une mise.",
  ];
  if(!srcModels.length&&!h)why.push("Probabilités indisponibles sur ce match.");
  if(h)why.push("NHL : gardien titulaire, blessures et données NHL Edge non vérifiés.");
  if(q.length)why.push("Une cote historique existe mais ne constitue pas une offre actuelle.");
  events.push({
    key,league:g.league,sport:g.sport||g.league,id:String(g.event_id),
    home:String(g.home),away:String(g.away),start:g.start_utc,
    modelCount:srcModels.length+(h?2:0),
    models:srcModels,hockey:h?{
      mc:h.research.monte_carlo_home,ensemble:h.research.ensemble_home,
      drawCount:h.research.simulation_draws,
      goalieHome:h.observed?.home?.goalie_name||null,
      goalieAway:h.observed?.away?.goalie_name||null,
      inputsComplete:false,
    }:null,
    historicalQuotes:q.slice(0,2),
    why,
    verdict:"AUCUN PARI RECOMMANDÉ",
    actionable:false,
  });
 }
 events.sort((a,b)=>(ms(a.start)||0)-(ms(b.start)||0));
 return {
  version:"arcade_simple_source_gated_v1",
  generatedAt:new Date(now).toISOString(),
  noValidatedBets:true,
  reason:"Aucune EV positive validée avec modèle calibré et cote française actuelle.",
  sources:{
   matches:gamesOk?"fresh":"missing_or_stale",
   research:picksOk?"archived_paper_only":"unverified",
   nhl:nhlOk?"partial_research":"missing_or_stale",
  },
  matchUpdated:gamesOk?sources.matches.generated_at_utc:null,
  paper:journal,
  events,
  hiddenCFB:true,
 };
}
return {build,paper,sourcePicks,sourceMatch,safeNhl,originalResearch};
});