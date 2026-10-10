/* Revue Phase14 public release truth. Cosmetic only; never creates tips or ROI. */
"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const root=document.getElementById("phase14-brief");if(!root)return;
 const add=(tag,text,klass,parent)=>{const n=document.createElement(tag);if(klass)n.className=klass;
  n.textContent=String(text);(parent||root).append(n);return n;};
 const fmt=n=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("fr-FR",{maximumFractionDigits:1}):"—";
 const route=document.body.dataset.page;
 const top=add("div","","p14-brief-top"),headline=add("strong","SOURCE CHECK / RECHERCHE","",top);
 const time=add("small","Vérification des sources…","",top);
 const tiles=add("div","","p14-metrics");
 const msg=add("p","Les matchs, les simulations fictives et les résultats des modèles doivent rester séparés.","p14-brief-msg");
 const links=add("div","","p14-brief-actions");
 const link=(target,text)=>{const a=add("a",text,"",links);a.href=target;};
 link("./play.html","01 À JOUER");link("./pourquoi.html","02 POURQUOI");
 link("./bilan.html","03 BILAN");link("./phase13-modeles.html","LAB : TESTS DES MODÈLES ↗");
 function tile(label,value,description){
  const box=add("article","","p14-metric",tiles);
  add("small",label,"",box);add("strong",value,"",box);add("span",description,"",box);
 }
 function fail(label){
  tiles.replaceChildren();headline.textContent="SOURCE CHECK / ABSTENTION";
  time.textContent="Source non validée";msg.textContent=label;
  tile("Paris certifiés","0","Aucune mise conseillée");
  tile("Matchs à étudier","—","Calendrier non confirmé");
  tile("Modèles validés","0","Validation insuffisante");
 }
 try{
  const resp=await fetch("./phase14-readiness-latest.json",{cache:"no-store"});
  if(!resp.ok)throw Error("Rapport indisponible (HTTP "+resp.status+")");
  const d=await resp.json();
  if(d.version!=="revue_phase14_public_contract_v1"||
     d.technical_gate_passed!==true||d.real_bets_enabled!==false||
     d.today?.certified_bet_recommendations!==0||
     d.today?.bookable_French_odds_verified!==false||
     d.models?.independently_approved_models!==0||
     d.models?.ROI!==null||d.simulation_paper?.real_money!==false||
     d.source_parity_100_percent!==false||d.blockers?.length||
     !Array.isArray(d.warnings))throw Error("Incohérence de provenance");
  const published=Date.parse(d.generated_at_utc),age=Date.now()-published;
  if(!Number.isFinite(published)||age< -120000||age>12*3600000||
     d.status==="research_only_data_stale"||d.status==="blocked")
   throw Error("Rapport trop ancien ou sources périmées : aucune sélection validable.");
  const sportAge=d.sources?.center;
  if(sportAge?.state!=="recent")throw Error("Calendrier périmé.");
  time.textContent="Mise à jour "+new Date(published).toLocaleString("fr-FR",
     {timeZone:"Europe/Paris",dateStyle:"short",timeStyle:"short"});
  tiles.replaceChildren();
  tile("Matchs à analyser",fmt(d.today.upcoming_fixtures),
       fmt(d.today.upcoming_with_research_models)+" avec modèle expérimental");
  tile("Paris réellement validés","0","Sans cotes jouables + calibration, SKIP");
  if(route==="bilan"){
   tile("Simulations fictives réglées",fmt(d.simulation_paper.settled),
     fmt(d.simulation_paper.excluded)+" exclues des résultats");
   msg.textContent="Le ROI et le profit en unités affichés plus bas sont uniquement fictifs. "+
     d.models.officially_settled_forecasts+" sorties de modèles multisports réglées, "+
     d.models.NHL_settled+" en NHL. Aucun avantage prouvé.";
  }else if(route==="pourquoi"){
   tile("Prédictions validées","0","Modèles non calibrés indépendamment");
   msg.textContent="Choisis un match : les sources, probabilités expérimentales et motifs d'abstention "+
     "sont distingués des vraies cotes. Aucun pronostic automatique.";
  }else{
   tile("Prédictions réglées",fmt(d.models.officially_settled_forecasts),
     "Évaluées sur résultat officiel, hors simulations");
   msg.textContent="Aucun pari validé à ce stade. Consulte les matchs disponibles pour les étudier, "+
     "ou leur bilan indépendant ; un modèle prometteur n'est pas une garantie.";
  }
  headline.textContent="SOURCE CHECK / DONNÉES HORODATÉES";
 }catch(e){fail("Revue ne peut pas certifier la fraîcheur de ses sources : "+e.message+
    " Les recherches restent consultables, sans conseil de mise.");}
});
