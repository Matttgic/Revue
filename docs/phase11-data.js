/* Phase 11 read-only source provenance view. No recommendations or real bets. */
"use strict";
document.addEventListener("DOMContentLoaded",async()=>{
 const $=id=>document.getElementById(id);
 const add=(root,tag,value)=>{const el=document.createElement(tag);el.textContent=String(value);root.append(el);return el;};
 const block=(sport,source)=>{
  const box=document.createElement("article");box.className="p11sport";
  add(box,"h2",sport);add(box,"strong",source);
  return box;
 };
 try{
  const resp=await fetch("./phase11-source-quality-latest.json",{cache:"no-store"});
  if(!resp.ok)throw Error("HTTP "+resp.status);
  const doc=await resp.json();
  if(doc.version!=="revue_phase11_source_quality_v1"||doc.real_bets_enabled!==false||
     doc.verified_EV_opportunities!==0||doc.model_probabilities_modified!==false||
     doc.paper_ledger_modified!==false||doc.source_parity_100_percent!==false)throw Error("Provenance non valide");
  $("p11-state").textContent="Audit "+new Date(doc.generated_at_utc).toLocaleString("fr-FR",{timeZone:"Europe/Paris",dateStyle:"short",timeStyle:"short"})+
   " · modèles toujours expérimentaux · "+doc.warnings.length+" avertissement(s).";
  const titles={
   NBA:"Données saison régulière courante : "+doc.sports.NBA.current_regular_season_teams+" équipes",
   NHL:"Gardiens effectivement titulaires : non vérifiés",
   MLB:"Lanceurs titulaires : non confirmés",
   FOOTBALL:"xG Opta sous licence : non connecté"
  };
  for(const [name,source] of Object.entries(doc.sports)){
   const box=block(name,titles[name]||"Source à vérifier"),ul=document.createElement("ul");
   for(const w of source.missing){add(ul,"li",w.replaceAll("_"," "));}
   if(!source.missing.length)add(ul,"li","Aucun manque enregistré pour ce contrôle");
   box.append(ul);$("p11-sports").append(box);
  }
  const h=doc.NHL_espn_observations;
  $("p11-goalie-stats").textContent=h.matched_upcoming_fixtures+" matchs rapprochés · "+h.goalie_sides_confirmed_by_espn+
   " mentions confirmées ESPN · "+h.goalie_sides_projected_by_espn+" pressenties · "+h.fixtures_with_both_espn_confirmed+" matchs avec deux mentions confirmées.";
  for(const x of h.fixtures.filter(x=>x.home_goalie||x.away_goalie)){
   const f=p=>p?p.name+" ("+(p.status==="confirmed"?"confirmé ESPN":"pressenti ESPN")+")":"non renseigné";
   add($("p11-goalies"),"li",x.away+" @ "+x.home+" : "+f(x.away_goalie)+" / "+f(x.home_goalie));
  }
  $("p11-pitcher-stats").textContent=doc.sports.MLB.official_probable_pitcher_sides_observed+
   " lanceurs probables observés, aucun titulaire confirmé. Source : "+doc.sports.MLB.official_probable_pitcher_source_status.replaceAll("_"," ")+".";
  try{
   const r=await fetch("./mlb-official-probable-pitchers-latest.json",{cache:"no-store"});
   if(!r.ok)throw Error("Indisponible");
   const m=await r.json();
   if(m.status==="official_MLB_probable_pitchers_observed_not_confirmed"&&
      m.real_bets_enabled===false&&m.model_recomputed===false){
    for(const x of m.rows){
     const f=p=>p?p.name+" (probable)":"non renseigné";
     add($("p11-pitchers"),"li",x.away+" @ "+x.home+" · "+f(x.away_pitcher)+" / "+f(x.home_pitcher));
    }
   }
  }catch(e){add($("p11-pitchers"),"li","Observations MLB indisponibles.");}
  $("p11-quarantine-count").textContent=doc.paper_market_quarantine.total+" entrées exclues des calculs du rendement.";
  for(const r of doc.paper_market_quarantine.records){
   add($("p11-quarantine"),"li",r.id+" · NHL "+r.event_id+" · "+r.market+" · règle non vérifiée, aucun règlement rétroactif");
  }
 }catch(e){$("p11-state").textContent="Rapport indisponible ou source non validée : "+e.message;}
});