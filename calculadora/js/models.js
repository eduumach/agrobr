import {
  AL_RANGE, CA_RANGE, CAO_RANGE, CLAY_RANGE, H_AL_RANGE,
  K_HEURISTIC_THRESHOLD, K_MG_TO_CMOLC, K_RANGE, MG_RANGE,
  MGO_RANGE, PH_SMP_RANGE, PRNT_RANGE,
} from "./constants.js";

export class ValidationError extends Error {
  constructor(field, message) {
    super(message);
    this.name = "ValidationError";
    this.field = field;
  }
}

function checkRange(name, value, [low, high]) {
  if (value < low || value > high) {
    throw new ValidationError(name, `${name} (${value}) fora do range [${low}, ${high}]`);
  }
}

export function createSoilLayer({ depth, ca, mg, k, al, h_al, clay_pct = null, ph_smp = null, ctc_lab = null }) {
  if (!["0-20", "20-40"].includes(depth)) {
    throw new ValidationError("depth", "depth deve ser '0-20' ou '20-40'");
  }

  if (k > K_HEURISTIC_THRESHOLD) {
    k = k / K_MG_TO_CMOLC;
  }

  checkRange("ca", ca, CA_RANGE);
  checkRange("mg", mg, MG_RANGE);
  checkRange("k", k, K_RANGE);
  checkRange("al", al, AL_RANGE);
  checkRange("h_al", h_al, H_AL_RANGE);
  if (clay_pct !== null) checkRange("clay_pct", clay_pct, CLAY_RANGE);
  if (ph_smp !== null) checkRange("ph_smp", ph_smp, PH_SMP_RANGE);

  if (al > h_al) {
    throw new ValidationError("al", `Al (${al}) não pode ser maior que H+Al (${h_al})`);
  }

  const ctc_ph7 = ca + mg + k + h_al;
  const v_pct = ctc_ph7 === 0.0 ? 0.0 : ((ca + mg + k) / ctc_ph7) * 100;
  const t_efetiva = ca + mg + k + al;

  return Object.freeze({
    depth, ca, mg, k, al, h_al, clay_pct, ph_smp, ctc_lab,
    ctc_ph7, v_pct, t_efetiva,
  });
}

export function createLimestone({ cao_pct, mgo_pct, prnt }) {
  checkRange("cao_pct", cao_pct, CAO_RANGE);
  checkRange("mgo_pct", mgo_pct, MGO_RANGE);
  checkRange("prnt", prnt, PRNT_RANGE);

  const tipo = mgo_pct > 12.0 ? "dolomítico" : mgo_pct >= 5.0 ? "magnesiano" : "calcítico";

  return Object.freeze({ cao_pct, mgo_pct, prnt, tipo });
}

export function createLimingRequest({ state, crop, system, layers, limestone }) {
  if (!["abertura", "spd"].includes(system)) {
    throw new ValidationError("system", "system deve ser 'abertura' ou 'spd'");
  }

  const depths = layers.map(l => l.depth);
  if (!depths.includes("0-20")) {
    throw new ValidationError("layers", "Camada 0-20 é obrigatória");
  }
  if (layers.length > 2) {
    throw new ValidationError("layers", "Máximo 2 camadas");
  }
  if (layers.length === 2) {
    const set = new Set(depths);
    if (!set.has("0-20") || !set.has("20-40") || set.size !== 2) {
      throw new ValidationError("layers", "Camadas devem ser 0-20 e 20-40");
    }
  }

  return Object.freeze({ state, crop, system, layers, limestone });
}

export function createLimingResult({ method, nc_tha, nc_per_layer, available, reason = null }) {
  return Object.freeze({ method, nc_tha, nc_per_layer: { ...nc_per_layer }, available, reason });
}

export function createDiagnosticReport(data) {
  return Object.freeze({
    results: [...data.results],
    primary_method: data.primary_method,
    moreira_result: data.moreira_result,
    system: data.system,
    delta_tha: data.delta_tha,
    nc_subsurface: data.nc_subsurface,
    mg_projection: { ...data.mg_projection },
    ca_projection: { ...data.ca_projection },
    ca_mg_ratio_projected: data.ca_mg_ratio_projected,
    mg_saturation_projected: { ...data.mg_saturation_projected },
    warnings: [...data.warnings],
  });
}
