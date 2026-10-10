"use strict";
/** Original-vs-independent props: compare numeric picks, not expressive text. */
const vm=require("node:vm");
const {sourceFunction}=require("./verify_clairvoyance_euro_hockey_matches.js");
const own=require("../modeles/reproduction/frontend_clairvoyance_nba_props.js");
const KEYS=["player","team","opp","hA","awA","stat","statAbbr","line",
            "over","ml","prob","grade","hitRate","adjustor","mu","sigma",
            "base","form"];
function comparable(arr){
 return arr.map(x=>Object.fromEntries(KEYS.map(key=>[key,x[key]])));
}
function verifyNBAProps(source,compare) {
 const fakeMC=(mu,sigma,line)=>({overP:Math.max(.02,Math.min(.98,
     1/(1+Math.exp(-(mu-line)/sigma))))});
 const grade=conf=>conf>70?"OPTIMAL":conf>60?"GOOD":conf>54?"LEAN":"SKIP";
 const half=n=>(Math.floor(n)+.5).toFixed(1);
 let count=0;
 const players={
  "id1":{name:"Player One",team:"BOS",ppg:27.5,rpg:8.4,apg:6.2,gp:68,
    last5:{n:5,ppg:32,rpg:6,apg:7.8},stdev:{pts:9.6,reb:3,ast:2.4}},
  "id2":{name:"Player Two",team:"NYK",ppg:19.3,rpg:6.4,apg:5.9,gp:51,
    last5:{n:2,ppg:29,rpg:8,apg:7},stdev:{pts:5.1,reb:4,ast:3.5}},
  "id3":{name:"Player Three",team:"BOS",ppg:15,rpg:9,apg:2,gp:12},
  "id4":{name:"Player Out",team:"NYK",ppg:31,rpg:10,apg:8,gp:60,status:"Out"},
  "id5":{name:"Player No GP",team:"BOS",ppg:40,rpg:12,apg:12,gp:2},
  "id6":{name:"Player Five",team:"BOS",ppg:13.4,rpg:4,apg:7,gp:29},
  "id7":{name:"Player Six",team:"NYK",ppg:29,rpg:8,apg:5,gp:21},
  "id8":{name:"Player Seven",team:"NYK",ppg:11,rpg:12,apg:6,gp:47},
 };
 const gamesVariants=[
   [{h:"BOS",a:"NYK"}],
   [{home:"BOS",away:"NYK"}],
   [{hA:"BOS",awA:"NYK"}],
   [{h:"BOS",a:"NYK",seasonType:1}],
   [{h:"BOS",a:"NYK",preseason:true}],
   [{h:"BOS",a:"ATL"}],
   [{h:"ORL",a:"NYK"}],
   [{h:"ORL",a:"ATL"}],
   [{h:"BOS",a:"NYK"},{h:"NYK",a:"BOS"}],
   [],
   null,
 ];
 const defenses=[0,.03,-.12,.2,-.4,-.95];
 for(const [k,games] of gamesVariants.entries()){
  for(const factor of defenses){
   const opponent=(sport,team)=>({factor,raw:111+factor*10,
      lgAvg:115,realAvg:true,note:false});
   const ctx=vm.createContext({
    _forceHalfLine:half,propMC:fakeMC,_propGradeByConf:grade,
    _propOppDefFactor:opponent,_withPropReasoning:x=>x
   });
   vm.runInContext(sourceFunction(source,"_generateNBAProps"),ctx,{timeout:800});
   const ref=ctx._generateNBAProps(games,players);
   const ours=own.nbaProps(games,players,{
      defense:opponent,halfLine:half,monteCarlo:fakeMC,classify:grade
   });
   compare("NBA props "+k+" factor="+factor,"frontend_nba_player_props",
          comparable(ref),comparable(ours));
   count++;
  }
 }
 for(const stat of [null,undefined,{},[]]){
  const ctx=vm.createContext({
    _forceHalfLine:half,propMC:fakeMC,_propGradeByConf:grade,
    _propOppDefFactor:()=>({factor:0,note:true}),
    _withPropReasoning:x=>x
  });
  vm.runInContext(sourceFunction(source,"_generateNBAProps"),ctx,{timeout:800});
  compare("NBA missing stats "+stat,"frontend_nba_player_props",
       comparable(ctx._generateNBAProps([{h:"BOS",a:"NYK"}],stat)),
       comparable(own.nbaProps([{h:"BOS",a:"NYK"}],stat,{
         monteCarlo:fakeMC,halfLine:half,classify:grade
       })));
  count++;
 }
 // The original NHL function is currently a no-op; faithfully keep it
 // inactive instead of fabricating props.
 const line=source.split("\n").find(x=>x.trim().startsWith("function _generateNHLPropsLive("));
 if(!line||line.length>160)throw Error("NHL no-op source changed unexpectedly");
 const cx=vm.createContext({});
 vm.runInContext(line,cx,{timeout:500});
 for(let i=0;i<11;i++){
  compare("NHL no-op "+i,"frontend_nhl_player_props",
    cx._generateNHLPropsLive(i),own.nhlPropsLive(i));
  count++;
 }
 return count;
}
module.exports={verifyNBAProps};
