/**
 * Brain-viewer side of the shared simulator boundary (PRD §10.2/§10.3).
 *
 * `SimulationResult` mirrors the simplified PRD contract exactly. The cortical
 * payload is NOT yet specified by the PRD; `CorticalPayloadV0` is this viewer's
 * proposal, carried inside `meta.cortical` so the agreed top-level keys stay
 * unchanged. It must be agreed with the TRIBE worker owner before the worker
 * emits it (TEAM.md "Implementation clarifications"). Everything here is
 * type-only so pure modules and tests can share it.
 */

import type { WorkerGroups } from "./backend";

export type VariantId = "A" | "B" | "C";

export interface SimulationEvent {
  t: number;
  type: "hold" | "drop";
  label: string;
}

/** PRD §10.3 SimulationResult (simplified), unchanged. */
export interface SimulationResult {
  variant_id: string;
  simulator: "tribe_v2" | "gemini_panel" | (string & {});
  version: string;
  hz: number;
  series: Record<string, number[]>;
  events: SimulationEvent[];
  precomputed: boolean;
  meta: Record<string, unknown>;
}

export const CORTICAL_SCHEMA = "preflight.cortical.v0";
export const FSAVERAGE5_VERTICES_PER_HEMI = 10242;
export const FSAVERAGE5_VERTICES = FSAVERAGE5_VERTICES_PER_HEMI * 2;
export const FSAVERAGE5_VERTEX_ORDER = "nilearn-fsaverage5:left-then-right";

/**
 * Proposed `meta.cortical` payload for `simulator: "tribe_v2"` (v0, unagreed).
 *
 * Values are TRIBE's genuine per-vertex predictions, row-major `[t][vertex]`,
 * vertex order as returned by TRIBE on nilearn's fsaverage5 (left 10,242 then
 * right 10,242). `times_s[i]` is the video time in seconds that sample `i`
 * describes, after whatever hemodynamic alignment the worker applied; record
 * that choice in `hemodynamic_alignment` so nobody shifts it twice.
 * Supply exactly one of `values`, `values_f32_b64` or `values_url`.
 */
export interface CorticalPayloadV0 {
  schema: typeof CORTICAL_SCHEMA;
  mesh: "fsaverage5";
  vertex_order: typeof FSAVERAGE5_VERTEX_ORDER;
  n_vertices: number;
  n_timesteps: number;
  times_s: number[];
  hemodynamic_alignment: "stimulus_time" | "acquisition_time";
  units: string;
  values?: number[][];
  /** Base64 of little-endian float32, row-major [t][vertex]. */
  values_f32_b64?: string;
  /** Same-origin URL of raw little-endian float32, row-major [t][vertex]. */
  values_url?: string;
}

/** Optional video reference the result was computed from (`meta.video`). */
export interface AnalyzedVideoRef {
  url?: string;
  duration_s?: number;
  sha256?: string;
}

/** Scene timing from the variant's CreativeConcept (PRD §10.3). */
export interface SceneRef {
  t_start: number;
  t_end: number;
  text: string;
}

/** Validated, viewer-ready binding of one genuine (or test-MOCK) result. */
export interface CorticalBinding {
  variantId: string;
  simulator: string;
  version: string;
  precomputed: boolean;
  /** True only for test fixtures; the UI must then show a MOCK banner. */
  mock: boolean;
  times: Float64Array;
  nTimesteps: number;
  nVertices: number;
  /** Row-major [t * nVertices + v]. Never modified after binding. */
  values: Float32Array;
  units: string;
  alignment: CorticalPayloadV0["hemodynamic_alignment"];
  video?: AnalyzedVideoRef;
  /** Nominal sample rate; with it, interpolation never bridges a gap in `times`. */
  hz?: number;
  /** Hash of the exact analyzed video, when the producer supplies one. */
  videoSha256?: string;
  /** Producer-defined region groups (e.g. the TRIBE worker's Destrieux groups.json). */
  workerGroups?: WorkerGroups;
}

export type AdaptResult =
  | { ok: true; binding: CorticalBinding }
  | { ok: false; reason: string; code: "not_cortical" | "invalid" };

/** Display normalization shared by every instance that is compared. */
export interface DisplayScale {
  /** Values at/above this are fully saturated (yellow). */
  vmax: number;
  /** Values below this stay anatomical gray. */
  threshold: number;
  rule: string;
}

/** Camera state shared between synchronized instances (FR-15 groundwork). */
export interface CameraState {
  position: [number, number, number];
  target: [number, number, number];
  zoom: number;
}

export type SurfaceKind = "pial" | "inflated";
export type Hemisphere = "left" | "right";
