/**
 * Cortex and wireframe materials owned by the brain viewer.
 *
 * Neutral clay-gray anatomy shaded by sulcal depth, a camera-locked studio
 * light rig with a restrained rim, and a thresholded dark-red -> yellow heat
 * overlay driven only by bound genuine values (PRD §12.6).
 */

import * as THREE from "three";
import { ACTIVITY_TEX_WIDTH, emptyActivityTexture } from "./activityTexture";

/** Uniforms shared by both hemispheres of one viewer instance. */
export function createInstanceUniforms() {
  return {
    uInflate: { value: 0 },
    uActivity: { value: emptyActivityTexture() as THREE.Texture },
    uRowsPerFrame: { value: 1 },
    uFrameA: { value: 0 },
    uFrameB: { value: 0 },
    uAlpha: { value: 0 },
    uHasActivity: { value: 0 },
    uThreshold: { value: 0 },
    uVmax: { value: 1 },
    uReveal: { value: 1 },
    uRevealRadius: { value: 100 },
    uOpacity: { value: 1 },
    uDim: { value: 0 },
    uHoverActive: { value: 0 },
  };
}

export type InstanceUniforms = ReturnType<typeof createInstanceUniforms>;

const cortexVertex = /* glsl */ `
precision highp float;
precision highp int;
precision highp sampler2D;

attribute vec3 aInflated;
attribute vec3 aInflatedNormal;
attribute float aSulc;
attribute float aCurv;
attribute float aLabel;
attribute float aBoundary;
attribute float aVid;
attribute float aVid2;

uniform float uInflate;
uniform sampler2D uActivity;
uniform int uRowsPerFrame;
uniform int uFrameA;
uniform int uFrameB;
uniform float uAlpha;
uniform float uHasActivity;
uniform float uSelected;
uniform float uHover;
uniform float uRevealRadius;

varying vec3 vNormalV;
varying vec3 vViewPos;
varying float vSulc;
varying float vCurv;
varying float vAct;
varying float vSel;
varying float vHover;
varying float vBoundary;
varying float vReveal;
varying float vUnknown;

float fetchVertex(int frame, float vid) {
  int idx = int(vid + 0.5);
  int row = frame * uRowsPerFrame + idx / ${ACTIVITY_TEX_WIDTH};
  int col = idx - (idx / ${ACTIVITY_TEX_WIDTH}) * ${ACTIVITY_TEX_WIDTH};
  return texelFetch(uActivity, ivec2(col, row), 0).r;
}

// Subdivision midpoints show the mean of their two parent fsaverage5 vertices (equal for originals).
float fetchActivity(int frame) {
  return 0.5 * (fetchVertex(frame, aVid) + fetchVertex(frame, aVid2));
}

void main() {
  vec3 p = mix(position, aInflated, uInflate);
  vec3 n = normalize(mix(normal, aInflatedNormal, uInflate));
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  vViewPos = mv.xyz;
  vNormalV = normalize(normalMatrix * n);
  vSulc = mix(aSulc, aSulc * 0.6, uInflate);
  vCurv = aCurv;
  vAct = uHasActivity > 0.5 ? mix(fetchActivity(uFrameA), fetchActivity(uFrameB), uAlpha) : 0.0;
  vSel = abs(aLabel - uSelected) < 0.5 ? 1.0 : 0.0;
  vHover = abs(aLabel - uHover) < 0.5 ? 1.0 : 0.0;
  vBoundary = aBoundary;
  vUnknown = aLabel > 254.5 ? 1.0 : 0.0;
  // Assembly sweep runs posterior -> anterior (scene +z is posterior).
  vec4 world = modelMatrix * vec4(position, 1.0);
  vReveal = clamp(0.5 - world.z / (2.0 * uRevealRadius) + world.y / (8.0 * uRevealRadius), 0.0, 1.0);
  gl_Position = projectionMatrix * mv;
}
`;

const cortexFragment = /* glsl */ `
precision highp float;
layout(location = 0) out highp vec4 pc_fragColor;
#define gl_FragColor pc_fragColor

uniform float uHasActivity;
uniform float uThreshold;
uniform float uVmax;
uniform float uReveal;
uniform float uOpacity;
uniform float uDim;
uniform float uHoverActive;

varying vec3 vNormalV;
varying vec3 vViewPos;
varying float vSulc;
varying float vCurv;
varying float vAct;
varying float vSel;
varying float vHover;
varying float vBoundary;
varying float vReveal;
varying float vUnknown;

vec3 toLinear(vec3 c) { return pow(c, vec3(2.2)); }

// Thresholded heat scale: dark red -> red -> orange -> yellow -> pale yellow.
vec3 heat(float x) {
  vec3 c0 = toLinear(vec3(0.42, 0.03, 0.02));
  vec3 c1 = toLinear(vec3(0.80, 0.10, 0.03));
  vec3 c2 = toLinear(vec3(0.98, 0.42, 0.04));
  vec3 c3 = toLinear(vec3(1.00, 0.78, 0.18));
  vec3 c4 = toLinear(vec3(1.00, 0.96, 0.72));
  if (x < 0.30) return mix(c0, c1, x / 0.30);
  if (x < 0.60) return mix(c1, c2, (x - 0.30) / 0.30);
  if (x < 0.85) return mix(c2, c3, (x - 0.60) / 0.25);
  return mix(c3, c4, (x - 0.85) / 0.15);
}

float wrapDiffuse(vec3 n, vec3 l, float w) {
  return max((dot(n, l) + w) / (1.0 + w), 0.0);
}

void main() {
  if (vReveal > uReveal) discard;

  vec3 N = normalize(vNormalV);
  if (!gl_FrontFacing) N = -N;
  vec3 V = normalize(-vViewPos);

  // Sculptural gray: gyral crowns light, sulcal fundi darker (FreeSurfer sulc > 0 is deep).
  float deep = smoothstep(-1.0, 1.4, vSulc);
  // Matte plaster rather than plastic: warm neutral gray, crowns lighter, fundi deeper.
  vec3 albedo = mix(toLinear(vec3(0.76, 0.75, 0.73)), toLinear(vec3(0.34, 0.335, 0.33)), deep);
  // Cavity occlusion from sulcal depth and local concavity (FreeSurfer curv > 0 is concave).
  float cavity = mix(1.0, 0.38, deep * deep) * (1.0 - 0.5 * smoothstep(0.0, 0.2, vCurv));
  cavity *= 1.0 + 0.1 * smoothstep(0.0, -0.25, vCurv);
  albedo = mix(albedo, toLinear(vec3(0.24)), vUnknown * 0.55);

  float act = 0.0;
  vec3 heatColor = vec3(0.0);
  if (uHasActivity > 0.5 && uVmax > uThreshold) {
    float x = (vAct - uThreshold) / (uVmax - uThreshold);
    act = smoothstep(0.0, 0.12, x);
    heatColor = heat(clamp(x, 0.0, 1.0));
    albedo = mix(albedo, heatColor, act);
  }

  // Camera-locked studio rig: warm key upper-left-front, cool fill right, rim behind.
  vec3 keyDir = normalize(vec3(-0.55, 0.65, 0.55));
  vec3 fillDir = normalize(vec3(0.75, -0.10, 0.45));
  vec3 backDir = normalize(vec3(0.2, 0.4, -0.9));
  float key = wrapDiffuse(N, keyDir, 0.18);
  key = key * key * (3.0 - 2.0 * key); // soft terminator, like a large diffuse source
  float fill = wrapDiffuse(N, fillDir, 0.5);
  float back = pow(max(dot(N, backDir), 0.0), 2.0);
  float hemi = 0.5 + 0.5 * N.y;
  vec3 ambient = mix(vec3(0.03, 0.03, 0.032), vec3(0.095, 0.094, 0.092), hemi);
  vec3 H = normalize(keyDir + V);
  // Broad, faint sheen only (no tight white highlight that reads as plastic).
  float sheen = pow(max(dot(N, H), 0.0), 10.0) * 0.045 * (1.0 - deep);
  float fres = pow(1.0 - max(dot(N, V), 0.0), 3.5);

  vec3 color = albedo * cavity * (ambient + key * vec3(1.06, 1.0, 0.93) * 1.0 + fill * vec3(0.52, 0.56, 0.62) * 0.22 + back * 0.12);
  color += sheen * vec3(1.0, 0.98, 0.95);
  color += fres * vec3(0.07, 0.075, 0.085) * (1.0 - act);
  color += heatColor * act * 0.28;

  // Region selection and hover (atlas boundaries outline the selected region).
  color = mix(color, color * 1.12 + vec3(0.03, 0.04, 0.05), vSel * 0.6);
  color = mix(color, vec3(0.92, 0.95, 1.0), vSel * smoothstep(0.55, 0.95, vBoundary) * 0.85);
  color = mix(color, color * 1.18 + vec3(0.02), vHover * uHoverActive * (1.0 - vSel) * 0.5);

  // Glowing front of the assembly sweep.
  float front = 1.0 - smoothstep(0.0, 0.035, uReveal - vReveal);
  color += front * vec3(0.55, 0.6, 0.7) * step(uReveal, 0.999);

  color *= 1.0 - uDim;
  gl_FragColor = vec4(color, uOpacity);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;

export function createCortexMaterial(shared: InstanceUniforms): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3,
    uniforms: { ...shared, uSelected: { value: -1 }, uHover: { value: -1 } },
    vertexShader: cortexVertex,
    fragmentShader: cortexFragment,
    // Opaque by default so depth against the head silhouette is correct; the
    // scene enables blending only while the intro fades the cortex.
    transparent: false,
    side: THREE.DoubleSide,
  });
}

const wireVertex = /* glsl */ `
attribute vec3 aInflated;
uniform float uInflate;
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(mix(position, aInflated, uInflate), 1.0);
}
`;

const wireFragment = /* glsl */ `
uniform float uWire;
void main() {
  gl_FragColor = vec4(vec3(0.62, 0.68, 0.78) * uWire, uWire);
}
`;

export function createWireMaterial(shared: InstanceUniforms, wire: { value: number }): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: { uInflate: shared.uInflate, uWire: wire },
    vertexShader: wireVertex,
    fragmentShader: wireFragment,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}
