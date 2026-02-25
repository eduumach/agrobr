import { SMP_PH_TARGET, SMP_TABLE } from "../constants.js";
import { createLimingResult } from "../models.js";

const SMP_MIN = 4.4;
const SMP_MAX = 7.1;
const PH_TARGET_INDEX = { "5.5": 0, "6.0": 1, "6.5": 2 };

function lookupNc(phSmp, phTarget) {
  const idx = PH_TARGET_INDEX[phTarget.toFixed(1)];

  if (phSmp <= SMP_MIN) {
    return SMP_TABLE[SMP_MIN.toFixed(1)][idx];
  }

  const lowerKey = (Math.floor(phSmp * 10) / 10).toFixed(1);
  const upperKey = (Math.ceil(phSmp * 10) / 10).toFixed(1);

  if (lowerKey === upperKey) {
    return SMP_TABLE[lowerKey][idx];
  }

  const fraction = (phSmp - parseFloat(lowerKey)) / (parseFloat(upperKey) - parseFloat(lowerKey));
  const ncLower = SMP_TABLE[lowerKey][idx];
  const ncUpper = SMP_TABLE[upperKey][idx];
  return ncLower + fraction * (ncUpper - ncLower);
}

export function calculate(request) {
  const phTarget = SMP_PH_TARGET[request.crop];

  if (phTarget === undefined) {
    return createLimingResult({
      method: "smp",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: `Sem pH alvo calibrado para ${request.crop}`,
    });
  }

  const layer020 = request.layers.find(l => l.depth === "0-20");

  if (layer020.ph_smp === null) {
    return createLimingResult({
      method: "smp",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: "pH SMP não informado",
    });
  }

  if (layer020.ph_smp > SMP_MAX) {
    return createLimingResult({
      method: "smp",
      nc_tha: 0.0,
      nc_per_layer: {},
      available: false,
      reason: "pH SMP acima do range da tabela (> 7.1)",
    });
  }

  const ncTabela = lookupNc(layer020.ph_smp, phTarget);
  const nc = ncTabela * (100 / request.limestone.prnt);

  return createLimingResult({
    method: "smp",
    nc_tha: nc,
    nc_per_layer: { "0-20": nc },
    available: true,
  });
}
