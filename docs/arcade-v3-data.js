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
function safeGoalies(doc,now){
 return !!(doc?.status==="espn_probable_goalies_observed_not_part_of_model"&&
   doc.source==="ESPN NHL scoreboard, separate from official NHL IDs"&&
   doc.used_in_prediction_model===false&&doc.real_bets_enabled===false&&
   doc.injuries_verified===false&&Array.isArray(doc.rows)&&
   age(doc.generated_at_utc,now,8)&&
   doc.rows.every(r=>r.used_in_model_probabilities===false&&
     r.sportsbook_prices_verified===false&&
     ["home_goalie","away_goalie"].every(k=>
       r[k]===null||(typeof r[k]==="object"&&
       typeof r[k].name==="string"&&r[k].name.length>0&&
       ["confirmed","projected"].includes(r[k].status)))));
}
function safeRadar(doc,now){
 return !!(doc?.version==="revue_pulsescore_six_hour_radar_v1"&&
    doc.status==="observed"&&doc.provider==="PulseScore"&&
    doc.horizon_hours===6&&Number.isInteger(doc.request_cap)&&
    doc.request_cap>0&&doc.request_cap<=8&&
    Number.isInteger(doc.requests_used)&&
    doc.requests_used>=0&&doc.requests_used<=doc.request_cap&&
    doc.market_prices_are_live===false&&
    doc.positive_ev_verified===false&&
    doc.model_is_calibrated===false&&
    doc.real_bets_enabled===false&&
    doc.new_paper_bets_created===false&&
    doc.existing_paper_ledger_modified===false&&
    age(doc.generated_at_utc,now,4)&&
    age(doc.source_model_generated_at_utc,ms(doc.generated_at_utc),6)&&
    Array.isArray(doc.observations)&&
    doc.matches_observed===doc.observations.length);
}
function radarComparisons(doc,now){
 const out=new Map();
 if(!safeRadar(doc,now))return out;
 const books=new Set(["betclic_fr","winamax_fr","unibet_fr","netbet_fr","pmu_fr"]);
 const selections=new Set(["home","away","draw","over","under"]);
 const seenEvents=new Set();
 const invalidEventIds=new Set();
 for(const game of doc.observations){
   if(!game||game.league==="CFB"||!game.league||!game.event_id||
      !future(game.start_utc,now))continue;
   const eventKey=game.league+":"+game.event_id;
   if(seenEvents.has(eventKey)){
     out.delete(eventKey);invalidEventIds.add(eventKey);continue;
   }
   if(invalidEventIds.has(eventKey))continue;
   seenEvents.add(eventKey);
   const groups=new Map();
   const rawSamples=[];
   for(const book of game.bookmakers||[]){
     if(!books.has(book.bookmaker))continue;
     for(const market of book.markets||[]){
       if(!["h2h","totals"].includes(market.market))continue;
       if(!age(market.quote_at,now,2)||ms(market.quote_at)>ms(game.start_utc)-20*60000)
         continue;
       for(const selection of market.outcomes||[]){
         if(!selections.has(selection.selection)||!finite(selection.price,1.01,100))
           continue;
         const line=market.market==="totals"?selection.line:null;
         if(market.market==="totals"&&!finite(line,.5,60))continue;
         if(market.market==="h2h"&&line!=null)continue;
         if(market.market==="totals"&&!["over","under"].includes(selection.selection))
           continue;
         if(market.market==="h2h"&&!["home","away","draw"].includes(selection.selection))
           continue;
         rawSamples.push({
           market:market.market,side:selection.selection,
           line,book:book.bookmaker,price:selection.price,
           observedAt:market.quote_at,
           periodRule:market.period_rule,
           comparableMarketRule:game.league!=="NHL"||
             market.period_rule==="including_ot_confirmed",
         });
         if(game.league==="NHL"&&market.period_rule!=="including_ot_confirmed")continue;
         const key=market.market+"|"+selection.selection+"|"+(line==null?"":line);
         if(!groups.has(key))groups.set(key,new Map());
         const peers=groups.get(key);
         if(peers.has(book.bookmaker)){peers.set(book.bookmaker,null);continue;}
         peers.set(book.bookmaker,{
           book:book.bookmaker,price:selection.price,quote_at:market.quote_at,
         });
       }
     }
   }
   const comparisons=[];
   for(const [key,group] of groups){
      const observed=[...group.values()].filter(Boolean);
      if(observed.length<2)continue;
      observed.sort((a,b)=>b.price-a.price);
      const [market,side,line]=key.split("|");
      const top=observed[0],bottom=observed[observed.length-1];
      comparisons.push({
       market,side,line:line===""?null:Number(line),
       topBook:top.book,topPrice:top.price,lowPrice:bottom.price,
       differencePercent:Math.round((top.price/bottom.price-1)*1000)/10,
       bookCount:observed.length,
       observedAt:top.quote_at,
       comparableVerified:true,
       impliedValueVerified:false,
      });
   }
   comparisons.sort((a,b)=>b.differencePercent-a.differencePercent);
   const referenceLine=game.league==="NHL"?5.5:2.5;
   rawSamples.sort((a,b)=>
     (a.market==="h2h"?0:1)-(b.market==="h2h"?0:1)||
     (a.market==="totals"?Math.abs(a.line-referenceLine):0)-
     (b.market==="totals"?Math.abs(b.line-referenceLine):0)||
     a.book.localeCompare(b.book));
   const examples=[],shown=new Set();
   for(const item of rawSamples){
     const sampleKey=item.market+":"+item.side;
     if(shown.has(sampleKey))continue;
     shown.add(sampleKey);examples.push(item);
     if(examples.length>=5)break;
   }
   out.set(eventKey,{home:game.home,away:game.away,start:game.start_utc,
      compared:comparisons.slice(0,5),examples});
 }
 return out;
}

const OWNED_LEAGUES=new Set(["PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","NBA","WNBA","NCAAB","NFL","MLB"]);
const OWNED_MODELS=new Set(["baseline","advanced_team","montecarlo_bayes","football_advanced","own_elo"]);
const OWNED_SOCCER=new Set(["PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1"]);
function ownedSnapshot(ledger,report,now){
 const empty={status:"unavailable",locked:0,settled:0,elo:0,rows:new Map(),stats:null,since:null};
 if(!ledger||!report||ledger.version!=="revue_phase2_owned_history_v1"||
   report.version!=="revue_phase2_owned_performance_v1"||
   report.status!=="new_revue_history_prospective_not_source_sql"||
   ledger.since_utc!==report.since_utc||
   report.identical_original_clairvoyance_sql_history!==false||
   report.replayed_old_results!==false||report.real_bets_enabled!==false||
   report.odds_queried!==false||report.roi_computed!==false||
   report.models_calibrated!==false||report.bet_recommendations_verified!==false||
   !age(report.generated_at_utc,now,18)||
   !ledger.events||typeof ledger.events!=="object"||Array.isArray(ledger.events)||
   !ledger.elo_events||typeof ledger.elo_events!=="object"||Array.isArray(ledger.elo_events)||
   !ledger.elo_ratings||typeof ledger.elo_ratings!=="object"||
   !report.per_league||typeof report.per_league!=="object")
   return empty;
 const since=ms(ledger.since_utc),updated=ms(ledger.updated_at_utc);
 if(since===null||since>now+120000||updated===null||updated<since||updated>now+120000||
   ms(report.generated_at_utc)<updated-120000)return empty;
 const rows=new Map(),perLeague=new Map(),count={settled:0};
 for(const [key,e] of Object.entries(ledger.events)){
  if(!e||typeof e!=="object"||!OWNED_LEAGUES.has(e.league)||
    key!==e.league+":"+e.event_id||rows.has(key)||
    typeof e.home!=="string"||!e.home||
    typeof e.away!=="string"||!e.away||e.home===e.away||
    !["pending","settled"].includes(e.status)||
    e.real_bet!==false||e.stake_units!==0||
    e.market!==(OWNED_SOCCER.has(e.league)?"1X2_90min":"full_game_two_way")||
    ms(e.start_utc)===null||ms(e.locked_at_utc)===null||
    ms(e.locked_at_utc)<since||ms(e.locked_at_utc)>now+120000||
    ms(e.locked_at_utc)>ms(e.start_utc)-20*60000||
    !e.probabilities||typeof e.probabilities!=="object"||
    !e.probabilities.baseline)return empty;
  const expected=OWNED_SOCCER.has(e.league)?3:2;
  const projections=[];
  for(const [id,m] of Object.entries(e.probabilities)){
   const probs=m?.probabilities;
   if(!OWNED_MODELS.has(id)||!Array.isArray(probs)||probs.length!==expected||
      !probs.every(p=>finite(p,0,1)&&p>0&&p<1)||
      Math.abs(probs.reduce((a,b)=>a+b,0)-1)>0.0001||
      typeof m.model_id!=="string"||!m.model_id||
      ms(m.published_at_utc)===null||ms(m.published_at_utc)>ms(e.locked_at_utc)||
      ms(m.published_at_utc)>ms(e.start_utc)-20*60000)return empty;
   projections.push({id,name:String(m.model_id),probabilities:[...probs],
     publishedAt:m.published_at_utc});
  }
  if(e.status==="settled"){
   if(ms(e.resolved_at_utc)===null||ms(e.resolved_at_utc)<ms(e.start_utc)||
     ms(e.resolved_at_utc)>now+120000||e.score_source!=="ESPN scoreboard"||
     !Number.isInteger(e.home_score)||!Number.isInteger(e.away_score)||
     e.home_score<0||e.away_score<0||
     !e.model_scores||Object.keys(e.model_scores).length!==projections.length||
     projections.some(p=>!finite(e.model_scores[p.id]?.brier,0,2)||
       !finite(e.model_scores[p.id]?.log_loss,0,100)))return empty;
   count.settled++;
  }else if(e.model_scores!==null||e.result!==null)return empty;
  const countFor=perLeague.get(e.league)||{locked:0,settled:0};
  countFor.locked++;
  if(e.status==="settled")countFor.settled++;
  perLeague.set(e.league,countFor);
  rows.set(key,{key,league:e.league,eventId:String(e.event_id),
    home:e.home,away:e.away,start:e.start_utc,lockedAt:e.locked_at_utc,
    market:e.market,status:e.status,result:e.result,
    projections,scores:e.status==="settled"?e.model_scores:null});
 }
 if(rows.size!==report.total_unique_matches_locked||
   count.settled!==report.total_unique_matches_settled||
   Object.keys(ledger.elo_events).length!==report.total_independent_elo_finals)return empty;
 for(const [lg,x] of perLeague){
  const sum=report.per_league[lg];
  if(!sum||x.locked!==sum.locked||x.settled!==sum.settled)return empty;
 }
 const validResearch=Object.values(report.per_league).every(group=>
   group&&typeof group==="object"&&group.models&&
   Object.values(group.models).every(stat=>
     Number.isInteger(stat?.settled)&&stat.settled>=0&&
     (stat.settled===0?(stat.brier===null&&stat.log_loss===null):
      finite(stat.brier,0,2)&&finite(stat.log_loss,0,100))));
 if(!validResearch)return empty;
 return {status:"prospective_independent_unvalidated",
   locked:rows.size,settled:count.settled,elo:report.total_independent_elo_finals,
   rows,stats:report.per_league,since:ledger.since_utc};
}

function build(sources,now){
 const gamesOk=sourceMatch(sources.matches,now);
 const picksOk=sourcePicks(sources.picks);
 const nhlOk=safeNhl(sources.nhl,now);
 const journal=paper(sources.picks);
 const quotes=originalResearch(sources.picks,now);
 const radar=radarComparisons(sources.radar,now);
 const owned=ownedSnapshot(sources.ownedLedger,sources.ownedPerformance,now);
 const goalieRows=new Map();
 if(safeGoalies(sources.goalies,now))for(const r of sources.goalies.rows){
   if(!future(r.start_utc,now)||
      ms(r.observed_at_utc)>now+120000||
      ms(r.observed_at_utc)>ms(r.start_utc)-20*60000)continue;
   const key=String(r.event_id);
   if(goalieRows.has(key))goalieRows.set(key,null);
   else goalieRows.set(key,r);
 }
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
  const observedRadar=radar.get(key);
  const matchRadar=observedRadar&&observedRadar.home===g.home&&
     observedRadar.away===g.away&&ms(observedRadar.start)===ms(g.start_utc);
  const comparisons=matchRadar?observedRadar.compared:[];
  const priceSamples=matchRadar?observedRadar.examples:[];
  const espn=goalieRows.get(String(g.event_id));
  const goalie=(espn&&espn.home===g.home&&espn.away===g.away&&
               ms(espn.start_utc)===ms(g.start_utc))?espn:null;
  const srcModels=sourceModels(g);
  const ownCandidate=owned.rows.get(key);
  const own=(ownCandidate&&ownCandidate.home===g.home&&ownCandidate.away===g.away&&
    ms(ownCandidate.start)===ms(g.start_utc))?ownCandidate:null;
  const why=[
    "Aucune cote française actuelle confirmée pour une comparaison EV.",
    "Aucun modèle calibré et validé pour recommander une mise.",
  ];
  if(!srcModels.length&&!h)why.push("Probabilités indisponibles sur ce match.");
  if(h)why.push(goalie?
    "NHL : ESPN distingue les gardiens confirmés/probables, mais les blessures et données NHL Edge restent non vérifiées.":
    "NHL : gardien titulaire, blessures et données NHL Edge non vérifiés.");
  if(own)why.push("Revue phase 2 : "+own.projections.length+" modèle(s) gelé(s) avant ce match, non calibré(s). Historique indépendant, pas un avantage vérifié.");
  if(q.length)why.push("Une cote historique existe mais ne constitue pas une offre actuelle.");
  if(comparisons.length)why.push("PulseScore : écarts entre bookmakers FR observés, sans EV ni disponibilité en temps réel vérifiées.");
  else if(priceSamples.length)why.push("PulseScore : prix réellement observés mais sans comparaison suffisamment concordante de bookmakers.");
  events.push({
    key,league:g.league,sport:g.sport||g.league,id:String(g.event_id),
    home:String(g.home),away:String(g.away),start:g.start_utc,
    modelCount:srcModels.length+(h?2:0)+(own?own.projections.length:0),
    owned:own,
    models:srcModels,hockey:h?{
      mc:h.research.monte_carlo_home,ensemble:h.research.ensemble_home,
      drawCount:h.research.simulation_draws,
      goalieHome:h.observed?.home?.goalie_name||null,
      goalieAway:h.observed?.away?.goalie_name||null,
      espnGoalieHome:goalie?.home_goalie||null,
      espnGoalieAway:goalie?.away_goalie||null,
      espnObservedAt:goalie?.observed_at_utc||null,
      espnInformationNotIncludedInProbabilities:true,
      inputsComplete:false,
    }:null,
    historicalQuotes:q.slice(0,2),
    recentCrossBookPrices:comparisons,
    recentObservedPriceExamples:priceSamples,
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
   espnGoalies:safeGoalies(sources.goalies,now)?"observed_status_separate":"missing_or_stale",
   radar:safeRadar(sources.radar,now)?"bounded_six_hour_observations":"missing_or_stale",
   own:owned.status,
  },
  matchUpdated:gamesOk?sources.matches.generated_at_utc:null,
  paper:journal,
  ownedSummary:{locked:owned.locked,settled:owned.settled,elo:owned.elo,
    since:owned.since,stats:owned.stats},
  events,
  hiddenCFB:true,
 };
}
return {build,paper,sourcePicks,sourceMatch,safeNhl,safeGoalies,safeRadar,radarComparisons,originalResearch,ownedSnapshot};
});