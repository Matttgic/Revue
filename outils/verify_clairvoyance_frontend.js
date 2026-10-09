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
const {verifyNHL} = require("./verify_clairvoyance_nhl.js");
const {verifySoccerXG} = require("./verify_clairvoyance_soccer_xg.js");

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
                 frontend_nba_mc: 0, frontend_nba_ensemble: 0,
                 frontend_nfl_mc: 0, frontend_nfl_ensemble: 0,
                 frontend_nhl_mc: 0, frontend_nhl_ensemble: 0,
                 frontend_soccer_xg: 0 };
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
  const fullNFL={
    standings:{
      KC:{wins:10,losses:5,ties:0,differential:80},
      SF:{wins:7,losses:8,ties:0,differential:-21}
    },
    stats:{
      KC:{
        offense:{netPassingYardsPerGame:253,rushingYardsPerGame:124,totalPointsPerGame:27.5},
        defenseAllowed:{yardsPerGame:334,totalTakeaways:19,totalPointsPerGame:20.6}
      },
      SF:{
        offense:{netPassingYardsPerGame:227,rushingYardsPerGame:139,totalPointsPerGame:24.2},
        defenseAllowed:{yardsPerGame:352,totalTakeaways:15,totalPointsPerGame:25.8}
      }
    }
  };
  const injured={
    KC:{pts:2.5,players:[{name:"Starting QB",pos:"QB",status:"Out",pts:2.5}],any:true},
    SF:{pts:.4,players:[{name:"RB1",pos:"RB",status:"Questionable",pts:.4}],any:true}
  };
  const wxCache={ "G9":{wind:23,precip:45,snow:0,temp:30},
                  "G10":{wind:5,precip:0,snow:.5,temp:20} };
  const nflMCCases=[
    {label:"missing NFL source",data:null,game:{id:"G1"},n:130},
    {label:"no points history no spread",data:{standings:{},stats:{}},game:{id:"G1"},n:130},
    {label:"fallback to market spread",data:{standings:{},stats:{}},game:{id:"G1",spread:-6.5},n:270},
    {label:"full regular season",data:fullNFL,game:{id:"G1"},n:340,ou:45.5},
    {label:"neutral ground",data:fullNFL,game:{id:"G2",neutralSite:true},n:300,ou:43.5},
    {label:"missing team passing stats",data:{standings:fullNFL.standings,stats:{}},game:{id:"G3"},n:340},
    {label:"injury both teams",data:fullNFL,game:{id:"G4",spread:-3},n:350,injuries:injured},
    {label:"unverified weather custom wind",data:fullNFL,game:{id:"G9"},n:300,weather:wxCache},
    {label:"hard snow and frozen ground",data:fullNFL,game:{id:"G10"},n:350,weather:wxCache},
    {label:"all default 15000 iterations",data:fullNFL,game:{id:"G12"},n:15000,ou:44.5},
  ];
  function simulateNFL(c,mode,i){
    const seed=5541+i*997;
    const r1=seeded(seed),r2=seeded(seed);
    const math=Object.create(Math);math.random=r1;
    const dummy=(team)=>c.injuries?.[team]||{pts:0,players:[],any:false};
    const env={
      _NFL_DATA:c.data, Math:math, _NFL_LG_TOTAL:44,
      _NFL_SIGMA_MARGIN:13.5,_NFL_SIGMA_TOTAL:10.0,
      NFL_INJ_TOTAL_SHARE:.5,
      _CFB_WX_CACHE:c.weather||{},
      window:{NFL_HFA_PTS:1.8,NFL_ENS:c.weights||{mc:.75,bay:.25}},
      _nflInjAdj:dummy,
    };
    if(c.calibrator)env.sportCalibrate=c.calibrator;
    const functions=["_nflHFA","_boxMullerZ","_forceHalfLine",
                     "cfbWeatherImpact","nflMC"];
    if(mode==="ensemble")functions.push("_nflBayes","nflEns");
    const context=vmFn(source,functions,env);
    // Explicitly pin the external injury dependency after loading the source
    // function; CI validates the same injected input on both implementations.
    context._nflInjAdj=dummy;
    const game=c.game||null;
    if(c.injuries){
      assert.equal(context._nflInjAdj("KC",game).pts,c.injuries.KC.pts,
                   "Reference VM missing injected injury input");
    }
    if(mode==="mc"){
      compare(c.label,"frontend_nfl_mc",
        context.nflMC("KC","SF",c.n,c.ou,game),
        own.nflMonteCarlo("KC","SF",c.n,c.ou,game,{
          data:c.data,weather:c.weather||{},random:r2,injury:dummy
        }));
    }else{
      compare(c.label,"frontend_nfl_ensemble",
        context.nflEns("KC","SF",c.ou,game),
        own.nflEnsemble("KC","SF",c.ou,game,{
          data:c.data,weather:c.weather||{},random:r2,injury:dummy,
          weights:c.weights||{mc:.75,bay:.25},calibrator:c.calibrator
        }));
    }
  }
  nflMCCases.forEach((c,i)=>simulateNFL(c,"mc",i));
  const ensembleCases=[
    {label:"NFL ensemble missing source",data:null,game:{id:"G1"}},
    {label:"NFL ensemble full season",data:fullNFL,game:{id:"G1"},ou:46.5},
    {label:"NFL ensemble injury override",data:fullNFL,game:{id:"G4"},injuries:injured,ou:43.5},
    {label:"NFL ensemble rainy neutral game",data:fullNFL,game:{id:"G9",neutralSite:true},
     weather:wxCache,ou:40.5,weights:{mc:.82,bay:.18},
     calibrator:(p)=>Math.max(.07,Math.min(.93,p*.96+.022))},
    {label:"NFL ensemble market fallback",data:{standings:{},stats:{}},
     game:{id:"G13",spread:-5.5},ou:42.5,weights:{mc:.6,bay:.4}},
  ];
  ensembleCases.forEach((c,i)=>simulateNFL(c,"ensemble",50+i));
  const nbaEnsCases=[
    {label:"missing all roster and ratings",game:{hL:-120,aL:110}},
    {label:"two live NBA teams",live:standard,game:{ou:225.5}},
    {label:"two live NBA teams market heavy home",live:standard,
     game:{ou:232.5,hL:-480,aL:390},elo:{BKN:1650,NY:1420}},
    {label:"two live NBA teams market away favorite",live:standard,
     game:{overUnder:227.5,hL:240,aL:-285},elo:{BKN:1380,NY:1720}},
    {label:"NBA only home bookmaker line",live:standard,
     game:{hL:210,ou:210.5}},
    {label:"NBA market odds absent",live:standard,game:{}},
    {label:"NBA live overrides prior ratings",live:standard,
     ratings:{BKN:{prior:{ortg:92,drtg:119,pace:84},priorWinPct:.40,current:{w:2,l:5}},
              NY:{prior:{ortg:114,drtg:100,pace:110},priorWinPct:.60,current:{w:6,l:1}}},
     game:{hL:-145,aL:124,ou:219.5}},
    {label:"NBA both team prior",live:{},
     ratings:{BKN:{prior:{ortg:118,drtg:109,pace:99},priorWinPct:.63,current:{w:0,l:0}},
              NY:{prior:{ortg:114,drtg:116,pace:96},priorWinPct:.42,current:{w:1,l:2}}},
     game:{hL:-109,aL:-103}},
    {label:"NBA team injury penalties",live:standard,
     game:{hL:-115,aL:105,ou:225.5},
     injuries:{BKN:{penalty:.085,players:["starter out"]},NY:{penalty:.015,players:["small issue"]}}},
    {label:"NBA calibration, adaptive weights",live:standard,
     game:{hL:165,aL:-185,ou:241.5},weights:{mc:.59,bay:.17,elo:.24},
     calibrator:p=>p*.93+.034},
    {label:"NBA prior standings ledger",live:standard,
     standings:{BKN:{w:"3",l:"9"},NY:{w:"11",l:"3"}},
     ledger:[{sport:"NBA",outcome:"win",hA:"BKN",awA:"NY",hScore:119,aScore:114}],
     game:{hL:-110,aL:100}},
  ];
  for(const [i,c] of nbaEnsCases.entries()){
    const seed=456123+i*2227;
    const r1=seeded(seed),r2=seeded(seed);
    const math=Object.create(Math);math.random=r1;
    const adv=c.live||{},ratings=c.ratings||{},bbref=c.bbref||{},
          teams=c.teams||{},stand=c.standings||{},ledger=c.ledger||[],
          elo=c.elo||{},weights=c.weights||{mc:.50,bay:.20,elo:.30},
          injuries=c.injuries||{},cal=c.calibrator||((p)=>p);
    const env={
      NBA_BBREF:bbref,NBA_TEAMS:teams,NBA_ELO:elo,NBA_ENS:weights,
      NBA_MKT_CAP:.065,Math:math,
      window:{__CV_DATA:{nba:{teamAdv:adv,standings:stand,teamRatings:{teams:ratings}}}},
      getP:()=>ledger,_normSport:p=>p.sport,
      sportCalibrate:cal,
      computeInjuryImpact:(team)=>injuries[team]||{penalty:0}
    };
    const ctx=vmFn(source,["ml2d","nbaMC","nbaGetBayes","nbaEloWP","nbaEns"],env);
    compare(c.label,"frontend_nba_ensemble",
      ctx.nbaEns("BKN","NY",c.game),
      own.nbaEnsemble("BKN","NY",c.game,{
        teamAdv:adv,priorRatings:ratings,staticBBref:bbref,teams,
        standings:stand,ledger,elo,weights,injuries,calibrator:cal,random:r2
      }));
  }
  verifyNHL(source,compare);
  verifySoccerXG(source,compare);
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
