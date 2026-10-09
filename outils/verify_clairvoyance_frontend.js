"use strict";
/**
 * Source-vs-replica function equality tests on a read-only checkout.
 * Only extracts THREE original functions and their TWO arithmetic helpers.
 * The original docs/app.html is never bundled or re-published.
 * Runs in an isolated Node vm with injected test data, not in a browser.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const own = require("../modeles/reproduction/frontend_clairvoyance.js");

function original(source, name) {
  const match = new RegExp("^function\\s+" + name + "\\s*\\(", "m").exec(source);
  if (!match) throw new Error("Original function not found: " + name);
  // All five audited source functions have a top-level closing brace at col 0.
  const end = source.indexOf("\n}", match.index);
  if (end < 0) throw new Error("Function ending not found: " + name);
  const def = source.slice(match.index, end + 2);
  if (def.length > 12000 || def.length < 35)
    throw new Error("Unexpected length for " + name + ": " + def.length);
  return def;
}

function vmFn(source, names, env) {
  const context = vm.createContext(env);
  for (const name of names) {
    vm.runInContext(original(source, name), context, { timeout: 1200 });
  }
  return context;
}

let checks = 0;
const counts = { frontend_nba_bayes: 0, frontend_nfl_bayes: 0,
                 frontend_soccer_market_blend: 0, frontend_soccer_mc: 0,
                 frontend_nba_mc: 0 };
function compare(label, name, target, actual) {
  const left = JSON.stringify(target), right = JSON.stringify(actual);
  assert.equal(right, left, "Parity difference on " + label + ": " + right + " vs " + left);
  checks++;
  counts[name]++;
}

function verify(source) {
  const standings = {
    empty: {},
    losing: { ATL: { w: "4", l: "10" } },
    winning: { ATL: { w: "50", l: "32" } },
  };
  const nbaCases = [
    { label: "unknown", abbr: "ATL", teams: {}, standing: {}, rating: {}, ledger: [] },
    { label: "standings loss", abbr: "ATL", teams: {}, standing: standings.losing, rating: {}, ledger: [] },
    { label: "standings wins", abbr: "ATL", teams: {}, standing: standings.winning, rating: {}, ledger: [] },
    { label: "original static team", abbr: "ATL", teams: { ATL: { pw: 24, pl: 10 } }, standing: {}, rating: {}, ledger: [] },
    { label: "prior 0.55 and 2-3 record", abbr: "ATL", teams: {}, standing: {}, rating: { ATL: { priorWinPct: .55, current: { w: 2, l: 3 } } }, ledger: [] },
    { label: "prior zero", abbr: "ATL", teams: {}, standing: {}, rating: { ATL: { priorWinPct: 0, current: { w: 0, l: 0 } } }, ledger: [] },
    { label: "prior one", abbr: "ATL", teams: {}, standing: {}, rating: { ATL: { priorWinPct: 1, current: { w: 5, l: 0 } } }, ledger: [] },
    { label: "teamRatings overrides old", abbr: "ATL", teams: { ATL: {pw: 82,pl: 0} }, standing: standings.losing,
      rating: { ATL: { priorWinPct: .4, current: { w: 1, l: 2 } } }, ledger: [] },
    { label: "ledger with verified finals", abbr: "ATL", teams: {}, standing: standings.losing, rating: {},
      ledger: [
        { sport: "NBA", outcome: "win", hA:"ATL", awA:"BOS",hScore:120,aScore:99 },
        { sport: "NBA", outcome: "loss", hA:"LAL", awA:"ATL",hScore:111,aScore:100 },
        { sport: "NBA", outcome: "pending", hA:"ATL", awA:"BOS",hScore:99,aScore:100 },
        { sport: "NBA", outcome: "win", hA:"ATL", awA:"BOS",hScore:null,aScore:null },
        { sport: "NHL", outcome: "win", hA:"ATL", awA:"BOS",hScore:5,aScore:2 },
      ] },
    { label: "prior skips archived ledger", abbr: "ATL", teams:{}, standing:{},
      rating:{ ATL: { priorWinPct: .35, current: { w: 1, l: 1 } } },
      ledger:[{sport:"NBA",outcome:"win",hA:"ATL",awA:"BOS",hScore:119,aScore:110}] },
  ];
  for (const x of nbaCases) {
    const env = {
      NBA_TEAMS: x.teams,
      window: { __CV_DATA: { nba: { standings: x.standing,
                  teamRatings: { teams: x.rating } } } },
      getP: () => x.ledger,
      _normSport: (p) => p.sport,
    };
    const reference = vmFn(source, ["nbaGetBayes"], env);
    compare(x.label, "frontend_nba_bayes",
      reference.nbaGetBayes(x.abbr),
      own.nbaGetBayes(x.abbr, { teams:x.teams,standings:x.standing,
                                ratings:x.rating,ledger:x.ledger }));
  }

  const nflCases = [
    {}, { NYJ: { wins: 0, losses: 0 } },
    { NYJ: { wins: "2", losses: "7" } },
    { NYJ: { wins: 15, losses: 1 } },
    { NYJ: { wins: 1.5, losses: 4.5 } },
    { NYJ: { wins: null, losses: undefined } },
    { NYJ: { wins: "not-a-number", losses: "-2" } },
  ];
  for (const [i, sample] of nflCases.entries()) {
    const ref = vmFn(source, ["_nflBayes"], { _NFL_DATA: { standings: sample } });
    compare("NFL "+i,"frontend_nfl_bayes",
      ref._nflBayes("NYJ"), own.nflBayes("NYJ", sample));
  }

  const soccerCases = [
    { label:"no market",p:[.44,.31,.25],lines:[null,-125,200],weights:{model:.8,market:.2} },
    { label:"invalid entry",p:[.44,.31,.25],lines:["no-price",230,-105],weights:{model:.8,market:.2} },
    { label:"even match",p:[.35,.31,.34],lines:[110,250,110],weights:{model:.7,market:.3} },
    { label:"favorite",p:[.77,.13,.10],lines:[-340,460,650],weights:{model:.75,market:.25} },
    { label:"away favorite",p:[.18,.21,.61],lines:[350,315,-210],weights:{model:.55,market:.45} },
    { label:"zero bookmaker odds",p:[.25,.35,.40],lines:[0,150,-120],weights:{model:.7,market:.3} },
    { label:"pure model",p:[.5,.25,.25],lines:[110,290,215],weights:{model:1,market:0} },
    { label:"pure market",p:[.1,.4,.5],lines:[110,290,215],weights:{model:0,market:1} },
    { label:"non normalized",p:[.9,.9,.9],lines:[150,255,-145],weights:{model:.67,market:.33} },
    { label:"calibrated",p:[.54,.2,.26],lines:[-210,390,450],weights:{model:.7,market:.3},
      cal:(p)=>p*.94+.013 },
    { label:"calibration no price",p:[.01,.99,.5],lines:[null,220,170],
      weights:{model:.7,market:.3},cal:(p)=>p*.94+.013 },
  ];
  for (const t of soccerCases) {
    const env = { window:{SOC_ENS:t.weights} };
    if (t.cal) env.sportCalibrate=t.cal;
    const ref = vmFn(source, ["ml2d","_socCal","_socMarketBlend"], env);
    compare(t.label,"frontend_soccer_market_blend",
      ref._socMarketBlend(...t.p,...t.lines),
      own.soccerMarketBlend(...t.p,...t.lines,t.weights,t.cal));
  }
  // Freeze the random stream in both functions. This verifies not merely
  // approximate Poisson probabilities but every simulated outcome, including
  // xG fallbacks, O/U thresholds, 1X2, expected scores and BTTS.
  function seeded(seed) {
    let state = seed | 0;
    return () => {
      state ^= state << 13;
      state ^= state >>> 17;
      state ^= state << 5;
      return (state >>> 0) / 4294967296;
    };
  }
  const mcCases = [
    [1.4,1.1,200,12345],
    [1.8,0.7,350,45678],
    [0.5,3.2,300,345678],
    [0,0,200,456789],
    [null,1.9,200,1337],
    [-1,2.1,200,77777],
    [NaN,NaN,200,1515],
    ["2.0","0.9",200,3001],
    [0.9,0.9,250,88888],
    [2.1,1.3,25000,44444],
  ];
  for (const [i,[hg,ag,n,seed]] of mcCases.entries()) {
    const randOriginal=seeded(seed);
    const randReplica=seeded(seed);
    const math=Object.create(Math);
    math.random=randOriginal;
    const ctx=vmFn(source,["_soccerMC"],{ Math:math, _SOC_MC_N:25000 });
    compare("soccer-mc "+i,"frontend_soccer_mc",
      ctx._soccerMC(hg,ag,n),
      own.soccerMonteCarlo(hg,ag,n,randReplica));
  }
  const standard = {
    BKN:{ortg:117.8,drtg:112.9,pace:99.7,ts_pct:.604},
    NY:{ortg:113.6,drtg:110.1,pace:96.2,ts_pct:.568},
  };
  const nbaMCCases=[
    {label:"truly missing both teams",live:{},ratings:{},bbref:{},teams:{},n:140,ou:220.5},
    {label:"real advanced two teams",live:standard,ratings:{},bbref:{},teams:{},n:350,ou:222.5},
    {label:"low totals and strong favorite",live:standard,ratings:{},bbref:{},teams:{},n:450,ou:200.5},
    {label:"high totals",live:standard,ratings:{},bbref:{},teams:{},n:330,ou:250.5},
    {label:"last-year teamRatings fallback",live:{},
     ratings:{BKN:{prior:{ortg:119,drtg:111,pace:99}},NY:{prior:{ortg:113,drtg:116,pace:97}}},
     bbref:{},teams:{},n:210,ou:222.5},
    {label:"partial teamRatings neutral other",live:{},
     ratings:{BKN:{prior:{ortg:119,drtg:111,pace:99}}},
     bbref:{},teams:{},n:320,ou:215.5},
    {label:"live outranks prior",live:standard,
     ratings:{BKN:{prior:{ortg:90,drtg:140,pace:80}}},
     bbref:{},teams:{},n:280,ou:235.5},
    {label:"original static teams",live:{},ratings:{},
     bbref:{BKN:{p100:{ortg:113,drtg:118,pace:97,ts_pct:.61}},
            NY:{p100:{ortg:119,drtg:109,pace:96,ts_pct:.59}}},
     teams:{BKN:{},NY:{}},n:260,ou:224.5},
    {label:"sample size >= 10 changes league rating",live:{
       ...standard,...Object.fromEntries(Array.from({length:10},(_,i)=>
         ["T"+i,{ortg:111+i*.8,drtg:109+i*.7,pace:94+i*.6,ts_pct:.56+i*.005}]))},
       ratings:{},bbref:{},teams:{},n:470,ou:219.5},
    {label:"all 25000 draws for genuine default",live:standard,
     ratings:{},bbref:{},teams:{},n:25000,ou:225.5},
  ];
  for (const [i,c] of nbaMCCases.entries()) {
    const seed=81727+i*997;
    const r1=seeded(seed),r2=seeded(seed);
    const math=Object.create(Math);math.random=r1;
    const env={
      NBA_BBREF:c.bbref,NBA_TEAMS:c.teams,Math:math,
      window:{__CV_DATA:{nba:{teamAdv:c.live,teamRatings:{teams:c.ratings}}}}
    };
    const ctx=vmFn(source,["nbaMC"],env);
    compare(c.label,"frontend_nba_mc",
      ctx.nbaMC("BKN","NY",c.n,c.ou),
      own.nbaMonteCarlo("BKN","NY",c.n,c.ou,{
        teamAdv:c.live,priorRatings:c.ratings,staticBBref:c.bbref,
        teams:c.teams,random:r2
      }));
  }
  return checks;
}

function main() {
  const dir = process.argv[2];
  const dest = process.argv[3] || "docs/parite-clairvoyance-frontend.json";
  if (!dir) throw new Error("Usage: node outils/verify_clairvoyance_frontend.js REF_PATH OUTPUT_PATH");
  const source = fs.readFileSync(path.join(dir, "docs/app.html"), "utf8");
  verify(source);
  const hash = execFileSync("git",["-C",dir,"rev-parse","HEAD"],{encoding:"utf8"}).trim();
  const report = {
    generated_at_utc:new Date().toISOString(),
    reference:"Purple-Wraith/clairvoyance-backend",
    reference_commit:hash,
    reference_file:"docs/app.html",
    implementation_file:"modeles/reproduction/frontend_clairvoyance.js",
    status:"frontend_function_output_parity_verified",
    exact_equality_tests_passed:checks,
    checked_examples:counts,
    verified_modules:Object.keys(counts).filter(k=>counts[k]>0),
    note:"Original functions extracted at CI runtime; original HTML/JS not redistributed. Synthetic input equality only. No live data parity or returns verified.",
  };
  fs.mkdirSync(path.dirname(dest),{recursive:true});
  fs.writeFileSync(dest,JSON.stringify(report,null,2)+"\n");
  process.stdout.write("FRONTEND SOURCE PARITY "+checks+" exact tests: "+
                       JSON.stringify(counts)+" @ "+hash+"\n");
}
if (require.main===module) main();
module.exports={original,verify};
