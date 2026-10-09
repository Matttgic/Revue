"use strict";
/**
 * Functional reconstruction of Clairvoyance's four EU hockey
 * previous-/current-season goal-rate blends.
 *
 * Reference functions (READ from source in CI, never copied):
 * _liigaBlendedRates / _nlaBlendedRates /
 * _extraligaBlendedRates / _shlBlendedRates in docs/app.html.
 *
 * Same branching, exact 20-game current-season transition,
 * GF/GA and independent G/M observations. No added coefficients.
 */
function previousSeasonRates(team) {
  if (!team) return {gf:2.8,ga:2.8,gm:5.5,gp:0};

  const played = team.gp || 0;
  const currentShare = Math.min(1,played/20);

  const currentGF = played ? team.gf/played : null;
  const currentGA = played ? team.ga/played : null;
  const before = team.prevSeason;
  const oldGF = (before && before.gp) ? before.gf/before.gp : null;
  const oldGA = (before && before.gp) ? before.ga/before.gp : null;

  const offense = currentGF!==null && oldGF!==null
    ? currentGF*currentShare + oldGF*(1-currentShare)
    : (currentGF ?? oldGF ?? 2.8);
  const defense = currentGA!==null && oldGA!==null
    ? currentGA*currentShare + oldGA*(1-currentShare)
    : (currentGA ?? oldGA ?? 2.8);
  const tempo = team.gm!=null && before?.gm!=null
    ? team.gm*currentShare + before.gm*(1-currentShare)
    : (team.gm ?? before?.gm ?? (offense+defense));

  return {gf:offense,ga:defense,gm:tempo,gp:played};
}

function liigaRates(team){return previousSeasonRates(team);}
function nlaRates(team){return previousSeasonRates(team);}
function extraligaRates(team){return previousSeasonRates(team);}
function shlRates(team){return previousSeasonRates(team);}

module.exports={previousSeasonRates,liigaRates,nlaRates,extraligaRates,shlRates};
