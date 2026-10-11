/* REVUE · effets « console de poche », chargés sur toutes les pages.
 * - bouton FX : coupe animations et lignes CRT (préférence mémorisée dans ce navigateur) ;
 * - volet pixel entre deux pages du site ;
 * - compteurs qui défilent jusqu'à leur valeur (le texte final reste celui des données) ;
 * - apparition des blocs au défilement ;
 * - menus [data-menu] pilotables au clavier (↑ ↓ Entrée).
 * Respecte prefers-reduced-motion. N'écrit que du texte (pas de HTML injecté).
 */
"use strict";
(function(){
  const root=document.documentElement;
  const reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  try{if(localStorage.getItem("revue-fx")==="off")root.classList.add("fx-off");}catch(e){}
  const motion=()=>!reduced&&!root.classList.contains("fx-off");

  function addFxToggle(){
    const bar=document.querySelector(".rv-top-inner");
    if(!bar||bar.querySelector(".px-fx"))return;
    const b=document.createElement("button");
    b.type="button";b.className="px-fx";b.textContent="FX";
    b.title="Activer ou couper les animations et l'effet écran rétro";
    b.setAttribute("aria-label","Effets visuels");
    b.setAttribute("aria-pressed",String(!root.classList.contains("fx-off")));
    b.addEventListener("click",()=>{
      const off=root.classList.toggle("fx-off");
      b.setAttribute("aria-pressed",String(!off));
      try{localStorage.setItem("revue-fx",off?"off":"on");}catch(e){}
    });
    bar.append(b);
  }

  /* Volet pixel ------------------------------------------------------------ */
  function wipe(mode){
    const w=document.createElement("div");
    w.className="px-wipe "+mode;w.setAttribute("aria-hidden","true");
    for(let i=0;i<12;i++){const c=document.createElement("i");c.style.animationDelay=(i*14)+"ms";w.append(c);}
    document.body.append(w);
    return w;
  }
  function wipeOut(){
    document.querySelectorAll(".px-wipe").forEach(x=>x.remove());
    if(!motion())return;
    const w=wipe("px-off");setTimeout(()=>w.remove(),520);
  }
  function internal(a,ev){
    if(ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return false;
    if(a.target&&a.target!=="_self")return false;
    if(a.hasAttribute("download"))return false;
    const url=new URL(a.href,location.href);
    if(url.origin!==location.origin)return false;
    if(url.pathname===location.pathname&&url.search===location.search)return false;
    return /\.html?$|\/$/.test(url.pathname);
  }
  document.addEventListener("click",ev=>{
    const a=ev.target.closest&&ev.target.closest("a[href]");
    if(!a||!motion()||!internal(a,ev))return;
    ev.preventDefault();
    wipe("px-on");
    setTimeout(()=>{location.href=a.href;},250);
  });
  window.addEventListener("pageshow",wipeOut);

  /* Compteurs façon score -------------------------------------------------- */
  const COUNTERS=".value,.p14-metric strong,.arc-odds,[data-px-count]";
  const NUM=/-?\d[\d   ]*(?:[.,]\d+)?/;
  function animateNumber(el){
    const target=el.textContent;
    const m=target.match(NUM);
    if(!m||!motion())return;
    const raw=m[0];
    const comma=raw.includes(",");
    const grouped=/[   ]/.test(raw.trim());
    const clean=raw.replace(/[   ]/g,"").replace(",",".");
    const end=parseFloat(clean);
    if(!Number.isFinite(end)||end===0)return;
    const dec=(clean.split(".")[1]||"").length;
    const fmt=v=>(comma||grouped)
      ?v.toLocaleString("fr-FR",{minimumFractionDigits:dec,maximumFractionDigits:dec})
      :v.toFixed(dec);
    const before=target.slice(0,m.index),after=target.slice(m.index+raw.length);
    clearInterval(el._pxTimer);
    let step=0;const steps=10;
    el._pxTimer=setInterval(()=>{
      step++;
      const text=step>=steps?target:before+fmt(end*step/steps)+after;
      el._pxText=text;el.textContent=text;
      if(step>=steps)clearInterval(el._pxTimer);
    },45);
  }
  function watchCounters(){
    const seen=new WeakSet();
    const check=el=>{
      if(!(el instanceof Element)||!el.matches(COUNTERS))return;
      if(el.textContent===el._pxText)return;
      seen.add(el);animateNumber(el);
    };
    document.querySelectorAll(COUNTERS).forEach(check);
    new MutationObserver(list=>{
      for(const r of list){
        const el=r.target.nodeType===3?r.target.parentElement:r.target;
        if(el)check(el);
        r.addedNodes&&r.addedNodes.forEach(n=>{if(n.nodeType===1){check(n);n.querySelectorAll&&n.querySelectorAll(COUNTERS).forEach(check);}});
      }
    }).observe(document.body,{subtree:true,childList:true,characterData:true});
  }

  /* Apparition au défilement ---------------------------------------------- */
  function reveal(){
    if(!("IntersectionObserver" in window)||!motion())return;
    const items=document.querySelectorAll(".arc-v3-section,.arc-section,.arc-surface,.arc-kpi,.px-menu-item,.p14-brief,main>section");
    const io=new IntersectionObserver(entries=>{
      for(const e of entries)if(e.isIntersecting){e.target.classList.add("px-in");io.unobserve(e.target);}
    },{rootMargin:"0px 0px -8% 0px"});
    const fold=window.innerHeight;
    items.forEach((el,i)=>{
      if(el.getBoundingClientRect().top<fold)return;          // déjà visible : rien à cacher
      el.classList.add("px-reveal");el.style.transitionDelay=Math.min(i%6,5)*40+"ms";io.observe(el);
    });
    // Sécurité : rien ne reste caché, même si l'observateur ne se déclenche pas.
    setTimeout(()=>document.querySelectorAll(".px-reveal:not(.px-in)").forEach(el=>el.classList.add("px-in")),2500);
  }

  /* Menus au clavier ------------------------------------------------------- */
  function menus(){
    document.querySelectorAll("[data-menu]").forEach(menu=>{
      menu.addEventListener("keydown",ev=>{
        if(ev.key!=="ArrowDown"&&ev.key!=="ArrowUp")return;
        const links=[...menu.querySelectorAll("a[href]")];
        const i=links.indexOf(document.activeElement);
        const next=ev.key==="ArrowDown"?(i+1)%links.length:(i-1+links.length)%links.length;
        links[next].focus();ev.preventDefault();
      });
    });
  }

  function start(){addFxToggle();watchCounters();reveal();menus();}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();
