import { V2_TARGETS } from "../constants.js";
import { createLimingResult } from "../models.js";

export function calculate(request) {
  const key = `${request.state}|${request.crop}`;
  const v2 = V2_TARGETS[key];

  if (v2 === undefined) {
    return createLimingResult({
      method: "v_percent",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: `Sem V2 calibrado para (${request.state}, ${request.crop})`,
    });
  }

  const layer020 = request.layers.find(l => l.depth === "0-20");
  const v1 = layer020.v_pct;
  const ctc = layer020.ctc_ph7;
  const prnt = request.limestone.prnt;

  const nc = Math.max(0.0, (v2 - v1) * ctc / prnt);

  return createLimingResult({
    method: "v_percent",
    nc_tha: nc,
    nc_per_layer: { "0-20": nc },
    available: true,
  });
}
