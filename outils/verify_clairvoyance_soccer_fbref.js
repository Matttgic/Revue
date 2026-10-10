"use strict";
/** Read-only source comparisons for _socXGFromFBref and UEFA blending. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const own=require("../modeles/reproduction/frontend_clairvoyance_soccer_fbref.js");
function verifySoccerFBref(source,compare){
 const adv={default:.07,pl:.10,liga:.09,ita:.08,bl:.12,cl:.03};
 const params={domesticLeagues:["pl","liga","ita","bl"],weightMax:.65,rampGames:12};
 const rows={
  pl:{teams:{
   "Manchester City":{mp:30,xg:70,xga:29,gf:67,ga:25,poss:65,xag:45,
    shots_pg:18,sot_pg:7,homeSplit:{games:14,gf:2.7,ga:.7},
    awaySplit:{games:16,gf:1.8,ga:1.2},recentForm:{games:5,gf:2,ga:.8},
    matchLog:[{opponent:"Arsenal",gf:1,ga:1}],gamesPlayedThisSeason:30},
   "Arsenal":{mp:24,xg:55,xga:21,gf:48,ga:22,poss:59,xag:27,
    shots_pg:14,sot_pg:4,homeSplit:{games:2,gf:3,ga:1},
    awaySplit:{games:3,gf:1.4,ga:.8},recentForm:{games:3,gf:1.5,ga:1},
    gamesPlayedThisSeason:24},
   "Chelsea":{mp:0,xg:1,xga:2,gf:0,ga:0,poss:52,xag:0,
    shots_pg:5,sot_pg:1,homeSplit:null,awaySplit:null,
    gamesPlayedThisSeason:0}
  }},
  cl:{teams:{
   "Manchester City":{mp:5,xg:11,xga:3,gf:13,ga:4,poss:63,xag:6,shots_pg:14,
    sot_pg:6,homeSplit:{games:3,gf:3,ga:.5},
    awaySplit:{games:3,gf:1.8,ga:1.2},
    recentForm:{games:4,gf:3,ga:1},gamesPlayedThisSeason:5},
   "Arsenal":{mp:2,xg:4,xga:2,gf:3,ga:2,poss:53,xag:1,
    shots_pg:13,sot_pg:5,homeSplit:null,awaySplit:null,
    gamesPlayedThisSeason:2},
   "Bayern Munich":{mp:1,xg:1,xga:1,gf:1,ga:1,poss:48,xag:1,
    shots_pg:10,sot_pg:3,homeSplit:null,awaySplit:null,
    gamesPlayedThisSeason:1}
  }},
  liga:{teams:{"Real Madrid":{mp:23,xg:49,xga:23,gf:51,ga:26,
    poss:58,xag:28,shots_pg:16,sot_pg:6,homeSplit:null,
    awaySplit:null,gamesPlayedThisSeason:23}}},
  bl:{teams:{"Bayern Munich":{mp:24,xg:67,xga:18,gf:73,ga:22,
    poss:66,xag:42,shots_pg:17,sot_pg:7,homeSplit:null,
    awaySplit:null,gamesPlayedThisSeason:24}}}
 };
 let count=0;
 const names=["Manchester City","manchester","MAN","Arsenal","Chelsea",
              "Bayern Munich","Bayern","Real Madrid","Real","Unknown","",null];
 const variants=[
  rows,
  {},
  {cl:{teams:rows.cl.teams}},
  {pl:{teams:rows.pl.teams}},
  {pl:{teams:rows.pl.teams},cl:{teams:rows.cl.teams}},
  {bl:{teams:rows.bl.teams},cl:{teams:rows.cl.teams}},
  {liga:{teams:rows.liga.teams}},
 ];
 for(const [vi,data] of variants.entries()){
  for(const name of names){
   const env={
     window:{__CV_FBREF:data},
     _SOC_HOME_ADV:adv,
     _CL_DOMESTIC_LEAGUES:params.domesticLeagues,
     _CL_WEIGHT_MAX:params.weightMax,
     _CL_WEIGHT_RAMP_GAMES:params.rampGames,
   };
   const cx=vm.createContext(env);
   for(const fn of ["_socHomeAdv","_socTeamHomeAwaySplit",
                    "_socXGFromFBref","_clDomesticContext","_socXGBlendCLDomestic"]){
      vm.runInContext(sourceFunction(source,fn),cx,{timeout:900});
   }
   for(const key of ["pl","liga","bl","cl","missing",undefined]){
     compare("FBref "+vi+" "+name+" "+key,"frontend_soccer_xg_fbref",
        cx._socXGFromFBref(name,key),
        own.fbrefXg(name,key,data,adv));
     count++;
   }
   compare("UEFA domestic "+vi+" "+name,"frontend_soccer_xg_cl_domestic",
     cx._socXGBlendCLDomestic(name),
     own.clDomesticXg(name,data,adv,params));
   count++;
  }
 }
 return count;
}
module.exports={verifySoccerFBref};
