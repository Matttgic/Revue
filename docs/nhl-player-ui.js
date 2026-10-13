'use strict';
(()=>{
 const $=id=>document.getElementById(id),A=window.NHLAnalytics;
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const missing='Données indisponibles';
 let profiles=[],history={players:{}},loadError=false;
 const option=(select,value,text)=>{const o=node('option',text);o.value=value;select.append(o);};
 function fillOpponents(){
  const saved=$('opponent').value;
  const games=history.players[$('athlete').value]?.games||[];
  $('opponent').replaceChildren();option($('opponent'),'','Tous');
  const opponents=[...new Set(games.filter(g=>!$('season').value||String(g.season)===$('season').value).map(g=>g.opponent).filter(Boolean))].sort();
  opponents.forEach(o=>option($('opponent'),o,o));
  if(opponents.includes(saved))$('opponent').value=saved;
  $('opponent').disabled=!opponents.length;
  $('venue').disabled=!games.some(g=>typeof g.home==='boolean');
 }
 function box(title,value,note){const b=node('div',undefined,'card');b.append(node('span',title),node('strong',value),node('p',note));return b;}
 function svgNode(tag,attrs,text){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n;}
 function chart(games,metric,line){
  $('performance-chart').replaceChildren();$('game-rows').replaceChildren();
  if(!games.length){$('performance-chart').append(node('p',missing));return;}
  // The graph and L20 use the same most recent 20 selected appearances.
  const recent=games.slice(0,20),shown=[...recent].reverse();
  const max=Math.max(1,line,...shown.map(g=>A.finite(g[metric])?g[metric]:0));
  const svg=svgNode('svg',{viewBox:'0 0 860 260',class:'chart',role:'img','aria-label':'Performances des 20 dernières apparitions sélectionnées. Tableau accessible ci-dessous.'});
  const y=value=>210-value/max*175;
  svg.append(svgNode('line',{x1:40,x2:850,y1:y(line),y2:y(line),class:'threshold'}),svgNode('text',{x:40,y:20},'Seuil Over : '+line));
  shown.forEach((g,i)=>{
   const x=50+i*790/shown.length,w=790/shown.length-7,v=g[metric];
   if(A.finite(v)){
    const bar=svgNode('rect',{x,y:y(v),width:w,height:Math.max(1,210-y(v)),rx:3,fill:v>line?'#c9f984':'#64758c'});
    bar.append(svgNode('title',{},`${g.date.slice(0,10)} · ${g.opponent||missing} : ${v}`));svg.append(bar,svgNode('text',{x,y:y(v)-6},v));
   }else svg.append(svgNode('text',{x,y:190},'N/D'));
   svg.append(svgNode('text',{x,y:230,transform:`rotate(35 ${x} 230)`},g.date.slice(5,10)));
  });
  $('performance-chart').append(svg);
  recent.forEach(g=>{const tr=node('tr');[g.date.slice(0,10),g.opponent||missing,g.home===true?'Domicile':g.home===false?'Extérieur':missing,A.finite(g[metric])?g[metric]:missing,A.finite(g[metric])?(g[metric]>line?'Au-dessus':'En dessous'):missing].forEach(v=>tr.append(node('td',v)));$('game-rows').append(tr);});
 }
 function render(){
  const pid=$('athlete').value,p=profiles.find(p=>p.player_id===pid),entry=history.players[pid],metric=$('stat').value,line=Number($('line').value);
  $('hit-rates').replaceChildren();$('estimates').replaceChildren();
  if(!$('line').value||!A.finite(line)||line%1!==.5||line>50.5){$('history-status').textContent='Choisissez un seuil entre 0,5 et 50,5, par pas de 1 (sans égalité possible).';chart([],metric,0);return;}
  const games=A.sample(entry?.games,metric,{venue:$('venue').value,opponent:$('opponent').value,season:$('season').value});
  $('history-status').textContent=loadError?missing+' — historique non chargé.':!entry?missing+' — historique pas encore collecté.':`${games.length} apparitions dans la sélection · Source : ESPN · Collecte : ${entry.attempted_at||missing} · ${entry.status==='ok'?'deux saisons interrogées':'collecte partielle ou indisponible'}`;
  if(entry?.attempted_at&&Date.now()-Date.parse(entry.attempted_at)>6*3600000)$('history-status').textContent+=' · Historique ancien : actualisation nécessaire';
  for(const size of [5,10,20]){const r=A.hitRate(games,metric,line,size);$('hit-rates').append(box('Fréquence historique L'+size,r.rate===null?missing:(100*r.rate).toLocaleString('fr-FR',{maximumFractionDigits:1})+' %',`${r.hits}/${r.n} matchs exploitables · ${r.missing} statistique(s) manquante(s)`));}
  const rate=p?.projected_rates?.[metric],prob=A.poisson(rate,line);
  $('estimates').append(box('Projection saisonnière',A.finite(rate)?rate.toLocaleString('fr-FR'):missing,'Moyenne régularisée du modèle existant ; les filtres historiques ne la recalculent pas.'),box('Probabilité modélisée',prob===null?missing:(100*prob).toLocaleString('fr-FR',{maximumFractionDigits:1})+' %','Poisson expérimental non calibré. Disponibilité, adversaire et minutes non intégrés.'),box('EV',missing,'Désactivée : probabilité insuffisamment validée et absence de cote joueur vérifiée.'));
  chart(games,metric,line);
 }
 function setup(){
  if(!profiles.length){render();return;}
  const old=$('athlete').value;
  $('athlete').replaceChildren();profiles.forEach(p=>option($('athlete'),p.player_id,`${p.name} · ${p.team}`));
  if(profiles.some(p=>p.player_id===old))$('athlete').value=old;
  const year=Number(String(window.nhlProfileSeason).slice(-4));
  const selected=$('season').value;
  $('season').replaceChildren();option($('season'),String(year),`${year-1}-${year} · régulière`);option($('season'),String(year-1),`${year-2}-${year-1} · régulière`);option($('season'),'','Deux saisons · régulières');
  if(selected)$('season').value=selected;
  fillOpponents();render();
 }
 window.addEventListener('nhl-profiles',event=>{
  window.nhlProfileSeason=event.detail.season;
  const map=new Map();Object.values(event.detail.teams||{}).flat().forEach(p=>{if(!map.has(String(p.player_id))||p.current_team_observed)map.set(String(p.player_id),{...p,player_id:String(p.player_id)});});profiles=[...map.values()].sort((a,b)=>a.name.localeCompare(b.name));setup();
 });
 ['athlete','season'].forEach(id=>$(id).addEventListener('change',()=>{fillOpponents();render();}));
 ['stat','line','venue','opponent'].forEach(id=>$(id).addEventListener('change',()=>{if(id==='stat')$('line').value=$('stat').value==='shots'?'2.5':'0.5';render();}));
 fetch('./nhl-player-history.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json();}).then(data=>{if(!data||!data.players||typeof data.players!=='object'||Array.isArray(data.players))throw Error('Unsupported history schema');history=data;setup();}).catch(()=>{loadError=true;setup();});
})();
