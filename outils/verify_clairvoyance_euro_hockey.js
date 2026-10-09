"use strict";
/**
 * Strict side-by-side parity of four European-hockey rate functions.
 * Reads original functions ONLY from disposable reference checkout at test time.
 * Never republishes or bundles third-party code.
 */
const assert=require("node:assert/strict");
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey.js");

const TARGETS=[
  ["_liigaBlendedRates","frontend_liiga_rates","liigaRates"],
  ["_nlaBlendedRates","frontend_nla_rates","nlaRates"],
  ["_extraligaBlendedRates","frontend_extraliga_rates","extraligaRates"],
  ["_shlBlendedRates","frontend_shl_rates","shlRates"],
];

function original(source,name) {
  const escaped=name.replace(/[.*+?^$\u007b\u007d()|[\]\\]/g,"\\$&");
  const match=new RegExp("^function\\s+"+escaped+"\\s*\\(","m").exec(source);
  if(!match)throw Error("Reference function is absent: "+name);
  const end=source.indexOf("\n}",match.index);
  if(end<0)throw Error("Unterminated reference function: "+name);
  const body=source.slice(match.index,end+2);
  if(body.length<250||body.length>5000)throw Error("Unexpected original size: "+name);
  return body;
}

function cases(){
  return [
    ["no object",null],
    ["empty object",{}],
    ["zero games", {gp:0,gf:0,ga:0}],
    ["zero games with previous season",{gp:0,gf:0,ga:0,prevSeason:{gp:60,gf:185,ga:150,gm:5.35}}],
    ["1 played",{gp:1,gf:4,ga:1,gm:5.1,prevSeason:{gp:60,gf:182,ga:160,gm:5.65}}],
    ["5 played",{gp:5,gf:21,ga:15,gm:7.0,prevSeason:{gp:55,gf:155,ga:151,gm:5.1}}],
    ["10 played",{gp:10,gf:29,ga:22,gm:5.8,prevSeason:{gp:55,gf:200,ga:181,gm:6.2}}],
    ["19 played",{gp:19,gf:56,ga:61,gm:6.24,prevSeason:{gp:52,gf:160,ga:124,gm:6.9}}],
    ["20 played",{gp:20,gf:55,ga:65,gm:5.65,prevSeason:{gp:52,gf:160,ga:124,gm:6.9}}],
    ["30 played",{gp:30,gf:80,ga:100,gm:6.1,prevSeason:{gp:52,gf:160,ga:124,gm:6.9}}],
    ["gm only new",{gp:4,gf:7,ga:12,gm:4.7,prevSeason:{gp:50,gf:148,ga:170}}],
    ["gm only old",{gp:4,gf:7,ga:12,prevSeason:{gp:50,gf:148,ga:170,gm:6.3}}],
    ["gm neither",{gp:4,gf:7,ga:12,prevSeason:{gp:50,gf:148,ga:170}}],
    ["previous stats gp zero",{gp:5,gf:13,ga:17,prevSeason:{gp:0,gf:0,ga:0,gm:5.4}}],
    ["no previous season",{gp:7,gf:20,ga:23,gm:5.9}],
    ["no current season but prior",{prevSeason:{gp:54,gf:177,ga:166,gm:6.1}}],
    ["zero scoring 20 matches",{gp:20,gf:0,ga:0,gm:0,prevSeason:{gp:50,gf:150,ga:180,gm:6.2}}],
    ["gm zero",{gp:3,gf:6,ga:12,gm:0,prevSeason:{gp:50,gf:138,ga:157,gm:6.1}}],
    ["missing prior gm and cur gm",{gp:20,gf:42,ga:46,prevSeason:{gp:50,gf:157,ga:170}}],
    ["half season",{gp:2.5,gf:8.1,ga:9.3,gm:5.4,prevSeason:{gp:50,gf:168,ga:172,gm:5.9}}],
  ];
}

function verifyEuroHockey(source,compare){
  let localCount=0;
  for(const [originalName,moduleKey,replicaName] of TARGETS){
    const sandbox=vm.createContext({});
    vm.runInContext(original(source,originalName),sandbox,{timeout:1200});
    assert.equal(typeof sandbox[originalName],"function");
    assert.equal(typeof own[replicaName],"function");
    for(const [label,team] of cases()){
      const expected=sandbox[originalName](team);
      const actual=own[replicaName](team);
      compare(originalName+" / "+label,moduleKey,expected,actual);
      localCount++;
    }
  }
  return localCount;
}
module.exports={verifyEuroHockey,TARGETS};
