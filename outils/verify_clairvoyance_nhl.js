"use strict";
/** Read-only, deterministic parity verifier for original NHL MC and NHL Ens. */
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_nhl.js");
function original(source,name){
  const m=new RegExp("^function\\s+"+name+"\\s*\\(","m").exec(source);
  if(!m)throw Error("Original NHL symbol unavailable: "+name);
  const end=source.indexOf("\n}",m.index);
  if(end<0)throw Error("No NHL source closing brace: "+name);
  return source.slice(m.index,end+2);
}
function reference(source,names,globals){
  const context=vm.createContext(globals);
  for(const name of names)vm.runInContext(original(source,name),context,{timeout:1100});
  return context;
}
function seeded(seed){
  let x=seed|0;return()=>{
    x^=x<<13;x^=x>>>17;x^=x<<5;
    return(x>>>0)/4294967296;
  };
}
function teamFixture(){
  return {
    BOS:{gf60:3.19,ga60:2.72,hv:{off:1.5,def:.6,fin:.7},
       edge:{zone_off:57,avg_spd:21.1},mp:{xgf_pct:53.9},
       pp:.226,pk:.835,cf5:.531,hdcf:54.5,gsax:9.4,sv:.916,
       hdsv:.925,gp:8,xgf5:1.5,sw:2.1},
    NYR:{gf60:2.92,ga60:3.12,hv:{off:.6,def:.3,fin:.4},
       edge:{zone_off:47,avg_spd:20.8},mp:{xgf_pct:47.7},
       pp:.185,pk:.795,cf5:.482,hdcf:47.8,gsax:-3.9,sv:.893,
       hdsv:.877,gp:9,xgf5:1.1,sw:-1.3},
  };
}
function verifyNHL(source,compare){
  const base=teamFixture();
  const withMp={teams:{
    BOS:{"5on5":{cfPct:.545,hdcfPct:.578,xgfPct:.551}},
    NYR:{"5on5":{cfPct:.469,hdcfPct:.443,xgfPct:.463}},
  }};
  const damaged={
    BOS:{frac:.04,goalie:{mp:.25,edge:.5},players:[{name:"RW",impact:.04}]},
    NYR:{frac:.03,goalie:{mp:.5,edge:.2},players:[{name:"G",impact:.03}]}
  };
  const cases=[
    {label:"NHL missing teams",teams:{},n:120},
    {label:"NHL baseline synthetic teams",teams:base,n:240},
    {label:"NHL full game 25k draws",teams:base,n:25000,ou:5.5},
    {label:"NHL same side unequal home rates",teams:base,n:400,ou:6.5},
    {label:"NHL full MoneyPuck live feeds",teams:base,mp:withMp,n:360,ou:5.5},
    {label:"NHL injury penalty and goalie attenuation",teams:base,injuries:damaged,n:360,ou:6.5},
    {label:"NHL full teams but first day cold-start",teams:{
       BOS:{...base.BOS,gp:0},NYR:{...base.NYR,gp:2}},n:400},
    {label:"NHL missing special teams, edge and goalie stats",teams:{
       BOS:{gf60:2.9,ga60:2.9,hv:{off:0,def:0,fin:0},gp:4},
       NYR:{gf60:2.8,ga60:2.7,hv:{off:0,def:0,fin:0},gp:5}},n:460,ou:5.5},
    {label:"NHL recent form context",teams:base,n:450,
      forms:{BOS:{mult:1.035,delta:.17,n:10,gfL:3.36},
             NYR:{mult:.98,delta:-.1,n:10,gfL:2.82}}},
    {label:"NHL static TONIGHT market fallback",teams:base,n:330,
     tonight:[{h:"BOS",a:"NYR",ou:7.5}]},
  ];
  function simulate(c,kind,i) {
    const r1=seeded(18719+i*977),r2=seeded(18719+i*977);
    const maths=Object.create(Math);maths.random=r1;
    const moneypuck=c.mp||{teams:{}};
    const inj=abbr=>c.injuries?.[abbr]||{frac:0,goalie:{mp:0,edge:0}};
    const form=(abbr)=>c.forms?.[abbr]||{mult:1,delta:null,n:0,gfL:null};
    const playerInj=abbr=>c.playerInjuries?.[abbr]||{penalty:0};
    const weights=c.weights||{mc:.50,bay:.20,elo:.30};
    const calibrator=c.calibrator||((p)=>p);
    const mh=(type,p,mkt,gp)=>mkt?.hML?{p:p*.85+.07,model:p,market:.50,kind:type,gp}:null;
    const legs=(price,isHome,mag)=>{
      const row=price?.pl?.[isHome?"-1.5":"+1.5"];
      return row?{fav:{dec:isHome?row.home:row.away},
                   dog:{dec:isHome?row.away:row.home}}:null;
    };
    const noVig=(a,b)=>((1/a)/((1/a)+(1/b)));
    const core=(model,market,type,gp)=>({p:model*.8+market*.2,model,market,kind:type,gp});
    const env={
      NHL:c.teams,MONEYPUCK:moneypuck,TONIGHT:c.tonight||[],
      _NHL_LG_PP:.205,_NHL_LG_PK:.795,_NHL_LG_GA60:2.9,
      HOCKEY_PL_MARGIN_LOGIT_SHIFT:.18,Math:maths,
      NHL_ENS:weights,sportCalibrate:calibrator,
      _nhlInjAdj:inj,_nhlFormFactor:form,
      computeInjuryImpact:playerInj,
      _hkBlendNhl:mh,_hkPlLegsAt:legs,_hkMktNoVig:noVig,_hkBlendCore:core,
    };
    const funcs=["_poisSampler","_hkMarginCal","_nhlLiveCf","nhlMC"];
    if(kind==="ens")funcs.push("nhlEns");
    const ctx=reference(source,funcs,env);
    for(const [nm,fn] of Object.entries({
      _nhlInjAdj:inj,_nhlFormFactor:form,computeInjuryImpact:playerInj,
      _hkBlendNhl:mh,_hkPlLegsAt:legs,_hkMktNoVig:noVig,_hkBlendCore:core,
    }))ctx[nm]=fn;
    const options={
      teams:c.teams,moneypuck,tonight:c.tonight||[],injury:inj,form,
      random:r2,weights,calibrator,playerInjury:playerInj,
      marketNhl:mh,plLegs:legs,marketNoVig:noVig,blendCore:core
    };
    if(kind==="mc"){
      compare(c.label,"frontend_nhl_mc",
        ctx.nhlMC("BOS","NYR",c.n,c.ou),
        own.nhlMonteCarlo("BOS","NYR",c.n,c.ou,options));
    }else{
      compare(c.label,"frontend_nhl_ensemble",
        ctx.nhlEns("BOS","NYR",c.ou,c.market),
        own.nhlEnsemble("BOS","NYR",c.ou,c.market,options));
    }
  }
  cases.forEach((c,i)=>simulate(c,"mc",i));
  const ensembles=[
    {label:"NHL ensemble missing team",teams:{}},
    {label:"NHL ensemble real teams default weights",teams:base,ou:5.5},
    {label:"NHL ensemble current MP, injured starter",teams:base,mp:withMp,
      injuries:damaged,ou:6.5},
    {label:"NHL ensemble weights and injury",teams:base,ou:5.5,
      playerInjuries:{BOS:{penalty:.035},NYR:{penalty:.015}},
      weights:{mc:.55,bay:.21,elo:.24},calibrator:p=>p*.94+.024},
    {label:"NHL ensemble ML market",teams:base,ou:5.5,
      market:{hML:-125,aML:110}},
    {label:"NHL ensemble O/U and puck lines",teams:base,ou:5.5,
      market:{hML:-150,aML:135,ouLine:5.5,
        pl:{"-1.5":{home:2.3,away:1.64},"+1.5":{home:1.55,away:2.65}}}},
    {label:"NHL ensemble early-season confidence",teams:{
      BOS:{...base.BOS,gp:1},NYR:{...base.NYR,gp:2}},ou:5.5},
  ];
  ensembles.forEach((c,i)=>simulate(c,"ens",100+i));
  return{mc:cases.length,ensemble:ensembles.length};
}
module.exports={verifyNHL};
