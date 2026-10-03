/**
 * Stylized head silhouette around the brain (presentation only).
 *
 * Mesh: original procedural artwork in fsaverage RAS mm (scripts/brain/
 * build_head_mesh.py), loaded once and shared. Rendered as a dark silhouette
 * drawn before the cortex plus a faint fresnel shell over it, so the brain
 * stays fully readable inside the profile (references 02/03).
 */

import * as THREE from "three";
import { rasToScene } from "./geometry";

export const HEAD_ASSET_BASE = "/brain/head";

interface HeadManifest {
  vertices: number;
  faces: number;
  layout: { positions: { offset: number }; faces: { offset: number } };
}

const geometryCache = new Map<string, Promise<THREE.BufferGeometry>>();

export function loadHeadGeometry(center: readonly number[], fetchImpl: typeof fetch = fetch): Promise<THREE.BufferGeometry> {
  const key = center.join(",");
  let hit = geometryCache.get(key);
  if (!hit) {
    hit = (async () => {
      const manifest = (await (await fetchImpl(`${HEAD_ASSET_BASE}/head.json`)).json()) as HeadManifest;
      const buffer = await (await fetchImpl(`${HEAD_ASSET_BASE}/head.bin`)).arrayBuffer();
      const ras = new Float32Array(buffer, manifest.layout.positions.offset, manifest.vertices * 3);
      const positions = new Float32Array(ras.length);
      for (let i = 0; i < ras.length; i += 3) positions.set(rasToScene(ras[i], ras[i + 1], ras[i + 2], center), i);
      const faces = new Uint16Array(buffer, manifest.layout.faces.offset, manifest.faces * 3);
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geometry.setIndex(new THREE.BufferAttribute(faces, 1));
      geometry.computeVertexNormals();
      geometry.computeBoundingSphere();
      return geometry;
    })();
    hit.catch(() => geometryCache.delete(key));
    geometryCache.set(key, hit);
  }
  return hit;
}

const vertex = /* glsl */ `
varying vec3 vN;
varying vec3 vV;
varying float vH;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vN = normalize(normalMatrix * normal);
  vV = -mv.xyz;
  vH = position.y;
  gl_Position = projectionMatrix * mv;
}
`;

const bodyFragment = /* glsl */ `
uniform float uOpacity;
varying vec3 vN;
varying vec3 vV;
varying float vH;
void main() {
  vec3 n = -normalize(vN);
  vec3 keyDir = normalize(vec3(-0.55, 0.65, 0.55));
  float key = max(dot(n, keyDir) * 0.5 + 0.5, 0.0);
  // Fade the neck into the black background.
  float fade = smoothstep(-230.0, -120.0, vH);
  vec3 c = vec3(0.030, 0.031, 0.034) + vec3(0.055, 0.056, 0.060) * key * key;
  float a = uOpacity * fade;
  // Drawn first without blending onto the cleared canvas: write premultiplied colour.
  gl_FragColor = vec4(c * a, a);
}
`;

const shellFragment = /* glsl */ `
uniform float uOpacity;
varying vec3 vN;
varying vec3 vV;
varying float vH;
void main() {
  vec3 n = normalize(vN);
  vec3 v = normalize(vV);
  float ndv = max(dot(n, v), 0.0);
  float fres = pow(1.0 - ndv, 2.4);
  vec3 keyDir = normalize(vec3(-0.55, 0.65, 0.55));
  float key = max(dot(n, keyDir), 0.0);
  float fade = smoothstep(-230.0, -120.0, vH);
  vec3 c = vec3(0.30, 0.31, 0.33) * fres + vec3(0.03) * key;
  float a = (0.02 + 0.5 * fres + 0.03 * key) * uOpacity * fade;
  gl_FragColor = vec4(c, a);
}
`;

export interface HeadObject {
  group: THREE.Group;
  setOpacity(value: number): void;
  dispose(): void;
}

export function createHeadObject(geometry: THREE.BufferGeometry): HeadObject {
  const opacity = { value: 1 };
  const body = new THREE.Mesh(
    geometry,
    // Background silhouette: opaque pass, first, no depth, so nothing of it can cover the cortex.
    new THREE.ShaderMaterial({ uniforms: { uOpacity: opacity }, vertexShader: vertex, fragmentShader: bodyFragment, side: THREE.BackSide, transparent: false, depthTest: false, depthWrite: false }),
  );
  body.renderOrder = -10;
  const shell = new THREE.Mesh(
    geometry,
    new THREE.ShaderMaterial({ uniforms: { uOpacity: opacity }, vertexShader: vertex, fragmentShader: shellFragment, side: THREE.FrontSide, transparent: true, depthWrite: false }),
  );
  shell.renderOrder = 3;
  const group = new THREE.Group();
  group.name = "head-silhouette";
  group.add(body, shell);
  return {
    group,
    setOpacity(value: number) {
      opacity.value = value;
    },
    dispose() {
      (body.material as THREE.Material).dispose();
      (shell.material as THREE.Material).dispose();
    },
  };
}
