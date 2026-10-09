"use strict";
/**
 * Source-conformant reconstruction of Clairvoyance's two NHL frontend models.
 *
 * Source: Purple-Wraith/clairvoyance-backend docs/app.html (nhlMC/nhlEns).
 * These are math kernels, NOT independently reconstructed injury/MoneyPuck
 * feeds. All external context is explicit for strictly repeatable source
 * parity tests; no automated bet / value recommendations.
 */
const LG_PP = .205, LG_PK = .795, LG_GA = 2.9;
const HOCKEY_PL_LOGIT_SHIFT = .18;
const NEUTRAL_FORM = () => ({mult:1,delta:null,n:0,gfL:null});
const NEUTRAL_INJURY = () => ({frac:0,goalie:{mp:0,edge:0}});
const EMPTY_PLAYER_INJURY = () => ({penalty:0});

function puckLineCal(p,shift=HOCKEY_PL_LOGIT_SHIFT) {
  if (!(p > 0 && p < 1)) return p;
  const logit=Math.log(p/(1-p))+shift;
  return 1/(1+Math.exp(-logit));
}
function poissonSampler(lambda,random=Math.random) {
  if(!(lambda>0)||lambda>60)
    throw new Error("NHL parity data must contain 0 < poisson lambda <= 60");
  const probabilities=[];
  let pk=Math.exp(-lambda),cdf=pk,k=0;
  probabilities.push(cdf);
  while(cdf<1-1e-12&&k<200){
    k++;pk*=lambda/k;cdf+=pk;probabilities.push(cdf);
  }
  const size=probabilities.length;
  return function() {
    const u=random();
    for(let i=0;i<size;i++)if(u<probabilities[i])return i;
    return size-1;
  };
}
function nhlLiveCf(team,moneypuck) {
  const row=moneypuck?.teams?.[team]?.["5on5"];
  if(!row)return null;
  return{cfPct:row.cfPct,hdcfPct:row.hdcfPct,xgfPct:row.xgfPct};
}

function nhlMonteCarlo(home,away,n=25000,marketOU,opts={}) {
  const teams=opts.teams||{};
  const h=teams[home],a=teams[away];
  if(!h||!a)return null;
  const random=opts.random||Math.random;
  const injury=opts.injury||NEUTRAL_INJURY;
  const form=opts.form||NEUTRAL_FORM;
  const moneypuck=opts.moneypuck||{teams:{}};
  const tonight=opts.tonight||[];
  const lgPP=opts.lgPP??LG_PP,lgPK=opts.lgPK??LG_PK,
        lgGa=opts.lgGa??LG_GA;
  const homeIce=.055;
  const hOff=h.gf60*(1+(h.hv.off-a.hv.def)*.11)*(1+h.hv.fin*.04);
  const aOff=a.gf60*(1+(a.hv.off-h.hv.def)*.11)*(1+a.hv.fin*.04);
  const hZone=h.edge?.zone_off||h.edge?.zoneOff||50,
        aZone=a.edge?.zone_off||a.edge?.zoneOff||50;
  const hZadj=1+(hZone-50)*.006,aZadj=1+(aZone-50)*.006;
  const hSpd=h.edge?.avg_spd||h.edge?.spd||20.5,
        aSpd=a.edge?.avg_spd||a.edge?.spd||20.5;
  const hSadj=1+(hSpd-20.5)*.01,aSadj=1+(aSpd-20.5)*.01;
  const hMP=h.mp?.xgf_pct||50,aMP=a.mp?.xgf_pct||50,mpAdj=(hMP-aMP)*.003;
  const stAdj=v=>Math.max(.94,Math.min(1.06,1+v));
  const hStAdj=stAdj(((h.pp??lgPP)-lgPP)*.5-((a.pk??lgPK)-lgPK)*.5);
  const aStAdj=stAdj(((a.pp??lgPP)-lgPP)*.5-((h.pk??lgPK)-lgPK)*.5);
  const sqAdj=v=>Math.max(.95,Math.min(1.05,1+v));
  const hCf=nhlLiveCf(home,moneypuck),aCf=nhlLiveCf(away,moneypuck);
  const hCfVal=hCf?.cfPct!=null?hCf.cfPct*100:(h.cf5!=null?h.cf5*100:50);
  const hHdcf=hCf?.hdcfPct!=null?hCf.hdcfPct*100:(h.hdcf??50);
  const aCfVal=aCf?.cfPct!=null?aCf.cfPct*100:(a.cf5!=null?a.cf5*100:50);
  const aHdcf=aCf?.hdcfPct!=null?aCf.hdcfPct*100:(a.hdcf??50);
  const hSqAdj=sqAdj(((hCfVal-50)+(hHdcf-50))/2*.002);
  const aSqAdj=sqAdj(((aCfVal-50)+(aHdcf-50))/2*.002);
  const injH=injury(home),injA=injury(away);
  const goalieRating=(team,inj)=>{
    const gsax=(team.gsax??0)*.7*(1-inj.mp);
    const save=team.sv!=null?(team.sv-.91)*100*.18*(1-inj.edge):0;
    const danger=team.hdsv!=null?(team.hdsv-.90)*100*.12*(1-inj.mp):0;
    return gsax+save+danger;
  };
  const hGoalie=Math.max(.87,Math.min(1.13,1-goalieRating(a,injA.goalie)/80)),
        aGoalie=Math.max(.87,Math.min(1.13,1-goalieRating(h,injH.goalie)/80));
  const gaAdj=v=>Math.max(.97,Math.min(1.03,1+v));
  const hGaAdj=gaAdj(((a.ga60??lgGa)-lgGa)*-.03),
        aGaAdj=gaAdj(((h.ga60??lgGa)-lgGa)*-.03);
  const hForm=form(home,h.gf60),aForm=form(away,a.gf60);
  const hLambda=Math.max(.4,hOff*.55*hGoalie*(1+homeIce)*hZadj*hSadj*
    (1+mpAdj)*hStAdj*hSqAdj*hGaAdj*hForm.mult*(1-injH.frac));
  const aLambda=Math.max(.4,aOff*.55*aGoalie*(1-homeIce*.5)*aZadj*aSadj*
    (1-mpAdj)*aStAdj*aSqAdj*aGaAdj*aForm.mult*(1-injA.frac));
  const ouLine=marketOU!=null?parseFloat(marketOU):
    (tonight.find(g=>(g.h===home&&g.a===away)||(g.h===away&&g.a===home))?.ou||5.5);
  let hw=0,aw=0,ot=0,hT=0,aT=0,rT=0,ov=0,rlH=0,rlA=0;
  const homeSampler=poissonSampler(hLambda,random);
  const awaySampler=poissonSampler(aLambda,random);
  for(let i=0;i<n;i++){
    const hg=homeSampler(),ag=awaySampler();
    hT+=hg;aT+=ag;rT+=hg+ag;
    if(hg+ag>ouLine)ov++;
    if(hg>ag){hw++;if(hg-ag>=2)rlH++;}
    else if(ag>hg){aw++;if(ag-hg>=2)rlA++;}
    else{ot++;hw+=.5;aw+=.5;}
  }
  const stEdge=(hStAdj-aStAdj)*100,sqEdge=(hSqAdj-aSqAdj)*100;
  const confidence=Math.min(1,Math.min(h.gp||0,a.gp||0)/5);
  const shrink=p=>.5+(p-.5)*confidence;
  const hwP=shrink(hw/n),overP=shrink(ov/n);
  const coverH=shrink(puckLineCal(rlH/n,opts.puckLineShift??HOCKEY_PL_LOGIT_SHIFT));
  const coverA=shrink(puckLineCal(rlA/n,opts.puckLineShift??HOCKEY_PL_LOGIT_SHIFT));
  return{
    hwP,awP:1-hwP,avgH:hT/n,avgA:aT/n,avgT:rT/n,
    overP,underP:1-overP,otP:ot/n,ouLine,
    rl15:coverH,rl15A:coverA,rlN:1-coverH,stEdge,sqEdge,
    gpConf:confidence,formH:hForm,formA:aForm,hA:home,aA:away,
    injAdj:{h:injH,a:injA}
  };
}

/**
 * NHL ensemble: linear components are not a true Elo signal. The "elo" slot
 * in Clairvoyance is only a situational-edge composite, as per source.
 * Market/line blending helper functions are injected to verify identical
 * behaviour. Their own upstream data/feed quality is separate.
 */
function nhlEnsemble(home,away,marketOU,mkt,opts={}){
  const teams=opts.teams||{},h=teams[home],a=teams[away];
  if(!h||!a)return{p:.5};
  const mc=nhlMonteCarlo(home,away,25000,marketOU,opts);
  if(!mc)return{p:.5};
  const xgf=(h.xgf5!=null&&a.xgf5!=null&&(h.xgf5+a.xgf5)>0)?
    h.xgf5/(h.xgf5+a.xgf5):.5;
  const gE=(h.gsax!=null&&a.gsax!=null)?
    (h.gsax*(1-(mc.injAdj?mc.injAdj.h.goalie.mp:0))-
     a.gsax*(1-(mc.injAdj?mc.injAdj.a.goalie.mp:0)))/100:0;
  const hvM=((h.hv.off-a.hv.def)+(h.hv.fin-a.hv.fin)*.5)*.04;
  const sm=((h.sw||0)-(a.sw||0))*.015;
  const mp=opts.moneypuck||{teams:{}};
  const mpH=(mp.teams&&mp.teams[home]&&mp.teams[home]["5on5"])||h.mp;
  const mpA=(mp.teams&&mp.teams[away]&&mp.teams[away]["5on5"])||a.mp;
  const normalize=v=>v==null?null:(v<=1?v*100:v);
  const mpHv=normalize(mpH?.xgfPct??mpH?.xgf_pct),
        mpAv=normalize(mpA?.xgfPct??mpA?.xgf_pct);
  const mpBoost=(mpHv!=null&&mpAv!=null)?(mpHv-mpAv)*.004:0;
  const edgeBoost=(h.edge?.avg_spd||20.5)-(a.edge?.avg_spd||20.5);
  const edgeRaw=gE*.19+sm*.625+hvM*.625+mpBoost+edgeBoost*.005;
  const weights=opts.weights||{mc:.50,bay:.20,elo:.30};
  const blended=mc.hwP*(.64/.50)*weights.mc+
                xgf*(.26/.20)*weights.bay+
                edgeRaw*(1/.30)*weights.elo+.04;
  const cal=opts.calibrator||((p)=>p);
  let p=cal(Math.min(.92,Math.max(.08,blended)),"NHL");
  p=.5+(p-.5)*(mc.gpConf??1);
  const playerInjury=opts.playerInjury||EMPTY_PLAYER_INJURY;
  const injH=playerInjury(home,"nhl"),injA=playerInjury(away,"nhl");
  p=Math.min(.92,Math.max(.08,p-injH.penalty+injA.penalty));
  const pModel=p;
  const gp=Math.min(h.gp||0,a.gp||0);
  const marketNhl=opts.marketNhl||(()=>null);
  const marketNoVig=opts.marketNoVig||(()=>null);
  const plLegs=opts.plLegs||(()=>null);
  const blendCore=opts.blendCore||(()=>null);
  const mbML=marketNhl("ML",pModel,mkt,gp);
  if(mbML)p=mbML.p;
  const mbOU=(mkt&&mkt.ouLine!=null&&Math.abs(parseFloat(mkt.ouLine)-mc.ouLine)<.01)?
    marketNhl("OU",mc.overP,mkt,gp):null;
  let mbPL=null,favCover=null;
  try{
    const favHome=p>=.5;
    favCover=favHome?mc.rl15:mc.rl15A;
    if(mkt&&mkt.pl&&favCover!=null&&isFinite(favCover)){
      const legs=plLegs({pl:mkt.pl},favHome,1.5);
      if(legs){const pk=marketNoVig(legs.fav.dec,legs.dog.dec);
        if(pk!=null)mbPL=blendCore(favCover,pk,"PL",gp);}
    }
  }catch(e){mbPL=null;}
  return{
    p,pModel,mc:mc.hwP,bay:xgf,elo:Math.min(1,Math.max(0,.5+edgeRaw)),
    xgf,gE,hvM,sm,mcD:mc,injH,injA,
    ouP:mbOU?mbOU.p:mc.overP,
    favCoverP:mbPL?mbPL.p:favCover,
    mkt:{ml:mbML,ou:mbOU,pl:mbPL}
  };
}

module.exports={nhlMonteCarlo,nhlEnsemble,poissonSampler,puckLineCal,nhlWeather:null};
