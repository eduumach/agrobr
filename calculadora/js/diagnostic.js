import {
  CA_MG_RATIO_MAX, CA_MG_RATIO_MIN, MG_MIN_020, MG_MIN_2040,
  MG_SAT_MAX_PCT, PARCEL_ABERTURA_THRESHOLD, PARCEL_SPD_THRESHOLD,
  STATE_PRIMARY_METHOD, caConversionFactor, mgConversionFactor,
} from "./constants.js";
import { METHOD_REGISTRY } from "./methods/index.js";
import { createDiagnosticReport } from "./models.js";
import {
  validateCtcDivergence, validateCtcHigh,
  validateLimestoneLegal, validateNcHigh, validatePrntSpecial,
} from "./validators.js";

export function runDiagnostic(request) {
  const layer020 = request.layers.find(l => l.depth === "0-20");
  const layer2040 = request.layers.find(l => l.depth === "20-40") || null;

  const moreiraResult = METHOD_REGISTRY.moreira_2025(request);

  const primaryMethodName = STATE_PRIMARY_METHOD[request.state] || null;

  const results = Object.values(METHOD_REGISTRY).map(fn => fn(request));

  let primaryResult = null;
  if (primaryMethodName !== null) {
    primaryResult = results.find(r => r.method === primaryMethodName) || null;
  }

  let deltaTha = null;
  if (primaryResult !== null && primaryResult.available) {
    deltaTha = moreiraResult.nc_per_layer["0-20"] - primaryResult.nc_tha;
  }

  let ncSubsurface = null;
  if (request.system === "abertura") {
    ncSubsurface = moreiraResult.nc_per_layer["20-40"] ?? null;
  }

  const caoPct = request.limestone.cao_pct;
  const mgoPct = request.limestone.mgo_pct;
  const caFactor = caConversionFactor();
  const mgFactor = mgConversionFactor();

  const caProjection = {};
  const mgProjection = {};
  const mgSaturationProjected = {};
  const ncEffective = {};

  const layers = [layer020];
  if (layer2040 !== null) layers.push(layer2040);

  for (const layer of layers) {
    let ncLayer;
    if (request.system === "spd" && layer.depth === "20-40") {
      ncLayer = 0.0;
    } else {
      ncLayer = moreiraResult.nc_per_layer[layer.depth] ?? 0.0;
    }
    ncEffective[layer.depth] = ncLayer;

    caProjection[layer.depth] = layer.ca + ncLayer * caoPct * caFactor;
    mgProjection[layer.depth] = layer.mg + ncLayer * mgoPct * mgFactor;

    if (layer.ctc_ph7 === 0.0) {
      mgSaturationProjected[layer.depth] = 0.0;
    } else {
      mgSaturationProjected[layer.depth] = (mgProjection[layer.depth] / layer.ctc_ph7) * 100;
    }
  }

  const mgProj020 = mgProjection["0-20"];
  let caMgRatioProjected = null;
  if (mgProj020 > 0) {
    caMgRatioProjected = caProjection["0-20"] / mgProj020;
  }

  const nc020 = ncEffective["0-20"];
  const warnings = [];

  for (const layer of layers) {
    warnings.push(...validateCtcDivergence(layer));
    warnings.push(...validateCtcHigh(layer));
  }

  warnings.push(...validateLimestoneLegal(request.limestone));
  warnings.push(...validatePrntSpecial(request.limestone));
  warnings.push(...validateNcHigh(moreiraResult.nc_tha));

  for (const layer of layers) {
    const ncEff = ncEffective[layer.depth];
    if (ncEff === 0.0) continue;
    const mgMin = layer.depth === "0-20" ? MG_MIN_020 : MG_MIN_2040;
    if (mgProjection[layer.depth] < mgMin) {
      warnings.push(
        `Mg projetado ficará deficiente na camada ${layer.depth}. Considere dolomítico.`
      );
    }
  }

  if (nc020 > 0.0 && caMgRatioProjected !== null) {
    if (caMgRatioProjected < CA_MG_RATIO_MIN || caMgRatioProjected > CA_MG_RATIO_MAX) {
      warnings.push("Relação Ca/Mg projetada fora do ideal (2-5).");
    }
  }

  for (const layer of layers) {
    const ncEff = ncEffective[layer.depth];
    if (ncEff === 0.0) continue;
    const mgSat = mgSaturationProjected[layer.depth];
    if (mgSat > MG_SAT_MAX_PCT) {
      warnings.push(
        `Mg projetado representa ${Math.round(mgSat)}% da CTC na camada ${layer.depth} — risco de antagonismo com Ca e K (ideal ≤25-30%). Considere calcário com menor teor de MgO.`
      );
    }
  }

  if (request.system === "spd" && nc020 > PARCEL_SPD_THRESHOLD) {
    warnings.push("Parcelar em 2-3 safras (sem incorporação profunda).");
  } else if (request.system === "abertura" && moreiraResult.nc_tha > PARCEL_ABERTURA_THRESHOLD) {
    warnings.push("Parcelar em 2-3 aplicações com incorporação.");
  }

  if (request.system === "abertura") {
    const nc020Raw = moreiraResult.nc_per_layer["0-20"] ?? 0.0;
    const nc2040Raw = moreiraResult.nc_per_layer["20-40"] ?? 0.0;
    if (nc020Raw === 0.0 && nc2040Raw > 0.0) {
      warnings.push("Camada 0-20 já corrigida. Considere gessagem para 20-40.");
    }
  }

  if (request.system === "abertura" && layer2040 === null) {
    warnings.push(
      "Camada 20-40 não informada. Para abertura de área, recomenda-se análise da subsuperfície para cálculo completo."
    );
  }

  return createDiagnosticReport({
    results,
    primary_method: primaryMethodName,
    moreira_result: moreiraResult,
    system: request.system,
    delta_tha: deltaTha,
    nc_subsurface: ncSubsurface,
    mg_projection: mgProjection,
    ca_projection: caProjection,
    ca_mg_ratio_projected: caMgRatioProjected,
    mg_saturation_projected: mgSaturationProjected,
    warnings,
  });
}
