"use strict";
/** Compare six independently implemented hockey helpers against the original JS. */
const vm=require("node:vm");
const {sourceFunction,fixtureCases}=
  require("./verify_clairvoyance_euro_hockey_matches.js");
const goals=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_games.js");
const team=require("../modeles/reproduction/frontend_clairvoyance_euro_hockey_ensemble.js");
const originals=[
  "_hkRecentRates","_hkFormFactorRaw","_hkFormFactor",
  "_hkBigMarginRate","_forceHalfLine","_hkMarginCal"
];
function verifyHockeyHelpers(source,compare) {
  const sandbox=vm.createContext({HOCKEY_PL_MARGIN_LOGIT_SHIFT:.18});
  for(const fn of originals)vm.runInContext(sourceFunction(source,fn),sandbox,{timeout:1200});
  let checks=0;
  function verify(id,description,reference,candidate){
    compare(description,id,reference,candidate);checks++;
  }
  const games=fixtureCases().filter(x=>x.data?.games?.length);
  for(const [index,c] of games.entries()){
    const list=c.data.games||[];
    for(const id of ["HOME","AWAY"]){
      for(const last of [undefined,0,2,3,5,8]){
        verify("frontend_hockey_recent_rates","recent "+index+"/"+id+"/"+last,
          sandbox._hkRecentRates(id,list,last),goals.recentRates(id,list,last));
      }
      const baseline=goals.euroHockeyGame?{
        gf:2.6+(index%3),ga:3.2+(index%2)
      }:{gf:2.8,ga:2.8};
      verify("frontend_hockey_form_delta","last5 delta "+index+"/"+id,
        sandbox._hkFormFactorRaw(id,list,baseline),
        goals.recentFormDelta(id,list,baseline));
      verify("frontend_hockey_form_factor","last5 multiplier "+index+"/"+id,
        sandbox._hkFormFactor(id,list,baseline),
        goals.lastFiveForm(id,list,baseline));
      verify("frontend_hockey_big_margins","big scores "+index+"/"+id,
        sandbox._hkBigMarginRate(id,list),team.majorMargin(id,list));
    }
  }
  for(const value of [0,1,1.2,1.3,1.45,1.5,2,2.2,2.8,3,3.6,4.9,5,
                      5.01,5.24,5.49,5.5,6.5,7.5,12,200,"3.6"]){
    verify("frontend_hockey_total_halfline","halfline "+value,
      sandbox._forceHalfLine(value),goals.marketHalfGoalLine(value));
  }
  for(const value of [0,.001,.01,.05,.1,.2,.3,.4,.5,.6,.75,.85,.9,.99,.999,1]){
    verify("frontend_hockey_margin_cal","margin "+value,
      sandbox._hkMarginCal(value),goals.clampMargin(value));
  }
  return checks;
}
module.exports={verifyHockeyHelpers};
