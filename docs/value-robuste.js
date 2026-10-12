(function(root){
  'use strict';
  const books={betclic_fr:'Betclic',pmu_fr:'PMU',unibet_fr:'Unibet',winamax_fr:'Winamax'};
  const number=(n,d=2)=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('fr-FR',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
  function view(data,now=Date.now()){
    const at=Date.parse(data.scan_at);
    const age=(now-at)/1000;
    const fresh=data.status==='fresh_snapshot'&&Number.isFinite(age)&&age>=0&&age<=data.rule.max_quote_age_seconds;
    return {fresh,candidates:fresh?(data.candidates||[]).filter(c=>{
      const quote=Date.parse(c.quote_at),start=Date.parse(c.start_utc);
      return Number.isFinite(quote)&&quote<=now&&(now-quote)/1000<=data.rule.max_quote_age_seconds
        &&Number.isFinite(start)&&(start-now)/1000>data.rule.kickoff_buffer_seconds;
    }):[],watchlist:fresh?data.watchlist||[]:[]};
  }
  function selection(c){
    if(c.market==='h2h')return c.side==='draw'?'Match nul':`Victoire ${c.side==='home'?c.home:c.away}`;
    return `${c.side==='over'?'Plus':'Moins'} de ${number(c.line,1)} buts`;
  }
  if(typeof module!=='undefined')module.exports={view,selection,number};
  if(typeof document==='undefined')return;
  function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
  function table(id,rows,headers,cells){
    const host=document.getElementById(id);host.replaceChildren();
    if(!rows.length){host.append(el('p','Aucune ligne disponible.','empty'));return;}
    const table=el('table');const head=el('thead'),hr=el('tr');headers.forEach(h=>hr.append(el('th',h)));head.append(hr);table.append(head);
    const body=el('tbody');rows.forEach(r=>{const tr=el('tr');cells(r).forEach(c=>tr.append(el('td',c)));body.append(tr);});table.append(body);host.append(table);
  }
  function render(data){
    const v=view(data);
    document.getElementById('status').textContent=v.fresh?'Relevé récent · vérifier le prix chez le bookmaker':'En attente d’un relevé récent · aucun candidat actuel';
    document.getElementById('stamp').textContent=data.scan_at?new Date(data.scan_at).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})+' · heure de Paris':'Premier relevé complet attendu';
    const p=data.performance;
    document.getElementById('n-candidates').textContent=String(v.candidates.length);
    document.getElementById('n-settled').textContent=String(p.settled);
    document.getElementById('pnl').textContent=number(p.profit_units)+' u';
    document.getElementById('roi').textContent=p.roi_pct===null?'Pas de résultat':number(p.roi_pct)+' %';
    document.getElementById('pending').textContent=`${p.pending} paris papier en attente · recul maximal : ${number(p.max_drawdown_units)} u`;
    const cards=document.getElementById('candidates');cards.replaceChildren();
    v.candidates.forEach(c=>{const card=el('article',undefined,'card');card.append(el('p',c.league,'eyebrow'),el('h3',`${c.home} – ${c.away}`),el('p',selection(c)),el('p',`${books[c.bookmaker]||c.bookmaker} · cote ${number(c.bookmaker_price)}`,'price'),el('p',`Cote minimale : ${number(c.minimum_required_price,3)} · écart conservateur : ${number(c.edge_min*100)} %`),el('p',`Référence : ${c.reference_evidence.map(r=>r.bookmaker).join(', ')} · mise papier : 1 u`,'muted'),el('p',new Date(c.start_utc).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})));cards.append(card);});
    if(!v.candidates.length)cards.append(el('p',v.fresh?'Aucune cote ne remplit les conditions. Le journal attend un prochain relevé.':'Les prix du dernier relevé ne sont plus assez récents pour proposer un candidat.','empty'));
    table('watchlist',v.watchlist,['Rencontre','Sélection','Bookmaker','Cote observée','Cote minimale','Écart conservateur'],c=>[`${c.home} – ${c.away}`,selection(c),books[c.bookmaker]||c.bookmaker,number(c.bookmaker_price),number(c.minimum_required_price,3),number(c.edge_min*100)+' %']);
    table('journal',(data.bets||[]).slice().reverse().slice(0,50),['Rencontre','Sélection','Cote figée','État','Résultat'],c=>[`${c.home} – ${c.away}`,selection(c),number(c.bookmaker_price),({pending:'En attente',won:'Gagné',lost:'Perdu',push:'Remboursé'})[c.status]||c.status,c.profit_units===undefined?'—':number(c.profit_units)+' u']);
    const diag=document.getElementById('diagnostics');diag.replaceChildren();
    const names={no_complete_fresh_sharp_reference:'Référence complète et récente manquante',below_robust_threshold:'Écart inférieur au seuil',stale_quote:'Prix trop ancien',incomplete_or_unsupported_market:'Marché incomplet ou non pris en charge',wrong_period_or_market:'Période ou marché incompatible',unmatched_event:'Rencontre non rattachée',started_or_too_close:'Rencontre commencée ou trop proche'};
    Object.entries(data.diagnostics||{}).forEach(([k,n])=>diag.append(el('li',`${names[k]||k} : ${n}`)));
    if(!diag.children.length)diag.append(el('li','Le relevé complet alimentera ce diagnostic.'));
  }
  let latest;
  async function load(){
    const button=document.getElementById('refresh');button.disabled=true;
    try{const response=await fetch('value-robuste-latest.json?t='+Date.now(),{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);latest=await response.json();render(latest);}
    catch(error){document.getElementById('status').textContent='Données indisponibles. Réessayer après la prochaine publication.';}
    finally{button.disabled=false;}
  }
  document.getElementById('refresh').addEventListener('click',load);
  setInterval(()=>{if(latest)render(latest);},30000);load();
})(typeof window==='undefined'?globalThis:window);
