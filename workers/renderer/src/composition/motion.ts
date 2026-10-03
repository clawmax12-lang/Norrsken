/** Easing curves and tiny helpers shared by every scene. Curves follow Apple-style ease-outs. */
import { Easing, interpolate, spring } from "remotion";

export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
export const easeStandard = Easing.bezier(0.28, 0.11, 0.32, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

/** Critically-damped spring: settles without bounce, like a system animation. */
export const SMOOTH_SPRING = { damping: 30, stiffness: 120, mass: 1 } as const;
/** Slightly livelier spring with a hint of overshoot, for the device entrance. */
export const SOFT_SPRING = { damping: 20, stiffness: 100, mass: 1 } as const;

/** 0 -> 1 over `duration` frames starting at `start`, eased; clamped outside the range. */
export function progress(
  frame: number,
  start: number,
  duration: number,
  easing: (t: number) => number = easeOut,
): number {
  return interpolate(frame, [start, start + duration], [0, 1], {
    easing,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
}

export function springIn(
  frame: number,
  fps: number,
  delay: number,
  config: typeof SMOOTH_SPRING | typeof SOFT_SPRING = SMOOTH_SPRING,
): number {
  return spring({ frame: frame - delay, fps, config });
}

export function lerp(from: number, to: number, t: number): number {
  return from + (to - from) * t;
}
