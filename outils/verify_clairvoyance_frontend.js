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
                 frontend_soccer_market_blend: 0 };
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
