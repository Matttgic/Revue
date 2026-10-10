/* Phase 3: one source-gated research leaderboard inside the existing Bilan.
   Completely distinct from the fictitious stake/profit/ROI journal. */
"use strict";
(()=>{
const mount=document.getElementById("phase3-owned-models");
if(!mount)return;
const el=(tag,text,klass)=>{
 const n=document.createElement(tag);
 if(klass)n.className=klass;
 if(text!==undefined)n.textContent=String(text);
 return n;
};
const fmt=x=>typeof x==="number"&&Number.isFinite(x)?
  x.toLocaleString("fr-FR",{maximumFractionDigits:4}):"—";
const names={
 baseline:"Modèle de base",advanced_team:"Elo + forme récente",
 montecarlo_bayes:"Monte-Carlo / Bayes",football_advanced:"Football avancé",
 own_elo:"Elo indépendant Revue"
};
const blank=note=>{
 mount.replaceChildren();
 mount.append(el("p",note,"arc-help"));
};
async function get(name){
 const r=await fetch("./"+name,{cache:"no-store"});
 if(!r.ok)throw Error("rapport manquant");
 return r.json();
}
async function init(){
 try{
  if(typeof window.RevueArcadeV3?.ownedSnapshot!=="function")
   throw Error("vérification des sources indisponible");
  const [ledger,summary]=await Promise.all([
   get("phase2-owned-ledger.json"),get("phase2-owned-performance.json")
  ]);
  const view=window.RevueArcadeV3.ownedSnapshot(ledger,summary,Date.now());
  if(view.status!=="prospective_independent_unvalidated")
   throw Error("historique périmé ou données non concordantes");
  mount.replaceChildren();
  const title=el("div",undefined,"arc-section-head");
  title.append(el("h2","Modèles Revue · historique indépendant"),
    el("span",view.locked+" matchs enregistrés","arc-chip"));
  mount.append(title);
  mount.append(el("p",
    "Depuis le début du suivi : "+view.settled+" matchs réglés, "+
    view.elo+" résultats pour notre Elo. Comparaison uniquement sur des pronostics gelés avant match, pas des paris.","arc-help"));
  const list=el("div",undefined,"arc-list");
  let comparisons=0;
  for(const [league,group] of Object.entries(view.stats||{})){
   if(!group.locked)continue;
   const best=Object.entries(group.models||{})
    .filter(([,x])=>x.settled>0&&typeof x.brier==="number"&&typeof x.log_loss==="number")
    .sort((a,b)=>a[1].brier-b[1].brier);
   const card=el("article",undefined,"arc-result-card");
   card.append(el("strong",league+" · "+group.settled+"/"+group.locked+" matchs réglés"));
   if(best.length){
    comparisons++;
    for(const [model,score] of best){
     card.append(el("p",(names[model]||model)+
       " · n="+score.settled+" · Brier "+fmt(score.brier)+
       " · Log Loss "+fmt(score.log_loss),"arc-help"));
    }
    card.append(el("small","Comparaison descriptive : échantillon faible, pas de rentabilité prouvée.","arc-help"));
   }else card.append(el("p","Premiers résultats officiels en attente.","arc-help"));
   list.append(card);
  }
  mount.append(list);
  mount.append(el("p",
    comparisons?"Aucun modèle automatiquement promu, aucune EV positive validée.":
    "Aucun score de modèle n'est inventé tant qu'il n'y a pas de résultats réglés.","arc-help"));
  const a=el("a","CONSULTER LES MATCHS ET NOTRE ELO ↗","arc-btn");
  a.href="./historique-phase2.html";
  mount.append(a);
 }catch(error){blank("Historique prospectif indisponible : "+
   error.message+". Aucun résultat ni classement inventé.");}
}
init();
})();