import { CA_SAT_TARGET, caConversionFactor } from "../constants.js";
import { createLimingResult } from "../models.js";

function ncLayer(layer, caoPct, prnt) {
  const caTarget = CA_SAT_TARGET * layer.ctc_ph7;
  const numerator = caTarget - layer.ca;
  const denominator = caoPct * caConversionFactor();
  return Math.max(0.0, (numerator / denominator) * (100 / prnt));
}

export function calculate(request) {
  const layer020 = request.layers.find(l => l.depth === "0-20");
  const layer2040 = request.layers.find(l => l.depth === "20-40") || null;

  const cao = request.limestone.cao_pct;
  const prnt = request.limestone.prnt;

  const nc020 = ncLayer(layer020, cao, prnt);
  const ncPerLayer = { "0-20": nc020 };

  if (layer2040 !== null) {
    ncPerLayer["20-40"] = ncLayer(layer2040, cao, prnt);
  }

  const ncTotal = request.system === "abertura"
    ? Object.values(ncPerLayer).reduce((a, b) => a + b, 0)
    : nc020;

  return createLimingResult({
    method: "moreira_2025",
    nc_tha: ncTotal,
    nc_per_layer: ncPerLayer,
    available: true,
  });
}
