/**
 * Read-only client for the backend contracts on `Mihir-Bhargav/hackathon-project-overview`
 * @ 8970609 (FastAPI). Nothing here changes worker or backend contracts; it consumes them:
 *
 * - `GET /api/projects/{id}/log` — SSE, `event: activity` frames with a numeric `id` and an
 *   `ActivityEvent` payload, then one `event: end` frame (do not reconnect after it).
 * - `GET /api/projects/{id}/results` — `ResultsResponse` with per-variant concept, render record,
 *   simulations and file URLs (`video`, `brain-activity`, `brain-groups`).
 * - The TRIBE `SimulationResult.brain` artifact: little-endian float16 `.npy`
 *   `[len(timestamps_s), 20484]`, left hemisphere first, plus a Destrieux `groups.json`.
 *   The worker states its timestamps already compensate the 5 s hemodynamic lag, so the
 *   adapter never shifts them again.
 */

import { FSAVERAGE5_VERTICES, type CorticalBinding, type SceneRef } from "./contract";

// ------------------------------------------------------------------ contracts (subset)

export type BackendStep = "plan" | "generate" | "render" | "simulate" | "score" | "explain" | "iterate" | "export";
export type BackendStepStatus = "started" | "succeeded" | "failed" | "skipped";
export type BackendRunState = "BRIEF_RECEIVED" | "PLANNED" | "RENDERED" | "SIMULATED" | "SCORED" | "EXPLAINED" | "ITERATED" | "DONE" | "FAILED";

const STEPS: readonly BackendStep[] = ["plan", "generate", "render", "simulate", "score", "explain", "iterate", "export"];
const STATUSES: readonly BackendStepStatus[] = ["started", "succeeded", "failed", "skipped"];

export interface ActivityEvent {
  at: string;
  step: BackendStep;
  status: BackendStepStatus;
  message: string;
  variant_id: string | null;
  duration_s: number | null;
}

export interface BackendBrainArtifact {
  mesh: "fsaverage5";
  n_vertices: number;
  activity_path: string;
  atlas: string;
  groups_path: string;
}

export interface BackendSimulationResult {
  variant_id: string;
  simulator: string;
  version: string;
  hz: number;
  video_sha256: string;
  duration_s: number;
  timestamps_s: number[];
  series: Record<string, number[]>;
  primary_series: string;
  events: Array<{ t: number; type: string; label: string }>;
  precomputed: boolean;
  brain: BackendBrainArtifact | null;
  meta: Record<string, unknown>;
}

export interface BackendVariantResults {
  variant_id: string;
  concept: { variant_id: string; scenes: Array<{ t_start: number; t_end: number; text: string; source_field?: string }> };
  render: { render_status: string; video_sha256?: string | null; render_seconds?: number | null } | null;
  simulations: BackendSimulationResult[];
  files: Record<string, string>;
}

export interface BackendResults {
  project_id: string;
  state: BackendRunState;
  variants: BackendVariantResults[];
}

/** Validate one `activity` frame's data; returns null for anything malformed. */
export function parseActivityEvent(data: string): ActivityEvent | null {
  let raw: unknown;
  try {
    raw = JSON.parse(data);
  } catch {
    return null;
  }
  const e = raw as Partial<ActivityEvent>;
  if (!e || typeof e !== "object") return null;
  if (typeof e.at !== "string" || Number.isNaN(Date.parse(e.at))) return null;
  if (!STEPS.includes(e.step as BackendStep) || !STATUSES.includes(e.status as BackendStepStatus)) return null;
  if (typeof e.message !== "string" || !e.message) return null;
  return {
    at: e.at,
    step: e.step as BackendStep,
    status: e.status as BackendStepStatus,
    message: e.message,
    variant_id: typeof e.variant_id === "string" ? e.variant_id : null,
    duration_s: typeof e.duration_s === "number" && Number.isFinite(e.duration_s) ? e.duration_s : null,
  };
}

// --------------------------------------------------------------------------- .npy

export interface NpyArray {
  shape: number[];
  data: Float32Array;
  dtype: "<f2" | "<f4";
}

function halfToFloat(h: number): number {
  const sign = h & 0x8000 ? -1 : 1;
  const exp = (h >> 10) & 0x1f;
  const frac = h & 0x3ff;
  if (exp === 0) return sign * Math.pow(2, -14) * (frac / 1024);
  if (exp === 31) return frac ? Number.NaN : sign * Infinity;
  return sign * Math.pow(2, exp - 15) * (1 + frac / 1024);
}

/** Parse a NumPy v1/v2/v3 `.npy` with little-endian float16/float32 data in C order. */
export function parseNpy(buffer: ArrayBuffer): NpyArray {
  const bytes = new Uint8Array(buffer);
  const magic = [0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59];
  if (bytes.length < 10 || magic.some((b, i) => bytes[i] !== b)) throw new Error("not a .npy file");
  const major = bytes[6];
  const view = new DataView(buffer);
  const headerLen = major === 1 ? view.getUint16(8, true) : view.getUint32(8, true);
  const headerStart = major === 1 ? 10 : 12;
  const header = new TextDecoder("latin1").decode(bytes.subarray(headerStart, headerStart + headerLen));
  const descr = /'descr':\s*'([^']+)'/.exec(header)?.[1];
  const fortran = /'fortran_order':\s*(True|False)/.exec(header)?.[1];
  const shapeText = /'shape':\s*\(([^)]*)\)/.exec(header)?.[1];
  if (descr !== "<f2" && descr !== "<f4") throw new Error(`unsupported dtype ${descr ?? "?"}`);
  if (fortran !== "False") throw new Error("Fortran-ordered arrays are not supported");
  if (shapeText === undefined) throw new Error("missing shape");
  const shape = shapeText.split(",").map((s) => s.trim()).filter(Boolean).map(Number);
  if (shape.some((n) => !Number.isInteger(n) || n < 0)) throw new Error("invalid shape");
  const count = shape.reduce((a, b) => a * b, 1);
  const offset = headerStart + headerLen;
  const width = descr === "<f2" ? 2 : 4;
  if (bytes.length - offset < count * width) throw new Error("truncated data");
  const out = new Float32Array(count);
  for (let i = 0; i < count; i++) out[i] = width === 2 ? halfToFloat(view.getUint16(offset + i * 2, true)) : view.getFloat32(offset + i * 4, true);
  return { shape, data: out, dtype: descr };
}

// ------------------------------------------------------------------ groups.json

export interface WorkerGroup {
  id: string;
  label: string;
  knownFor: string;
  atlasLabels: string[];
  vertexIndices: Uint32Array;
}

export interface WorkerGroups {
  /** The worker's atlas, e.g. "Destrieux 2009 (a2009s) …" — not the viewer's picking atlas. */
  atlas: string;
  groups: WorkerGroup[];
}

export function parseWorkerGroups(json: unknown, nVertices = FSAVERAGE5_VERTICES): WorkerGroups {
  const g = json as { atlas?: unknown; mesh?: unknown; n_vertices?: unknown; groups?: Record<string, { label?: unknown; known_for?: unknown; atlas_labels?: unknown; vertex_indices?: unknown }> };
  if (!g || typeof g !== "object" || typeof g.atlas !== "string" || !g.groups || typeof g.groups !== "object") throw new Error("groups.json: unexpected shape");
  if (g.mesh !== undefined && g.mesh !== "fsaverage5") throw new Error("groups.json: mesh is not fsaverage5");
  if (g.n_vertices !== undefined && g.n_vertices !== nVertices) throw new Error("groups.json: vertex count differs");
  const groups: WorkerGroup[] = Object.entries(g.groups).map(([id, v]) => {
    const idx = Array.isArray(v.vertex_indices) ? v.vertex_indices : [];
    if (!idx.every((n) => Number.isInteger(n) && n >= 0 && n < nVertices)) throw new Error(`groups.json: ${id} has out-of-range vertices`);
    return {
      id,
      label: typeof v.label === "string" ? v.label : id,
      knownFor: typeof v.known_for === "string" ? v.known_for : "",
      atlasLabels: Array.isArray(v.atlas_labels) ? v.atlas_labels.map(String) : [],
      vertexIndices: Uint32Array.from(idx as number[]),
    };
  });
  return { atlas: g.atlas, groups };
}

// --------------------------------------------------------------------- adapter

export type BackendAdaptResult = { ok: true; binding: CorticalBinding } | { ok: false; reason: string };

/**
 * Turn one backend TRIBE result plus its downloaded artifacts into a viewer binding.
 * Rejects (never repairs) mismatched shapes, meshes, hashes or non-finite values.
 */
export function adaptBackendTribe(
  sim: BackendSimulationResult,
  activity: NpyArray,
  options: { renderSha256?: string | null; groups?: WorkerGroups; videoUrl?: string } = {},
): BackendAdaptResult {
  if (sim.simulator !== "tribe_v2") return { ok: false, reason: `simulator ${sim.simulator} has no cortical data` };
  if (!sim.brain) return { ok: false, reason: "result has no brain artifact" };
  if (sim.brain.mesh !== "fsaverage5" || sim.brain.n_vertices !== FSAVERAGE5_VERTICES) return { ok: false, reason: "brain artifact is not fsaverage5 with 20,484 vertices" };
  if (options.renderSha256 && options.renderSha256 !== sim.video_sha256) return { ok: false, reason: "result belongs to a different video (sha256 mismatch)" };
  const times = sim.timestamps_s;
  if (!Array.isArray(times) || times.length === 0) return { ok: false, reason: "no timestamps" };
  for (let i = 1; i < times.length; i++) if (!(times[i] > times[i - 1])) return { ok: false, reason: "timestamps are not strictly increasing" };
  if (activity.shape.length !== 2 || activity.shape[0] !== times.length || activity.shape[1] !== FSAVERAGE5_VERTICES) {
    return { ok: false, reason: `activity shape ${activity.shape.join("×")} does not match ${times.length}×${FSAVERAGE5_VERTICES}` };
  }
  for (let i = 0; i < activity.data.length; i++) if (!Number.isFinite(activity.data[i])) return { ok: false, reason: `activity value ${i} is not finite` };
  return {
    ok: true,
    binding: {
      variantId: sim.variant_id,
      simulator: sim.simulator,
      version: sim.version,
      precomputed: sim.precomputed === true,
      mock: sim.meta?.mock === true,
      times: Float64Array.from(times),
      nTimesteps: times.length,
      nVertices: FSAVERAGE5_VERTICES,
      values: activity.data,
      units: "predicted response (TRIBE v2 model units)",
      // The worker documents that its timestamps already include the hemodynamic compensation.
      alignment: "stimulus_time",
      hz: sim.hz,
      videoSha256: sim.video_sha256,
      video: { url: options.videoUrl, duration_s: sim.duration_s, sha256: sim.video_sha256 },
      workerGroups: options.groups,
    },
  };
}

/** Join a backend-relative path (`/api/...`) to the configured API base. */
export function backendUrl(apiBase: string, path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${apiBase.replace(/\/+$/, "")}${path.startsWith("/") ? "" : "/"}${path}`;
}

export interface AdaptedRun {
  state: BackendRunState;
  bindings: Record<string, CorticalBinding>;
  scenes: Record<string, SceneRef[]>;
  videos: Record<string, string>;
  /** Per-variant reasons a TRIBE result was not shown (honest "No brain data" detail). */
  problems: string[];
}

/** Fetch results and adapt every variant's genuine TRIBE artifact. No inference is triggered. */
export async function loadBackendRun(apiBase: string, projectId: string, fetchImpl: typeof fetch = fetch): Promise<AdaptedRun> {
  const res = await fetchImpl(backendUrl(apiBase, `/api/projects/${encodeURIComponent(projectId)}/results`));
  if (!res.ok) throw new Error(`results request failed (${res.status})`);
  const results = (await res.json()) as BackendResults;
  const out: AdaptedRun = { state: results.state, bindings: {}, scenes: {}, videos: {}, problems: [] };
  for (const v of results.variants ?? []) {
    out.scenes[v.variant_id] = (v.concept?.scenes ?? []).map((s) => ({ t_start: s.t_start, t_end: s.t_end, text: s.text }));
    if (v.files?.video) out.videos[v.variant_id] = backendUrl(apiBase, v.files.video);
    const sim = v.simulations?.find((s) => s.simulator === "tribe_v2");
    if (!sim) continue;
    if (!sim.brain || !v.files?.["brain-activity"]) {
      out.problems.push(`Variant ${v.variant_id}: TRIBE result has no downloadable brain activity`);
      continue;
    }
    try {
      const [actRes, groupsRes] = await Promise.all([
        fetchImpl(backendUrl(apiBase, v.files["brain-activity"])),
        v.files["brain-groups"] ? fetchImpl(backendUrl(apiBase, v.files["brain-groups"])) : Promise.resolve(null),
      ]);
      if (!actRes.ok) throw new Error(`brain activity request failed (${actRes.status})`);
      const activity = parseNpy(await actRes.arrayBuffer());
      const groups = groupsRes && groupsRes.ok ? parseWorkerGroups(await groupsRes.json()) : undefined;
      const adapted = adaptBackendTribe(sim, activity, { renderSha256: v.render?.video_sha256 ?? null, groups, videoUrl: out.videos[v.variant_id] });
      if (adapted.ok) out.bindings[v.variant_id] = adapted.binding;
      else out.problems.push(`Variant ${v.variant_id}: ${adapted.reason}`);
    } catch (e) {
      out.problems.push(`Variant ${v.variant_id}: ${(e as Error).message}`);
    }
  }
  return out;
}
