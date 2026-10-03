/**
 * Adapter from the shared `SimulationResult` boundary to the brain viewer.
 *
 * The only accepted cortical source is `meta.cortical` (CorticalPayloadV0) on a
 * `tribe_v2` result. Anything else yields a truthful "no cortical data" result;
 * this module never synthesizes, smooths in time or fills gaps in values.
 */

import {
  CORTICAL_SCHEMA,
  FSAVERAGE5_VERTEX_ORDER,
  FSAVERAGE5_VERTICES,
  type AdaptResult,
  type AnalyzedVideoRef,
  type CorticalBinding,
  type CorticalPayloadV0,
  type DisplayScale,
  type SimulationResult,
} from "./contract.ts";

function invalid(reason: string): AdaptResult {
  return { ok: false, code: "invalid", reason };
}

function decodeBase64(b64: string): Uint8Array {
  if (typeof atob === "function") {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  // Node (tests) fallback.
  const NodeBuffer = (globalThis as { Buffer?: { from(s: string, enc: string): Uint8Array } }).Buffer;
  if (!NodeBuffer) throw new Error("No base64 decoder available");
  return new Uint8Array(NodeBuffer.from(b64, "base64"));
}

function float32FromLittleEndian(bytes: Uint8Array): Float32Array {
  if (bytes.byteLength % 4 !== 0) throw new Error("byte length is not a multiple of 4");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const out = new Float32Array(bytes.byteLength / 4);
  for (let i = 0; i < out.length; i++) out[i] = view.getFloat32(i * 4, true);
  return out;
}

export function isMockResult(result: SimulationResult): boolean {
  return result.meta?.mock === true;
}

/**
 * Validate a result and produce an immutable binding. `fetchedValues` lets the
 * caller resolve `values_url` (see `resolveCorticalValues`) before adapting.
 */
export function adaptSimulationResult(result: SimulationResult, fetchedValues?: Float32Array): AdaptResult {
  if (!result || typeof result !== "object") return invalid("Result is not an object");
  if (result.simulator !== "tribe_v2") {
    return { ok: false, code: "not_cortical", reason: `Simulator ${String(result.simulator)} has no cortical surface data` };
  }
  const cortical = result.meta?.cortical as Partial<CorticalPayloadV0> | undefined;
  if (!cortical) return { ok: false, code: "not_cortical", reason: "Result carries no meta.cortical payload" };
  if (cortical.schema !== CORTICAL_SCHEMA) return invalid(`Unsupported cortical schema ${String(cortical.schema)}`);
  if (cortical.mesh !== "fsaverage5") return invalid(`Mesh ${String(cortical.mesh)} is not fsaverage5`);
  if (cortical.vertex_order !== FSAVERAGE5_VERTEX_ORDER) return invalid(`Unknown vertex order ${String(cortical.vertex_order)}`);
  if (cortical.n_vertices !== FSAVERAGE5_VERTICES) return invalid(`Expected ${FSAVERAGE5_VERTICES} vertices, got ${String(cortical.n_vertices)}`);
  if (cortical.hemodynamic_alignment !== "stimulus_time" && cortical.hemodynamic_alignment !== "acquisition_time") {
    return invalid("hemodynamic_alignment must be stimulus_time or acquisition_time");
  }

  const nT = cortical.n_timesteps;
  if (!Number.isInteger(nT) || (nT as number) < 1) return invalid("n_timesteps must be a positive integer");
  const times = cortical.times_s;
  if (!Array.isArray(times) || times.length !== nT) return invalid("times_s length must equal n_timesteps");
  for (let i = 0; i < times.length; i++) {
    if (!Number.isFinite(times[i])) return invalid(`times_s[${i}] is not finite`);
    if (i > 0 && times[i] <= times[i - 1]) return invalid("times_s must be strictly increasing");
  }

  const nV = FSAVERAGE5_VERTICES;
  const expected = (nT as number) * nV;
  let values: Float32Array;
  const sources = [cortical.values, cortical.values_f32_b64, cortical.values_url].filter((v) => v !== undefined).length;
  if (sources !== 1) return invalid("Provide exactly one of values, values_f32_b64 or values_url");
  try {
    if (cortical.values) {
      if (cortical.values.length !== nT) return invalid("values must have n_timesteps rows");
      values = new Float32Array(expected);
      for (let t = 0; t < (nT as number); t++) {
        const row = cortical.values[t];
        if (!Array.isArray(row) || row.length !== nV) return invalid(`values[${t}] must have ${nV} entries`);
        values.set(row, t * nV);
      }
    } else if (cortical.values_f32_b64) {
      values = float32FromLittleEndian(decodeBase64(cortical.values_f32_b64));
    } else {
      if (!fetchedValues) return invalid("values_url must be resolved before adapting");
      values = fetchedValues;
    }
  } catch (error) {
    return invalid(`Could not decode cortical values: ${(error as Error).message}`);
  }
  if (values.length !== expected) return invalid(`Expected ${expected} values, got ${values.length}`);
  for (let i = 0; i < values.length; i++) {
    if (!Number.isFinite(values[i])) return invalid(`Value ${i} is not finite`);
  }

  const video = result.meta?.video as AnalyzedVideoRef | undefined;
  const binding: CorticalBinding = {
    variantId: String(result.variant_id),
    simulator: result.simulator,
    version: String(result.version ?? ""),
    precomputed: result.precomputed === true,
    mock: isMockResult(result),
    times: Float64Array.from(times),
    nTimesteps: nT as number,
    nVertices: nV,
    values,
    units: String(cortical.units ?? "model units"),
    alignment: cortical.hemodynamic_alignment,
    video: video && typeof video === "object" ? video : undefined,
  };
  return { ok: true, binding };
}

/** Fetch `values_url` as little-endian float32 (same-origin static file). */
export async function resolveCorticalValues(
  result: SimulationResult,
  fetchImpl: typeof fetch = fetch,
): Promise<Float32Array | undefined> {
  const url = (result.meta?.cortical as Partial<CorticalPayloadV0> | undefined)?.values_url;
  if (!url) return undefined;
  const response = await fetchImpl(url);
  if (!response.ok) throw new Error(`Could not load cortical values (${response.status})`);
  return float32FromLittleEndian(new Uint8Array(await response.arrayBuffer()));
}

export const SCALE_PERCENTILE = 0.99;
export const THRESHOLD_FRACTION = 0.35;

/**
 * One display scale for every binding shown together (A/B/C share it so an
 * unchanged response never looks different through auto-scaling).
 * vmax = 99th percentile of positive values pooled across bindings;
 * threshold = 35% of vmax. Values at/below zero stay gray.
 */
export function computeDisplayScale(bindings: readonly CorticalBinding[]): DisplayScale | null {
  let count = 0;
  for (const b of bindings) for (let i = 0; i < b.values.length; i++) if (b.values[i] > 0) count++;
  if (count === 0) return null;
  const positives = new Float32Array(count);
  let k = 0;
  for (const b of bindings) for (let i = 0; i < b.values.length; i++) if (b.values[i] > 0) positives[k++] = b.values[i];
  positives.sort();
  const vmax = positives[Math.min(count - 1, Math.floor(SCALE_PERCENTILE * (count - 1)))];
  return {
    vmax,
    threshold: vmax * THRESHOLD_FRACTION,
    rule: `shared p${Math.round(SCALE_PERCENTILE * 100)} of positive values across ${bindings.length} variant(s); threshold ${Math.round(THRESHOLD_FRACTION * 100)}%`,
  };
}

/** Whether two bindings can be differenced (B − A) on the same mesh/time axis. */
export function canDifference(a: CorticalBinding, b: CorticalBinding): { ok: boolean; reason?: string } {
  if (a.nVertices !== b.nVertices) return { ok: false, reason: "Different vertex counts" };
  if (a.alignment !== b.alignment) return { ok: false, reason: "Different hemodynamic alignment" };
  if (a.nTimesteps !== b.nTimesteps) return { ok: false, reason: "Different number of samples" };
  for (let i = 0; i < a.nTimesteps; i++) {
    if (Math.abs(a.times[i] - b.times[i]) > 1e-6) return { ok: false, reason: `Sample ${i} timestamps differ` };
  }
  return { ok: true };
}
