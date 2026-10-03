import assert from "node:assert/strict";
import { test } from "vitest";
import { adaptBackendTribe, backendUrl, loadBackendRun, parseActivityEvent, parseNpy, parseWorkerGroups, type BackendSimulationResult } from "../../lib/brain/backend";
import { computeRegionStatistics } from "../../lib/brain/atlas";
import { FSAVERAGE5_VERTICES } from "../../lib/brain/contract";
import { sampleAt } from "../../lib/brain/timeline";

const NV = FSAVERAGE5_VERTICES;

/** Build a little-endian float16 .npy (NumPy v1 header), as the TRIBE worker writes. */
function npyF16(rows: number, cols: number, fill: (t: number, v: number) => number): ArrayBuffer {
  const header = `{'descr': '<f2', 'fortran_order': False, 'shape': (${rows}, ${cols}), }`;
  const pad = 64 - ((10 + header.length + 1) % 64);
  const h = header + " ".repeat(pad) + "\n";
  const buf = new ArrayBuffer(10 + h.length + rows * cols * 2);
  const u8 = new Uint8Array(buf);
  u8.set([0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59, 1, 0]);
  new DataView(buf).setUint16(8, h.length, true);
  for (let i = 0; i < h.length; i++) u8[10 + i] = h.charCodeAt(i);
  const dv = new DataView(buf, 10 + h.length);
  for (let t = 0; t < rows; t++) for (let v = 0; v < cols; v++) dv.setUint16((t * cols + v) * 2, toHalf(fill(t, v)), true);
  return buf;
}

function toHalf(x: number): number {
  // Exact for the small dyadic values used below (0, ±0.25, ±0.5, 1, 2…).
  if (x === 0) return 0;
  const sign = x < 0 ? 0x8000 : 0;
  const a = Math.abs(x);
  const e = Math.floor(Math.log2(a));
  const frac = Math.round((a / Math.pow(2, e) - 1) * 1024);
  return sign | ((e + 15) << 10) | frac;
}

const SHA = "a".repeat(64);

function sim(timestamps: number[], overrides: Partial<BackendSimulationResult> = {}): BackendSimulationResult {
  return {
    variant_id: "A",
    simulator: "tribe_v2",
    version: "tribev2 test",
    hz: 1,
    video_sha256: SHA,
    duration_s: 15,
    timestamps_s: timestamps,
    series: { visual: timestamps.map(() => 0.5) },
    primary_series: "visual",
    events: [],
    precomputed: false,
    brain: { mesh: "fsaverage5", n_vertices: NV, activity_path: "activity.npy", atlas: "destrieux2009", groups_path: "groups.json" },
    meta: {},
    ...overrides,
  };
}

test("parses the worker's float16 activity.npy exactly", () => {
  const arr = parseNpy(npyF16(3, NV, (t, v) => (v === 7 ? t * 0.5 : -0.25)));
  assert.deepEqual(arr.shape, [3, NV]);
  assert.equal(arr.dtype, "<f2");
  assert.equal(arr.data[2 * NV + 7], 1);
  assert.equal(arr.data[NV], -0.25);
  assert.throws(() => parseNpy(new ArrayBuffer(8)));
});

test("adapts a genuine backend TRIBE result without shifting time", () => {
  const ts = [0, 1, 2];
  const r = adaptBackendTribe(sim(ts), parseNpy(npyF16(3, NV, () => 0.5)), { renderSha256: SHA });
  assert.ok(r.ok);
  assert.deepEqual(Array.from(r.binding.times), ts);
  assert.equal(r.binding.alignment, "stimulus_time");
  assert.equal(r.binding.videoSha256, SHA);
  assert.equal(r.binding.hz, 1);
});

test("rejects a different video, wrong shape, non-fsaverage5 or missing brain", () => {
  const act = parseNpy(npyF16(3, NV, () => 0));
  assert.equal(adaptBackendTribe(sim([0, 1, 2]), act, { renderSha256: "b".repeat(64) }).ok, false);
  assert.equal(adaptBackendTribe(sim([0, 1]), act).ok, false);
  assert.equal(adaptBackendTribe(sim([0, 1, 2], { brain: null }), act).ok, false);
  assert.equal(adaptBackendTribe(sim([0, 2, 1]), act).ok, false);
  assert.equal(adaptBackendTribe(sim([0, 1, 2], { simulator: "gemini_panel" }), act).ok, false);
});

test("worker groups drive meters and are labelled as the worker's atlas", () => {
  const groups = parseWorkerGroups({
    atlas: "Destrieux 2009 (a2009s) parcellation on fsaverage5",
    mesh: "fsaverage5",
    n_vertices: NV,
    groups: { visual: { label: "Visual cortex", known_for: "x", atlas_labels: ["S_calcarine"], vertex_indices: [0, 1] } },
  });
  const r = adaptBackendTribe(sim([0, 1]), parseNpy(npyF16(2, NV, (t, v) => (v < 2 ? 1 + t : 0))), { groups });
  assert.ok(r.ok);
  const atlas = { left: new Uint8Array(10242).fill(255), right: new Uint8Array(10242).fill(255), names: ["unknown"], unknownLabel: 255 };
  const stats = computeRegionStatistics(r.binding, atlas);
  assert.match(stats.groupSource, /^worker groups · Destrieux/);
  assert.deepEqual(Array.from(stats.groupMeans.visual), [1, 2]);
  assert.throws(() => parseWorkerGroups({ atlas: "x", groups: { v: { vertex_indices: [NV] } } }));
});

test("gaps in backend timestamps are never interpolated across", () => {
  const times = [0, 1, 5, 6];
  assert.equal(sampleAt(times, 1.5, 1).i1, 1); // held from sample 1
  assert.equal(sampleAt(times, 3, 1).inRange, false); // silent stretch: nothing shown
  assert.equal(sampleAt(times, 5.5, 1).alpha, 0.5);
});

test("validates activity frames from the SSE log", () => {
  const ok = parseActivityEvent(JSON.stringify({ at: "2026-10-03T12:00:00Z", step: "render", status: "succeeded", message: "Render A: 41.2 s", variant_id: "A", duration_s: 41.2 }));
  assert.equal(ok?.step, "render");
  assert.equal(parseActivityEvent("{"), null);
  assert.equal(parseActivityEvent(JSON.stringify({ at: "x", step: "render", status: "succeeded", message: "m" })), null);
  assert.equal(parseActivityEvent(JSON.stringify({ at: "2026-10-03T12:00:00Z", step: "dance", status: "succeeded", message: "m" })), null);
});

test("loads results and adapts artifacts through the files URLs", async () => {
  const act = npyF16(2, NV, () => 0.5);
  const calls: string[] = [];
  const fakeFetch = (async (url: string) => {
    calls.push(url);
    if (url.endsWith("/results"))
      return Response.json({
        project_id: "p1",
        state: "SIMULATED",
        variants: [
          {
            variant_id: "A",
            concept: { variant_id: "A", scenes: [{ t_start: 0, t_end: 3, text: "Hook" }] },
            render: { render_status: "rendered", video_sha256: SHA },
            simulations: [sim([0, 1])],
            files: { video: "/api/projects/p1/files/video/A", "brain-activity": "/api/projects/p1/files/brain-activity/A" },
          },
          { variant_id: "B", concept: { variant_id: "B", scenes: [] }, render: null, simulations: [], files: {} },
        ],
      });
    if (url.includes("brain-activity")) return new Response(act.slice(0));
    return new Response("missing", { status: 404 });
  }) as unknown as typeof fetch;
  const run = await loadBackendRun("http://api.test/", "p1", fakeFetch);
  assert.equal(run.state, "SIMULATED");
  assert.ok(run.bindings.A);
  assert.equal(run.bindings.B, undefined);
  assert.equal(run.videos.A, "http://api.test/api/projects/p1/files/video/A");
  assert.deepEqual(run.scenes.A, [{ t_start: 0, t_end: 3, text: "Hook" }]);
  assert.equal(calls[0], "http://api.test/api/projects/p1/results");
  assert.equal(backendUrl("http://x/", "/api/y"), "http://x/api/y");
});

test("the audio step from the sound stage is kept, not dropped as unknown", () => {
  const event = parseActivityEvent(
    JSON.stringify({ at: "2026-10-03T12:00:00Z", step: "audio", status: "succeeded", message: "Added sound to variant B", variant_id: "B", duration_s: 4.2 }),
  );
  assert.equal(event?.step, "audio");
  assert.equal(event?.variant_id, "B");
});
