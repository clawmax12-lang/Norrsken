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

function vertexNormals(positions: Float32Array, faces: ArrayLike<number>): Float32Array {
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
export function regionBoundaries(labels: ArrayLike<number>, faces: ArrayLike<number>): Float32Array {
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

/**
 * One level of interpolating subdivision for display smoothness.
 *
 * Original fsaverage5 vertices keep their index (0..n-1) and exact position, so the TRIBE
 * vertex mapping is untouched. Each edge gets one new vertex on a PN-triangle (cubic Bezier)
 * curve built from the endpoint normals; its activity is the mean of its two parent
 * vertices' genuine values (`parentA`/`parentB`), and labels/sulc/curv follow the parents.
 */
export interface SubdividedSurface {
  positions: Float32Array;
  parentA: Uint32Array;
  parentB: Uint32Array;
  faces: Uint32Array;
}

function curvedMidpoint(p: Float32Array, n: Float32Array, a: number, b: number, out: Float32Array, o: number) {
  const ax = p[a * 3], ay = p[a * 3 + 1], az = p[a * 3 + 2];
  const bx = p[b * 3], by = p[b * 3 + 1], bz = p[b * 3 + 2];
  const nax = n[a * 3], nay = n[a * 3 + 1], naz = n[a * 3 + 2];
  const nbx = n[b * 3], nby = n[b * 3 + 1], nbz = n[b * 3 + 2];
  const wab = (bx - ax) * nax + (by - ay) * nay + (bz - az) * naz;
  const wba = (ax - bx) * nbx + (ay - by) * nby + (az - bz) * nbz;
  // b210 = (2a + b - wab·na)/3, b120 = (2b + a - wba·nb)/3, curve(0.5) = (a + 3b210 + 3b120 + b)/8.
  out[o] = (ax + bx) / 2 + (-wab * nax - wba * nbx) / 8;
  out[o + 1] = (ay + by) / 2 + (-wab * nay - wba * nby) / 8;
  out[o + 2] = (az + bz) / 2 + (-wab * naz - wba * nbz) / 8;
}

export function subdivideSurface(positions: Float32Array, normals: Float32Array, faces: ArrayLike<number>, edgeVertex?: Map<number, number>): SubdividedSurface {
  const n = positions.length / 3;
  const edges = edgeVertex ?? new Map<number, number>();
  if (!edgeVertex) {
    for (let f = 0; f < faces.length; f += 3) {
      for (let k = 0; k < 3; k++) {
        const a = faces[f + k];
        const b = faces[f + ((k + 1) % 3)];
        const key = Math.min(a, b) * 1_048_576 + Math.max(a, b);
        if (!edges.has(key)) edges.set(key, n + edges.size);
      }
    }
  }
  const total = n + edges.size;
  const out = new Float32Array(total * 3);
  out.set(positions);
  const parentA = new Uint32Array(total);
  const parentB = new Uint32Array(total);
  for (let v = 0; v < n; v++) parentA[v] = parentB[v] = v;
  for (const [key, idx] of edges) {
    const a = Math.floor(key / 1_048_576);
    const b = key % 1_048_576;
    parentA[idx] = a;
    parentB[idx] = b;
    curvedMidpoint(positions, normals, a, b, out, idx * 3);
  }
  const newFaces = new Uint32Array(faces.length * 4);
  const mid = (a: number, b: number) => edges.get(Math.min(a, b) * 1_048_576 + Math.max(a, b)) as number;
  for (let f = 0, o = 0; f < faces.length; f += 3) {
    const a = faces[f], b = faces[f + 1], c = faces[f + 2];
    const ab = mid(a, b), bc = mid(b, c), ca = mid(c, a);
    newFaces.set([a, ab, ca, ab, b, bc, ca, bc, c, ab, bc, ca], o);
    o += 12;
  }
  return { positions: out, parentA, parentB, faces: newFaces };
}

function edgeMapOf(faces: ArrayLike<number>, n: number): Map<number, number> {
  const edges = new Map<number, number>();
  for (let f = 0; f < faces.length; f += 3) {
    for (let k = 0; k < 3; k++) {
      const a = faces[f + k];
      const b = faces[f + ((k + 1) % 3)];
      const key = Math.min(a, b) * 1_048_576 + Math.max(a, b);
      if (!edges.has(key)) edges.set(key, n + edges.size);
    }
  }
  return edges;
}

function buildHemisphere(hemi: Hemisphere, data: HemisphereAssets, center: number[], vertexOffset: number): HemisphereGeometry {
  const pial0 = toScene(data.pial, center);
  const inflated0 = toScene(data.inflated, center);
  const n0 = data.labels.length;
  const edgeMap = edgeMapOf(data.faces, n0);
  const pialSub = subdivideSurface(pial0, vertexNormals(pial0, data.faces), data.faces, edgeMap);
  const inflSub = subdivideSurface(inflated0, vertexNormals(inflated0, data.faces), data.faces, edgeMap);
  const faces = pialSub.faces;
  const total = pialSub.positions.length / 3;

  const index = new THREE.BufferAttribute(faces, 1);
  const pialAttr = new THREE.BufferAttribute(pialSub.positions, 3);
  const inflatedAttr = new THREE.BufferAttribute(inflSub.positions, 3);

  const vidA = new Float32Array(total);
  const vidB = new Float32Array(total);
  const labels = new Uint8Array(total);
  const sulc = new Float32Array(total);
  const curv = new Float32Array(total);
  for (let v = 0; v < total; v++) {
    const a = pialSub.parentA[v];
    const b = pialSub.parentB[v];
    vidA[v] = vertexOffset + a;
    vidB[v] = vertexOffset + b;
    // A midpoint inherits a label only when both parents agree; otherwise the first parent's.
    labels[v] = data.labels[a];
    sulc[v] = (data.sulc[a] + data.sulc[b]) / 2;
    curv[v] = (data.curv[a] + data.curv[b]) / 2;
  }
  const labelAttr = Float32Array.from(labels);

  const surface = new THREE.BufferGeometry();
  surface.setIndex(index);
  surface.setAttribute("position", pialAttr);
  surface.setAttribute("normal", new THREE.BufferAttribute(vertexNormals(pialSub.positions, faces), 3));
  surface.setAttribute("aInflated", inflatedAttr);
  surface.setAttribute("aInflatedNormal", new THREE.BufferAttribute(vertexNormals(inflSub.positions, faces), 3));
  surface.setAttribute("aSulc", new THREE.BufferAttribute(sulc, 1));
  surface.setAttribute("aCurv", new THREE.BufferAttribute(curv, 1));
  surface.setAttribute("aLabel", new THREE.BufferAttribute(labelAttr, 1));
  surface.setAttribute("aBoundary", new THREE.BufferAttribute(regionBoundaries(labels, faces), 1));
  surface.setAttribute("aVid", new THREE.BufferAttribute(vidA, 1));
  surface.setAttribute("aVid2", new THREE.BufferAttribute(vidB, 1));
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

  // Wireframe shows the original fsaverage5 edges (original vertices keep indices 0..n-1).
  const edges = new THREE.BufferGeometry();
  edges.setIndex(new THREE.BufferAttribute(uniqueEdges(data.faces), 1));
  edges.setAttribute("position", pialAttr);
  edges.setAttribute("aInflated", inflatedAttr);

  return { hemi, surface, pickPial, pickInflated, edges, labels };
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
