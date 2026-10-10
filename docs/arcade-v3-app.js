/* REVUE Arcade V3 public renderer: WHAT -> WHY -> PAPER RESULTS.
 * Only DOM text nodes; no real offers, invented probabilities, or bookmaker EV.
 */
"use strict";
(function(){
const $=id=>document.getElementById(id);
const h=(tag,cl,text)=>{const n=document.createElement(tag);if(cl)n.className=cl;if(text!==undefined)n.textContent=String(text);return n;};
const add=(parent,...elements)=>{for(const e of elements)parent.append(e);return parent;};
const put=(id,value)=>{const x=$(id);if(x)x.textContent=String(value);};
const pf=n=>typeof n==="number"&&Number.isFinite(n)?(100*n).toLocaleString("fr-FR",{maximumFractionDigits:1})+" %":"—";
const f=n=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("fr-FR",{maximumFractionDigits:2}):"—";
const date=iso=>iso?new Date(iso).toLocaleString("fr-FR",{timeZone:"Europe/Paris",day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"}):"date indisponible";
const dest=x=>"./match-dossier.html?league="+encodeURIComponent(x.league)+"&id="+encodeURIComponent(x.id);
let state=null;
let selected=null;
let activeSport="all";
let query="";
async function load(name){
 const r=await fetch("./"+name,{cache:"no-store"});
 if(!r.ok)throw Error(name+": "+r.status);
 return r.json();
}
function blank(where,title,subtitle){
 const root=$(where);if(!root)return;
 root.replaceChildren();
 const box=h("div","arc-v3-empty");add(box,h("strong","",title),h("p","",subtitle));
 root.append(box);
}
function renderWhy(e){
 const root=$("v3-explain");if(!root)return;
 root.replaceChildren();
 if(!e) {
  add(root,h("h3","","Pourquoi aucune sélection ?"),
    h("p","","Sans modèle calibré et cote française actuelle, aucune espérance de gain ne peut être validée. Les rencontres peuvent être étudiées sans être proposées comme paris."));
  return;
 }
 selected=e.key;
 add(root,h("div","arc-v3-overline",e.league+" · "+date(e.start)),
  h("h3","",e.away+" — "+e.home),
  h("div","arc-v3-not-playable","AUCUN PARI RECOMMANDÉ"));
 const explanation=h("ul","arc-v3-reasons");
 for(const why of e.why)explanation.append(h("li","",why));
 root.append(explanation);
 const title=h("h4","","Modèles disponibles");
 root.append(title);
 if(!e.models.length&&!e.hockey)root.append(h("p","","Aucune probabilité exploitable pour cette rencontre."));
 for(const m of e.models){
  const block=h("div","arc-v3-model");
  block.append(h("strong","",m.name+" · non calibré"));
  for(const [k,v] of Object.entries(m.probabilities)){
   const row=h("div","arc-v3-model-row");
   add(row,h("span","",k.replaceAll("_"," ")),h("strong","",pf(v)));
   block.append(row);
  }
  root.append(block);
 }
 if(e.hockey){
  const block=h("div","arc-v3-model");
  add(block,h("strong","","NHL Monte-Carlo / Ensemble · partiel, non calibré"),
   h("p","","Monte-Carlo domicile : "+pf(e.hockey.mc)+
     " · Ensemble domicile : "+pf(e.hockey.ensemble)),
   h("small","","25 000 simulations sous hypothèses incomplètes. Gardiens historiques "+
      (e.hockey.goalieHome||"non vérifié")+" / "+
      (e.hockey.goalieAway||"non vérifié")+
      ", titulaires non confirmés."));
  if(e.hockey.espnGoalieHome||e.hockey.espnGoalieAway){
    const describe=(x)=>x?x.name+" ("+(x.status==="confirmed"?"confirmé ESPN":"probable ESPN")+")":"non renseigné";
    block.append(h("p","","ESPN observé le "+date(e.hockey.espnObservedAt)+
      " : domicile "+describe(e.hockey.espnGoalieHome)+
      " · extérieur "+describe(e.hockey.espnGoalieAway)+
      ". Informations distinctes des probabilités ci-dessus."));
  }
  root.append(block);
 }
 if(e.recentObservedPriceExamples?.length){
  const observation=h("div","arc-v3-price");
  observation.append(h("strong","","Cotes PulseScore observées · pas de disponibilité en temps réel"));
  for(const q of e.recentObservedPriceExamples){
    const side=q.market==="h2h"?
      (q.side==="home"?"Domicile":q.side==="away"?"Extérieur":"Nul"):
      (q.side==="over"?"Plus de ":"Moins de ")+q.line;
    observation.append(h("p","",
      side+" · "+q.book.replace("_fr","")+" @ "+f(q.price)+
      " · relevé "+date(q.observedAt)+
      (!q.comparableMarketRule?" · RÈGLEMENT / PROLONGATION NON VÉRIFIÉ":"")));
  }
  observation.append(h("small","","Prix déjà observés, non garantis toujours proposés. Aucune valeur positive validée."));
  root.append(observation);
 }
 if(e.recentCrossBookPrices?.length){
  const panel=h("div","arc-v3-model");
  panel.append(h("strong","","PulseScore · différences observées (PAS une EV)"));
  for(const c of e.recentCrossBookPrices.slice(0,4)){
    const descr=c.market==="h2h"?
      (c.side==="home"?"Victoire domicile":c.side==="away"?"Victoire extérieur":"Match nul"):
      ((c.side==="over"?"Plus de ":"Moins de ")+c.line);
    panel.append(h("p","",descr+" · "+c.topBook.replace("_fr","")+
      " "+f(c.topPrice)+" contre "+f(c.lowPrice)+
      " (écart relatif "+f(c.differencePercent)+" %) · "+
      c.bookCount+" bookmakers · relevé "+date(c.observedAt)));
  }
  panel.append(h("small","","Prix historiques authentifiés, susceptibles de changer. Écart de cotes ≠ avantage ni disponibilité à la mise."));
  root.append(panel);
 }
 if(e.historicalQuotes.length){
  const hist=h("div","arc-v3-price");
  hist.append(h("strong","","Prix historiques (PAS de cote actuelle)"));
  for(const q of e.historicalQuotes){
   hist.append(h("p","",q.bookmaker.replace("_fr","")+" : "+
     f(q.quote)+" observée le "+date(q.observedAt)+". Non vérifiée actuellement."));
  }
  root.append(hist);
 }
 const link=h("a","arc-btn","Dossier et sources ↗");link.href=dest(e);
 root.append(link);
}
function createCard(e){
 const c=h("article","arc-v3-game");
 const a=h("div","arc-v3-game-header");
 add(a,h("span","arc-v3-league",e.league),
  h("span","arc-v3-date",date(e.start)));
 c.append(a,h("h3","",e.away+" — "+e.home));
 const info=h("p","arc-v3-game-info",e.modelCount+
  " modèle(s) expérimental(aux) · "+
  (e.recentCrossBookPrices?.length?
    e.recentCrossBookPrices.length+" écarts de cotes PulseScore observés":
    e.recentObservedPriceExamples?.length?
    "cotes PulseScore observées (non garanties)":
    e.historicalQuotes.length?"prix historiques disponibles":"aucune cote vérifiée"));
 c.append(info);
 const bottom=h("div","arc-v3-game-bottom");
 add(bottom,h("span","arc-v3-status","À ANALYSER · NON VALIDÉ"));
 const button=h("button","arc-v3-why-button","Pourquoi ?");
 button.type="button";
 button.setAttribute("aria-label","Voir pourquoi aucun pari n'est validé pour "+e.away+" contre "+e.home);
 button.addEventListener("click",()=>{
  renderWhy(e);
  const why=$("home-pourquoi");
  if(why)why.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});
 });
 bottom.append(button);c.append(bottom);
 return c;
}
function sportOf(e){
 const label=(e.sport+" "+e.league).toLowerCase();
 if(label.includes("nhl")||label.includes("hockey")||label.includes("shl")||label.includes("liiga"))return"hockey";
 if(label.includes("tennis")||label.includes("atp")||label.includes("wta"))return"tennis";
 if(label.includes("football")||["PL","LIGUE1","SERIEA","LALIGA","BUNDESLIGA","MLS"].includes(e.league))return"football";
 return"other";
}
function drawEvents(){
 const root=$("home-picks");if(!root)return;
 const source=state?.events||[];
 const items=source.filter(e=>(activeSport==="all"||sportOf(e)===activeSport)&&
  (!query||(e.away+" "+e.home+" "+e.league).toLowerCase().includes(query)));
 const chosen=items.slice(0,10);
 put("v3-count",items.length+" rencontre(s) à surveiller");
 put("home-active",0);
 root.replaceChildren();
 if(!chosen.length){
  blank("home-picks","Aucun match vérifié pour ce filtre",
    state?.sources.matches==="fresh"?"Essaie un autre sport ou attends de nouveaux matchs.":"Calendrier manquant ou trop ancien : aucun événement inventé.");
 }else{
  for(const e of chosen)root.append(createCard(e));
 }
 if(!selected||!source.some(e=>e.key===selected)){
  renderWhy(chosen[0]||null);
 }else{
  renderWhy(source.find(e=>e.key===selected));
 }
}
function drawPaper(){
 const p=state?.paper;
 if(!p){
  for(const id of ["home-profit","home-roi","home-settled","v3-winrate","v3-pending"])put(id,"—");
  blank("home-recent","Bilan indisponible","Journal non vérifié : aucune performance inventée.");
  put("v3-paper-detail","La provenance du journal ne permet pas de calculer un ROI.");
  return;
 }
 put("home-profit",(p.profit>0?"+":"")+f(p.profit)+" u");
 put("home-roi",p.roi===null?"—":(p.roi>0?"+":"")+f(p.roi)+" %");
 put("home-settled",p.settled);
 put("v3-winrate",p.winrate===null?"—":f(p.winrate)+" %");
 put("v3-pending",p.pending);
 put("v3-paper-detail",p.won+" gagné(s) · "+p.lost+" perdu(s) · "+
    p.push+" remboursé(s) · "+p.excluded+" exclu(s). "+
    "Seulement "+f(p.stake)+" unités fictives engagées sur résultats réglés.");
 const root=$("home-recent");root.replaceChildren();
 const settled=p.records.filter(r=>["won","lost","push"].includes(r.status));
 if(!settled.length){
  blank("home-recent","Aucun résultat réglé","Il n'y a pas encore de résultat pré-match contrôlé.");
  return;
 }
 for(const r of settled.slice(0,5)){
  const row=h("div","arc-v3-result");
  const title=h("div");
  add(title,h("strong","",r.away+" — "+r.home),
   h("small","",r.league+" · "+date(r.start_utc)+" · simulation"));
  const outcome=r.status==="won"?"GAGNÉ":r.status==="lost"?"PERDU":"REMBOURSÉ";
  add(row,title,h("span","arc-v3-state "+(r.status==="won"?"win":"loss"),outcome),
    h("strong","",(r.paper_profit_units>0?"+":"")+f(r.paper_profit_units)+" u"));
  root.append(row);
 }
}
function renderState(){
 const m=state.sources.matches==="fresh";
 put("home-status",m?"0 pari certifié · calendrier vérifié":"0 pari certifié · calendrier non actualisé");
 put("home-when",m?"Rencontres : "+date(state.matchUpdated)+" · données horodatées":"Aucune prédiction générée depuis un calendrier périmé");
 put("v3-why-summary",state.reason);
 const n=state.sources.nhl==="partial_research";
 put("v3-data-status",
   (m?"CALENDRIER VÉRIFIÉ":"CALENDRIER INDISPONIBLE")+" · "+
   (n?"NHL EXPÉRIMENTAL":"NHL NON ACTUALISÉ")+" · "+
   (state.sources.radar==="bounded_six_hour_observations"?"PULSESCORE 6H OBSERVÉ":"PULSESCORE 6H INDISPONIBLE")+" · "+
   (state.paper?"BILAN FICTIF VÉRIFIÉ":"BILAN NON VÉRIFIÉ"));
 drawEvents();drawPaper();
}
function bootEvents(){
 const input=$("v3-search");
 if(input)input.addEventListener("input",()=>{query=input.value.toLowerCase().trim();selected=null;drawEvents();});
 const group=$("v3-sports");
 if(group)group.addEventListener("click",e=>{
  const btn=e.target.closest("button[data-sport]");if(!btn)return;
  activeSport=btn.dataset.sport;
  selected=null;
  for(const item of group.querySelectorAll("button[data-sport]")){
   item.setAttribute("aria-pressed",String(item===btn));
  }
  drawEvents();
 });
}
document.addEventListener("DOMContentLoaded",async()=>{
 bootEvents();
 const names=["match-center-latest.json","picks-center-latest.json","nhl-frontend-observed-latest.json","nhl-espn-goalies-latest.json","pulsescore-radar-latest.json"];
 const result=await Promise.allSettled(names.map(load));
 const inputs={
  matches:result[0].status==="fulfilled"?result[0].value:null,
  picks:result[1].status==="fulfilled"?result[1].value:null,
  nhl:result[2].status==="fulfilled"?result[2].value:null,
  goalies:result[3].status==="fulfilled"?result[3].value:null,
  radar:result[4].status==="fulfilled"?result[4].value:null,
 };
 if(!window.RevueArcadeV3) {
  put("home-status","Erreur moteur de présentation");
  return;
 }
 state=window.RevueArcadeV3.build(inputs,Date.now());
 renderState();
});
})();