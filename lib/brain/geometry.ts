/**
 * Shared, immutable three.js geometry for both fsaverage5 hemispheres.
 *
 * Built once per BrainAssets object and cached; every viewer instance (single
 * view, intro, A/B) reuses the same BufferGeometry objects. Per-instance state
 * (activity, selection, surface morph) lives in materials/uniforms only, so
 * playback, orbit and variant changes never rebuild or re-upload these buffers.
 */

import * as THREE from "three";
import type { BrainAssets, HemisphereAssets } from "./assets";
import type { Hemisphere } from "./contract";

export interface HemisphereGeometry {
  hemi: Hemisphere;
  /** Render geometry: position = pial, aInflated = inflated (morph in shader). */
  surface: THREE.BufferGeometry;
  /** CPU picking geometries for each surface (same index buffer). */
  pickPial: THREE.BufferGeometry;
  pickInflated: THREE.BufferGeometry;
  /** Unique mesh edges, for the intro's wireframe assembly beat. */
  edges: THREE.BufferGeometry;
  labels: Uint8Array;
}

export interface BrainGeometry {
  left: HemisphereGeometry;
  right: HemisphereGeometry;
  /** RAS-mm point placed at the scene origin. */
  center: [number, number, number];
  /** Radius of the pial bounding sphere (scene units = mm). */
  radius: number;
}

/** fsaverage RAS (x right, y anterior, z superior) -> three (x right, y up, z = posterior). */
export function rasToScene(x: number, y: number, z: number, center: readonly number[]): [number, number, number] {
  return [x - center[0], z - center[2], -(y - center[1])];
}

function toScene(ras: Float32Array, center: readonly number[]): Float32Array {
  const out = new Float32Array(ras.length);
  for (let i = 0; i < ras.length; i += 3) {
    const p = rasToScene(ras[i], ras[i + 1], ras[i + 2], center);
    out[i] = p[0];
    out[i + 1] = p[1];
    out[i + 2] = p[2];
  }
  return out;
}

function vertexNormals(positions: Float32Array, faces: Uint16Array): Float32Array {
  const normals = new Float32Array(positions.length);
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f] * 3;
    const b = faces[f + 1] * 3;
    const c = faces[f + 2] * 3;
    const abx = positions[b] - positions[a];
    const aby = positions[b + 1] - positions[a + 1];
    const abz = positions[b + 2] - positions[a + 2];
    const acx = positions[c] - positions[a];
    const acy = positions[c + 1] - positions[a + 1];
    const acz = positions[c + 2] - positions[a + 2];
    // Area-weighted face normal.
    const nx = aby * acz - abz * acy;
    const ny = abz * acx - abx * acz;
    const nz = abx * acy - aby * acx;
    for (const v of [a, b, c]) {
      normals[v] += nx;
      normals[v + 1] += ny;
      normals[v + 2] += nz;
    }
  }
  for (let i = 0; i < normals.length; i += 3) {
    const len = Math.hypot(normals[i], normals[i + 1], normals[i + 2]) || 1;
    normals[i] /= len;
    normals[i + 1] /= len;
    normals[i + 2] /= len;
  }
  return normals;
}

/** 1 where a vertex touches a face spanning two atlas regions. */
export function regionBoundaries(labels: Uint8Array, faces: Uint16Array): Float32Array {
  const out = new Float32Array(labels.length);
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f];
    const b = faces[f + 1];
    const c = faces[f + 2];
    if (labels[a] !== labels[b] || labels[b] !== labels[c]) {
      out[a] = 1;
      out[b] = 1;
      out[c] = 1;
    }
  }
  return out;
}

function uniqueEdges(faces: Uint16Array): Uint16Array {
  const seen = new Set<number>();
  const edges: number[] = [];
  for (let f = 0; f < faces.length; f += 3) {
    for (let k = 0; k < 3; k++) {
      const a = faces[f + k];
      const b = faces[f + ((k + 1) % 3)];
      const lo = Math.min(a, b);
      const hi = Math.max(a, b);
      const key = lo * 65536 + hi;
      if (!seen.has(key)) {
        seen.add(key);
        edges.push(lo, hi);
      }
    }
  }
  return Uint16Array.from(edges);
}

function buildHemisphere(hemi: Hemisphere, data: HemisphereAssets, center: number[], vertexOffset: number): HemisphereGeometry {
  const pial = toScene(data.pial, center);
  const inflated = toScene(data.inflated, center);
  const index = new THREE.BufferAttribute(data.faces, 1);
  const pialAttr = new THREE.BufferAttribute(pial, 3);
  const inflatedAttr = new THREE.BufferAttribute(inflated, 3);

  const n = data.labels.length;
  const vid = new Float32Array(n);
  for (let i = 0; i < n; i++) vid[i] = vertexOffset + i;
  const labelAttr = new Float32Array(n);
  for (let i = 0; i < n; i++) labelAttr[i] = data.labels[i];

  const surface = new THREE.BufferGeometry();
  surface.setIndex(index);
  surface.setAttribute("position", pialAttr);
  surface.setAttribute("normal", new THREE.BufferAttribute(vertexNormals(pial, data.faces), 3));
  surface.setAttribute("aInflated", inflatedAttr);
  surface.setAttribute("aInflatedNormal", new THREE.BufferAttribute(vertexNormals(inflated, data.faces), 3));
  surface.setAttribute("aSulc", new THREE.BufferAttribute(data.sulc, 1));
  surface.setAttribute("aCurv", new THREE.BufferAttribute(data.curv, 1));
  surface.setAttribute("aLabel", new THREE.BufferAttribute(labelAttr, 1));
  surface.setAttribute("aBoundary", new THREE.BufferAttribute(regionBoundaries(data.labels, data.faces), 1));
  surface.setAttribute("aVid", new THREE.BufferAttribute(vid, 1));
  surface.computeBoundingSphere();
  // The inflated surface is larger; keep frustum culling conservative.
  if (surface.boundingSphere) surface.boundingSphere.radius *= 1.6;

  const pickPial = new THREE.BufferGeometry();
  pickPial.setIndex(index);
  pickPial.setAttribute("position", pialAttr);
  pickPial.computeBoundingSphere();
  const pickInflated = new THREE.BufferGeometry();
  pickInflated.setIndex(index);
  pickInflated.setAttribute("position", inflatedAttr);
  pickInflated.computeBoundingSphere();

  const edges = new THREE.BufferGeometry();
  edges.setIndex(new THREE.BufferAttribute(uniqueEdges(data.faces), 1));
  edges.setAttribute("position", pialAttr);
  edges.setAttribute("aInflated", inflatedAttr);

  return { hemi, surface, pickPial, pickInflated, edges, labels: data.labels };
}

const cache = new WeakMap<BrainAssets, BrainGeometry>();
let buildCount = 0;

export function brainGeometryBuildCount(): number {
  return buildCount;
}

export function getBrainGeometry(assets: BrainAssets): BrainGeometry {
  const hit = cache.get(assets);
  if (hit) return hit;
  buildCount++;
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (const h of [assets.left, assets.right]) {
    for (let i = 0; i < h.pial.length; i += 3) {
      for (let k = 0; k < 3; k++) {
        min[k] = Math.min(min[k], h.pial[i + k]);
        max[k] = Math.max(max[k], h.pial[i + k]);
      }
    }
  }
  const center = [0, 1, 2].map((k) => (min[k] + max[k]) / 2);
  const radius = Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2;
  const perHemi = assets.manifest.vertices_per_hemisphere;
  const geometry: BrainGeometry = {
    left: buildHemisphere("left", assets.left, center, 0),
    right: buildHemisphere("right", assets.right, center, perHemi),
    center: center as [number, number, number],
    radius,
  };
  cache.set(assets, geometry);
  return geometry;
}
