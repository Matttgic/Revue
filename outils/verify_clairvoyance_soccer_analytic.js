"use strict";
/** Exact tests against original _poissonOverProb/_socSpreadProb family. */
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_soccer_analytic.js");
const names=["_poissonOverProb","_socPoissonPmf","_socMarginDist","_socSpreadProb"];
function extracted(src,name){
  const match=new RegExp("^function\\s+"+name+"\\s*\\(","m").exec(src);
  if(!match)throw Error("Missing original analytical function "+name);
  const end=src.indexOf("\n}",match.index);
  if(end<0)throw Error("Unclosed function "+name);
  return src.slice(match.index,end+2);
}
function verifySoccerAnalytics(source,compare){
  const ctx=vm.createContext({});
  for(const name of names){
    vm.runInContext(extracted(source,name),ctx,{timeout:300});
  }
  const rates=[0,.15,.5,.9,1.3,1.85,2.4,3.8,6.2];
  const lines=[.5,1.5,2.5,3,3.5,4.5,6.5];
  const probs=[[.4,.4],[.9,1.4],[1.2,1.5],[1.7,.7],[2.4,1.8],[3.9,2.6]];
  for(const lam of rates){
    for(const k of [0,1,2,3,5,8,12,15]){
      compare("Poisson pmf "+lam+"/"+k,"frontend_soccer_poisson_pmf",
        ctx._socPoissonPmf(lam,k),own.poissonMass(lam,k));
    }
    for(const line of lines){
      compare("Poisson over "+lam+"/"+line,"frontend_soccer_poisson_over",
        ctx._poissonOverProb(lam,line),own.poissonOver(lam,line));
    }
  }
  for(const [home,away] of probs){
    compare("Poisson margin "+home+"/"+away,"frontend_soccer_margin_dist",
      ctx._socMarginDist(home,away),own.marginDistribution(home,away));
    for(const line of [-2.5,-1.5,-.5,.5,1.5,2.5]){
      compare("Poisson home spread "+home+"/"+away+"/"+line,
        "frontend_soccer_spread_prob",
        ctx._socSpreadProb(home,away,line),
        own.asianHomeCover(home,away,line));
    }
  }
  return 9*8+9*7+6+6*6;
}
module.exports={verifySoccerAnalytics};
