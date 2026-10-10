"use strict";
/**
 * Source-aligned NHL frontend research bridge, with strictly observed features.
 * Uses Revue's independent official NHL + MoneyPuck snapshots, and the frozen
 * Revue fixture map. Unknown NHL Edge, injury, form, calibration and market
 * inputs are passed as explicit neutral defaults; NOT source production parity.
 * Never writes to the frozen forecasts, results ledger or places a bet.
 */
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const {nhlMonteCarlo, nhlEnsemble} =
  require("../modeles/reproduction/frontend_clairvoyance_nhl.js");

const VERSION = "revue_nhl_frontend_observed_v1";
const MIN_LEAD_MS = 20 * 60 * 1000;
const MAX_AGE_MS = 48 * 3600 * 1000;
const FIXED_MC_DRAWS = 25000;
const UNKNOWN = [
  "NHL Edge zone/speed", "high-danger chances", "Clairvoyance situational HV",
  "verified player injuries", "goalie availability/confirmed starter",
  "recent-game form", "original calibration coefficients",
  "NHL markets and confirmed bookmaker quotes",
  "original frontend goals-per-60 calculation",
  "original frontend xGF5 base rate (xGF/60 proxy used)",
];
const finite = (v,min,max) =>
  typeof v==="number" && Number.isFinite(v) && v>=min && v<=max;
const utc = s => {
  if(typeof s!=="string" || !/(Z|[+-]\d\d:\d\d)$/.test(s)) throw Error("Timestamp without timezone");
  const t=Date.parse(s);
  if(!Number.isFinite(t))throw Error("Bad ISO timestamp");
  return t;
};
function seedRng(key) {
  let state=crypto.createHash("sha256").update(key).digest().readUInt32LE(0);
  if(!state)state=1;
  return ()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return(state>>>0)/4294967296;};
}
function strictTeams(rows,key,season,allowed) {
  const seen=new Map();
  for(const r of rows) {
    if(!r || r.season!==season || (allowed && r.situation!==allowed))continue;
    const team=r[key];
    if(typeof team!=="string"||!(/^[A-Z]{2,4}$/.test(team)))throw Error("Invalid team identifier");
    if(seen.has(team))throw Error("Duplicated team "+team);
    seen.set(team,r);
  }
  return seen;
}
function goalieByTeam(rows,season) {
  const grouped=new Map();
  for(const r of rows) {
    if(r?.season!==season)continue;
    if(!/^[A-Z]{2,4}$/.test(r.team||"")||
      !Number.isInteger(r.games_played)||r.games_played<0||
      !finite(r.save_pct,0,1)||!finite(r.gsax,-200,200))
      throw Error("Invalid MoneyPuck goalie row");
    if(!grouped.has(r.team))grouped.set(r.team,[]);
    grouped.get(r.team).push(r);
  }
  const out=new Map();
  for(const [team,group] of grouped) {
    const n=Math.max(...group.map(g=>g.games_played));
    const tied=group.filter(g=>g.games_played===n);
    // The original uses the most-played goalie, NOT today's confirmed starter.
    // Equal GP would make the selection order-dependent: fail closed.
    out.set(team,tied.length===1&&n>0?tied[0]:null);
  }
  return out;
}
function snapshotState(d,expectedSource,now,maxAge=MAX_AGE_MS) {
  if(d?.source!==expectedSource)throw Error("Source identity mismatch: "+expectedSource);
  const observed=utc(d.generated_at_utc);
  if(observed>now||now-observed>maxAge)throw Error("Source stale or future: "+expectedSource);
  return observed;
}
function sanitizedTeams(mp,official,goalies,season) {
  const mp5=strictTeams(mp.seasons[season],"team",season,"5on5");
  const officialTeam=strictTeams(official.teams,"team_abbrev",season.replace("-",""));
  const primary=goalieByTeam(goalies.seasons[season],season);
  const teams={}, provenance={};
  for(const [team,row] of mp5) {
    const n=officialTeam.get(team),g=primary.get(team);
    if(!n||!g)continue;
    if(n.game_type_id!==2 || !finite(n.games_played,0,100)||
      !finite(n.goals_for_per_game,0,15)||!finite(n.goals_against_per_game,0,15)||
      !finite(n.pp_pct,0,1)||!finite(n.pk_pct,0,1)||
      !finite(row.xg_share,0,1)||!finite(row.xg_for_60,0,15)||
      !finite(row.xg_against_60,0,15)||
      !finite(g.gsax,-200,200)||!finite(g.save_pct,0,1))continue;
    // All provided numerical values are from observed sources. The historical
    // frontend's rich HV/Edge/injury/form fields aren't synthesized from stats.
    teams[team]={
      gf60:n.goals_for_per_game,ga60:n.goals_against_per_game,
      hv:{off:0,def:0,fin:0},
      edge:{},mp:{xgf_pct:row.xg_share*100},
      pp:n.pp_pct,pk:n.pk_pct,
      gsax:g.gsax,sv:g.save_pct,
      gp:n.games_played,
      xgf5:row.xg_for_60,
    };
    provenance[team]={
      games:row.games_played,official_games:n.games_played,
      goalie_name:g.name,goalie_games:g.games_played,
      goalie_is_confirmed_starter:false,
      xg5_share:row.xg_share, xg_for_60:row.xg_for_60,
      goal_rate_is_per_game_proxy_not_exact_source_gf60:true,
    };
  }
  return {teams,provenance,mp5};
}
function validateSources({shadow,mp,goalies,official},now) {
  if(!Number.isFinite(now))throw Error("Invalid clock");
  const season=mp?.current_season;
  if(!/^\d{4}-\d{4}$/.test(season||"")||
    Number(season.slice(5))!==Number(season.slice(0,4))+1||
    goalies?.current_season!==season||
    official?.season!==season.replace("-","")||
    shadow?.season!==season.replace("-",""))
    throw Error("Source seasons do not match");
  if(mp.is_live!==false||goalies.is_live!==false||
    goalies.confirmed_starters!==false||
    mp?.status?.[season]?.status!=="available"||
    goalies?.statuses?.[season]?.status!=="available"||
    official?.status!=="verified_nhl_official_stats_snapshot"||
    official.game_type_id!==2||
    official?.reports?.team_summary?.status!=="available"||
    shadow?.status!=="experimental_not_calibrated"||
    shadow.bookmaker_odds_available!==false||
    shadow.confirmed_starters!==false||
    shadow?.point_in_time_audit?.status!=="verified_temporal_bounds")
    throw Error("Snapshot provenance or research-only protection invalid");
  if(!Array.isArray(shadow.games)||!Array.isArray(official.teams)||
    !Array.isArray(goalies.seasons?.[season])||
    !Array.isArray(mp.seasons?.[season]))throw Error("Snapshot tables missing");
  const stamps={
    shadow:utc(shadow.generated_at_utc),
    moneypuck: snapshotState(mp,"MoneyPuck.com",now),
    moneyPuckGoalies: snapshotState(goalies,"MoneyPuck.com",now),
    official: snapshotState(official,"api.nhle.com/stats/rest/en",now),
    moneypuckProvider:utc(mp.status[season].source_updated_utc),
    goalieProvider:utc(goalies.statuses[season].source_updated_utc),
  };
  if(stamps.shadow>now||now-stamps.shadow>MAX_AGE_MS||
    stamps.moneypuckProvider>stamps.moneypuck||
    stamps.goalieProvider>stamps.moneyPuckGoalies)
    throw Error("Cross-source timestamps inconsistent");
  if(utc(shadow.point_in_time_audit.as_of_utc)!==stamps.shadow)
    throw Error("Frozen shadow observation timestamp mismatch");
  return {season,stamps};
}
function generate(source,now=Date.now()) {
  const {shadow,mp,goalies,official}=source;
  const {season,stamps}=validateSources(source,now);
  const {teams,provenance,mp5}=sanitizedTeams(mp,official,goalies,season);
  const seen=new Set(), skipped={},games=[];
  const skip=reason=>{skipped[reason]=(skipped[reason]||0)+1;};
  const kickoffCutoff=Math.max(...Object.values(stamps));
  for(const game of shadow.games){
    const id=String(game.event_id);
    if(!/^\d{8,14}$/.test(id)||seen.has(id))throw Error("Invalid or duplicated NHL fixture ID");
    seen.add(id);
    const kickoff=utc(game.start_utc);
    if(kickoff<now+MIN_LEAD_MS){skip("not_upcoming");continue;}
    if(kickoffCutoff>kickoff-MIN_LEAD_MS){skip("source_not_available_at_cutoff");continue;}
    const h=game.home,a=game.away;
    if(h===a||!teams[h]||!teams[a]){skip("missing_observed_team_or_unique_goalie");continue;}
    const originalXg=game.xg_5v5_share_pct||{};
    if(!finite(originalXg.home,0,100)||!finite(originalXg.away,0,100)||
      Math.abs(originalXg.home/100-mp5.get(h).xg_share)>1e-5||
      Math.abs(originalXg.away/100-mp5.get(a).xg_share)>1e-5){
      skip("different_money_puck_snapshot");continue;
    }
    // Explicitly neutral for unavailable independent measurements.
    const opts={
      teams,moneypuck:{teams:{
        [h]:{"5on5":{xgfPct:mp5.get(h).xg_share}},
        [a]:{"5on5":{xgfPct:mp5.get(a).xg_share}},
      }},
      injury:()=>({frac:0,goalie:{mp:0,edge:0}}),
      form:()=>({mult:1,delta:null,n:0,gfL:null}),
      playerInjury:()=>({penalty:0}),
      calibrator:p=>p,
      marketNhl:()=>null,
      random:seedRng(VERSION+"|"+id+"|"+stamps.shadow),
    };
    // Exactly 25k seeded draws, same canonical frontend JS kernel.
    const ensemble=nhlEnsemble(h,a,undefined,null,opts);
    if(!ensemble?.mcD||![ensemble.p,ensemble.pModel,ensemble.mc,
       ensemble.ouP,ensemble.mcD.avgT].every(x=>finite(x,0,20))){
      skip("invalid_model_output");continue;
    }
    if(!finite(ensemble.p,0,1)||!finite(ensemble.pModel,0,1)||
       !finite(ensemble.mc,0,1)||!finite(ensemble.ouP,0,1)){
      skip("invalid_probability");continue;
    }
    const m=ensemble.mcD;
    games.push({
      event_id:id,home:h,away:a,start_utc:game.start_utc,
      original_shadow_home_win:game.home_win,
      research:{
        ensemble_home:Math.round(ensemble.p*1e5)/1e5,
        ensemble_raw_home:Math.round(ensemble.pModel*1e5)/1e5,
        monte_carlo_home:Math.round(ensemble.mc*1e5)/1e5,
        monte_carlo_total_expected:Math.round(m.avgT*1e4)/1e4,
        total_over_reference_line:m.ouLine,
        probability_over_reference_line:Math.round(ensemble.ouP*1e5)/1e5,
        p_home_puck_line_minus_1_5:Math.round(m.rl15*1e5)/1e5,
        simulation_draws:FIXED_MC_DRAWS,
        market_blended:false, calibrated:false, actionable:false,
      },
      observed:{home:provenance[h],away:provenance[a]},
      feature_status:"partial_neutral_inputs_not_original_frontend_parity",
      pending_inputs:UNKNOWN,
      injuries_verified:false,
      starting_goalies_verified:false,
      bookmaker_quotes_available:false,
      source_equivalent_predictions:false,
      retroactive_prediction:false,
    });
  }
  return {
    version:VERSION,generated_at_utc:new Date(now).toISOString(),
    source_snapshot_utc:Object.fromEntries(Object.entries(stamps).map(([k,v])=>[k,new Date(v).toISOString()])),
    status:"prospective_research_partial_input_frontend_not_parity",
    data_season:season,fixtures_from:"Revue frozen NHL shadow",
    reference_models:["nhlMC","nhlEns"],
    formula_implementation:"modeles/reproduction/frontend_clairvoyance_nhl.js",
    team_data_from:["NHL Stats REST regular season","MoneyPuck current season 5on5","MoneyPuck goalie all situation"],
    missing_or_neutral_inputs:UNKNOWN,
    no_fictitious_injuries_or_confirmed_goalies:true,
    exact_original_frontend_predictions_verified:false,
    odds_and_value_bets_enabled:false,
    real_bets_enabled:false,
    paper_bets_auto_created:false,
    updated_frozen_ledgers:false,
    games_evaluated:shadow.games.length,games_emitted:games.length,
    skipped,games,
    caveat:"Observed team stats only: per-game goals proxy is not true source GF60; xGF/60 proxy differs from original xGF5, and missing HV/EDGE/injury/form/calibration are neutral. Not exact live Clairvoyance or calibrated probabilities.",
  };
}
function main(){
  const root=process.argv[2]||"docs",dest=process.argv[3]||
    path.join(root,"nhl-frontend-observed-latest.json");
  const load=name=>JSON.parse(fs.readFileSync(path.join(root,name),"utf8"));
  const result=generate({
    shadow:load("nhl-clairvoyance-shadow-latest.json"),
    mp:load("moneypuck-nhl-latest.json"),
    goalies:load("moneypuck-goalies-latest.json"),
    official:load("nhl-official-stats-latest.json"),
  });
  fs.writeFileSync(dest,JSON.stringify(result,null,2)+"\n","utf8");
  console.log("NHL frontend observed",result.games_emitted,"/",result.games_evaluated,
              "partial-input research predictions; no bets");
}
if(require.main===module)main();
module.exports={generate,validateSources,sanitizedTeams,goalieByTeam,seedRng,VERSION};
