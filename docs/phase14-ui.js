/* Revue Phase14 public release truth. Cosmetic only; never creates tips or ROI. */
"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const root=document.getElementById("phase14-brief");if(!root)return;
 root.querySelectorAll(".p14-brief-msg").forEach(n=>n.remove());
 const add=(tag,text,klass,parent)=>{const n=document.createElement(tag);if(klass)n.className=klass;
  n.textContent=String(text);(parent||root).append(n);return n;};
 const fmt=n=>typeof n==="number"&&Number.isFinite(n)?n.toLocaleString("fr-FR",{maximumFractionDigits:1}):"—";
 const route=document.body.dataset.page;
 const top=add("div","","p14-brief-top"),headline=add("strong","ÉTAT DU JEU","",top);
 const time=add("small","Lecture des données…","",top);
 const tiles=add("div","","p14-metrics");
 const msg=add("p","Les matchs, les simulations fictives et les résultats des modèles doivent rester séparés.","p14-brief-msg");
 const links=add("div","","p14-brief-actions");
 const link=(target,text)=>{const a=add("a",text,"",links);a.href=target;};
 link("./regle-decision.html","★ RÈGLE DE DÉCISION");link("./phase13-modeles.html","⚙ TESTS DES MODÈLES");
 function tile(label,value,description){
  const box=add("article","","p14-metric",tiles);
  add("small",label,"",box);add("strong",value,"",box);add("span",description,"",box);
 }
 function fail(label){
  tiles.replaceChildren();headline.textContent="PAUSE : DONNÉES À VÉRIFIER";
  time.textContent="Données non confirmées";msg.textContent=label;
  tile("Paris certifiés","0","Aucune mise conseillée");
  tile("Matchs à étudier","—","Calendrier non confirmé");
  tile("Modèles fiables","0","Pas encore assez de preuves");
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
  tile("Matchs à étudier",fmt(d.today.upcoming_fixtures),
       fmt(d.today.upcoming_with_research_models)+" avec un avis des modèles");
  tile("Paris conseillés","0","Aucun tant que rien n'est prouvé");
  if(route==="bilan"){
   tile("Paris fictifs terminés",fmt(d.simulation_paper.settled),
     fmt(d.simulation_paper.excluded)+" écartés (règles non vérifiées)");
   msg.textContent="Les gains et pertes ci-dessous sont fictifs (aucun argent réel). "+
     d.models.officially_settled_forecasts+" prévisions des modèles déjà vérifiées, dont "+
     d.models.NHL_settled+" en NHL. Aucun avantage prouvé pour l'instant.";
  }else if(route==="pourquoi"){
   tile("Modèles fiables","0","Pas encore assez de preuves");
   msg.textContent="Choisis un match pour voir ce que disent les modèles et pourquoi Revue ne conseille "+
     "pas de parier. Les chiffres des modèles ne sont pas des cotes de bookmaker.";
  }else{
   tile("Prévisions vérifiées",fmt(d.models.officially_settled_forecasts),
     "Comparées au score final officiel");
   msg.textContent="Aucun pari conseillé pour l'instant. Tu peux étudier les matchs du jour "+
     "et suivre le score des paris fictifs : un bon modèle n'est jamais une garantie.";
  }
  headline.textContent="ÉTAT DU JEU · DONNÉES À JOUR";
 }catch(e){fail("Les données ne sont pas assez récentes pour être sûres : "+e.message+
    " Tu peux tout consulter, mais sans aucun conseil de pari.");}
});
