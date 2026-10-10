"use strict";
/** Direct source-output comparisons for two original Clairvoyance JS form functions. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const clone=x=>JSON.parse(JSON.stringify(x));
const own=require("../modeles/reproduction/frontend_clairvoyance_soccer_form.js");

function verifySoccerForm(source,compare){
 const seed={
  pl:{teams:{
   "Manchester City":{mp:20,gf:44,ga:15,recentForm:{games:5,gf:2.2,ga:.6}},
   "Arsenal":{mp:16,gf:20,ga:18,recentForm:{games:5,gf:1.8,ga:1.2}},
   "Chelsea":{mp:13,gf:19,ga:20,recentForm:{games:2,gf:1.4,ga:1.8}},
   "Brighton":{mp:0,gf:0,ga:0,recentForm:{games:4,gf:0,ga:1.5}},
  }},
  cl:{teams:{
   "Manchester City":{mp:5,gf:11,ga:2,recentForm:{games:3,gf:2.4,ga:.4}},
   "Arsenal":{mp:2,gf:2,ga:2,recentForm:{games:2,gf:1,ga:1}},
  }},
  liga:{teams:{
   "Real Madrid":{mp:10,gf:18,ga:7,recentForm:{games:3,gf:3.5,ga:.5}},
  }},
  bl:{teams:{
   "Bayern Munich":{mp:11,gf:25,ga:15,recentForm:{games:3,gf:1,ga:2}},
  }}
 };
 let count=0;
 const seen=["Manchester City","manchester","Arsenal","Chelsea","Brighton",
             "Real Madrid","Real","Bayern Munich","Unknown","",null];
 const contexts={
    "Manchester City":{domKey:"pl",wCL:.25,wDom:.75},
    "Arsenal":{domKey:"pl",wCL:.4,wDom:.6},
    "Real Madrid":{domKey:"liga",wCL:.3,wDom:.7}
 };
 const leagues=["pl","cl","liga","bl","missing"];
 const states=[seed,{},{pl:{teams:{}},cl:{teams:{}}},
               {pl:{teams:{"Manchester City":{mp:0,recentForm:{games:3,gf:4,ga:.1}}}}},
               {pl:{teams:{"Manchester City":{mp:18,gf:20,ga:20,recentForm:{games:3,gf:1,ga:1}}}}}];
 for(const [ix,blocks] of states.entries()){
  for(const name of seen){
   for(const lg of leagues){
    const env={
      window:{__CV_FBREF:blocks},
      _clDomesticContext:name=>contexts[name]||null,
    };
    const context=vm.createContext(env);
    for(const fn of ["_socFuzzyFind","_socFormFactorRaw","_socFormFactor"])
      vm.runInContext(sourceFunction(source,fn),context,{timeout:800});
    compare("soc form raw state "+ix+" "+name+" "+lg,
      "frontend_soccer_form_raw",context._socFormFactorRaw(name,lg),
      own.rawFormFactor(name,lg,blocks));
    compare("soc form factor state "+ix+" "+name+" "+lg,
      "frontend_soccer_form",context._socFormFactor(name,lg),
      own.formFactor(name,lg,blocks,contexts));
    count+=2;
   }
  }
 }
 return count;
}
module.exports={verifySoccerForm};
