import { AL_TOLERANCE, CA_MG_MIN, CLAY_Y_FACTOR, CROP_GROUP } from "../constants.js";
import { createLimingResult } from "../models.js";

function getYFactor(clayPct) {
  for (const [lower, upper, y] of CLAY_Y_FACTOR) {
    if (clayPct >= lower && clayPct < upper) return y;
  }
  return CLAY_Y_FACTOR[CLAY_Y_FACTOR.length - 1][2];
}

export function calculate(request) {
  const crop = request.crop;
  const mt = AL_TOLERANCE[crop];
  const group = CROP_GROUP[crop];

  if (mt === undefined || group === undefined) {
    return createLimingResult({
      method: "al_ca_mg",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: `Sem parâmetro calibrado para ${crop}`,
    });
  }

  const x = CA_MG_MIN[group];
  const layer020 = request.layers.find(l => l.depth === "0-20");

  if (layer020.clay_pct === null) {
    return createLimingResult({
      method: "al_ca_mg",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: "Argila necessária para fator Y",
    });
  }

  const y = getYFactor(layer020.clay_pct);
  const t = layer020.t_efetiva;
  const prnt = request.limestone.prnt;

  const caTerm = Math.max(0.0, y * (layer020.al - (mt * t / 100)));
  const cdTerm = Math.max(0.0, x - (layer020.ca + layer020.mg));
  const nc = (caTerm + cdTerm) * (100 / prnt);

  return createLimingResult({
    method: "al_ca_mg",
    nc_tha: nc,
    nc_per_layer: { "0-20": nc },
    available: true,
  });
}
