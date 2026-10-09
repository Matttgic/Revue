"use strict";
/** Direct source-vs-reconstructed four Euro hockey log5/MC market ensembles. */
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_ensemble.js");
const {sourceFunction,fixtureCases}=
  require("./verify_clairvoyance_euro_hockey_matches.js");
const dependencies=[
  "_hkRecentRates","_hkFormFactorRaw","_hkFormFactor","_hkBigMarginRate",
  "_socPoissonPmf","_socMarginDist","_socSpreadProb",
  "_forceHalfLine","_hkMarginCal"
];
const specs=[
  ["liiga","_LIIGA_DATA","_liigaBlendedRates","liigaMC","liigaEns","frontend_liiga_ensemble","liigaEnsemble"],
  ["nla","_NLA_DATA","_nlaBlendedRates","nlaMC","nlaEns","frontend_nla_ensemble","swissEnsemble"],
  ["extraliga","_EXTRALIGA_DATA","_extraligaBlendedRates","extraligaMC","extraligaEns","frontend_extraliga_ensemble","czechEnsemble"],
  ["shl","_SHL_DATA","_shlBlendedRates","shlMC","shlEns","frontend_shl_ensemble","shlEnsemble"]
];
const identity=p=>p;
function mkt(kind,p,game,used,flag){
  if(!game||!game[flag])return null;
  const impact=kind==="ML"?.08:kind==="PL"?.04:.045;
  const prob=Math.min(.95,Math.max(.05,p*(1-impact)+.5*impact));
  return {p:prob,model:p,market:.5,alpha:impact,kind};
}
const moneyline=(p,g,n)=>mkt("ML",p,g,n,"ml");
const spread=(p,g,home,n)=>mkt("PL",p,g,n,"pl");
const totals=(p,g,line,n)=>mkt("OU",p,g,n,"ou");
function calibrated(p,league){return Math.min(.95,Math.max(.05,p*.98+.013));}
function adjusted(p,market,league){return p*.96+.018;}

function verifyEuroHockeyEnsembles(source,compare){
  const scenarios=fixtureCases().map(x=>({...x}));
  scenarios.push(
    {label:"all three market blends",data:fixtureCases()[3].data,market:{ml:true,pl:true,ou:true}},
    {label:"moneyline only",data:fixtureCases()[3].data,market:{ml:true}},
    {label:"spread only",data:fixtureCases()[3].data,market:{pl:true}},
    {label:"total only",data:fixtureCases()[3].data,market:{ou:true}},
    {label:"stronger MC weight",data:fixtureCases()[4].data,weights:{mc:.9,bay:.08,elo:.02},market:{ml:true,ou:true}},
    {label:"stronger Bayes weight",data:fixtureCases()[5].data,weights:{mc:.3,bay:.45,elo:.25},market:{ml:true,pl:true}},
    {label:"zero total Bayesian share",data:fixtureCases()[3].data,weights:{mc:1,bay:0,elo:0}},
    {label:"spread calibration",data:fixtureCases()[3].data,adjust:true,market:{pl:true}},
    {label:"sport probability calibration",data:fixtureCases()[3].data,cal:true},
    {label:"negative market favorite",data:fixtureCases()[3].data,market:{ml:true},weights:{mc:.1,bay:.9,elo:0}}
  );
  let count=0;
  for(const [league,globalData,rateFn,mcFn,ensFn,label,replica] of specs){
    for(const c of scenarios){
      const calibrator=c.cal?calibrated:identity;
      const spreadAdjust=c.adjust?adjusted:undefined;
      const context={
        HOCKEY_PL_MARGIN_LOGIT_SHIFT:.18,
        HOCKEY_ENS:{[league]:c.weights||{mc:.7,bay:.2,elo:.1}},
        sportCalibrate:calibrator,
        _hkBlendML:moneyline,
        _hkBlendPL:spread,
        _hkBlendOU:totals,
        window:{_calAdjProbByType:spreadAdjust}
      };
      context[globalData]=c.data;
      const vmState=vm.createContext(context);
      for(const fn of [rateFn,...dependencies,mcFn,ensFn])
        vm.runInContext(sourceFunction(source,fn),vmState,{timeout:1200});
      const reference=vmState[ensFn]("HOME","AWAY",c.ou,c.market);
      const candidate=own[replica]("HOME","AWAY",c.ou,c.market,{
        data:c.data,weights:c.weights,calibrate:calibrator,
        moneylineBlend:moneyline,spreadBlend:spread,totalBlend:totals,
        adjustByMarketType:spreadAdjust
      });
      compare(ensFn+" / "+c.label,label,reference,candidate);
      count++;
    }
  }
  return count;
}
module.exports={verifyEuroHockeyEnsembles};
