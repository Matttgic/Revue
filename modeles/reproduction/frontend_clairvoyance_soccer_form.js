"use strict";
/**
 * Independently reconstructed Clairvoyance football form adjustment.
 * Original: docs/app.html functions _socFormFactorRaw and _socFormFactor.
 * Deliberately preserves source fallbacks, 3-match minimum, and +/-6% clamp.
 * No original code or sports data redistributed.
 */
function findTeam(name,available){
  if(!name||!available)return undefined;
  const lower=name.toLowerCase().trim();
  for(const candidate of available){
    const key=String(candidate||"").toLowerCase();
    if(key===lower || lower.includes(key) || key.includes(lower))
      return candidate;
  }
  return undefined;
}
function rawFormFactor(name,league,leagues){
  const teams=leagues?.[league]?.teams;
  if(!teams||!name)return null;
  const match=findTeam(name,Object.keys(teams));
  if(!match)return null;
  const row=teams[match];
  const recent=row.recentForm;
  if(!recent||recent.games<3)return null;
  const seasonRate=row.mp?((row.gf||0)-(row.ga||0))/row.mp:0;
  const recentRate=recent.gf-recent.ga;
  return recentRate-seasonRate;
}
function formFactor(name,league,leagues,domestic){
  let change;
  if(league==="cl"){
    const context=typeof domestic==="function"?domestic(name):domestic?.[name];
    const champions=rawFormFactor(name,"cl",leagues);
    const national=context?rawFormFactor(name,context.domKey,leagues):null;
    if(champions==null&&national==null)return 1;
    change=champions!=null&&national!=null
      ?champions*context.wCL+national*context.wDom
      :national!=null?national:champions;
  } else {
    change=rawFormFactor(name,league,leagues);
    if(change==null)return 1;
  }
  return 1+Math.max(-.06,Math.min(.06,change*.05));
}
module.exports={findTeam,rawFormFactor,formFactor};
