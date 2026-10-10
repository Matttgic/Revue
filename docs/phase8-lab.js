/* Filter old technical screens by name without altering any sports data. */
"use strict";
document.addEventListener("DOMContentLoaded",()=>{
 const input=document.getElementById("lab-filter"),status=document.getElementById("lab-filter-count");
 if(!input||!status)return;
 const links=[...document.querySelectorAll(".arc-lab-grid a.arc-lab-link")];
 const clean=x=>x.toLocaleLowerCase("fr-FR").normalize("NFD").replace(/[\u0300-\u036f]/g,"");
 const render=()=>{const q=clean(input.value).trim();let shown=0;
  for(const link of links){const visible=!q||clean(link.textContent).includes(q);
   link.hidden=!visible;if(visible)shown++;}
  status.textContent=shown+" / "+links.length+" outils";
 };
 input.addEventListener("input",render);render();
});
