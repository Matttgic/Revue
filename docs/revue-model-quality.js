/* Revue paper model quality: read-only, qualified small sample. */
"use strict";
(()=>{
const div=document.getElementById("revue-model-quality");
if(!div)return;
const add=(tag,text,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n};
const num=x=>typeof x==="number"&&Number.isFinite(x)?x.toLocaleString("fr-FR",{maximumFractionDigits:4}):"—";
async function main(){
 try{
  const res=await fetch("./revue-model-quality-latest.json",{cache:"no-store"});
  if(!res.ok)throw Error("rapport absent");
  const r=await res.json();
  const age=Date.now()-Date.parse(r.generated_at_utc);
  if(r.version!=="revue_prospective_paper_calibration_v1"||
     r.status!=="prospective_probabilities_descriptive_not_calibrated"||
     r.real_bets_enabled!==false||r.fitted_or_recalibrated_model!==false||
     r.claim_model_profitable!==false||r.verified_positive_ev!==false||
     r.bookmaker_baseline_includes_vig!==true||
     !Number.isFinite(age)||age < -120000||age>6*3600000||
     !r.total||typeof r.total.count!=="number"||
     typeof r.total.distinct_events!=="number")throw Error("données anciennes ou non vérifiées");
  div.replaceChildren();
  const top=add("div",undefined,"arc-section-head");
  top.append(add("h2","Qualité des modèles · probabilités"));
  top.append(add("span",r.total.count+" prévisions réglées admissibles","arc-chip"));
  div.append(top);
  div.append(add("p","Comparaison des prévisions réellement verrouillées avant match avec les résultats officiels. Cotes bookmakers brutes (marge incluse).","arc-subtitle"));
  const grid=add("div",undefined,"arc-kpis");
  for(const [label,key] of [
    ["Brier Revue","brier_model"],
    ["Brier bookmaker brut","brier_bookmaker_raw"],
    ["Log Loss Revue","log_loss_model"],
    ["Log Loss bookmaker brut","log_loss_bookmaker_raw"]
  ]){
    const cell=add("article",undefined,"arc-kpi");
    cell.append(add("div",label,"caption"));
    cell.append(add("strong",num(r.total[key]),"value"));
    grid.append(cell);
  }
  div.append(grid);
  div.append(add("p",
    r.total.distinct_events+" rencontres différentes pour "+r.total.count+
    " prévisions · "+r.min_independent_fixtures_for_preliminary_evaluation+
    " rencontres minimales pour une première évaluation. Plus bas = meilleur pour les deux erreurs.",
    "arc-help"));
  div.append(add("p","Échantillon insuffisant : aucune calibration, EV positive ou rentabilité démontrée. Les pronostics exclus et les matchs non réglés ne sont jamais utilisés.","arc-help"));
  if(r.by_sport&&Object.keys(r.by_sport).length){
    const details=add("details");
    details.append(add("summary","Détails de précision par sport"));
    const list=add("div",undefined,"arc-list");
    for(const [lg,stat] of Object.entries(r.by_sport)){
      list.append(add("p",lg+" · "+stat.count+" prévisions · Brier "+num(stat.brier_model)+
        " · Log Loss "+num(stat.log_loss_model),"arc-help"));
    }
    details.append(list);div.append(details);
  }
  const link=add("a","VOIR LE RAPPORT SOURCE ↗","arc-btn");
  link.href="./revue-model-quality-latest.json";div.append(link);
 }catch(err){div.replaceChildren(add("p","Évaluation des modèles indisponible : "+err.message+". Aucun score extrapolé.","arc-help"));}
}
main();
})();