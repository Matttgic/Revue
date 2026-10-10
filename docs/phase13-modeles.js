"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const $=id=>document.getElementById(id),format=(v,n=3)=>v===null||v===undefined?"—":Number(v).toLocaleString("fr-FR",{maximumFractionDigits:n,minimumFractionDigits:0});
 const el=(tag,value,cls)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(value!==undefined)x.textContent=String(value);return x;};
 let data,filter="all";
 const mkStat=(card,label,value)=>{const row=el("div",undefined,"p13stat");row.append(el("span",label),el("strong",value));card.append(row);};
 const sport=(x)=>x==="NBA"||x==="MLB"?x:"FOOT";
 function modelCard(m){
  const card=el("article",undefined,"p13model");
  card.append(el("small",m.league+" / PRÉ-MATCH · NON CALIBRÉ"));
  card.append(el("h3",m.model_id.replaceAll("revue_","").replaceAll("_"," ")));
  mkStat(card,"Prévisions verrouillées",m.frozen_locked);
  mkStat(card,"Finales reconnues",m.settled);
  mkStat(card,"Brier (non normalisé)",format(m.raw.brier));
  mkStat(card,"Log Loss",format(m.raw.logloss));
  mkStat(card,"Brier référence uniforme",format(m.uniform_reference_same_matches.brier));
  mkStat(card,"Phase d'entraînement",m.calibration.training_n+" / "+m.calibration.training_required);
  mkStat(card,"Holdout futur",m.calibration.holdout_n+" / "+m.calibration.holdout_required);
  if(m.calibration.holdout){
   mkStat(card,"Δ Brier calibré − brut",format(m.calibration.holdout.brier_delta_scaled_minus_raw,4));
  }
  card.append(el("p",m.settled===0?"Aucun résultat exploitable : pas de classement.":m.settled<100?
       "Échantillon exploratoire insuffisant, aucune validation.":"Validation future indépendante requise.","p13note"));
  if(m.settled&&Array.isArray(m.reliability)&&m.reliability.length){
   const detail=document.createElement("details"),sum=el("summary","Courbe de fiabilité (classes de résultat)");
   detail.append(sum);
   for(const group of m.reliability){
    detail.append(el("p",group.outcome.toUpperCase(),"p13note"));
    const bars=el("div",undefined,"p13chart");
    for(const bucket of group.bins){
     const b=el("div",undefined,"p13bar");
     b.append(el("small",Math.round(bucket.lower*100)+"–"+Math.round(bucket.upper*100)+"%"));
     b.append(el("span",bucket.n?format(100*bucket.observed_rate,1)+"%":"—"));
     b.append(el("small","n="+bucket.n));bars.append(b);
    }
    detail.append(bars);
   }
   card.append(detail);
  }
  return card;
 }
 const render=()=>{
  const root=$("p13-models");root.replaceChildren();
  const all=Object.values(data.models).filter(m=>filter==="all"||sport(m.league)===filter)
   .sort((a,b)=>a.league.localeCompare(b.league)||a.model_id.localeCompare(b.model_id));
  if(!all.length)root.append(el("p","Pas de modèle enregistré pour ce sport.","p13notice"));
  else for(const m of all)root.append(modelCard(m));
 };
 try{
  const response=await fetch("./phase13-modeles-evaluation-latest.json",{cache:"no-store"});
  if(!response.ok)throw Error("Source JSON HTTP indisponible");
  data=await response.json();
  if(data.version!=="revue_phase13_model_evaluation_v1"||
     data.status!=="research_only_awaiting_prospective_evidence"||
     data.real_bets_enabled!==false||data.verified_profitable_models!==0||
     data.calibrated_models_approved!==0||data.ROI!==null||
     data.protocol.no_auto_model_selection!==true)throw Error("Provenance ou validation refusée");
  $("p13-locked").textContent=data.metrics.locked;
  $("p13-settled").textContent=data.metrics.settled;
  $("p13-fixtures").textContent=data.metrics.distinct_settled_fixtures;
  $("p13-approved").textContent="0";
  $("p13-status").textContent="Dernière évaluation : "+new Date(data.generated_at_utc).toLocaleString("fr-FR",{timeZone:"Europe/Paris",dateStyle:"short",timeStyle:"short"})+
   " · "+data.metrics.settled+" résultats de modèles · aucune rentabilité prouvée ni sélection validée.";
  $("p13-calibration").textContent="Seuils préétablis : "+data.protocol.calibration_train_first_official_finals+" matchs d'entraînement puis "+
   data.protocol.holdout_new_kickoffs_strictly_after_training_resolution+" matchs de validation chronologiquement ultérieurs. Méthode : softmax(log(p) / température), recherche limitée à une grille fixe. Aucune promotion automatique.";
  $("p13-filters").addEventListener("click",event=>{
   const target=event.target.closest("button[data-filter]");if(!target)return;
   filter=target.dataset.filter;
   for(const b of $("p13-filters").querySelectorAll("button"))b.setAttribute("aria-pressed",String(b===target));
   render();
  });
  render();
  const pairs=$("p13-pairs");
  if(!data.paired_comparisons.length)pairs.append(el("p","Aucune paire comparable terminée.","p13note"));
  for(const pair of data.paired_comparisons){
   const node=el("article",undefined,"p13pair");
   node.append(el("h3",pair.league+" · "+pair.reference.replaceAll("revue_nba_","")+" vs "+pair.candidate.replaceAll("revue_nba_","")));
   node.append(el("p",pair.paired_games+" matchs identiques terminés · "+(pair.paired_games>=30?
      "comparaison exploratoire, pas de sélection automatique":"au moins 30 matchs communs requis pour une estimation exploratoire")));
   if(pair.paired_games){
    node.append(el("p","Δ Brier candidat − référence : "+format(pair.delta_brier_candidate_minus_reference,5)+
      " ; Δ Log Loss : "+format(pair.delta_logloss_candidate_minus_reference,5)+
      ". Négatif = meilleur sur cet échantillon (sans preuve de supériorité durable)."));
   }
   pairs.append(node);
  }
  const n=data.NHL,output=$("p13-nhl");
  const summary=el("article",undefined,"p13model");
  summary.append(el("h3",n.settled+" / "+n.locked+" résultats NHL officiels"));
  mkStat(summary,"Matchs comparables avec modèle prudent",n.paired_settled);
  mkStat(summary,"Brier natif binaire",format(n.native_binary_scalar_brier,6));
  mkStat(summary,"Log Loss modèle de référence",format(n.reference_score.logloss,5));
  summary.append(el("p","Évaluation NHL indépendante des scores NBA/MLB/football. Aucun modèle déclaré fiable.","p13note"));
  output.append(summary);
 }catch(error){$("p13-status").textContent="Aucun classement présenté : "+error.message;}
});