"use strict";
/** Same arithmetic/selection as original docs/app.html _modelLineForProp.
 * Data cache, stat label normalizer, defensive factor and half-line function
 * are passed in as dependencies; never invent missing stats or prices.
 */
function modelLineForProp(sport,player,statLabel,opponent,{
  caches={},normalize=label=>label,defFactor=()=>({factor:0}),
  halfLine=value=>Math.floor(value)+.5
}={}) {
 const cache=sport==="nba"?caches.nba:
             sport==="wnba"?caches.wnba:
             sport==="nhl"?caches.nhl:null;
 if(!cache)return null;
 const row=cache[(player||"").toLowerCase().trim()];
 if(!row)return null;
 const field=normalize(statLabel);
 const factor=opponent?defFactor(sport.toUpperCase(),opponent).factor:0;
 let average=null;
 if(field==="pra")average=(row.ppg||0)+(row.rpg||0)+(row.apg||0);
 else if(field==="pts")average=row.ppg;
 else if(field==="reb")average=row.rpg;
 else if(field==="ast")average=row.apg;
 else if(field==="goal")average=row.gpg;
 else if(field==="shot")average=row.shpg;
 if(average==null||!average)return null;
 return parseFloat(halfLine(Math.max(.05,average*(1+factor))));
}
module.exports={modelLineForProp};
