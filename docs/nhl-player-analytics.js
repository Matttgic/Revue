/* Independent research calculations. No empirical frequency is used as model probability. */
(function(root){
 'use strict';
 const finite=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
 function sample(games,metric,{venue='',opponent='',season=''}={}){
  const seen=new Set();
  return (Array.isArray(games)?games:[]).filter(g=>g&&g.event_id&&Number.isFinite(Date.parse(g.date)))
   .sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)||String(a.event_id).localeCompare(String(b.event_id)))
   .filter(g=>{if(seen.has(g.event_id))return false;seen.add(g.event_id);return true;})
   .filter(g=>(!season||String(g.season)===season)&&(!venue||g.home===(venue==='home'))&&(!opponent||g.opponent===opponent));
 }
 function hitRate(games,metric,line,window){
  if(!finite(line)||!Number.isInteger(window)||window<1)return {n:0,hits:0,rate:null,missing:0};
  // Latest N appearances after context filtering; missing stats do not backfill older games.
  const selected=games.slice(0,window),known=selected.filter(g=>finite(g[metric]));
  const hits=known.filter(g=>g[metric]>line).length;
  return {n:known.length,hits,rate:known.length?hits/known.length:null,missing:selected.length-known.length};
 }
 function poisson(rate,line){
  if(!finite(rate)||!finite(line)||line%1!==.5)return null;
  let term=Math.exp(-rate),cdf=term;
  for(let i=1;i<=Math.floor(line);i++){term*=rate/i;cdf+=term;}
  return Math.max(0,Math.min(1,1-cdf));
 }
 const api={sample,hitRate,poisson,finite};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else root.NHLAnalytics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
