/* Independent research calculations. No empirical frequency is used as model probability. */
(function(root){
 'use strict';
 const finite=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
 function sample(games,metric,{venue='',opponent='',season=''}={}){
  const seen=new Set();
  return (Array.isArray(games)?games:[]).filter(g=>g&&g.event_id&&Number.isFinite(Date.parse(g.date)))
   .sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)||String(a.event_id).localeCompare(String(b.event_id)))
   .filter(g=>{const id=String(g.event_id);if(seen.has(id))return false;seen.add(id);return true;})
   .filter(g=>(!season||String(g.season)===season)&&(!venue||g.home===(venue==='home'))&&(!opponent||g.opponent===opponent));
 }
 function hitRate(games,metric,line,window){
  if(!finite(line)||!Number.isInteger(window)||window<1)return {n:0,hits:0,rate:null,missing:0};
  // Latest N appearances after context filtering; missing stats do not backfill older games.
  const selected=games.slice(0,window),known=selected.filter(g=>finite(g[metric]));
  const hits=known.filter(g=>g[metric]>line).length;
  return {n:known.length,hits,rate:known.length?hits/known.length:null,missing:selected.length-known.length};
 }
 function reliability(games,metric,entry,currentSeason,now=Date.now()){
  const selected=games.slice(0,20),n=selected.filter(g=>finite(g[metric])).length;
  const seasons=[...new Set(selected.map(g=>String(g.season)))];
  const stamps=entry?.season_collected_at||{};
  let fresh=seasons.length>0,unknown=false,oldestHours=0;
  for(const season of seasons){
   const fallback=entry?.status==='ok'?entry.attempted_at:null;
   const time=Date.parse(stamps[season]||fallback),age=(now-time)/3600000;
   if(!Number.isFinite(age)||age<0){unknown=true;fresh=false;continue;}
   oldestHours=Math.max(oldestHours,age);
   if(age>(season===String(currentSeason)?6:30*24))fresh=false;
  }
  const sourceIssue=(entry?.diagnostics||[]).some(d=>seasons.includes(String(d.season))&&d.status!=='ok');
  const label=!selected.length?'Données indisponibles':unknown?'Fraîcheur inconnue':!fresh?'À actualiser':n<20?'Échantillon incomplet':sourceIssue?'Collecte partielle':'Données bien couvertes';
  return {n,target:20,incomplete:n<20,fresh,unknown,sourceIssue,oldestHours,label};
 }
 const normalizeName=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 function searchPlayers(players,query){const key=normalizeName(query).trim();return players.filter(p=>normalizeName(p.name).includes(key));}
 function poisson(rate,line){
  if(!finite(rate)||!finite(line)||line%1!==.5)return null;
  let term=Math.exp(-rate),cdf=term;
  for(let i=1;i<=Math.floor(line);i++){term*=rate/i;cdf+=term;}
  return Math.max(0,Math.min(1,1-cdf));
 }
 const api={sample,hitRate,poisson,finite,reliability,searchPlayers};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 else root.NHLAnalytics=api;
})(typeof globalThis!=='undefined'?globalThis:this);
