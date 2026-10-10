/* Revue NHL prospective model diagnostics. Predictions are locked, not bets.
   Text-only DOM rendering; never display Brier on non-settled fixtures. */
"use strict";
(()=>{
const id=k=>document.getElementById(k);
const add=(tag,txt,cls)=>{
 const n=document.createElement(tag);
 if(txt!==undefined)n.textContent=String(txt);
 if(cls)n.className=cls;
 return n;
};
const fmt=n=>typeof n==="number"&&Number.isFinite(n)?
  n.toLocaleString("fr-FR",{minimumFractionDigits:3,maximumFractionDigits:3}):"—";
const quality=r=>r?.status==="prospective_partial_input_nhl_comparison_no_bets" &&
  r?.real_bets_enabled===false && r?.roi===null &&
  r?.statistically_valid_profitability_proven===false &&
  r?.same_game_comparison===true &&
  r?.locked_games>=r?.settled_games &&
  r?.pending_games+r?.settled_games===r?.locked_games &&
  Number.isInteger(r?.locked_games) &&
  Number.isInteger(r?.settled_games) &&
  Number.isInteger(r?.pending_games) &&
  r?.models?.monte_carlo?.settled_sample===r?.settled_games &&
  r?.models?.ensemble?.settled_sample===r?.settled_games;
async function mount(root){
 try{
  const request=await fetch("./nhl-frontend-prospective-performance.json",{cache:"no-store"});
  if(!request.ok)throw Error("rapport non publié");
  const r=await request.json();
  const age=Date.now()-Date.parse(r.generated_at_utc);
  if(!quality(r)||!Number.isFinite(age)||age < -120000||age>48*3600000){
   throw Error("rapport ancien ou provenance non vérifiée");
  }
  root.replaceChildren();
  const head=add("div",undefined,"arc-section-head");
  head.append(add("h2","NHL · Monte-Carlo contre Ensemble"));
  const stamp=add("span",r.locked_games+" pronostics verrouillés","arc-chip");
  head.append(stamp);root.append(head);
  root.append(add("p",
   r.settled_games+" matchs réglés · "+r.pending_games+
   " en attente · même échantillon pour les deux modèles. Aucun pari ni cote utilisée.",
   "arc-subtitle"));
  const table=add("div",undefined,"arc-list");
  for(const [label,ref] of [
    ["MONTE-CARLO",r.models.monte_carlo],
    ["ENSEMBLE",r.models.ensemble],
  ]){
    const card=add("article",undefined,"arc-pick");
    card.append(add("strong",label));
    card.append(add("p",r.settled_games?
      "Brier : "+fmt(ref.brier)+" · Log Loss : "+fmt(ref.log_loss):
      "Pas encore de résultat officiel réglé · erreurs non calculées",
      "arc-help"));
    table.append(card);
  }
  root.append(table);
  root.append(add("p","Statistiques préliminaires. Un minimum de "+
    r.min_settled_for_initial_assessment+
    " résultats est prévu avant une première évaluation ; aucune rentabilité prouvée.","arc-help"));
  const link=add("a","Voir les données prospectives ↗","arc-btn");
  link.href="./nhl-frontend-prospective-performance.json";
  root.append(link);
 }catch(error){
   root.replaceChildren();
   root.append(add("p","Comparaison NHL indisponible : "+error.message+".","arc-help"));
 }
}
document.addEventListener("DOMContentLoaded",()=>{
 for(const root of document.querySelectorAll("[data-nhl-performance]"))mount(root);
});
})();