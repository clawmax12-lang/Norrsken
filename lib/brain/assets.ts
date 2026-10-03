/**
 * Loads the committed fsaverage5 mesh + atlas once per browser session.
 * Every viewer instance shares the returned object; it is never mutated.
 */

import type { Hemisphere } from "./contract";
import type { AtlasLabels, AtlasRegionRecord } from "./atlas";

export const BRAIN_ASSET_BASE = "/brain/fsaverage5";

interface LayoutEntry {
  offset: number;
  length: number;
  dtype: "float32" | "uint8" | "uint16";
}

export interface BrainManifest {
  mesh: "fsaverage5";
  vertex_order: string;
  vertices_per_hemisphere: number;
  faces_per_hemisphere: number;
  binary: string;
  binary_sha256: string;
  layout: Record<Hemisphere, Record<"pial" | "inflated" | "sulc" | "curv" | "labels" | "faces", LayoutEntry>>;
  atlas: { name: string; unknown_label: number; regions: AtlasRegionRecord[] };
}

export interface HemisphereAssets {
  pial: Float32Array;
  inflated: Float32Array;
  sulc: Float32Array;
  curv: Float32Array;
  labels: Uint8Array;
  faces: Uint16Array;
}

export interface BrainAssets {
  manifest: BrainManifest;
  left: HemisphereAssets;
  right: HemisphereAssets;
  atlas: AtlasLabels;
}

function view(buffer: ArrayBuffer, entry: LayoutEntry): Float32Array | Uint8Array | Uint16Array {
  switch (entry.dtype) {
    case "float32":
      return new Float32Array(buffer, entry.offset, entry.length);
    case "uint16":
      return new Uint16Array(buffer, entry.offset, entry.length);
    case "uint8":
      return new Uint8Array(buffer, entry.offset, entry.length);
  }
}

export function parseBrainAssets(manifest: BrainManifest, buffer: ArrayBuffer): BrainAssets {
  const n = manifest.vertices_per_hemisphere;
  const hemi = (h: Hemisphere): HemisphereAssets => {
    const l = manifest.layout[h];
    const out = {
      pial: view(buffer, l.pial) as Float32Array,
      inflated: view(buffer, l.inflated) as Float32Array,
      sulc: view(buffer, l.sulc) as Float32Array,
      curv: view(buffer, l.curv) as Float32Array,
      labels: view(buffer, l.labels) as Uint8Array,
      faces: view(buffer, l.faces) as Uint16Array,
    };
    if (out.pial.length !== n * 3 || out.labels.length !== n || out.faces.length !== manifest.faces_per_hemisphere * 3) {
      throw new Error(`fsaverage5 ${h} hemisphere asset has unexpected size`);
    }
    return out;
  };
  const left = hemi("left");
  const right = hemi("right");
  const names: string[] = [];
  for (const r of manifest.atlas.regions) names[r.index] = r.name;
  return { manifest, left, right, atlas: { left: left.labels, right: right.labels, names, unknownLabel: manifest.atlas.unknown_label } };
}

let cached: Promise<BrainAssets> | null = null;
let loadCount = 0;

/** Number of network loads performed (tests/diagnostics: must stay 1). */
export function brainAssetLoadCount(): number {
  return loadCount;
}

export function loadBrainAssets(fetchImpl: typeof fetch = fetch, base = BRAIN_ASSET_BASE): Promise<BrainAssets> {
  if (!cached) {
    loadCount++;
    cached = (async () => {
      const manifestResponse = await fetchImpl(`${base}/manifest.json`);
      if (!manifestResponse.ok) throw new Error(`Brain manifest failed to load (${manifestResponse.status})`);
      const manifest = (await manifestResponse.json()) as BrainManifest;
      const binResponse = await fetchImpl(`${base}/${manifest.binary}`);
      if (!binResponse.ok) throw new Error(`Brain mesh failed to load (${binResponse.status})`);
      return parseBrainAssets(manifest, await binResponse.arrayBuffer());
    })();
    cached.catch(() => {
      cached = null;
    });
  }
  return cached;
}

/** Test hook only. */
export function resetBrainAssetCacheForTests(): void {
  cached = null;
  loadCount = 0;
}
