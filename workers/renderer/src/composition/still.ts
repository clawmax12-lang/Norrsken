import { DEVICE } from "./tokens.ts";

/** A region of the screenshot to zoom into: x, y, width, height as fractions of the image. */
export type FocusBox = readonly [number, number, number, number];

/** The focus box of a scene, or null when it has none or it is not four fractions. */
export function focusOf(value: unknown): FocusBox | null {
  if (!Array.isArray(value) || value.length !== 4) return null;
  const numbers = value.map(Number);
  if (numbers.some((n) => !Number.isFinite(n) || n < 0 || n > 1)) return null;
  const [x, y, w, h] = numbers as [number, number, number, number];
  return w > 0 && h > 0 ? [x, y, w, h] : null;
}

const FOCUS_START = 0.22;
const FOCUS_END = 0.72;
const FOCUS_MIN_SCALE = 1.15;
const FOCUS_MAX_SCALE = 2.0;
const FOCUS_FILL = 0.85;

/**
 * Two-phase punch-in: the whole screen first (context), then an eased zoom that centres the
 * focus region and holds. The image never slides past its own edges, and never zooms past
 * ``maxScale`` so a small source is not enlarged into blur.
 */
export function focusTransform(
  t: number,
  focus: FocusBox,
  maxScale: number = FOCUS_MAX_SCALE,
): { scale: number; x: number; y: number } {
  const [fx, fy, fw, fh] = focus;
  const ceiling = Math.max(1, Math.min(FOCUS_MAX_SCALE, maxScale));
  const floor = Math.min(FOCUS_MIN_SCALE, ceiling, 1 / Math.max(fw, fh));
  const target = Math.min(ceiling, Math.max(floor, FOCUS_FILL / Math.max(fw, fh)));
  const p = smooth(clamp01((clamp01(t) - FOCUS_START) / (FOCUS_END - FOCUS_START)));
  const scale = 1 + (target - 1) * p;
  const limit = 0.5 - 0.5 / scale;
  const shift = (centre: number) => Math.min(limit, Math.max(-limit, (0.5 - centre) * p)) + 0;
  return { scale, x: shift(fx + fw / 2), y: shift(fy + fh / 2) };
}

/** No source pixel is drawn larger than this; beyond it a screenshot visibly softens. */
export const MAX_UPSCALE = 2.0;
const DRIFT = 0.05;

export interface ImageSize {
  readonly width: number;
  readonly height: number;
}

/** Where to draw the whole image so that ``crop`` (or all of it) covers a box, centred. */
export function coverLayout(
  image: ImageSize,
  crop: FocusBox | null,
  boxW: number,
  boxH: number,
): { left: number; top: number; width: number; height: number; scale: number } {
  const [cx, cy, cw, ch] = crop ?? [0, 0, 1, 1];
  const regionW = cw * image.width;
  const regionH = ch * image.height;
  const scale = Math.max(boxW / regionW, boxH / regionH);
  return {
    left: (boxW - regionW * scale) / 2 - cx * image.width * scale,
    top: (boxH - regionH * scale) / 2 - cy * image.height * scale,
    width: image.width * scale,
    height: image.height * scale,
    scale,
  };
}

/** The motion on top of the cover fit: focus punch-in, else a slow drift, both within the cap. */
export function stageTransform(t: number, focus: FocusBox | null, coverScale: number): string {
  const room = MAX_UPSCALE / coverScale;
  if (focus) {
    const { scale, x, y } = focusTransform(t, focus, room);
    return `scale(${scale.toFixed(3)}) translate(${(x * 100).toFixed(2)}%, ${(y * 100).toFixed(2)}%)`;
  }
  const drift = Math.max(0, Math.min(DRIFT, room - 1));
  return `scale(${(1 + drift * clamp01(t)).toFixed(3)})`;
}

/** Aspect (width / height) of what a scene shows: the device display of a mockup, else the image. */
export function regionAspect(image: ImageSize, crop: FocusBox | null): number {
  const [, , cw, ch] = crop ?? [0, 0, 1, 1];
  return (cw * image.width) / (ch * image.height);
}

function smooth(p: number): number {
  return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
}

export function isPhoneAspect(aspect: number): boolean {
  return aspect <= DEVICE.phoneMaxAspect;
}

function clamp01(t: number): number {
  return Math.min(1, Math.max(0, t));
}
