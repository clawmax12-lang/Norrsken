/**
 * One interactive brain view: renderer, camera, controls and per-instance
 * materials over the shared fsaverage5 geometry. React components own the DOM
 * around it; this class owns WebGL. Nothing here calls a model or the network.
 */

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { getActivityTexture, emptyActivityTexture } from "./activityTexture.ts";
import type { CameraState, CorticalBinding, DisplayScale, Hemisphere, SurfaceKind } from "./contract.ts";
import type { BrainGeometry, HemisphereGeometry } from "./geometry.ts";
import { createCortexMaterial, createInstanceUniforms, createWireMaterial, type InstanceUniforms } from "./materials.ts";
import { sampleAt } from "./timeline.ts";

export interface PickResult {
  hemi: Hemisphere;
  label: number;
  vertex: number;
}

export interface BrainSceneOptions {
  reducedMotion?: boolean;
  onPick?: (pick: PickResult | null) => void;
  onCameraChange?: (state: CameraState) => void;
  onContextLost?: () => void;
}

export type CameraPreset = "profile" | "open" | "intro-start" | "front";

interface HemiView {
  geo: HemisphereGeometry;
  group: THREE.Group;
  material: THREE.ShaderMaterial;
  surface: THREE.Mesh;
  pickPial: THREE.Mesh;
  pickInflated: THREE.Mesh;
  wire: THREE.LineSegments;
}

interface Tween {
  from: number;
  to: number;
  start: number;
  duration: number;
  apply: (v: number) => void;
  done?: () => void;
}

const easeInOut = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

export const OPEN_OFFSET_MM = 22;
export const OPEN_TILT_RAD = (38 * Math.PI) / 180;

export class BrainScene {
  readonly renderer: THREE.WebGLRenderer;
  readonly camera: THREE.PerspectiveCamera;
  readonly controls: OrbitControls;
  readonly scene = new THREE.Scene();
  readonly uniforms: InstanceUniforms;

  private readonly container: HTMLElement;
  private readonly geometry: BrainGeometry;
  private readonly options: BrainSceneOptions;
  private readonly root = new THREE.Group();
  private readonly hemis: Record<Hemisphere, HemiView>;
  private readonly wire = { value: 0 };
  private readonly raycaster = new THREE.Raycaster();
  private readonly pointer = new THREE.Vector2();
  private readonly resizeObserver: ResizeObserver;
  private readonly tweens = new Map<string, Tween>();
  private readonly regionCentroids = new Map<string, { pial: THREE.Vector3; inflated: THREE.Vector3 }>();
  private binding: CorticalBinding | null = null;
  private time = 0;
  private frame = 0;
  private surface: SurfaceKind = "pial";
  private open = false;
  private disposed = false;
  private downAt: { x: number; y: number } | null = null;
  private hoverQueued: PointerEvent | null = null;
  private pickingEnabled = true;
  private autoRotateSpeed = 0;
  private lastFrameTime = performance.now();
  private headObject: THREE.Object3D | null = null;
  reducedMotion: boolean;

  constructor(container: HTMLElement, geometry: BrainGeometry, options: BrainSceneOptions = {}) {
    this.container = container;
    this.geometry = geometry;
    this.options = options;
    this.reducedMotion = options.reducedMotion ?? false;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.domElement.className = "brain-canvas";
    this.renderer.domElement.setAttribute("aria-hidden", "true");
    container.appendChild(this.renderer.domElement);
    this.renderer.domElement.addEventListener("webglcontextlost", this.handleContextLost);

    this.camera = new THREE.PerspectiveCamera(28, 1, 1, 5000);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = false;
    this.controls.rotateSpeed = 0.6;
    this.controls.zoomSpeed = 0.8;
    this.controls.minDistance = geometry.radius * 1.5;
    this.controls.maxDistance = geometry.radius * 7;
    this.controls.addEventListener("change", this.handleControlsChange);

    this.uniforms = createInstanceUniforms();
    this.uniforms.uRevealRadius.value = geometry.radius;
    this.scene.add(this.root);
    this.hemis = {
      left: this.buildHemi(geometry.left),
      right: this.buildHemi(geometry.right),
    };
    this.computeRegionCentroids();

    this.applyCameraPreset("profile", 0);
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();

    const el = this.renderer.domElement;
    el.addEventListener("pointerdown", this.handlePointerDown);
    el.addEventListener("pointerup", this.handlePointerUp);
    el.addEventListener("pointermove", this.handlePointerMove);
    el.addEventListener("pointerleave", this.handlePointerLeave);
    el.addEventListener("dblclick", this.handleDoubleClick);
    this.renderer.setAnimationLoop(this.tick);
  }

  private buildHemi(geo: HemisphereGeometry): HemiView {
    const group = new THREE.Group();
    group.name = `hemisphere-${geo.hemi}`;
    const material = createCortexMaterial(this.uniforms);
    const surface = new THREE.Mesh(geo.surface, material);
    surface.renderOrder = 1;
    const pickMaterial = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide });
    const pickPial = new THREE.Mesh(geo.pickPial, pickMaterial);
    const pickInflated = new THREE.Mesh(geo.pickInflated, pickMaterial);
    pickPial.visible = false;
    pickInflated.visible = false;
    const wire = new THREE.LineSegments(geo.edges, createWireMaterial(this.uniforms, this.wire));
    wire.visible = false;
    wire.renderOrder = 2;
    group.add(surface, pickPial, pickInflated, wire);
    this.root.add(group);
    return { geo, group, material, surface, pickPial, pickInflated, wire };
  }

  private computeRegionCentroids() {
    for (const hemi of ["left", "right"] as const) {
      const geo = this.geometry[hemi];
      const pial = geo.surface.getAttribute("position") as THREE.BufferAttribute;
      const infl = geo.surface.getAttribute("aInflated") as THREE.BufferAttribute;
      const sums = new Map<number, { p: THREE.Vector3; i: THREE.Vector3; n: number }>();
      for (let v = 0; v < geo.labels.length; v++) {
        const label = geo.labels[v];
        let s = sums.get(label);
        if (!s) sums.set(label, (s = { p: new THREE.Vector3(), i: new THREE.Vector3(), n: 0 }));
        s.p.x += pial.getX(v);
        s.p.y += pial.getY(v);
        s.p.z += pial.getZ(v);
        s.i.x += infl.getX(v);
        s.i.y += infl.getY(v);
        s.i.z += infl.getZ(v);
        s.n++;
      }
      for (const [label, s] of sums) {
        this.regionCentroids.set(`${hemi}:${label}`, { pial: s.p.divideScalar(s.n), inflated: s.i.divideScalar(s.n) });
      }
    }
  }

  // ---------------------------------------------------------------- data/time

  setActivity(binding: CorticalBinding | null, scale: DisplayScale | null) {
    this.binding = binding;
    if (binding && scale) {
      const packed = getActivityTexture(binding);
      this.uniforms.uActivity.value = packed.texture;
      this.uniforms.uRowsPerFrame.value = packed.rowsPerFrame;
      this.uniforms.uThreshold.value = scale.threshold;
      this.uniforms.uVmax.value = scale.vmax;
      this.uniforms.uHasActivity.value = 1;
    } else {
      this.uniforms.uActivity.value = emptyActivityTexture();
      this.uniforms.uHasActivity.value = 0;
    }
    this.applyTime();
  }

  setTime(t: number) {
    this.time = t;
    this.applyTime();
  }

  private applyTime() {
    const b = this.binding;
    if (!b) return;
    const s = sampleAt(b.times, this.time);
    this.uniforms.uHasActivity.value = s.inRange ? 1 : 0;
    this.uniforms.uFrameA.value = s.i0;
    this.uniforms.uFrameB.value = s.i1;
    this.uniforms.uAlpha.value = s.alpha;
  }

  // ------------------------------------------------------------ presentation

  setSurface(kind: SurfaceKind) {
    if (kind === this.surface) return;
    this.surface = kind;
    const to = kind === "inflated" ? 1 : 0;
    this.pickingEnabled = false;
    this.tween("inflate", this.uniforms.uInflate.value, to, this.reducedMotion ? 0 : 900, (v) => (this.uniforms.uInflate.value = v), () => (this.pickingEnabled = true));
    // The inflated surface is larger: dolly to keep it framed.
    const target = this.controls.target.clone();
    const offset = this.camera.position.clone().sub(target).multiplyScalar(kind === "inflated" ? 1.3 : 1 / 1.3);
    this.flyTo(target.clone().add(offset), target, this.reducedMotion ? 0 : 900);
  }

  setOpen(open: boolean) {
    if (open === this.open) return;
    this.open = open;
    const from = this.hemis.right.group.position.x / OPEN_OFFSET_MM;
    this.pickingEnabled = false;
    this.tween("open", from, open ? 1 : 0, this.reducedMotion ? 0 : 900, (v) => this.applyOpen(v), () => (this.pickingEnabled = true));
    this.applyCameraPreset(open ? "open" : "profile", this.reducedMotion ? 0 : 1100);
  }

  private applyOpen(v: number) {
    this.hemis.left.group.position.x = -OPEN_OFFSET_MM * v;
    this.hemis.right.group.position.x = OPEN_OFFSET_MM * v;
    this.hemis.left.group.rotation.z = OPEN_TILT_RAD * v;
    this.hemis.right.group.rotation.z = -OPEN_TILT_RAD * v;
  }

  setSelected(pick: { hemi: Hemisphere; label: number } | null) {
    for (const hemi of ["left", "right"] as const) {
      this.hemis[hemi].material.uniforms.uSelected.value = pick && pick.hemi === hemi ? pick.label : -1;
    }
  }

  /** Assembly controls for the Preflight sequence. */
  setAssembly({ reveal, wire, opacity, dim }: { reveal?: number; wire?: number; opacity?: number; dim?: number }) {
    if (reveal !== undefined) this.uniforms.uReveal.value = reveal;
    if (wire !== undefined) {
      this.wire.value = wire;
      this.hemis.left.wire.visible = this.hemis.right.wire.visible = wire > 0.001;
    }
    if (opacity !== undefined) {
      this.uniforms.uOpacity.value = opacity;
      for (const h of Object.values(this.hemis)) h.material.transparent = opacity < 0.999;
    }
    if (dim !== undefined) this.uniforms.uDim.value = dim;
  }

  setAutoRotate(speedRadPerSecond: number) {
    this.autoRotateSpeed = this.reducedMotion ? 0 : speedRadPerSecond;
  }

  setInteractive(enabled: boolean) {
    this.controls.enabled = enabled;
    this.pickingEnabled = enabled;
  }

  setHead(object: THREE.Object3D | null) {
    if (this.headObject) this.scene.remove(this.headObject);
    this.headObject = object;
    if (object) this.scene.add(object);
  }

  // ------------------------------------------------------------------ camera

  private presetPose(preset: CameraPreset): { dir: THREE.Vector3; distance: number } {
    const r = this.geometry.radius;
    switch (preset) {
      case "open":
        return { dir: new THREE.Vector3(0, 1, 0.55).normalize(), distance: r * 3.7 };
      case "intro-start":
        return { dir: new THREE.Vector3(-0.35, 0.3, -1).normalize(), distance: r * 4.6 };
      case "front":
        return { dir: new THREE.Vector3(0, 0.15, -1).normalize(), distance: r * 3.6 };
      case "profile":
      default:
        // Right-hemisphere lateral 3/4 profile, face toward screen right.
        return { dir: new THREE.Vector3(1, 0.24, -0.3).normalize(), distance: r * 3.55 };
    }
  }

  applyCameraPreset(preset: CameraPreset, durationMs = 900) {
    const pose = this.presetPose(preset);
    pose.distance *= this.surfaceDistanceFactor();
    // Aim slightly below and in front of the brain centre so the head profile frames it.
    const target = new THREE.Vector3(0, -6, -6);
    this.flyTo(target.clone().add(pose.dir.multiplyScalar(pose.distance)), target, durationMs);
  }

  resetCamera() {
    this.applyCameraPreset(this.open ? "open" : "profile", this.reducedMotion ? 0 : 800);
  }

  private surfaceDistanceFactor(): number {
    return this.surface === "inflated" ? 1.3 : 1;
  }

  flyTo(position: THREE.Vector3, target: THREE.Vector3, durationMs = 900) {
    const fromPos = this.camera.position.clone();
    const fromTarget = this.controls.target.clone();
    if (durationMs <= 0 || this.reducedMotion) {
      this.tweens.delete("camera");
      this.camera.position.copy(position);
      this.controls.target.copy(target);
      this.controls.update();
      return;
    }
    // Interpolate on a sphere around the target for a natural orbit.
    const fromOffset = fromPos.clone().sub(fromTarget);
    const toOffset = position.clone().sub(target);
    const fromLen = fromOffset.length();
    const toLen = toOffset.length();
    const fromDir = fromOffset.normalize();
    const toDir = toOffset.normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(fromDir, toDir);
    const qi = new THREE.Quaternion();
    this.tween("camera", 0, 1, durationMs, (v) => {
      qi.identity().slerp(q, v);
      const dir = fromDir.clone().applyQuaternion(qi);
      const t = fromTarget.clone().lerp(target, v);
      this.controls.target.copy(t);
      this.camera.position.copy(t).add(dir.multiplyScalar(fromLen + (toLen - fromLen) * v));
    });
  }

  /** Push the camera toward a region (intro lock-on). */
  focusRegion(hemi: Hemisphere, label: number, durationMs = 1600) {
    const world = this.regionWorldPosition(hemi, label);
    if (!world) return;
    const outward = world.clone().normalize();
    if (outward.lengthSq() < 1e-6) outward.set(1, 0, 0);
    const viewDir = outward.add(new THREE.Vector3(0, 0.25, 0)).normalize();
    const target = world.clone().multiplyScalar(0.55);
    this.flyTo(target.clone().add(viewDir.multiplyScalar(this.geometry.radius * 2.3)), target, durationMs);
  }

  getCameraState(): CameraState {
    return {
      position: this.camera.position.toArray() as [number, number, number],
      target: this.controls.target.toArray() as [number, number, number],
      zoom: this.camera.zoom,
    };
  }

  setCameraState(state: CameraState) {
    this.camera.position.fromArray(state.position);
    this.controls.target.fromArray(state.target);
    this.camera.zoom = state.zoom;
    this.camera.updateProjectionMatrix();
    this.controls.update();
  }

  regionWorldPosition(hemi: Hemisphere, label: number): THREE.Vector3 | null {
    const c = this.regionCentroids.get(`${hemi}:${label}`);
    if (!c) return null;
    const local = c.pial.clone().lerp(c.inflated, this.uniforms.uInflate.value);
    this.hemis[hemi].group.updateMatrixWorld();
    return local.applyMatrix4(this.hemis[hemi].group.matrixWorld);
  }

  /** CSS-pixel position of a region centroid within the container. */
  projectRegion(hemi: Hemisphere, label: number): { x: number; y: number } | null {
    const world = this.regionWorldPosition(hemi, label);
    if (!world) return null;
    const ndc = world.project(this.camera);
    const rect = this.container.getBoundingClientRect();
    return { x: ((ndc.x + 1) / 2) * rect.width, y: ((1 - ndc.y) / 2) * rect.height };
  }

  // ----------------------------------------------------------------- picking

  pickAt(clientX: number, clientY: number): PickResult | null {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const useInflated = this.uniforms.uInflate.value > 0.5;
    const hits: THREE.Intersection[] = [];
    for (const hemi of ["left", "right"] as const) {
      const h = this.hemis[hemi];
      h.group.updateMatrixWorld();
      (useInflated ? h.pickInflated : h.pickPial).raycast(this.raycaster, hits);
    }
    hits.sort((a, b) => a.distance - b.distance);
    const hit = hits[0];
    if (!hit || !hit.face) return null;
    const hemi: Hemisphere = hit.object.parent === this.hemis.left.group ? "left" : "right";
    const labels = this.hemis[hemi].geo.labels;
    // Nearest of the triangle's vertices to the hit point.
    const geo = (hit.object as THREE.Mesh).geometry;
    const pos = geo.getAttribute("position") as THREE.BufferAttribute;
    const local = hit.object.worldToLocal(hit.point.clone());
    let best = hit.face.a;
    let bestD = Infinity;
    for (const v of [hit.face.a, hit.face.b, hit.face.c]) {
      const d = local.distanceToSquared(new THREE.Vector3(pos.getX(v), pos.getY(v), pos.getZ(v)));
      if (d < bestD) {
        bestD = d;
        best = v;
      }
    }
    return { hemi, label: labels[best], vertex: best };
  }

  private handlePointerDown = (e: PointerEvent) => {
    this.downAt = { x: e.clientX, y: e.clientY };
  };

  private handlePointerUp = (e: PointerEvent) => {
    if (!this.downAt) return;
    const moved = Math.hypot(e.clientX - this.downAt.x, e.clientY - this.downAt.y);
    this.downAt = null;
    if (moved > 5 || !this.pickingEnabled || e.button !== 0) return;
    this.options.onPick?.(this.pickAt(e.clientX, e.clientY));
  };

  private handlePointerMove = (e: PointerEvent) => {
    this.hoverQueued = e;
  };

  private handlePointerLeave = () => {
    this.hoverQueued = null;
    for (const h of Object.values(this.hemis)) h.material.uniforms.uHover.value = -1;
    this.renderer.domElement.style.cursor = "";
  };

  private handleDoubleClick = () => {
    this.resetCamera();
  };

  private processHover() {
    const e = this.hoverQueued;
    this.hoverQueued = null;
    if (!e || !this.pickingEnabled || e.buttons !== 0) return;
    const pick = this.pickAt(e.clientX, e.clientY);
    for (const hemi of ["left", "right"] as const) {
      this.hemis[hemi].material.uniforms.uHover.value = pick && pick.hemi === hemi ? pick.label : -1;
    }
    this.uniforms.uHoverActive.value = pick ? 1 : 0;
    this.renderer.domElement.style.cursor = pick ? "pointer" : "grab";
  }

  // ------------------------------------------------------------------- loop

  private tween(key: string, from: number, to: number, duration: number, apply: (v: number) => void, done?: () => void) {
    if (duration <= 0) {
      apply(to);
      this.tweens.delete(key);
      done?.();
      return;
    }
    this.tweens.set(key, { from, to, start: performance.now(), duration, apply, done });
  }

  private tick = (now: number) => {
    if (this.disposed) return;
    const dt = Math.min(0.1, (now - this.lastFrameTime) / 1000);
    this.lastFrameTime = now;
    for (const [key, tw] of this.tweens) {
      const x = Math.min(1, (now - tw.start) / tw.duration);
      tw.apply(tw.from + (tw.to - tw.from) * easeInOut(x));
      if (x >= 1) {
        this.tweens.delete(key);
        tw.done?.();
      }
    }
    if (this.autoRotateSpeed && !this.tweens.has("camera")) {
      const offset = this.camera.position.clone().sub(this.controls.target);
      offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), this.autoRotateSpeed * dt);
      this.camera.position.copy(this.controls.target).add(offset);
    }
    if (this.frame++ % 2 === 0) this.processHover();
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  };

  private handleControlsChange = () => {
    this.options.onCameraChange?.(this.getCameraState());
  };

  private handleContextLost = (event: Event) => {
    event.preventDefault();
    this.options.onContextLost?.();
  };

  resize() {
    const w = Math.max(1, this.container.clientWidth);
    const h = Math.max(1, this.container.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    // Keep the brain framed on narrow/tall stages.
    this.camera.fov = w / h < 1 ? 28 / Math.max(0.55, w / h) : 28;
    this.camera.updateProjectionMatrix();
    // setSize clears the drawing buffer; repaint now to avoid a blank frame.
    if (!this.disposed) this.renderer.render(this.scene, this.camera);
  }

  /** Disposes this instance only; shared geometry and activity textures stay cached. */
  dispose() {
    this.disposed = true;
    this.renderer.setAnimationLoop(null);
    this.resizeObserver.disconnect();
    this.controls.dispose();
    const el = this.renderer.domElement;
    el.removeEventListener("pointerdown", this.handlePointerDown);
    el.removeEventListener("pointerup", this.handlePointerUp);
    el.removeEventListener("pointermove", this.handlePointerMove);
    el.removeEventListener("pointerleave", this.handlePointerLeave);
    el.removeEventListener("dblclick", this.handleDoubleClick);
    el.removeEventListener("webglcontextlost", this.handleContextLost);
    for (const h of Object.values(this.hemis)) {
      h.material.dispose();
      (h.wire.material as THREE.Material).dispose();
      (h.pickPial.material as THREE.Material).dispose();
    }
    this.renderer.dispose();
    el.remove();
  }
}
