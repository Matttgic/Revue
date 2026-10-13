/* Browser integration check: serve docs on 127.0.0.1:8765, then run with Playwright installed. */
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
 try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:8765/')?r.continue():r.abort());
  await page.goto('http://127.0.0.1:8765/nhl-joueurs.html');
  await page.waitForFunction(()=>document.querySelectorAll('#athlete option').length>0&&document.querySelectorAll('#hit-rates .card').length===3);
  assert.equal(await page.locator('#estimates .card').count(),3);
  assert.match(await page.locator('#estimates').innerText(),/EV[\s\S]*Données indisponibles/);
  await page.selectOption('#season','');
  // Pick a real player whose collected history exists; never mock real performance data.
  const collected=await page.evaluate(async()=>{
   const h=await fetch('./nhl-player-history.json').then(r=>r.json());
   return Object.keys(h.players).find(id=>h.players[id].games.length&&document.querySelector(`#athlete option[value="${id}"]`));
  });
  assert.ok(collected,'At least one real player history is required for integration verification');
  await page.selectOption('#athlete',collected);
  await page.waitForSelector('#performance-chart svg rect');
  for(const metric of ['shots','goals','assists','points']){
   await page.selectOption('#stat',metric);assert.ok(await page.locator('#game-rows tr').count());
  }
  await page.fill('#line','1');await page.locator('#line').dispatchEvent('change');
  assert.match(await page.locator('#history-status').innerText(),/Choisissez un seuil/);
  await page.fill('#line','0.5');await page.locator('#line').dispatchEvent('change');
  await page.selectOption('#venue','home');
  const places=await page.locator('#game-rows tr td:nth-child(3)').allTextContents();assert.ok(places.every(p=>p==='Domicile'));
  const opponents=await page.locator('#opponent option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));
  if(opponents.length){await page.selectOption('#opponent',opponents[0]);const names=await page.locator('#game-rows tr td:nth-child(2)').allTextContents();assert.ok(names.every(n=>n===opponents[0]));}
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'No page-level horizontal overflow: '+JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,id:e.id,cls:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right})).slice(0,12))));
  await page.route('**/nhl-player-history.json',r=>r.fulfill({status:503,body:'Unavailable'}));
  await page.reload();await page.waitForFunction(()=>document.querySelector('#history-status').textContent.includes('historique non chargé'));
  assert.match(await page.locator('#hit-rates').innerText(),/Données indisponibles/);
  assert.equal(await page.locator('#performance-chart svg').count(),0);
  await page.route('**/nhl-player-history.json',r=>r.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await page.reload();await page.waitForFunction(()=>document.querySelector('#history-status').textContent.includes('historique non chargé'));
  assert.match(await page.locator('#hit-rates').innerText(),/Données indisponibles/);
  assert.deepEqual(errors,[]);console.log('PASS: real graphs, 4 metrics, context filters, threshold, mobile, missing feed, no JS errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
