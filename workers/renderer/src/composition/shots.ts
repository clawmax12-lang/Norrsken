/**
 * Pure camera maths for the hero phone: one device that stays on screen across every product
 * scene and glides from shot to shot, so a scene change never leaves an empty frame.
 *
 * Each scene asks for a shot (hero, close_up, takeover, tilt). A shot that would enlarge the
 * source past the upscale cap, or that needs a focus region the scene lacks, falls back to
 * hero. Poses are in frame pixels and interpolate linearly, so the device morphs between them.
 */
import type { Beat, CompositionSpec, SceneSpec, Shot } from "../spec/types.generated.ts";
import { firstBeat, punchState, sceneBeats } from "./beats.ts";
import {
  MAX_UPSCALE,
  clamp01,
  coverLayout,
  focusOf,
  focusTransform,
  isPhoneAspect,
  regionAspect,
  smooth,
  type FocusBox,
  type ImageSize,
} from "./still.ts";
import { ctaStartFrame } from "./timeline.ts";
import { DEVICE, FRAME, PRODUCT_ZONE, SAFE_WIDTH } from "./tokens.ts";

export const ZONE_HEIGHT = FRAME.height - PRODUCT_ZONE.top - PRODUCT_ZONE.bottom;
const ZONE_CX = PRODUCT_ZONE.left + SAFE_WIDTH / 2;
const ZONE_CY = PRODUCT_ZONE.top + ZONE_HEIGHT / 2;

/** Edge plus bezel around the glass at hero size, in px. */
export const BEZEL = DEVICE.edge + DEVICE.bezel;
/** Share of the product zone's height the hero phone fills, so its shadow stays in frame. */
const HERO_SHARE = 0.9;
/** Frames the device takes to glide to the next scene's shot (0.6 s at 30 fps). */
export const MOVE_FRAMES = 18;
/** Frames the next screen takes to push the previous one up and out of the glass. */
export const SWAP_FRAMES = 12;
/** The push waits until the device is into its glide, so a shrinking takeover never shows the next screen enlarged. */
export const SWAP_DELAY = 4;
const CLOSE_UP_MAX = 1.75;
/** A close-up is the shot viewers inspect, so it keeps more headroom than the global cap. */
const CLOSE_UP_UPSCALE = 1.5;
/** Below this enlargement a close-up reads as a slightly bigger hero; use hero instead. */
export const CLOSE_UP_MIN = 1.35;
/** Where the close-up puts the focus region, as a share of the product zone's height. */
const CLOSE_UP_TARGET = 0.42;
const CLOSE_UP_PAN = 36;
const EDGE_MARGIN = 24;
const HERO_DRIFT = 10;
const TILT = { scale: 0.9, shift: 64, yawFrom: -16, yawTo: -10, roll: 2, drift: 8 } as const;
const GLASS_RADIUS = 0.13;
/** How far each shot punches in on a tap; a takeover already fills the frame. */
const PUNCH_SCALE: Readonly<Record<Shot, number>> = { hero: 0.14, tilt: 0.12, close_up: 0.07, takeover: 0 };

/** Where and how the device is drawn: glass rectangle centred on (cx, cy), plus its frame. */
export interface Pose {
  readonly cx: number;
  readonly cy: number;
  readonly glassW: number;
  readonly glassH: number;
  /** Edge plus bezel thickness around the glass, in px. */
  readonly bezel: number;
  readonly radius: number;
  /** Opacity of the device body (edge, bezel, shadow); 0 for a full-bleed takeover. */
  readonly frame: number;
  readonly rotateY: number;
  readonly rotateZ: number;
  readonly opacity: number;
}

export interface HeroScene {
  readonly index: number;
  readonly scene: SceneSpec;
  readonly from: number;
  /** Exclusive end frame, clipped at the end card. */
  readonly to: number;
  /** Drawn on the hero phone (a portrait screen); otherwise the scene draws its own product. */
  readonly on: boolean;
  readonly shot: Shot;
  readonly image: ImageSize | null;
  readonly crop: FocusBox | null;
  readonly focus: FocusBox | null;
  /** Width / height of the shown region (the display of a mockup, else the image). */
  readonly aspect: number;
  /** The finger tap on the screen's focus, the punch-in after it and any pull back out. */
  readonly tap: Beat | null;
  /** Every tap, in order: the finished ad taps through several elements of one screen. */
  readonly taps: readonly Beat[];
  readonly punches: readonly Beat[];
}

/** The scenes before the end card, each with the shot it can actually use. */
export function heroTrack(spec: CompositionSpec, sizes: Readonly<Record<string, ImageSize>>): HeroScene[] {
  const ctaStart = ctaStartFrame(spec);
  return spec.scenes
    .filter((scene) => scene.start_frame < ctaStart)
    .map((scene, index) => {
      const image = sizes[scene.screenshot] ?? null;
      const crop = focusOf(scene.crop);
      const focus = focusOf(scene.focus);
      const aspect = image ? regionAspect(image, crop) : 1;
      const on = image !== null && scene.layout !== "text_only" && isPhoneAspect(aspect);
      const requested: Shot = scene.shot ?? (scene.layout === "device_float" ? "tilt" : "hero");
      const shot = on && image ? resolveShot(requested, image, crop, focus, aspect) : "hero";
      const beats = sceneBeats(spec, index);
      return {
        index,
        scene,
        from: scene.start_frame,
        to: Math.min(scene.end_frame, ctaStart),
        on,
        shot,
        image,
        crop,
        focus,
        aspect,
        tap: on ? firstBeat(beats, "tap") : null,
        taps: on ? beats.filter((beat) => beat.kind === "tap") : [],
        punches: on ? beats.filter((beat) => beat.kind === "punch") : [],
      };
    });
}

/** ``requested`` when the source can carry it sharply, else hero. */
export function resolveShot(requested: Shot, image: ImageSize, crop: FocusBox | null, focus: FocusBox | null, aspect: number): Shot {
  if (requested === "takeover") {
    const [, , cw] = crop ?? [0, 0, 1, 1];
    return FRAME.width / (image.width * cw) <= MAX_UPSCALE ? "takeover" : "hero";
  }
  if (requested === "close_up") {
    return focus !== null && closeUpScale(image, crop, aspect) >= CLOSE_UP_MIN ? "close_up" : "hero";
  }
  return requested;
}

/** Glass size of the hero phone for a screen of ``aspect``: exactly that aspect, never cropped. */
export function heroGlass(aspect: number): { readonly w: number; readonly h: number } {
  let h = HERO_SHARE * ZONE_HEIGHT - 2 * BEZEL;
  let w = h * aspect;
  if (w + 2 * BEZEL > SAFE_WIDTH) {
    w = SAFE_WIDTH - 2 * BEZEL;
    h = w / aspect;
  }
  return { w, h };
}

function closeUpScale(image: ImageSize, crop: FocusBox | null, aspect: number): number {
  const sourceW = image.width * (crop?.[2] ?? 1);
  return Math.min(CLOSE_UP_MAX, (CLOSE_UP_UPSCALE * sourceW) / heroGlass(aspect).w);
}

/** The pose of ``scene`` at its own progress ``t`` (0-1), including its slow in-scene move. */
export function restPose(scene: HeroScene, t: number): Pose {
  const glass = heroGlass(scene.aspect);
  const e = smooth(clamp01(t));
  const base: Pose = {
    cx: ZONE_CX,
    cy: ZONE_CY,
    glassW: glass.w,
    glassH: glass.h,
    bezel: BEZEL,
    radius: glass.w * GLASS_RADIUS,
    frame: 1,
    rotateY: 0,
    rotateZ: 0,
    opacity: 1,
  };
  switch (scene.shot) {
    case "hero":
      return { ...base, cy: ZONE_CY + lerp(HERO_DRIFT, -HERO_DRIFT, e), rotateY: lerp(-2, 2, e) };
    case "tilt":
      return {
        ...scaled(base, TILT.scale),
        cx: ZONE_CX + TILT.shift,
        cy: ZONE_CY + lerp(-TILT.drift, TILT.drift, e),
        rotateY: lerp(TILT.yawFrom, TILT.yawTo, e),
        rotateZ: TILT.roll,
      };
    case "close_up": {
      const s = scene.image ? closeUpScale(scene.image, scene.crop, scene.aspect) : 1;
      const big = scaled(base, s);
      const [, fy, , fh] = scene.focus ?? [0, 0.5, 1, 0];
      const wanted = PRODUCT_ZONE.top + ZONE_HEIGHT * CLOSE_UP_TARGET - (fy + fh / 2 - 0.5) * big.glassH;
      const outerHalf = big.glassH / 2 + big.bezel;
      // Bottom edge at or past the frame's bottom, top edge at or above the product zone.
      const low = FRAME.height - EDGE_MARGIN - outerHalf;
      const high = PRODUCT_ZONE.top + EDGE_MARGIN + outerHalf;
      const panned = wanted + lerp(CLOSE_UP_PAN, 0, e);
      const cy = low <= high ? Math.min(high, Math.max(low, panned)) : (low + high) / 2;
      return { ...big, cy };
    }
    case "takeover": {
      const glassH = FRAME.width / scene.aspect;
      const room = FRAME.height - PRODUCT_ZONE.top;
      const topAligned = PRODUCT_ZONE.top + glassH / 2;
      const cy = glassH > room ? lerp(topAligned, FRAME.height - glassH / 2, e) : PRODUCT_ZONE.top + room / 2;
      return { ...base, cx: FRAME.width / 2, cy, glassW: FRAME.width, glassH, bezel: 0, radius: 0, frame: 0 };
    }
  }
}

function scaled(pose: Pose, s: number): Pose {
  return { ...pose, glassW: pose.glassW * s, glassH: pose.glassH * s, bezel: pose.bezel * s, radius: pose.radius * s };
}

/** The device at absolute ``frame``: the current shot, gliding in from the previous one. */
export function heroPose(frame: number, track: readonly HeroScene[]): Pose {
  const i = currentIndex(frame, track);
  const current = track[i];
  if (current === undefined) return HIDDEN;
  const t = sceneProgress(frame, current);
  const pose = punched(current, poseOf(current, t, track), t, frame);
  const previous = track[i - 1];
  const since = frame - current.from;
  if (previous === undefined || since >= MOVE_FRAMES) return pose;
  const leaving = punched(previous, poseOf(previous, 1, track), 1, current.from);
  return mix(leaving, pose, smooth(since / MOVE_FRAMES));
}

/** ``pose`` punched in toward the tapped point, which stays where it is on screen. */
export function punched(scene: HeroScene, pose: Pose, t: number, frame: number): Pose {
  const state = punchState(frame, scene.taps, scene.punches);
  const amount = state.amount * PUNCH_SCALE[scene.shot];
  const point = state.point;
  if (amount <= 0 || point === null) return pose;
  const [qx, qy] = glassPoint(scene, pose, t, point);
  const px = pose.cx + (qx - 0.5) * pose.glassW;
  const py = pose.cy + (qy - 0.5) * pose.glassH;
  const s = 1 + amount;
  return { ...scaled(pose, s), cx: px + (pose.cx - px) * s, cy: py + (pose.cy - py) * s };
}

/** Where ``point`` (a share of the shown region) sits in the glass, after the in-screen zoom. */
export function glassPoint(scene: HeroScene, pose: Pose, t: number, point: readonly [number, number]): [number, number] {
  const focus = contentFocus(scene);
  if (focus === null || scene.image === null) return [point[0], point[1]];
  const cover = coverLayout(scene.image, scene.crop, pose.glassW, pose.glassH).scale;
  const { scale, x, y } = focusTransform(t, focus, MAX_UPSCALE / cover, true);
  return [0.5 + scale * (point[0] + x - 0.5), 0.5 + scale * (point[1] + y - 0.5)];
}

export interface ScreenLayer {
  readonly scene: HeroScene;
  readonly t: number;
  /** Vertical offset as a share of the glass height: the next screen scrolls in from below. */
  readonly shift: number;
}

/**
 * Screens inside the glass at ``frame``. On a scene change the next screen pushes the previous
 * one up, like scrolling to the next page of the app, so two screens never show through each other.
 */
export function screenLayers(frame: number, track: readonly HeroScene[]): ScreenLayer[] {
  const i = currentIndex(frame, track);
  const current = track[i];
  if (current === undefined) return [];
  const previous = track[i - 1];
  const since = frame - current.from;
  const own = { scene: current, t: sceneProgress(frame, current), shift: 0 };
  if (previous === undefined || !previous.on || since >= SWAP_DELAY + SWAP_FRAMES) return current.on ? [own] : [];
  if (!current.on) return [{ scene: previous, t: 1, shift: 0 }];
  const p = smooth(clamp01((since - SWAP_DELAY) / SWAP_FRAMES));
  return [
    { scene: previous, t: 1, shift: -p },
    { ...own, shift: 1 - p },
  ];
}

/** The focus the screen inside the glass zooms into; close-ups and takeovers move the device instead. */
export function contentFocus(scene: HeroScene): FocusBox | null {
  return scene.shot === "hero" || scene.shot === "tilt" ? scene.focus : null;
}

export function headlineAlign(shot: Shot): "left" | "center" {
  return shot === "tilt" ? "left" : "center";
}

const HIDDEN: Pose = { cx: ZONE_CX, cy: ZONE_CY, glassW: 0, glassH: 0, bezel: 0, radius: 0, frame: 0, rotateY: 0, rotateZ: 0, opacity: 0 };

function poseOf(scene: HeroScene, t: number, track: readonly HeroScene[]): Pose {
  if (scene.on) return restPose(scene, t);
  // Off-device scenes keep the shape of the nearest device shot, so the phone fades in place.
  const nearest = [...track].sort((a, b) => Math.abs(a.index - scene.index) - Math.abs(b.index - scene.index)).find((s) => s.on);
  return nearest ? { ...restPose(nearest, t), opacity: 0 } : HIDDEN;
}

function currentIndex(frame: number, track: readonly HeroScene[]): number {
  let index = 0;
  track.forEach((scene, i) => {
    if (scene.from <= frame) index = i;
  });
  return index;
}

function sceneProgress(frame: number, scene: HeroScene): number {
  return clamp01((frame - scene.from) / Math.max(1, scene.to - scene.from));
}

function mix(a: Pose, b: Pose, p: number): Pose {
  return {
    cx: lerp(a.cx, b.cx, p),
    cy: lerp(a.cy, b.cy, p),
    glassW: lerp(a.glassW, b.glassW, p),
    glassH: lerp(a.glassH, b.glassH, p),
    bezel: lerp(a.bezel, b.bezel, p),
    radius: lerp(a.radius, b.radius, p),
    frame: lerp(a.frame, b.frame, p),
    rotateY: lerp(a.rotateY, b.rotateY, p),
    rotateZ: lerp(a.rotateZ, b.rotateZ, p),
    opacity: lerp(a.opacity, b.opacity, p),
  };
}

function lerp(from: number, to: number, t: number): number {
  return from + (to - from) * t;
}
