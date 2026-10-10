"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const $=x=>document.getElementById(x);
 const add=(root,tag,value)=>{const child=document.createElement(tag);child.textContent=String(value);root.append(child);};
 try{
  const urls=["./phase12-result-integrity-latest.json","./phase12-reconciliation-latest.json"];
  const responses=await Promise.all(urls.map(u=>fetch(u,{cache:"no-store"})));
  if(responses.some(r=>!r.ok))throw Error("Source indisponible");
  const [a,recon]=await Promise.all(responses.map(r=>r.json()));
  if(a.version!=="revue_phase12_settlement_audit_v1"||a.real_bets_enabled!==false||
     a.original_predictions_modified!==false||a.ROI!==null||
     recon.version!=="revue_phase12_settlement_reconciliation_v1"||
     recon.real_bets_enabled!==false)throw Error("Provenance non validée");
  $("s12-all").textContent=a.multisport.locked;
  $("s12-settled").textContent=a.multisport.settled;
  $("s12-nhl").textContent=a.NHL.settled+" / "+a.NHL.locked;
  $("s12-quarantine").textContent=a.unverified_historical_NHL_bookmaker_markets_excluded;
  $("s12-state").textContent="Audit "+new Date(a.generated_at_utc).toLocaleString("fr-FR",{timeZone:"Europe/Paris",dateStyle:"short",timeStyle:"short"})+" · "+a.status.replaceAll("_"," ")+". NBA/MLB/football : "+a.multisport.pending+" en attente. NHL : "+a.NHL.pending+" en attente. Brier et Log Loss calculés seulement après résultat final.";
  const bySports={};for(const [league,total] of Object.entries(a.multisport.by_league||{})){
   const sport=league==="NBA"?"NBA":league==="MLB"?"MLB":"FOOTBALL";
   bySports[sport]=(bySports[sport]||0)+total;
  }
  for(const [sport,n] of Object.entries(bySports))add($("s12-leagues"),"li",sport+" : "+n+" prévisions figées");
  add($("s12-leagues"),"li","NHL : "+a.NHL.locked+" prévisions dans le registre officiel séparé, "+a.NHL.settled+" réglées");
  $("s12-recovery").textContent="Dernier rapprochement : "+recon.newly_settled+" nouvelles prévisions réglées · "+recon.official_recovered_finals+" finales ESPN retrouvées · "+recon.cross_source_conflicts.length+" contradiction(s).";
  if(!a.multisport.overdue_examples?.length)add($("s12-overdue"),"li","Aucun résultat officiellement dû et non réglé dans le dernier audit.");
  for(const r of (a.multisport.overdue_examples||[]).slice(0,15)){
   add($("s12-overdue"),"li",r.league+" · "+r.event_id+" · "+r.hours+" h depuis le coup d'envoi · statut non vérifié");
  }
  if(a.audit_errors?.length){$("s12-state").textContent="ALERTE : contrôle d'intégrité en échec. Ne pas traiter les résultats comme validés.";}
 }catch(e){$("s12-state").textContent="Contrôle des résultats indisponible : "+e.message;}
});