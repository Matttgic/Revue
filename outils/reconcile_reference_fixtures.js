"use strict";
const fs=require("node:fs"),path=require("node:path");
const REFERENCE="https://raw.githubusercontent.com/Purple-Wraith/clairvoyance-backend/main/docs/data.json";
const sports=["nhl","nba","mlb"];
function stamp(s){if(typeof s!=="string"||!/(Z|[+-]\d\d:\d\d)$/.test(s))return NaN;return Date.parse(s);}
function id(x){return String(x??"").toUpperCase().replace(/[^A-Z0-9]/g,"");}
function reconcile(ref,local,now=Date.now()){
 if(!ref||!Array.isArray(local?.events)||!Number.isFinite(stamp(ref.generated))||!Number.isFinite(stamp(local.generated_at_utc)))throw Error("Source invalide");
 if(stamp(ref.generated)>now+120000||stamp(local.generated_at_utc)>now+120000)throw Error("Future data");
 const leagues={},matches=[];
 for(const sport of sports){
  const l=sport.toUpperCase(),up=ref[sport]||{};
  if(!Array.isArray(up.today)||!Array.isArray(up.tomorrow))throw Error("Missing source schedule "+l);
  const candidates=new Map();
  for(const e of [...up.today,...up.tomorrow]){
   if(e.id==null||!Number.isFinite(stamp(e.date)))continue;
   const key=String(e.id);
   const existing=candidates.get(key);
   if(existing&&(id(existing.home)!==id(e.home)||id(existing.away)!==id(e.away)||stamp(existing.date)!==stamp(e.date)))throw Error("Contradictory upstream event");
   candidates.set(key,e);
  }
  let matched=0,disagreements=0,overlap=0;
  const seen=new Set(),ours=local.events.filter(e=>e.league===l);
  for(const e of ours){
   const k=String(e.event_id);if(seen.has(k))throw Error("Duplicate local id");seen.add(k);
   const source=candidates.get(k);if(!source)continue;
   overlap++;
   const names=id(source.home)===id(e.home)&&id(source.away)===id(e.away);
   const time=Number.isFinite(stamp(e.start_utc))&&Math.abs(stamp(source.date)-stamp(e.start_utc))<=60000;
   const same=names&&time;if(same)matched++;else disagreements++;
   matches.push({league:l,event_id:k,teams_equal:names,time_equal:time,
    status:same?"fixture_verified":"identity_disagreement",
    model_output_parity_verified:false,price_parity_verified:false});
  }
  leagues[l]={reference_count:candidates.size,revue_count:ours.length,overlapping_ids:overlap,
   matched_exact_fixture:matched,identity_disagreements:disagreements,verified_model_outputs:0};
 }
 return{status:"reference_vs_revue_factual_fixture_match",generated_at_utc:new Date(now).toISOString(),
  reference_generated_at_utc:new Date(stamp(ref.generated)).toISOString(),
  revue_generated_at_utc:new Date(stamp(local.generated_at_utc)).toISOString(),
  stale:now-stamp(ref.generated)>12*3600000||now-stamp(local.generated_at_utc)>12*3600000,
  source:"Purple-Wraith/clairvoyance-backend docs/data.json",
  leagues,matches,exact_fixture_matches:matches.filter(x=>x.status==="fixture_verified").length,
  model_probability_parity_proven:0,bookmaker_prices_included:false,real_bets:false,
  note:"Verified event IDs, normalized team codes and UTC kickoff only. Not proof of shared model inputs or identical probabilities."};
}
async function main(){
 const root=path.resolve(process.argv[2]||"docs");
 const res=await fetch(REFERENCE,{signal:AbortSignal.timeout(20000)});
 if(!res.ok)throw Error("Upstream HTTP "+res.status);
 const body=await res.text();if(body.length>2500000)throw Error("Unexpected source size");
 const upstream=JSON.parse(body),local=JSON.parse(fs.readFileSync(path.join(root,"match-center-latest.json"),"utf8"));
 const result=reconcile(upstream,local);
 fs.writeFileSync(path.join(root,"clairvoyance-fixture-reconciliation.json"),JSON.stringify(result,null,2)+"\n");
 process.stdout.write("Shared strict fixtures: "+result.exact_fixture_matches+"; model parity unknown.\n");
}
if(require.main===module)main().catch(e=>{process.stderr.write(String(e.stack)+"\n");process.exitCode=1;});
module.exports={reconcile};