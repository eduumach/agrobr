export const CA_SAT_TARGET = 0.60;

export const BASE_CA_FACTOR = 0.01783;
export const BASE_MG_FACTOR = 0.0248;
export const BASE_DEPTH_CM = 20;

export function caConversionFactor(depthCm = 20) {
  if (depthCm <= 0) throw new Error("depthCm deve ser > 0");
  return BASE_CA_FACTOR * (BASE_DEPTH_CM / depthCm);
}

export function mgConversionFactor(depthCm = 20) {
  if (depthCm <= 0) throw new Error("depthCm deve ser > 0");
  return BASE_MG_FACTOR * (BASE_DEPTH_CM / depthCm);
}

export const STATE_PRIMARY_METHOD = {
  SP: "v_percent",
  PR: "v_percent",
  MT: "v_percent",
  GO: "v_percent",
  MS: "v_percent",
  BA: "v_percent",
  MG: "al_ca_mg",
  RS: "smp",
  SC: "smp",
};

export const V2_TARGETS = {
  "SP|soja": 70,
  "SP|milho": 60,
  "SP|café": 80,
  "SP|feijão": 60,
  "SP|pastagem": 60,
  "PR|soja": 70,
  "PR|milho": 70,
  "PR|café": 70,
  "MT|soja": 50,
  "MT|milho": 50,
  "GO|soja": 50,
  "GO|milho": 50,
  "MS|soja": 60,
  "MS|milho": 60,
  "BA|soja": 60,
  "BA|milho": 60,
};

export const AL_TOLERANCE = {
  soja: 20,
  milho: 15,
  café: 25,
  feijão: 20,
  pastagem: 25,
  eucalipto: 30,
  trigo: 15,
};

export const CA_MG_MIN = {
  geral: 2.0,
  café: 3.0,
  eucalipto: 1.0,
};

export const CROP_GROUP = {
  soja: "geral",
  milho: "geral",
  feijão: "geral",
  café: "café",
  pastagem: "geral",
  eucalipto: "eucalipto",
  trigo: "geral",
};

export const SMP_PH_TARGET = {
  soja: 6.0,
  milho: 6.0,
  feijão: 6.0,
  pastagem: 5.5,
  trigo: 6.0,
};

export const SMP_TABLE = {
  "4.4": [15.0, 21.0, 29.0],
  "4.5": [12.5, 17.3, 24.0],
  "4.6": [10.9, 15.1, 20.0],
  "4.7": [9.6, 13.3, 17.5],
  "4.8": [8.5, 11.9, 15.7],
  "4.9": [7.7, 10.7, 14.2],
  "5.0": [6.6, 9.9, 13.3],
  "5.1": [6.0, 9.1, 12.3],
  "5.2": [5.3, 8.3, 11.3],
  "5.3": [4.8, 7.5, 10.4],
  "5.4": [4.2, 6.8, 9.5],
  "5.5": [3.7, 6.1, 8.6],
  "5.6": [3.2, 5.4, 7.8],
  "5.7": [2.8, 4.8, 7.0],
  "5.8": [2.3, 4.2, 6.3],
  "5.9": [2.0, 3.7, 5.6],
  "6.0": [1.6, 3.2, 4.9],
  "6.1": [1.3, 2.7, 4.3],
  "6.2": [1.0, 2.2, 3.7],
  "6.3": [0.8, 1.8, 3.1],
  "6.4": [0.6, 1.4, 2.6],
  "6.5": [0.4, 1.1, 2.1],
  "6.6": [0.2, 0.8, 1.6],
  "6.7": [0.0, 0.5, 1.2],
  "6.8": [0.0, 0.3, 0.8],
  "6.9": [0.0, 0.2, 0.5],
  "7.0": [0.0, 0.0, 0.2],
  "7.1": [0.0, 0.0, 0.0],
};

export const CLAY_Y_FACTOR = [
  [0.0, 15.0, 1],
  [15.0, 35.0, 2],
  [35.0, 60.0, 3],
  [60.0, 100.1, 4],
];

export const CA_RANGE = [0.0, 20.0];
export const MG_RANGE = [0.0, 10.0];
export const AL_RANGE = [0.0, 10.0];
export const H_AL_RANGE = [0.0, 30.0];
export const K_RANGE = [0.0, 2.0];
export const CLAY_RANGE = [0.0, 100.0];
export const PH_SMP_RANGE = [3.5, 8.0];

export const CAO_RANGE = [15.0, 56.0];
export const MGO_RANGE = [0.0, 25.0];
export const PRNT_RANGE = [45.0, 125.0];

export const K_HEURISTIC_THRESHOLD = 5.0;
export const K_MG_TO_CMOLC = 391.0;

export const CTC_DIVERGENCE_THRESHOLD = 0.5;
export const CTC_HIGH_THRESHOLD = 40.0;
export const NC_HIGH_THRESHOLD = 15.0;

export const MG_MIN_020 = 2.0;
export const MG_MIN_2040 = 1.0;
export const CA_MG_RATIO_MIN = 1.5;
export const CA_MG_RATIO_MAX = 10.0;
export const MG_SAT_MAX_PCT = 30.0;

export const PARCEL_SPD_THRESHOLD = 5.0;
export const PARCEL_ABERTURA_THRESHOLD = 6.0;

export const CAO_MGO_LEGAL_MIN = 38.0;
