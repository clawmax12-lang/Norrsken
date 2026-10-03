/**
 * Packs one binding's genuine values into a float texture, once per binding.
 * Playback only changes which rows the shader reads (uniforms); no per-frame
 * buffer or texture rebuilds.
 */

import * as THREE from "three";
import type { CorticalBinding } from "./contract.ts";

export const ACTIVITY_TEX_WIDTH = 2048;

export interface ActivityTexture {
  texture: THREE.DataTexture;
  rowsPerFrame: number;
  nTimesteps: number;
}

/** Row/column of vertex v at frame t in the packed layout (shared with the shader). */
export function packedCoord(t: number, v: number, nVertices: number, width = ACTIVITY_TEX_WIDTH): [number, number] {
  const rowsPerFrame = Math.ceil(nVertices / width);
  return [v % width, t * rowsPerFrame + Math.floor(v / width)];
}

const cache = new WeakMap<CorticalBinding, ActivityTexture>();

export function getActivityTexture(binding: CorticalBinding): ActivityTexture {
  const hit = cache.get(binding);
  if (hit) return hit;
  const width = ACTIVITY_TEX_WIDTH;
  const rowsPerFrame = Math.ceil(binding.nVertices / width);
  const height = rowsPerFrame * binding.nTimesteps;
  const data = new Float32Array(width * height);
  for (let t = 0; t < binding.nTimesteps; t++) {
    data.set(binding.values.subarray(t * binding.nVertices, (t + 1) * binding.nVertices), t * rowsPerFrame * width);
  }
  const texture = new THREE.DataTexture(data, width, height, THREE.RedFormat, THREE.FloatType);
  texture.minFilter = THREE.NearestFilter;
  texture.magFilter = THREE.NearestFilter;
  texture.generateMipmaps = false;
  texture.needsUpdate = true;
  const out = { texture, rowsPerFrame, nTimesteps: binding.nTimesteps };
  cache.set(binding, out);
  return out;
}

let placeholder: THREE.DataTexture | null = null;

/** 1x1 texture bound when there is no data (the shader ignores it). */
export function emptyActivityTexture(): THREE.DataTexture {
  if (!placeholder) {
    placeholder = new THREE.DataTexture(new Float32Array([0]), 1, 1, THREE.RedFormat, THREE.FloatType);
    placeholder.needsUpdate = true;
  }
  return placeholder;
}
