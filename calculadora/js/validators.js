import {
  CAO_MGO_LEGAL_MIN, CTC_DIVERGENCE_THRESHOLD,
  CTC_HIGH_THRESHOLD, NC_HIGH_THRESHOLD,
} from "./constants.js";

export function validateCtcDivergence(layer) {
  if (layer.ctc_lab === null) return [];
  const diff = Math.abs(layer.ctc_lab - layer.ctc_ph7);
  if (diff > CTC_DIVERGENCE_THRESHOLD) {
    return [`CTC lab (${layer.ctc_lab.toFixed(1)}) diverge da calculada (${layer.ctc_ph7.toFixed(1)}) na camada ${layer.depth}.`];
  }
  return [];
}

export function validateLimestoneLegal(limestone) {
  if (limestone.cao_pct + limestone.mgo_pct < CAO_MGO_LEGAL_MIN) {
    return ["Produto não atende requisito legal (CaO+MgO ≥ 38%)."];
  }
  return [];
}

export function validatePrntSpecial(limestone) {
  if (limestone.prnt > 100.0) {
    return ["Corretivo especial. Método calibrado para calcário agrícola padrão."];
  }
  return [];
}

export function validateCtcHigh(layer) {
  if (layer.ctc_ph7 > CTC_HIGH_THRESHOLD) {
    return [`CTC muito alta na camada ${layer.depth} (${layer.ctc_ph7.toFixed(1)} cmolc/dm³). Verificar dados.`];
  }
  return [];
}

export function validateNcHigh(ncTha) {
  if (ncTha > NC_HIGH_THRESHOLD) {
    return [`NC muito alta (${ncTha.toFixed(1)} t/ha). Verificar dados de entrada.`];
  }
  return [];
}
