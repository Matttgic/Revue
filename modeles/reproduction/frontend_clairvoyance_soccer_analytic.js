"use strict";
/**
 * Independent arithmetic matching Clairvoyance's soccer goal models.
 * Specifically _poissonOverProb, _socPoissonPmf, _socMarginDist,
 * _socSpreadProb. This version keeps the original 15-goal cutoff for
 * the distribution, including its tiny truncated tail.
 */
function poissonOver(lambda,line){
  const limit=Math.floor(line);
  let cdf=0,prob=Math.exp(-lambda);
  for(let i=0;i<=limit;i++){
    if(i>0)prob*=lambda/i;
    cdf+=prob;
  }
  return Math.max(0,Math.min(1,1-cdf));
}
function poissonMass(lambda,k){
  let p=Math.exp(-lambda);
  for(let i=1;i<=k;i++)p*=lambda/i;
  return p;
}
function marginDistribution(homeXG,awayXG){
  const max=15,home=[],away=[];
  for(let k=0;k<=max;k++){
    home[k]=poissonMass(homeXG,k);
    away[k]=poissonMass(awayXG,k);
  }
  const distribution={};
  for(let h=0;h<=max;h++)for(let a=0;a<=max;a++){
    const margin=h-a;
    distribution[margin]=(distribution[margin]||0)+home[h]*away[a];
  }
  return distribution;
}
function asianHomeCover(homeXG,awayXG,homeLine){
  const margins=marginDistribution(homeXG,awayXG);
  let probability=0;
  Object.keys(margins).forEach(margin=>{
    if(parseFloat(margin)>-homeLine)probability+=margins[margin];
  });
  return Math.max(0,Math.min(1,probability));
}
module.exports={poissonOver,poissonMass,marginDistribution,asianHomeCover};
