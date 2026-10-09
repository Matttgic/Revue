"use strict";
/** Compare original Clairvoyance no-vig/logit market blend on the same data. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const own=require("../modeles/reproduction/frontend_clairvoyance_hockey_market.js");

function verifyHockeyMarket(source,compare) {
  const context=vm.createContext({
    HOCKEY_MKT_BLEND_ALPHA:{ML:.75,OU:.65,PL:.70},
    HOCKEY_MKT_BLEND_ALPHA_EARLY:.95,
    HOCKEY_MKT_BLEND_FULL_GP:10,
    _HK_MKT_OVERROUND_MIN:1,
    _HK_MKT_OVERROUND_MAX:1.2,
    _HK_MKT_PMIN:.05,
    _HK_MKT_PMAX:.95
  });
  // One-line source helper cannot use the multiline extractor.
  const line=source.split("\n").find(s=>s.startsWith("function _hkValidDec("));
  if(!line||line.length>350)throw Error("Original valid decimal helper absent");
  vm.runInContext(line,context,{timeout:400});
  for(const fn of ["_hkMktNoVig","_hkBlendAlpha","_hkBlendCore"])
    vm.runInContext(sourceFunction(source,fn),context,{timeout:800});
  let count=0;
  const test=(label,kind,orig,repro)=>{
    compare(label,kind,orig,repro);count++;
  };
  for(const v of [undefined,null,0,1,1.0001,1.01,1.1,1.5,1.8,2,
                  2.1,3.5,12,80,199.99,200,200.01,500,-150,"2.1",NaN,Infinity]){
    for(const b of [1.01,1.5,1.91,2.1,3.5]){
      test("two-sided margin "+v+"/"+b,"frontend_hockey_novig",
        context._hkMktNoVig(v,b),own.noVigTwoWay(v,b));
    }
  }
  for(const market of ["ML","OU","PL","UNKNOWN"]){
    for(const n of [undefined,null,-2,0,1,3,5,10,15,50,"4",NaN,Infinity]){
      test("blend alpha "+market+"/"+n,"frontend_hockey_alpha",
           context._hkBlendAlpha(market,n),own.alphaForMarket(market,n));
      for(const prob of [.01,.05,.15,.25,.4,.5,.61,.75,.85,.95,.99]){
        const price=.36+.4*prob;
        test("logit blend "+market+"/"+n+"/"+prob,"frontend_hockey_blend_core",
             context._hkBlendCore(prob,price,market,n),
             own.calibratedBlend(prob,price,market,n));
      }
    }
  }
  return count;
}
module.exports={verifyHockeyMarket};
