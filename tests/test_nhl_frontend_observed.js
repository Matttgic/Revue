"use strict";
const assert=require("node:assert/strict");
const {test}=require("node:test");
const {generate}=require("../outils/suivi/nhl_frontend_observed.js");

const T=Date.parse("2026-10-10T12:00:00Z");
const past="2026-10-10T10:00:00Z";
const start="2026-10-10T19:00:00Z";
const season="2026-2027";
function fixture(){
  const stats=[
    {team:"BOS",xg_share:.53,xg_for_60:2.9,xg_against_60:2.5,games_played:5},
    {team:"NYR",xg_share:.46,xg_for_60:2.3,xg_against_60:2.7,games_played:5}
  ].map(x=>({...x,situation:"5on5",season}));
  const goalie=[
    {team:"BOS",name:"Officially observed MP A",gsax:3.3,save_pct:.92,games_played:4},
    {team:"NYR",name:"Officially observed MP B",gsax:-1.3,save_pct:.9,games_played:3}
  ].map(g=>({...g,season}));
  const teamOfficial=[
    {team_abbrev:"BOS",goals_for_per_game:3.4,goals_against_per_game:2.8,
      pp_pct:.215,pk_pct:.825,games_played:5},
    {team_abbrev:"NYR",goals_for_per_game:2.7,goals_against_per_game:3,
      pp_pct:.175,pk_pct:.765,games_played:5}
  ].map(x=>({...x,season:"20262027",game_type_id:2}));
  return {
    mp:{source:"MoneyPuck.com",generated_at_utc:past,is_live:false,
      current_season:season,status:{[season]:{status:"available",source_updated_utc:past}},
      seasons:{[season]:stats}},
    goalies:{source:"MoneyPuck.com",generated_at_utc:past,is_live:false,
      confirmed_starters:false,current_season:season,
      statuses:{[season]:{status:"available",source_updated_utc:past}},
      seasons:{[season]:goalie}},
    official:{source:"api.nhle.com/stats/rest/en",
      status:"verified_nhl_official_stats_snapshot",season:"20262027",
      generated_at_utc:past,game_type_id:2,
      reports:{team_summary:{status:"available"}},teams:teamOfficial},
    shadow:{status:"experimental_not_calibrated",season:"20262027",
      generated_at_utc:past,bookmaker_odds_available:false,confirmed_starters:false,
      point_in_time_audit:{status:"verified_temporal_bounds",as_of_utc:past},
      games:[{event_id:"2026020070",home:"BOS",away:"NYR",start_utc:start,
        xg_5v5_share_pct:{home:53,away:46},home_win:.53}]}
  };
}
const copy=x=>structuredClone(x);
test("observed snapshots produce reproducible 25k NHL MC/ensemble WITHOUT bookmaker or bet",()=>{
  const src=fixture(),initial=copy(src);
  const out=generate(src,T),again=generate(src,T);
  assert.deepEqual(out,again);
  assert.deepEqual(src,initial);
  assert.equal(out.games_emitted,1);
  const g=out.games[0];
  assert.equal(g.research.simulation_draws,25000);
  for(const k of ["ensemble_home","ensemble_raw_home","monte_carlo_home",
                  "probability_over_reference_line","p_home_puck_line_minus_1_5"]){
    assert.ok(g.research[k]>=0&&g.research[k]<=1,k);
  }
  assert.ok(g.research.monte_carlo_total_expected>0);
  assert.equal(out.real_bets_enabled,false);
  assert.equal(out.paper_bets_auto_created,false);
  assert.equal(out.updated_frozen_ledgers,false);
  assert.equal(out.exact_original_frontend_predictions_verified,false);
  assert.equal(out.odds_and_value_bets_enabled,false);
  assert.equal(g.starting_goalies_verified,false);
  assert.equal(g.injuries_verified,false);
  assert.equal(g.observed.home.goalie_is_confirmed_starter,false);
  assert.ok(out.missing_or_neutral_inputs.includes("verified player injuries"));
  assert.equal(g.research.total_over_reference_line,5.5);
});
test("market is never synthesized, team ratings do not claim exact parity",()=>{
  const g=generate(fixture(),T).games[0];
  assert.equal(g.research.market_blended,false);
  assert.equal(g.feature_status,"partial_neutral_inputs_not_original_frontend_parity");
  assert.equal(g.source_equivalent_predictions,false);
  assert.equal(g.observed.home.goal_rate_is_per_game_proxy_not_exact_source_gf60,true);
});
test("no forecasts after start nor under twenty minutes",()=>{
  const src=fixture();
  src.shadow.games[0].start_utc="2026-10-10T12:15:00Z";
  const out=generate(src,T);
  assert.equal(out.games_emitted,0);
  assert.equal(out.skipped.not_upcoming,1);
});
test("not reusing data observed after cutoff, even for future fixtures",()=>{
  const src=fixture();
  src.official.generated_at_utc="2026-10-10T18:45:00Z";
  assert.throws(()=>generate(src,T),/stale or future/);
  // Source timestamp is valid now, kickoff is within 20 minutes of observation.
  src.official.generated_at_utc="2026-10-10T11:55:00Z";
  src.shadow.games[0].start_utc="2026-10-10T12:21:00Z";
  src.shadow.generated_at_utc="2026-10-10T12:05:00Z";
  src.shadow.point_in_time_audit.as_of_utc="2026-10-10T12:05:00Z";
  assert.throws(()=>generate(src,T),/Source stale or future|timestamps|clock|invalid/i);
});
test("fail on ambiguous MoneyPuck most-played goalie and never choose randomly",()=>{
  const src=fixture();
  src.goalies.seasons[season].push({
    ...src.goalies.seasons[season][0],name:"Goalie with equal starts",save_pct:.98
  });
  const out=generate(src,T);
  assert.equal(out.games_emitted,0);
  assert.equal(out.skipped.missing_observed_team_or_unique_goalie,1);
});
test("fail closed on snapshots with different observed 5v5 xG values",()=>{
  const src=fixture();
  src.mp.seasons[season][0].xg_share=.60;
  const out=generate(src,T);
  assert.equal(out.games_emitted,0);
  assert.equal(out.skipped.different_money_puck_snapshot,1);
});
test("stale, unknown teams and invalid seasons cannot produce output",()=>{
  const src=fixture();
  src.official.generated_at_utc="2026-10-06T08:00:00Z";
  assert.throws(()=>generate(src,T),/stale or future/);
  const wrong=fixture();
  wrong.shadow.season="20252026";
  assert.throws(()=>generate(wrong,T),/seasons do not match/);
  const missing=fixture();
  missing.shadow.games[0].away="INVALID";
  const out=generate(missing,T);
  assert.equal(out.games_emitted,0);
  assert.equal(out.skipped.missing_observed_team_or_unique_goalie,1);
});
test("duplicates and source mismatches are fatal",()=>{
  const src=fixture();
  src.shadow.games.push({...src.shadow.games[0]});
  assert.throws(()=>generate(src,T),/duplicated NHL fixture/);
  const bad=fixture();
  bad.mp.source="not observed";
  assert.throws(()=>generate(bad,T),/Source identity mismatch/);
  const fake=fixture();
  fake.shadow.point_in_time_audit.status="unverified";
  assert.throws(()=>generate(fake,T),/protection invalid/);
});
test("no synthetic confirmed starters or fabricated injuries",()=>{
  const src=fixture();
  src.goalies.confirmed_starters=true;
  assert.throws(()=>generate(src,T),/protection invalid/);
});
