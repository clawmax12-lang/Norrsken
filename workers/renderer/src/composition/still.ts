import type { CSSProperties } from "react";
import { DEVICE } from "./tokens.ts";

/** Slow zoom and pan of a still inside the phone glass (0–1 through the scene). */
export function kenBurnsImageStyle(t: number): CSSProperties {
  const p = clamp01(t);
  return {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    objectPosition: `${50 + 8 * p}% ${p * 14}%`,
    transform: `scale(${(1.08 + 0.04 * p).toFixed(3)})`,
    transformOrigin: `${44 + 12 * p}% ${20 + 22 * p}%`,
    display: "block",
  };
}

/** Landscape mockups have no second device frame. Zoom 1.00 → 1.16, clipped by the product band. */
export function fullBleedStyle(t: number): CSSProperties {
  const p = clamp01(t);
  return {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    objectPosition: "center",
    transform: `scale(${(1 + 0.16 * p).toFixed(3)})`,
    transformOrigin: "50% 42%",
    display: "block",
  };
}

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
 * focus region and holds. The image never slides past its own edges.
 */
export function focusTransform(t: number, focus: FocusBox): { scale: number; x: number; y: number } {
  const [fx, fy, fw, fh] = focus;
  const target = Math.min(FOCUS_MAX_SCALE, Math.max(FOCUS_MIN_SCALE, FOCUS_FILL / Math.max(fw, fh)));
  const p = smooth(clamp01((clamp01(t) - FOCUS_START) / (FOCUS_END - FOCUS_START)));
  const scale = 1 + (target - 1) * p;
  const limit = 0.5 - 0.5 / scale;
  const shift = (centre: number) => Math.min(limit, Math.max(-limit, (0.5 - centre) * p)) + 0;
  return { scale, x: shift(fx + fw / 2), y: shift(fy + fh / 2) };
}

/** CSS for an image that fills its box and punches in on ``focus``. */
export function focusImageStyle(t: number, focus: FocusBox): CSSProperties {
  const { scale, x, y } = focusTransform(t, focus);
  return {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    objectPosition: "center",
    transform: `scale(${scale.toFixed(3)}) translate(${(x * 100).toFixed(2)}%, ${(y * 100).toFixed(2)}%)`,
    transformOrigin: "50% 50%",
    display: "block",
  };
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
