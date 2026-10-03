import assert from "node:assert/strict";
import { test } from "node:test";
import { adaptSimulationResult, canDifference, computeDisplayScale, resolveCorticalValues, THRESHOLD_FRACTION } from "../../lib/brain/adapter.ts";
import { CORTICAL_SCHEMA, FSAVERAGE5_VERTEX_ORDER, FSAVERAGE5_VERTICES, type CorticalBinding, type SimulationResult } from "../../lib/brain/contract.ts";

const NV = FSAVERAGE5_VERTICES;

function rows(nT: number, f: (t: number, v: number) => number): number[][] {
  return Array.from({ length: nT }, (_, t) => Array.from({ length: NV }, (_, v) => f(t, v)));
}

function result(overrides: Partial<SimulationResult> = {}, cortical: Record<string, unknown> = {}): SimulationResult {
  const nT = (cortical.n_timesteps as number | undefined) ?? 3;
  return {
    variant_id: "A",
    simulator: "tribe_v2",
    version: "test",
    hz: 1,
    series: {},
    events: [],
    precomputed: false,
    meta: {
      cortical: {
        schema: CORTICAL_SCHEMA,
        mesh: "fsaverage5",
        vertex_order: FSAVERAGE5_VERTEX_ORDER,
        n_vertices: NV,
        n_timesteps: nT,
        times_s: Array.from({ length: nT }, (_, i) => i),
        hemodynamic_alignment: "stimulus_time",
        units: "test units",
        values: rows(nT, (t, v) => t + v / NV),
        ...cortical,
      },
    },
    ...overrides,
  };
}

test("binds genuine JSON values without altering them", () => {
  const r = adaptSimulationResult(result());
  assert.ok(r.ok);
  const b = r.binding;
  assert.equal(b.nTimesteps, 3);
  assert.equal(b.values.length, 3 * NV);
  assert.equal(b.values[NV * 2 + 10], Math.fround(2 + 10 / NV));
  assert.deepEqual(Array.from(b.times), [0, 1, 2]);
  assert.equal(b.mock, false);
  assert.equal(b.precomputed, false);
});

test("decodes little-endian float32 base64 and passes precomputed through", () => {
  const values = new Float32Array(2 * NV).map((_, i) => (i % 7) - 3);
  const b64 = Buffer.from(values.buffer).toString("base64");
  const r = adaptSimulationResult(result({ precomputed: true }, { n_timesteps: 2, times_s: [0.5, 1.5], values: undefined, values_f32_b64: b64 }));
  assert.ok(r.ok);
  assert.deepEqual(Array.from(r.binding.values.slice(0, 8)), Array.from(values.slice(0, 8)));
  assert.equal(r.binding.precomputed, true);
});

test("gemini_panel and payload-less results are truthful no-cortical cases", () => {
  const panel = adaptSimulationResult(result({ simulator: "gemini_panel" }));
  assert.equal(panel.ok, false);
  assert.equal(!panel.ok && panel.code, "not_cortical");
  const missing = adaptSimulationResult(result({ meta: {} }));
  assert.equal(!missing.ok && missing.code, "not_cortical");
});

test("rejects incompatible meshes, timings and values instead of repairing them", () => {
  const cases: Array<[string, Record<string, unknown>]> = [
    ["vertex count", { n_vertices: 20000 }],
    ["mesh", { mesh: "fsaverage6" }],
    ["order", { vertex_order: "right-then-left" }],
    ["times length", { times_s: [0, 1] }],
    ["monotonic", { times_s: [0, 2, 1] }],
    ["row width", { values: rows(3, () => 0).map((r) => r.slice(1)) }],
    ["finite", { values: rows(3, (t, v) => (t === 1 && v === 5 ? Number.NaN : 0)) }],
    ["two sources", { values_f32_b64: "AAAA" }],
    ["alignment", { hemodynamic_alignment: undefined }],
  ];
  for (const [name, patch] of cases) {
    const r = adaptSimulationResult(result({}, patch));
    assert.equal(r.ok, false, name);
    assert.equal(!r.ok && r.code, "invalid", name);
  }
});

test("values_url must be resolved through the fetch hook", async () => {
  const raw = new Float32Array(NV).fill(0.25);
  const res = result({}, { n_timesteps: 1, times_s: [0], values: undefined, values_url: "/runs/a.f32" });
  assert.equal(adaptSimulationResult(res).ok, false);
  const fakeFetch = (async (url: string) => {
    assert.equal(url, "/runs/a.f32");
    return new Response(raw.buffer.slice(0));
  }) as unknown as typeof fetch;
  const fetched = await resolveCorticalValues(res, fakeFetch);
  const r = adaptSimulationResult(res, fetched);
  assert.ok(r.ok);
  assert.equal(r.binding.values[100], 0.25);
});

test("mock flag is carried so the UI can label MOCK", () => {
  const r = adaptSimulationResult(result({ meta: { ...result().meta, mock: true } }));
  assert.ok(r.ok && r.binding.mock);
});

function binding(values: number[], times = [0, 1]): CorticalBinding {
  const nT = times.length;
  const v = new Float32Array(nT * NV);
  values.forEach((x, i) => (v[i] = x));
  return { variantId: "A", simulator: "tribe_v2", version: "t", precomputed: false, mock: false, times: Float64Array.from(times), nTimesteps: nT, nVertices: NV, values: v, units: "u", alignment: "stimulus_time" };
}

test("display scale is shared across variants and leaves non-positive data gray", () => {
  assert.equal(computeDisplayScale([binding([0, -1, -2])]), null);
  const a = binding([1, 2, 3]);
  const b = binding([10]);
  const shared = computeDisplayScale([a, b]);
  assert.ok(shared);
  assert.equal(shared.threshold, shared.vmax * THRESHOLD_FRACTION);
  // The pooled scale differs from A alone: variants never auto-scale independently.
  assert.notEqual(computeDisplayScale([a])?.vmax, shared.vmax);
});

test("difference requires identical sampling", () => {
  assert.ok(canDifference(binding([1]), binding([2])).ok);
  assert.equal(canDifference(binding([1]), binding([2], [0, 1.5])).ok, false);
  assert.equal(canDifference(binding([1]), binding([2], [0, 1, 2])).ok, false);
});
