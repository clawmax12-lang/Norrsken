/**
 * TEST-ONLY MOCK cortical results (PRD §15 rule 2).
 *
 * Deterministic synthetic patterns shaped by atlas groups so the shader,
 * meters, curves and intro can be exercised before genuine TRIBE output
 * exists. Every result is flagged `meta.mock = true`; the viewer then shows a
 * MOCK banner. This is not simulation output and must never be used as
 * evidence, in the demo path or in production builds (the app only imports it
 * behind a development-only guard).
 */

import { CORTICAL_SCHEMA, FSAVERAGE5_VERTEX_ORDER, type SceneRef, type SimulationResult, type VariantId } from "../../../lib/brain/contract";
import { REGION_INFO, type AtlasLabels, type GroupId } from "../../../lib/brain/atlas";

const N_T = 15;

/** Smooth bump centred on c with width w (seconds). */
function bump(t: number, c: number, w: number): number {
  const x = (t - c) / w;
  return Math.exp(-x * x);
}

const ENVELOPES: Record<VariantId, Partial<Record<GroupId, (t: number) => number>>> = {
  A: {
    visual: (t) => 0.55 + 0.45 * (bump(t, 1, 1.2) + bump(t, 5, 1.2) + bump(t, 10, 1.4)),
    auditory: (t) => 0.7 * bump(t, 6, 2.5),
    language: (t) => 0.9 * bump(t, 3, 1.5) + 0.5 * bump(t, 12, 1.5),
  },
  B: {
    visual: (t) => 0.4 + 0.5 * (bump(t, 2, 1.5) + bump(t, 8, 1.5)),
    auditory: (t) => 0.4 * bump(t, 9, 3),
    language: (t) => 0.6 * bump(t, 6, 2),
  },
  C: {
    visual: (t) => 0.6 + 0.6 * (bump(t, 3, 1) + bump(t, 7, 1) + bump(t, 11, 1)),
    auditory: (t) => 0.8 * bump(t, 4, 2),
    language: (t) => 1.0 * bump(t, 9, 1.8),
  },
};

export const MOCK_SCENES: Record<VariantId, SceneRef[]> = {
  A: [
    { t_start: 0, t_end: 3, text: "MOCK scene 1 · hook text" },
    { t_start: 3, t_end: 7, text: "MOCK scene 2 · product screen" },
    { t_start: 7, t_end: 11, text: "MOCK scene 3 · feature screen" },
    { t_start: 11, t_end: 15, text: "MOCK scene 4 · call to action" },
  ],
  B: [
    { t_start: 0, t_end: 5, text: "MOCK scene 1 · outcome first" },
    { t_start: 5, t_end: 10, text: "MOCK scene 2 · product screen" },
    { t_start: 10, t_end: 15, text: "MOCK scene 3 · call to action" },
  ],
  C: [
    { t_start: 0, t_end: 4, text: "MOCK scene 1 · product first" },
    { t_start: 4, t_end: 8, text: "MOCK scene 2 · detail screen" },
    { t_start: 8, t_end: 12, text: "MOCK scene 3 · second screen" },
    { t_start: 12, t_end: 15, text: "MOCK scene 4 · call to action" },
  ],
};

export function buildMockResult(variant: VariantId, atlas: AtlasLabels, sulc: { left: Float32Array; right: Float32Array }): SimulationResult {
  const perHemi = atlas.left.length;
  const nV = perHemi * 2;
  const env = ENVELOPES[variant];
  const groupOf: (GroupId | null)[] = new Array(nV).fill(null);
  const texture = new Float32Array(nV);
  (["left", "right"] as const).forEach((hemi, h) => {
    const labels = atlas[hemi];
    const s = sulc[hemi];
    for (let v = 0; v < perHemi; v++) {
      const info = REGION_INFO[atlas.names[labels[v]]];
      groupOf[h * perHemi + v] = info ? info.group : null;
      // Gyral crowns slightly stronger than fundi, so the pattern follows folds.
      texture[h * perHemi + v] = 1 - 0.35 * Math.max(-1, Math.min(1, s[v]));
    }
  });
  const values: number[][] = [];
  for (let t = 0; t < N_T; t++) {
    const row = new Array<number>(nV);
    for (let v = 0; v < nV; v++) {
      const g = groupOf[v];
      const f = g ? env[g] : undefined;
      row[v] = f ? 0.25 * f(t) * texture[v] - 0.03 : -0.03;
    }
    values.push(row);
  }
  return {
    variant_id: variant,
    simulator: "tribe_v2",
    version: "MOCK-fixture",
    hz: 1,
    series: {},
    events: [],
    precomputed: false,
    meta: {
      mock: true,
      note: "MOCK synthetic fixture for tests; not a simulation result",
      cortical: {
        schema: CORTICAL_SCHEMA,
        mesh: "fsaverage5",
        vertex_order: FSAVERAGE5_VERTEX_ORDER,
        n_vertices: nV,
        n_timesteps: N_T,
        times_s: Array.from({ length: N_T }, (_, i) => i),
        hemodynamic_alignment: "stimulus_time",
        units: "MOCK units",
        values,
      },
    },
  };
}
