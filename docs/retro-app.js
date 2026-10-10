/* REVUE / Arcade 2.0 - source-gated interface for daily use.
 * A displayed historical bookmaker price is NEVER an actionable betting offer.
 * No fictitious recommendations, confidence ratings, bank balance or profit.
 */
"use strict";
(()=>{
const $=id=>document.getElementById(id);
const el=(tag,cls,value)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;};
const put=(id,value)=>{if($(id))$(id).textContent=String(value);};
const now=()=>Date.now();
const parseTime=value=>{const t=Date.parse(value);return Number.isFinite(t)?t:null;};
const fmtTime=(v,options={dateStyle:"short",timeStyle:"short"})=>{
  const n=parseTime(v);return n===null?"heure indisponible":new Date(n).toLocaleString("fr-FR",{timeZone:"Europe/Paris",...options});
};
const compact=n=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("fr-FR",{maximumFractionDigits:2}):"—";
const money=n=>typeof n==="number"&&Number.isFinite(n)?(n>0?"+":"")+compact(n)+" u":"—";
const pct=n=>typeof n==="number"&&Number.isFinite(n)?compact(n)+" %":"—";
const price=n=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("fr-FR",{minimumFractionDigits:2,maximumFractionDigits:2}):"—";
const statustxt={won:"GAGNÉ",lost:"PERDU",push:"REMBOURSÉ",pending:"EN ATTENTE",unverified:"EXCLU"};
const windowHours=2;
let picks=null, matches=null;
function safePicks(doc){
 return doc&&doc.status==="revue_independent_picks_hub_static_research_paper_only"&&
 doc.research_model_calibrated===false&&doc.verified_real_ev===false&&
 doc.live_bookmaker_prices===false&&doc.real_bets_enabled===false&&
 doc.original_clairvoyance_sql_parity===false&&
 Array.isArray(doc.research_selections)&&Array.isArray(doc.paper_records)&&
 doc.unique_research_selections===doc.research_selections.length&&
 doc.paper_summary?.settled>=0&&doc.paper_summary?.total===doc.paper_records.length&&
 doc.paper_records.every(r=>r.real_bet===false&&
  ["won","lost","push","pending","unverified"].includes(r.status)&&
  (r.status==="won"||r.status==="lost"||r.status==="push"?r.verified_pregame===true&&typeof r.paper_profit_units==="number":r.paper_profit_units===null));
}
function safeMatches(doc){
 return doc&&doc.status==="experimental_revue_match_center"&&
 doc.bookmaker_prices_are_live===false&&doc.real_bets_enabled===false&&
 doc.validated_value_bets===0&&Array.isArray(doc.events)&&
 doc.metrics?.upcoming_matches===doc.events.length;
}
async function json(file){
 const res=await fetch("./"+file+"?rev="+now(),{cache:"no-store"});
 if(!res.ok)throw Error(file+": "+res.status);
 return res.json();
}
async function bootData(){
 const [p,m]=await Promise.allSettled([json("picks-center-latest.json"),json("match-center-latest.json")]);
 picks=p.status==="fulfilled"&&safePicks(p.value)?p.value:null;
 matches=m.status==="fulfilled"&&safeMatches(m.value)?m.value:null;
 if(!picks){const msg="Journal de simulations absent ou source non vérifiée";put("home-status",msg);put("play-status",msg);put("bilan-status",msg);put("history-status",msg);}
 if(!matches){put("match-status","Calendrier indisponible ou provenance non vérifiée");}
}
function sourceFresh(iso,hours=windowHours){
 const date=parseTime(iso);return date!==null&&date<=now()+120000&&now()-date<=hours*3600000;
}
function actualUpcoming(r){
 const start=parseTime(r.start_utc);return start!==null&&start>now()+20*60000;
}
function sourceObserved(g){
 const at=parseTime(g?.best_observed_price?.quote_at_utc),kick=parseTime(g?.start_utc);
 return at!==null&&kick!==null&&at<=now()&&at<=kick-20*60000;
}
function researchCandidates(){
 if(!picks||!sourceFresh(picks.source_engine_generated_at_utc,3))return [];
 // Archived bookmaker observations must never be promoted as verified picks.
 return picks.research_selections.filter(g=>g.league!=="CFB"&&
  g.real_bet===false&&g.model_is_calibrated===false&&
  g.qualified_positive_ev===false&&g.available_as_real_market===false&&
  actualUpcoming(g)&&sourceObserved(g))
  .sort((a,b)=>parseTime(a.start_utc)-parseTime(b.start_utc));
}
function upcomingMatches(){
 if(!matches||!sourceFresh(matches.generated_at_utc,12))return [];
 return matches.events.filter(g=>g.league!=="CFB"&&actualUpcoming(g)&&
 g.qualified_for_real_betting===false&&g.recommendation===null&&g.ev===null)
  .sort((a,b)=>parseTime(a.start_utc)-parseTime(b.start_utc));
}
function selectionName(g){
 if(g.market==="totals")return(g.side==="over"?"Plus de ":"Moins de ")+compact(g.line)+" buts/points (règlement à vérifier)";
 if(g.side==="draw")return"Match nul";
 if(g.side==="home")return g.home;
 if(g.side==="away")return g.away;
 return "Marché non identifié";
}
function matchUrl(g){return"./match-dossier.html?league="+encodeURIComponent(g.league)+"&id="+encodeURIComponent(g.event_id);}
function label(text,type){return el("span","arc-chip"+(type?" arc-chip--"+type:""),text);}
function createResearch(g){
 const card=el("article","arc-pick");
 const head=el("div","arc-pick-head");
 head.append(el("span","",g.league+" · "+g.market.toUpperCase()),el("span","",fmtTime(g.start_utc)));
 card.append(head,el("h3","",g.away+" — "+g.home));
 card.append(el("p","selection","À examiner : "+selectionName(g)));
 const bot=el("div","arc-pick-bottom");
 const odds=el("div");odds.append(el("div","arc-odds",price(g.best_observed_price.decimal_odds)),el("small","arc-muted","Cote OBSERVÉE · "+String(g.best_observed_price.bookmaker).replace("_fr","")));
 bot.append(odds,label("NON VALIDÉ","off"));card.append(bot);
 card.append(el("p","arc-help","Relevé le "+fmtTime(g.best_observed_price.quote_at_utc)+". Modèle expérimental non calibré. Cette cote peut ne plus être disponible."));
 const link=el("a","arc-btn","Fiche match ↗");link.href=matchUrl(g);card.append(link);
 return card;
}
function createMatch(g){
 const card=el("article","arc-pick");
 const head=el("div","arc-pick-head");
 head.append(el("span","",g.league),el("span","",fmtTime(g.start_utc)));
 card.append(head,el("h3","",g.away+" — "+g.home));
 card.append(el("p","arc-help","Rencontre à suivre · "+g.research.length+" modèle(s) de recherche · aucune sélection validée"));
 const bottom=el("div","arc-pick-bottom");
 bottom.append(label("PAS DE PARI VALIDÉ","off"));
 const link=el("a","arc-btn","Voir la rencontre ↗");link.href=matchUrl(g);bottom.append(link);
 card.append(bottom);return card;
}
function empty(labelText,msg){
 const box=el("div","arc-placeholder");box.append(el("strong","",labelText),el("span","",msg));return box;
}
function validatePaper(){
 if(!picks)return null;
 const recs=picks.paper_records;
 const settled=recs.filter(x=>["won","lost","push"].includes(x.status));
 const stake=settled.reduce((a,x)=>a+x.paper_stake_units,0);
 const net=settled.reduce((a,x)=>a+x.paper_profit_units,0);
 const wins=settled.filter(x=>x.status==="won").length;
 const summary=picks.paper_summary;
 if(summary.settled!==settled.length||
 summary.wins!==wins||summary.total!==recs.length||
 summary.excluded!==recs.filter(x=>x.status==="unverified").length||
 Math.abs(summary.paper_profit_units-net)>.011||
 Math.abs(summary.settled_stake_units-stake)>.011)return null;
 return {records:recs,settled,stake,net,wins,roi:stake>0?net/stake*100:null,summary};
}
function statusBox(nodeId){
 if(!$(nodeId))return;
 const t=picks?("Simulation publiée "+fmtTime(picks.source_ledger_generated_at_utc)+
 " · cotes passées, PAS en direct · aucun gain réel"): "Source non vérifiée : aucune performance affichée";
 put(nodeId,t);
}
function renderHome(){
 const good=validatePaper();
 put("home-active",0); // no calibrated, bookmaker-confirmed opportunities exist
 put("home-status","Aucun pari certifié par le modèle · cotes non temps réel");
 if(good){
  put("home-profit",money(good.net));put("home-roi",pct(good.roi));put("home-settled",good.settled.length);
  put("home-scope",good.summary.total+" simulations · "+good.summary.pending+" en attente · "+
    good.summary.excluded+" exclues");
 }
 const root=$("home-picks");if(root){
  root.replaceChildren();
  const candidates=researchCandidates().slice(0,3);
  put("home-research-count",candidates.length);
  if(!candidates.length)root.append(empty("Aucun pari validé aujourd'hui",
   "La sélection automatique n'est pas calibrée et aucune cote actuelle n'est confirmée. Ne rien jouer est une option. Les matchs à venir restent consultables ci-dessous."));
  else {root.append(el("p","arc-help","Observations expérimentales uniquement : aucune recommandation de mise."));for(const c of candidates)root.append(createResearch(c));}
 }
 const m=$("home-matches");if(m){
  m.replaceChildren();
  const games=upcomingMatches().slice(0,3);
  if(!games.length)m.append(empty("Aucun match récent à afficher","Les dernières données n'ont pas été vérifiées récemment."));
  else for(const g of games)m.append(createMatch(g));
 }
 const latest=$("home-recent");if(latest){
  latest.replaceChildren();
  if(!good||!good.settled.length)latest.append(empty("Bilan en construction","Aucune simulation pré-match n'a encore un résultat vérifié."));
  else for(const r of [...good.settled].sort((a,b)=>parseTime(b.start_utc)-parseTime(a.start_utc)).slice(0,3))latest.append(createResult(r));
 }
 put("home-when",matches&&sourceFresh(matches.generated_at_utc,12)?
 "Calendrier observé "+fmtTime(matches.generated_at_utc):
 "Calendrier en attente de données récentes");
}
function createResult(r){
 const row=el("article","arc-result");
 const desc=el("div");desc.append(el("strong","",r.away+" — "+r.home),
 el("small","",r.league+" · "+fmtTime(r.start_utc)+" · "+(r.outcome||selectionName(r))));
 row.append(desc,label(statustxt[r.status]||r.status,r.status==="won"?"won":r.status==="lost"?"lost":"off"),
 el("span","",price(r.decimal_odds)),el("span","",compact(r.paper_stake_units)+" u"),
 el("strong","",r.paper_profit_units==null?"—":money(r.paper_profit_units)));
 return row;
}
function renderPlay(){
 const root=$("play-results"), matchRoot=$("play-matches");
 if(!root)return;
 root.replaceChildren();if(matchRoot)matchRoot.replaceChildren();
 const candidates=researchCandidates();
 const filter=($("play-filter")?.value||"").toLowerCase();
 const valid=candidates.filter(x=>!filter||[x.league,x.home,x.away,x.market,x.selection_label].some(v=>String(v||"").toLowerCase().includes(filter)));
 put("play-count",valid.length);
 put("play-status",picks?
 "Flux enregistré le "+fmtTime(picks.source_engine_generated_at_utc)+
 " · aucune EV confirmée · meilleure cote = prix passé, non disponible en direct":
 "Aucune source de prix vérifiée");
 if(valid.length)for(const c of valid.slice(0,60))root.append(createResearch(c));
 else root.append(empty("Aucun pari recommandé","Les probabilités ne sont pas calibrées et aucune cote n'est confirmée en temps réel. Pas de sélection forcée."));
 const games=upcomingMatches().filter(x=>!filter||[x.league,x.home,x.away].some(v=>String(v).toLowerCase().includes(filter)));
 put("play-match-count",games.length);
 if(matchRoot){
  if(games.length)for(const g of games.slice(0,35))matchRoot.append(createMatch(g));
  else matchRoot.append(empty("Pas de calendrier récent vérifié","Le radar ne remplace pas des données sportives fraîches."));
 }
}
function dateRange(records,period){
 if(period==="all")return records;
 const ms={"1d":86400000,"7d":7*86400000,"30d":30*86400000}[period];
 return ms?records.filter(r=>{const t=parseTime(r.start_utc);return t!==null&&t<=now()&&now()-t<=ms;}):records;
}
function gradeSubset(records){
 const settled=records.filter(r=>["won","lost","push"].includes(r.status));
 const stake=settled.reduce((x,r)=>x+r.paper_stake_units,0);
 const net=settled.reduce((x,r)=>x+r.paper_profit_units,0);
 const wins=settled.filter(r=>r.status==="won").length;
 return {settled,stake,net,wins,roi:stake>0?net/stake*100:null,
  winrate:settled.length?wins/settled.length*100:null,
  pending:records.filter(r=>r.status==="pending").length,
  excluded:records.filter(r=>r.status==="unverified").length};
}
function makeEquity(svg,graded){
 svg.replaceChildren();
 const ns="http://www.w3.org/2000/svg";
 const create=(tag,attrs,txt)=>{const x=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))x.setAttribute(k,String(v));if(txt!==undefined)x.textContent=txt;return x;};
 svg.setAttribute("viewBox","0 0 620 210");
 svg.setAttribute("role","img");
 svg.setAttribute("aria-label","Cumul fictif en unités, uniquement sur les simulations réglées avant match");
 const ordered=graded.slice().sort((a,b)=>parseTime(a.start_utc)-parseTime(b.start_utc));
 let values=[0],sum=0;for(const r of ordered){sum+=r.paper_profit_units;values.push(sum);}
 const min=Math.min(...values,-.5),max=Math.max(...values,.5),range=Math.max(1,max-min);
 const coords=values.map((v,i)=>[30+i/(values.length-1||1)*555,170-(v-min)/range*135]);
 for(const y of [40,80,120,160])svg.append(create("line",{x1:30,x2:585,y1:y,y2:y,class:"arc-chart-axis"}));
 const points=coords.map(c=>c.join(",")).join(" ");
 svg.append(create("polyline",{points,class:"arc-chart-line"}));
 for(const [i,c] of coords.entries())svg.append(create("circle",{cx:c[0],cy:c[1],r:i===coords.length-1?5:3,fill:"#79f3e1"}));
 svg.append(create("text",{x:30,y:195,class:"arc-chart-label"},"Début : 0 u"));
 svg.append(create("text",{x:585,y:195,"text-anchor":"end",class:"arc-chart-label"},"Fin : "+money(sum)));
}
function renderBilan(){
 const base=validatePaper();
 put("bilan-status",picks?
 "Chiffres exclusivement fictifs et vérifiés · dernier journal "+fmtTime(picks.source_ledger_generated_at_utc):
 "Journal fictif indisponible ou provenance invalide");
 if(!base)return;
 const period=$("period-select")?.value||"all";
 const records=dateRange(base.records,period),v=gradeSubset(records);
 put("bilan-profit",money(v.net));put("bilan-roi",pct(v.roi));
 put("bilan-winrate",pct(v.winrate));put("bilan-settled",v.settled.length);
 put("bilan-pending",v.pending);put("bilan-excluded",v.excluded);
 put("bilan-note","Seulement "+v.settled.length+" résultat(s) réglé(s) et "+compact(v.stake)+" u fictives engagées sur cette période. Aucune bankroll réelle connue.");
 if($("equity-chart"))makeEquity($("equity-chart"),v.settled);
 const sport=$("bilan-sports");if(sport){
  sport.replaceChildren();
  const groups=[...new Set(records.map(r=>r.league))].sort();
  if(!groups.length)sport.append(empty("Aucune donnée","Aucune simulation enregistrée sur cette période."));
  for(const lg of groups){
   const sub=gradeSubset(records.filter(r=>r.league===lg));
   const row=el("div","arc-pick-bottom");
   const title=el("div");title.append(el("strong","",lg),el("small","arc-muted"," · "+sub.settled.length+" réglées"));
   row.append(title,el("strong","",money(sub.net)),label(pct(sub.roi),sub.roi!==null&&sub.roi>=0?"won":"off"));
   const wrap=el("div","");wrap.append(row,el("div","arc-rule"));sport.append(wrap);
  }
 }
 const recent=$("bilan-recent");if(recent){
  recent.replaceChildren();for(const r of [...v.settled].sort((a,b)=>parseTime(b.start_utc)-parseTime(a.start_utc)).slice(0,5))recent.append(createResult(r));
  if(!v.settled.length)recent.append(empty("Aucun résultat réglé","Impossible de calculer un taux de réussite sur cette période."));
 }
}
function visibleHistory(){
 if(!validatePaper())return [];
 const status=$("history-filter")?.value||"all",q=($("history-search")?.value||"").trim().toLowerCase();
 return picks.paper_records.filter(r=>(status==="all"||status===r.status)&&
 (!q||[r.home,r.away,r.league,r.bookmaker,r.outcome,r.id].some(s=>String(s||"").toLowerCase().includes(q))))
 .sort((a,b)=>parseTime(b.start_utc)-parseTime(a.start_utc));
}
function renderHistory(){
 const root=$("history-list");if(!root)return;root.replaceChildren();
 put("history-status",picks?"Journal horodaté · simulation, pas des paris réellement misés":
 "Journal source absent ou non vérifié");
 const rows=visibleHistory();put("history-count",rows.length);
 if(!rows.length){root.append(empty("Aucune entrée","Modifie le filtre ou attends des données vérifiées."));return;}
 for(const rec of rows)root.append(createResult(rec));
}
function exportCSV(rows){
 const keys=["id","league","event_id","home","away","start_utc","outcome","market","side","line","bookmaker","decimal_odds","paper_stake_units","status","paper_profit_units","exclusion_reason"];
 const q=v=>'"'+String(v??"").replaceAll('"','""')+'"';
 const result=[keys.join(";"),...rows.map(r=>keys.map(k=>q(r[k])).join(";"))].join("\n");
 const blob=new Blob(["\uFEFF"+result],{type:"text/csv;charset=utf-8"});
 const url=URL.createObjectURL(blob);const link=el("a");link.href=url;link.download="revue-historique-simulations.csv";link.click();setTimeout(()=>URL.revokeObjectURL(url),6000);
}
function setupEvents(){
 $("period-select")?.addEventListener("change",renderBilan);
 $("play-filter")?.addEventListener("input",renderPlay);
 $("history-filter")?.addEventListener("change",renderHistory);
 $("history-search")?.addEventListener("input",renderHistory);
 $("history-export")?.addEventListener("click",()=>exportCSV(visibleHistory()));
}
function setupTilt(){
 const stage=$(".arc-hero");if(!stage)return;
 const reduce=window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
 if(reduce||window.matchMedia?.("(pointer: coarse)")?.matches)return;
 stage.addEventListener("pointermove",evt=>{
  const r=stage.getBoundingClientRect(),x=(evt.clientX-r.left)/r.width-.5,y=(evt.clientY-r.top)/r.height-.5;
  stage.style.setProperty("--tilt-x",(13-y*9).toFixed(1)+"deg");
  stage.style.setProperty("--tilt-y",(-16+x*13).toFixed(1)+"deg");
 });
 stage.addEventListener("pointerleave",()=>{stage.style.removeProperty("--tilt-x");stage.style.removeProperty("--tilt-y");});
}
document.addEventListener("DOMContentLoaded",async()=>{
 setupEvents();setupTilt();
 const route=document.body.dataset.page;
 if(route==="lab"){put("lab-status","Laboratoire de recherche · réservé aux outils techniques, sans mise réelle");return;}
 await bootData();
 if(route==="home")renderHome();
 if(route==="play")renderPlay();
 if(route==="bilan")renderBilan();
 if(route==="historique")renderHistory();
});
})();