"use strict";
/**
 * Independently reconstructed Clairvoyance hockey market mathematics.
 * Constants copied as numeric mathematical parameters identified from
 * the source, not code or proprietary bookmaker prices.
 *
 * The live odds parser/settlement rules are NOT implied by this module.
 */
const LEVELS={ML:.75,OU:.65,PL:.70};
function validDecimal(odds){
  return typeof odds==="number" && Number.isFinite(odds) &&
         odds>1 && odds<=200;
}
function noVigTwoWay(a,b){
  if(!validDecimal(a)||!validDecimal(b))return null;
  const pa=1/a,pb=1/b,margin=pa+pb;
  if(!(margin>=1&&margin<=1.20))return null;
  const fair=pa/margin;
  return (fair>=.05&&fair<=.95)?fair:null;
}
function alphaForMarket(type,played){
  const alpha=LEVELS[type];
  if(alpha==null)return null;
  const weight=(played==null||!Number.isFinite(Number(played)))
    ?1:Math.max(0,Math.min(1,played/10));
  return alpha+(Math.max(alpha,.95)-alpha)*(1-weight);
}
function calibratedBlend(model,market,kind,played){
  try{
    if(!(model>0&&model<1)||!(market>0&&market<1))return null;
    const weight=alphaForMarket(kind,played);
    if(weight==null)return null;
    const bounded=Math.min(1-1e-4,Math.max(1e-4,model));
    const logit=(1-weight)*Math.log(bounded/(1-bounded)) +
      weight*Math.log(market/(1-market));
    const result=Math.min(.95,Math.max(.05,1/(1+Math.exp(-logit))));
    if(!Number.isFinite(result))return null;
    return {p:result,model,market,alpha:weight,kind};
  }catch(_){return null;}
}
module.exports={validDecimal,noVigTwoWay,alphaForMarket,calibratedBlend,LEVELS};
