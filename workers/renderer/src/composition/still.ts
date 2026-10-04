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

export function isPhoneAspect(aspect: number): boolean {
  return aspect <= DEVICE.phoneMaxAspect;
}

function clamp01(t: number): number {
  return Math.min(1, Math.max(0, t));
}
