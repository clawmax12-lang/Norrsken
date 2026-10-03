/**
 * Region names, groups and fixed "known for" text for the brain viewer.
 *
 * Region identities come from the Desikan-Killiany atlas (FreeSurfer `aparc`)
 * on fsaverage5, shipped in public/brain/fsaverage5. The "known for" lines are
 * a fixed list written for Preflight from standard neuroanatomy descriptions
 * and reviewed against PRD §11/§12.5 by the coding agent: they state what a
 * region is commonly studied for, never emotions, desire, buying intent or
 * guaranteed attention. They are not generated at runtime. Product/neuroscience
 * review is still requested before the demo (see README).
 */

import type { CorticalBinding, Hemisphere } from "./contract";

export type GroupId = "visual" | "auditory" | "language" | "somatomotor" | "parietal" | "frontal" | "medial_temporal" | "cingulate_insula";

export interface RegionGroup {
  id: GroupId;
  label: string;
  knownFor: string;
  /** Shown as a live meter (PRD §12.2 beat 3). */
  meter: boolean;
}

export const REGION_GROUPS: Record<GroupId, RegionGroup> = {
  visual: { id: "visual", label: "Visual", knownFor: "Occipital and ventral temporal cortex that processes what is seen.", meter: true },
  auditory: { id: "auditory", label: "Auditory", knownFor: "Superior temporal cortex that processes sound, including speech.", meter: true },
  language: { id: "language", label: "Language", knownFor: "Frontal and temporal regions engaged when processing words and sentences.", meter: true },
  somatomotor: { id: "somatomotor", label: "Somatomotor", knownFor: "Strips of cortex that control movement and process touch.", meter: false },
  parietal: { id: "parietal", label: "Parietal", knownFor: "Cortex that combines spatial and multisensory information.", meter: false },
  frontal: { id: "frontal", label: "Frontal", knownFor: "Prefrontal cortex involved in planning and cognitive control.", meter: false },
  medial_temporal: { id: "medial_temporal", label: "Medial temporal", knownFor: "Cortex linked with memory and recognizing places.", meter: false },
  cingulate_insula: { id: "cingulate_insula", label: "Cingulate and insula", knownFor: "Medial and deep cortex involved in monitoring and bodily signals.", meter: false },
};

export const METER_GROUPS: GroupId[] = ["visual", "auditory", "language"];

export interface RegionInfo {
  /** FreeSurfer aparc name, as stored in the manifest. */
  key: string;
  name: string;
  group: GroupId;
  knownFor: string;
}

/** Fixed, hand-written list. Keys must match the manifest's atlas names. */
export const REGION_INFO: Record<string, Omit<RegionInfo, "key">> = {
  pericalcarine: { name: "Pericalcarine cortex", group: "visual", knownFor: "Primary visual cortex (V1) around the calcarine sulcus; the first cortical stage of seeing." },
  cuneus: { name: "Cuneus", group: "visual", knownFor: "Medial occipital visual cortex above the calcarine sulcus; processes the lower visual field." },
  lingual: { name: "Lingual gyrus", group: "visual", knownFor: "Medial occipital visual cortex below the calcarine sulcus; studied in processing scenes and color." },
  lateraloccipital: { name: "Lateral occipital cortex", group: "visual", knownFor: "Lateral visual cortex that responds to object shape and visual motion." },
  fusiform: { name: "Fusiform gyrus", group: "visual", knownFor: "Ventral visual cortex involved in recognizing faces, objects and written words." },
  inferiortemporal: { name: "Inferior temporal gyrus", group: "visual", knownFor: "Ventral temporal cortex involved in high-level visual object recognition." },
  transversetemporal: { name: "Transverse temporal gyrus", group: "auditory", knownFor: "Heschl's gyrus: primary auditory cortex, the first cortical stage of hearing." },
  superiortemporal: { name: "Superior temporal gyrus", group: "auditory", knownFor: "Auditory association cortex that processes complex sounds and speech." },
  bankssts: { name: "Banks of the superior temporal sulcus", group: "language", knownFor: "Multisensory cortex studied in speech and voice perception." },
  middletemporal: { name: "Middle temporal gyrus", group: "language", knownFor: "Lateral temporal cortex involved in understanding word and sentence meaning." },
  parsopercularis: { name: "Pars opercularis", group: "language", knownFor: "Part of Broca's area (usually left-dominant); involved in speech production and sentence structure." },
  parstriangularis: { name: "Pars triangularis", group: "language", knownFor: "Part of Broca's area (usually left-dominant); involved in retrieving and selecting word meaning." },
  parsorbitalis: { name: "Pars orbitalis", group: "language", knownFor: "Front of the inferior frontal gyrus; studied in processing word meaning." },
  precentral: { name: "Precentral gyrus", group: "somatomotor", knownFor: "Primary motor cortex; controls voluntary movement, including the mouth and face." },
  postcentral: { name: "Postcentral gyrus", group: "somatomotor", knownFor: "Primary somatosensory cortex; processes touch and body position." },
  paracentral: { name: "Paracentral lobule", group: "somatomotor", knownFor: "Medial continuation of the motor and touch strips, representing the legs and feet." },
  superiorparietal: { name: "Superior parietal lobule", group: "parietal", knownFor: "Dorsal parietal cortex involved in spatial processing and visually guided reaching." },
  inferiorparietal: { name: "Inferior parietal lobule", group: "parietal", knownFor: "Includes the angular gyrus; studied in reading, number and spatial tasks." },
  supramarginal: { name: "Supramarginal gyrus", group: "parietal", knownFor: "Studied in processing speech sounds and relating touch to space." },
  precuneus: { name: "Precuneus", group: "parietal", knownFor: "Medial parietal cortex studied in visuospatial imagery and memory retrieval." },
  superiorfrontal: { name: "Superior frontal gyrus", group: "frontal", knownFor: "Dorsal frontal cortex including the supplementary motor area; involved in planning movement." },
  rostralmiddlefrontal: { name: "Rostral middle frontal gyrus", group: "frontal", knownFor: "Dorsolateral prefrontal cortex; involved in working memory and planning." },
  caudalmiddlefrontal: { name: "Caudal middle frontal gyrus", group: "frontal", knownFor: "Contains the frontal eye fields, which help control voluntary eye movements." },
  lateralorbitofrontal: { name: "Lateral orbitofrontal cortex", group: "frontal", knownFor: "Ventral frontal cortex studied in flexible decision-making and in taste and smell." },
  medialorbitofrontal: { name: "Medial orbitofrontal cortex", group: "frontal", knownFor: "Ventromedial frontal cortex studied in decision-making." },
  frontalpole: { name: "Frontal pole", group: "frontal", knownFor: "Most anterior prefrontal cortex; studied in complex, multi-step planning." },
  entorhinal: { name: "Entorhinal cortex", group: "medial_temporal", knownFor: "Main gateway between the neocortex and the hippocampus; studied in memory and navigation." },
  parahippocampal: { name: "Parahippocampal gyrus", group: "medial_temporal", knownFor: "Medial temporal cortex involved in recognizing places and scenes." },
  temporalpole: { name: "Temporal pole", group: "medial_temporal", knownFor: "Anterior tip of the temporal lobe; studied in knowledge about people and objects." },
  caudalanteriorcingulate: { name: "Caudal anterior cingulate", group: "cingulate_insula", knownFor: "Medial frontal cortex involved in monitoring performance and conflict during tasks." },
  rostralanteriorcingulate: { name: "Rostral anterior cingulate", group: "cingulate_insula", knownFor: "Anterior medial cortex studied in autonomic regulation and outcome monitoring." },
  posteriorcingulate: { name: "Posterior cingulate", group: "cingulate_insula", knownFor: "Posterior medial hub of the default mode network; studied in memory." },
  isthmuscingulate: { name: "Isthmus of the cingulate", group: "cingulate_insula", knownFor: "Links the posterior cingulate with medial temporal cortex; studied in memory and orientation." },
  insula: { name: "Insula", group: "cingulate_insula", knownFor: "Cortex deep in the lateral sulcus; studied in sensing bodily signals, taste and speech articulation." },
};

export interface AtlasRegionRecord {
  index: number;
  name: string;
  rgb: [number, number, number];
}

export function regionInfo(atlasName: string | undefined): RegionInfo | undefined {
  if (!atlasName) return undefined;
  const info = REGION_INFO[atlasName];
  return info ? { key: atlasName, ...info } : undefined;
}

export interface AtlasLabels {
  left: Uint8Array;
  right: Uint8Array;
  /** Atlas table names indexed by label value. */
  names: string[];
  unknownLabel: number;
}

/** Stable per-region key used for selection, e.g. "left:superiortemporal". */
export function regionKey(hemi: Hemisphere, name: string): string {
  return `${hemi}:${name}`;
}

export interface RegionStatistics {
  /** Region keys in column order. */
  keys: string[];
  /** Row-major [t][key] mean of genuine vertex values. */
  regionMeans: Float32Array;
  groupMeans: Record<GroupId, Float32Array>;
  nTimesteps: number;
}

/**
 * Per-sample means over atlas regions and groups. A deterministic reduction of
 * the bound values; it does not create samples or alter timing.
 */
export function computeRegionStatistics(binding: CorticalBinding, atlas: AtlasLabels): RegionStatistics {
  const nT = binding.nTimesteps;
  const perHemi = atlas.left.length;
  const keys: string[] = [];
  const columnOf = new Map<string, number>();
  const vertexColumn = new Int32Array(perHemi * 2).fill(-1);
  const vertexGroup: (GroupId | null)[] = new Array(perHemi * 2).fill(null);
  (["left", "right"] as const).forEach((hemi, h) => {
    const labels = hemi === "left" ? atlas.left : atlas.right;
    for (let v = 0; v < perHemi; v++) {
      const label = labels[v];
      if (label === atlas.unknownLabel) continue;
      const name = atlas.names[label];
      const info = REGION_INFO[name];
      if (!info) continue;
      const key = regionKey(hemi, name);
      let col = columnOf.get(key);
      if (col === undefined) {
        col = keys.length;
        keys.push(key);
        columnOf.set(key, col);
      }
      vertexColumn[h * perHemi + v] = col;
      vertexGroup[h * perHemi + v] = info.group;
    }
  });

  const counts = new Float32Array(keys.length);
  for (let i = 0; i < vertexColumn.length; i++) if (vertexColumn[i] >= 0) counts[vertexColumn[i]]++;
  const groupIds = Object.keys(REGION_GROUPS) as GroupId[];
  const groupCounts = Object.fromEntries(groupIds.map((g) => [g, 0])) as Record<GroupId, number>;
  for (const g of vertexGroup) if (g) groupCounts[g]++;

  const regionMeans = new Float32Array(nT * keys.length);
  const groupMeans = Object.fromEntries(groupIds.map((g) => [g, new Float32Array(nT)])) as Record<GroupId, Float32Array>;
  for (let t = 0; t < nT; t++) {
    const base = t * binding.nVertices;
    const rowOffset = t * keys.length;
    for (let v = 0; v < vertexColumn.length; v++) {
      const col = vertexColumn[v];
      if (col < 0) continue;
      const value = binding.values[base + v];
      regionMeans[rowOffset + col] += value;
      groupMeans[vertexGroup[v] as GroupId][t] += value;
    }
    for (let c = 0; c < keys.length; c++) regionMeans[rowOffset + c] /= counts[c];
    for (const g of groupIds) if (groupCounts[g] > 0) groupMeans[g][t] /= groupCounts[g];
  }
  return { keys, regionMeans, groupMeans, nTimesteps: nT };
}

export function regionSeries(stats: RegionStatistics, key: string): Float32Array | undefined {
  const col = stats.keys.indexOf(key);
  if (col < 0) return undefined;
  const out = new Float32Array(stats.nTimesteps);
  for (let t = 0; t < stats.nTimesteps; t++) out[t] = stats.regionMeans[t * stats.keys.length + col];
  return out;
}

/** Sample index and region with the highest mean genuine response (intro lock-on). */
export function strongestMoment(stats: RegionStatistics): { sampleIndex: number; key: string; value: number } | null {
  let best: { sampleIndex: number; key: string; value: number } | null = null;
  for (let t = 0; t < stats.nTimesteps; t++) {
    for (let c = 0; c < stats.keys.length; c++) {
      const value = stats.regionMeans[t * stats.keys.length + c];
      if (!best || value > best.value) best = { sampleIndex: t, key: stats.keys[c], value };
    }
  }
  return best && best.value > 0 ? best : null;
}
