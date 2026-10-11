"use strict";
/** Reproduction of the source non-moneyline confidence ceiling
 * (MARKET_P_CEILING / _mktCeiling / _capMktP in docs/app.html, added
 * upstream on 2026-10-10, commit fe5eba7a).
 *
 * The source clamps every stated SPREAD / O-U / PROP probability to
 * [1-c, c] after all of its other corrections. Moneyline is never clamped.
 * Upstream evidence for the rule: non-moneyline picks stated at .703 won
 * .622 (n=863); CFB O/U stated .786 won .576 (n=184).
 */
const CEILINGS=Object.freeze({
 default:Object.freeze({SPREAD:.68,OU:.68,PROP:.68}),
 byLeague:Object.freeze({
  CFB:Object.freeze({SPREAD:.62,OU:.62}),
  NFL:Object.freeze({SPREAD:.62,OU:.62,PROP:.62}),
 }),
});

function marketCeiling(league,marketType){
 const code=String(league||"").toUpperCase().replace(/^SOC_/,"");
 const kind=(marketType==="PL"||marketType==="RL")?"SPREAD":marketType;
 const own=CEILINGS.byLeague[code];
 if(own&&own[kind]!=null)return own[kind];
 const fallback=CEILINGS.default[kind];
 return fallback!=null?fallback:null;
}

function capMarketProbability(p,marketType,league){
 const ceiling=marketCeiling(league,marketType);
 if(ceiling==null||!(p>0&&p<1))return p;
 return Math.max(1-ceiling,Math.min(ceiling,p));
}

module.exports={CEILINGS,marketCeiling,capMarketProbability};
