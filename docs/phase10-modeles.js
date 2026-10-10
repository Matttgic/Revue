/* Revue Phase10 - presentation only, no pricing/EV recommendation. */
"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const $=x=>document.getElementById(x),label=(n)=>Number(n).toLocaleString("fr-FR",{maximumFractionDigits:1});
 const node=(tag,text,cls)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;};
 let data,center,perf,filter="all";
 const soccer=new Set(["PL","LALIGA","SERIEA","BUNDESLIGA","LIGUE1","MLS","UCL"]);
 const selection=(x)=>x.league==="NBA"||x.league==="MLB"||x.league==="NHL"||soccer.has(x.league);
 function draw(){
  const root=$("m10-matches");root.replaceChildren();let shown=0;
  for(const e of center.events){
   if(!selection(e)||filter!=="all"&&(filter==="SOCCER"?!soccer.has(e.league):e.league!==filter))continue;
   const candidates=(e.research||[]).filter(x=>x.calibrated===false&&x.probabilities&&(
     x.id.startsWith("revue_")||x.id==="football_espn_advanced_shadow"||x.id==="clairvoyance_nhl_formula_revue_inputs"));
   if(!candidates.length)continue;
   shown++;
   const card=node("article",undefined,"m10card");
   card.append(node("p",e.league+" · "+new Date(e.start_utc).toLocaleString("fr-FR",{timeZone:"Europe/Paris",dateStyle:"short",timeStyle:"short"}),"m10meta"));
   card.append(node("h3",e.home+" — "+e.away));
   for(const m of candidates){
    const p=m.probabilities;
    if(typeof p.home_win!=="number"&&typeof p.home_win_90!=="number")continue;
    const div=node("div",undefined,"m10model");div.append(node("span",m.label||m.id));
    const h=p.home_win??p.home_win_90,a=p.away_win??p.away_win_90;
    const pieces=["1 : "+label(100*h)+" %"];if(typeof p.draw_90==="number")pieces.push("N : "+label(100*p.draw_90)+" %");
    pieces.push("2 : "+label(100*a)+" %");div.append(node("strong",pieces.join(" · ")));
    card.append(div);
   }
   const a=node("a","POURQUOI CE MATCH ? ↗","arc-btn");
   a.href="./pourquoi.html?league="+encodeURIComponent(e.league)+"&id="+encodeURIComponent(e.event_id);card.append(a);
   root.append(card);
  }
  if(!shown)root.append(node("p","Aucun match futur avec une prévision disponible pour ce sport.","m10note"));
 }
 try{
  const urls=["./phase10-modeles-multisports-latest.json","./match-center-latest.json","./phase10-modeles-performance.json"];
  const resp=await Promise.all(urls.map(x=>fetch(x,{cache:"no-store"})));
  if(resp.some(x=>!x.ok))throw Error("Source JSON HTTP indisponible");
  [data,center,perf]=await Promise.all(resp.map(x=>x.json()));
  if(data.version!=="revue_phase10_multisport_model_candidates_v1"||
     data.real_bets_enabled!==false||data.verified_positive_EV!==0||
     center.status!=="experimental_revue_match_center"||
     center.bookmaker_prices_are_live!==false||perf.version!=="revue_phase10_forward_ledger_v1"||
     perf.real_bets_enabled!==false||perf.roi!==null)throw Error("Contrôle de provenance refusé");
  $("m10-out").textContent=data.metrics.candidates;
  $("m10-games").textContent=data.metrics.events_covered;
  $("m10-locked").textContent=perf.total_locked;
  $("m10-settled").textContent=perf.settled;
  $("m10-status").textContent="Données générées le "+new Date(data.generated_at_utc).toLocaleString("fr-FR",{dateStyle:"short",timeStyle:"short",timeZone:"Europe/Paris"})+" · sorties de recherche non calibrées · cotes jouables non vérifiées.";
  const models=$("m10-performance");
  for(const [id,k] of Object.entries(perf.models)){
   const li=node("li",id+" : "+k.settled+" / "+k.locked+" prévisions réglées"+
      (k.mean_brier_multiclass_unscaled===null?" · Brier indisponible":
       " · Brier "+label(k.mean_brier_multiclass_unscaled)+
       " · Log Loss "+label(k.mean_logloss)));models.append(li);
  }
  $("m10-filters").addEventListener("click",e=>{
   const button=e.target.closest("button[data-sport]");if(!button)return;
   filter=button.dataset.sport;
   for(const c of $("m10-filters").querySelectorAll("button"))c.setAttribute("aria-pressed",String(c===button));
   draw();
  });
  draw();
 }catch(e){$("m10-status").textContent="Données non confirmées : "+e.message;}
});
