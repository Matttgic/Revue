"use strict";
/** Check source vs independently derived xG formula incl FBref/Opta/CL pipeline. */
const vm=require("node:vm");
const own=require("../modeles/reproduction/frontend_clairvoyance_soccer_xg.js");

function original(source,name){
  const re=new RegExp("^function\\s+"+name+"\\s*\\(","m");
  const found=re.exec(source);
  if(!found)throw new Error("Original source has no "+name);
  const end=source.indexOf("\n}",found.index);
  if(end<0)throw new Error("Missing end brace for "+name);
  const piece=source.slice(found.index,end+2);
  if(piece.length>17000)throw new Error("Function too large "+name);
  return piece;
}
const NAMES=[
 "_socHomeAdv","_socTeamHomeAwaySplit","_socXGFromFBref",
 "_socFuzzyFind","_optaBaseXG","_blendLeagueOpta",
 "_clDomesticContext","_socXGBlendCLDomestic","_socXGRaw","_socXG"
];
function fbTeam(config={}){
  return{
    xg:49,xga:32,gf:42,ga:30,mp:28,poss:54.3,xag:30.8,
    shots_pg:13.6,sot_pg:5.6,
    recentForm:["W","D","L"],
    homeSplit:{games:2,gf:1.9,ga:1.02},
    awaySplit:{games:2,gf:1.2,ga:1.4},
    matchLog:[],gamesPlayedThisSeason:18,
    ...config
  };
}
const sources={
  fb:{
    pl:{teams:{"London Lions":fbTeam()}},
    liga:{teams:{"Barcelona City":fbTeam({xg:63,xga:34,mp:30,gf:50,ga:31})}},
    cl:{teams:{"London Lions":fbTeam({xg:12,xga:11,mp:9,gf:10,ga:13,gamesPlayedThisSeason:2}),
               "Fener Mock":fbTeam({xg:9,xga:6,mp:6,gf:7,ga:7})}},
  },
  opta:{
    pl:{attacking:[{team:"London Lions",played:20,xg:43}],
        defending:[{team:"London Lions",played:22,xg_against:27}]},
    liga:{attacking:[{team:"Barcelona City",played:20,xg:55}],
          defending:[{team:"Barcelona City",played:20,xg_against:25}]},
    bl:{attacking:[{team:"Berlin United",played:17,xg:24}],
        defending:[{team:"Berlin United",played:17,xg_against:23}]},
  },
  mls:{
    attacking:[{team:"Portland Mock",played:20,xg:29}],
    defending:[{team:"Portland Mock",played:20,xg_against:30}],
  },
  staticXG:{
    "old town":{xg:1.71,xga:1.32,hxg:1.87,hxga:1.21,axg:1.59,axga:1.44,
                 gf:1.5,ga:1.3,mp:34,src:"static"},
    "berlin":{xg:1.48,xga:1.2,hxg:1.63,hxga:1.10,axg:1.33,axga:1.30,
              gf:1.6,ga:1.4,mp:34,src:"static"},
    "portland mock":{xg:1.62,xga:1.41,hxg:1.77,hxga:1.26,
              axg:1.47,axga:1.56,gf:1.7,ga:1.4,mp:34,src:"static"}
  },
  homeAdv:{default:.08,pl:.11,liga:.07,cl:.05,bl:.09,mls:.12},
};
function verifySoccerXG(source,compare){
  const scenarios=[
    {label:"name empty",name:"",league:"pl"},
    {label:"unknown team no inputs",name:"Alien Team",league:"pl",empty:true},
    {label:"FBref exact case",name:"London Lions",league:"pl",noOpta:true},
    {label:"FBref case-insensitive",name:"LONDON LIONS",league:"pl",noOpta:true},
    {label:"FBref shortened substring",name:"London",league:"pl",noOpta:true},
    {label:"FBref real venue split >=3",name:"London Lions",league:"pl",noOpta:true,
      split:{homeSplit:{games:4,gf:2.5,ga:.9},
             awaySplit:{games:3,gf:1.1,ga:1.6}}},
    {label:"FBref one side below minimum",name:"London Lions",league:"pl",noOpta:true,
      split:{homeSplit:{games:3,gf:2.5,ga:.9},
             awaySplit:{games:2,gf:1.1,ga:1.6}}},
    {label:"FBref fallback mp=34",name:"London Lions",league:"pl",noOpta:true,
      split:{mp:0}},
    {label:"FBref and Opta 50/50",name:"London Lions",league:"pl"},
    {label:"FBref with venue splits and Opta",name:"London Lions",league:"pl",
      split:{homeSplit:{games:5,gf:2.5,ga:.8},awaySplit:{games:6,gf:.9,ga:1.8}}},
    {label:"Opta missing defense preserves FBref",name:"London Lions",league:"pl",
      damagedOpta:true},
    {label:"Opta missing all preserves FBref",name:"London Lions",league:"pl",noOpta:true},
    {label:"Spanish league Opta and FBref",name:"Barcelona City",league:"liga"},
    {label:"static exact no FBref",name:"Old Town",league:"bl",noFBref:true,noOpta:true},
    {label:"static fuzzy both directions",name:"Old Town FC",league:"bl",noFBref:true,noOpta:true},
    {label:"static prefix first word",name:"Portland Athletic",league:"noleague",noFBref:true,noOpta:true},
    {label:"static plus Opta Berlin",name:"Berlin United",league:"bl",noFBref:true},
    {label:"MLS separate Opta fallback",name:"Portland Mock",league:"mls",noFBref:true,noOpta:false},
    {label:"CL only unknown domestic",name:"Fener Mock",league:"cl"},
    {label:"CL no current games",name:"London Lions",league:"cl",clGames:0},
    {label:"CL one current game",name:"London Lions",league:"cl",clGames:1},
    {label:"CL two current games",name:"London Lions",league:"cl",clGames:2},
    {label:"CL at full 3-game blend",name:"London Lions",league:"cl",clGames:3},
    {label:"CL over 3-game cap",name:"London Lions",league:"cl",clGames:8},
    {label:"CL missing current season uses domestic",name:"London Lions",league:"cl",noCL:true},
    {label:"missing Opta xG rows no fake estimate",name:"Alien Team",league:"ita"},
    {label:"static exact with empty Opta League",name:"Old Town",league:"pl",noFBref:true},
  ];
  for(const scenario of scenarios){
    const opts={
      fbref:scenario.empty||scenario.noFBref?null:structuredClone(sources.fb),
      opta:scenario.empty||scenario.noOpta?{}:structuredClone(sources.opta),
      mlsOpta:scenario.empty||scenario.noOpta?null:structuredClone(sources.mls),
      staticXG:scenario.empty?{}:structuredClone(sources.staticXG),
      homeAdv:sources.homeAdv
    };
    if(opts.fbref&&scenario.split){
      Object.assign(opts.fbref.pl.teams["London Lions"],scenario.split);
    }
    if(opts.fbref&&scenario.clGames!==undefined){
      opts.fbref.cl.teams["London Lions"].gamesPlayedThisSeason=scenario.clGames;
    }
    if(opts.fbref&&scenario.noCL){
      delete opts.fbref.cl.teams["London Lions"];
    }
    if(scenario.damagedOpta){
      opts.opta.pl.defending=[];
    }
    const context=vm.createContext({
      window:{
        __CV_FBREF:opts.fbref,__CV_OPTA:opts.opta,
        __CV_MLS_OPTA:opts.mlsOpta
      },
      _SOC_HOME_ADV:opts.homeAdv,
      _SOC_XG:opts.staticXG,
      _OPTA_LEAGUES:["pl","liga","ita","bl","mls","cl"],
      _CL_DOMESTIC_LEAGUES:["pl","liga","bl","ita"],
      _CL_WEIGHT_MAX:.35,_CL_WEIGHT_RAMP_GAMES:3
    });
    for(const name of NAMES){
      vm.runInContext(original(source,name),context,{timeout:1500});
    }
    compare(scenario.label,"frontend_soccer_xg",
      context._socXG(scenario.name,scenario.league),
      own.soccerXG(scenario.name,scenario.league,opts));
  }
  return scenarios.length;
}
module.exports={verifySoccerXG};
