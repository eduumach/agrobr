import { calculate as moreira } from "./moreira.js";
import { calculate as vPercent } from "./v-percent.js";
import { calculate as alCaMg } from "./al-ca-mg.js";
import { calculate as smp } from "./smp.js";

export const METHOD_REGISTRY = {
  moreira_2025: moreira,
  v_percent: vPercent,
  al_ca_mg: alCaMg,
  smp,
};
