/**
 * Pure maths for the spec's beats: the shared clock the soundtrack also plays to. Each headline
 * word rises on the frame it is heard, the keyword slams in (a number counts up while the
 * ticks play), a finger taps the screen's focus and the camera punches in right after.
 */
import type { Beat, BeatKind, CompositionSpec, SceneSpec } from "../spec/types.generated.ts";
import { clamp01, smooth } from "./still.ts";

/** Frames the finger takes to come down onto the screen before the tap lands. */
export const TAP_APPROACH = 7;
/** Frames the ripple takes to spread and fade after the tap. */
export const RIPPLE_FRAMES = 16;
/** How much bigger the keyword gets at the top of its slam. */
export const SLAM_SCALE = 0.22;
/** The hook headline lands from this much bigger on frame 0, still readable. */
export const HOOK_SCALE = 0.08;
/** Share of the punch-in the camera keeps after its overshoot, until the scene ends. */
const PUNCH_HOLD = 0.7;
const PUNCH_SETTLE = 18;

const NUMBER = /^(\D*?)(\d+(?:[.,]\d+)?)(.*)$/u;

export function sceneBeats(spec: CompositionSpec, index: number): Beat[] {
  return (spec.beats ?? []).filter((beat) => beat.scene === index);
}

export function firstBeat(beats: readonly Beat[], ...kinds: BeatKind[]): Beat | null {
  return beats.find((beat) => kinds.includes(beat.kind)) ?? null;
}

/** Local frame at which each headline word starts to rise, or null when the spec has none. */
export function wordDelays(scene: SceneSpec): number[] | null {
  const frames = scene.text_frames ?? [];
  return frames.length > 0 ? frames.map((f) => f - scene.start_frame) : null;
}

export interface Keyword {
  /** Index of the word in ``text.split(/\s+/)``. */
  readonly index: number;
  /** Local frame the keyword is spoken. */
  readonly at: number;
  readonly frames: number;
  readonly count: boolean;
}

/** The headline word that lands on its own beat: a number first, else the emphasis word. */
export function keywordOf(scene: SceneSpec, beats: readonly Beat[]): Keyword | null {
  const beat = firstBeat(beats, "word", "count");
  if (beat === null) return null;
  const words = scene.text.split(/\s+/).filter((w) => w.length > 0);
  let index = words.findIndex((w) => /^\d+([.,]\d+)?$/u.test(bare(w)));
  if (index < 0 && scene.emphasis) index = words.findIndex((w) => bare(w) === bare(scene.emphasis ?? ""));
  if (index < 0) return null;
  return { index, at: beat.frame - scene.start_frame, frames: beat.frames, count: beat.kind === "count" };
}

/** Extra scale of a word that slams in at ``at``: a fast rise, then a settle back to 1. */
export function slam(frame: number, at: number, frames: number): number {
  const up = smooth(clamp01((frame - at) / 3));
  const down = smooth(clamp01((frame - at - 3) / (frames + 6)));
  return SLAM_SCALE * up * (1 - down);
}

/** ``word`` with its number counted up to share ``p``, keeping prefix, suffix and decimals. */
export function countText(word: string, p: number): string {
  const match = NUMBER.exec(word);
  if (match === null) return word;
  const [, prefix = "", digits = "", suffix = ""] = match;
  const separator = digits.includes(",") ? "," : ".";
  const decimals = digits.split(/[.,]/u)[1]?.length ?? 0;
  const value = Number(digits.replace(",", ".")) * clamp01(p);
  return `${prefix}${value.toFixed(decimals).replace(".", separator)}${suffix}`;
}

export interface TapMark {
  /** Opacity of the fingertip. */
  readonly touch: number;
  /** Fingertip scale: comes down from larger, dips as it presses. */
  readonly scale: number;
  /** Ripple radius as a multiple of the fingertip. */
  readonly ripple: number;
  readonly rippleOpacity: number;
}

/** The fingertip and ripple of a tap landing at absolute ``tapFrame``, or null when off. */
export function tapMark(frame: number, tapFrame: number): TapMark | null {
  const since = frame - tapFrame;
  if (since < -TAP_APPROACH || since > RIPPLE_FRAMES) return null;
  if (since < 0) {
    const p = smooth(1 + since / TAP_APPROACH);
    return { touch: 0.9 * p, scale: 1.5 - 0.5 * p, ripple: 1, rippleOpacity: 0 };
  }
  const press = since < 4 ? 1 - 0.18 * Math.sin((Math.PI * since) / 4) : 1;
  const r = smooth(since / RIPPLE_FRAMES);
  return { touch: 0.9 * (1 - smooth(clamp01((since - 6) / 10))), scale: press, ripple: 1 + 1.8 * r, rippleOpacity: 0.55 * (1 - r) };
}

/**
 * 0-1 punch-in at ``frame``: an overshoot to full, then held at ``PUNCH_HOLD``. A second
 * punch in the same scene pulls the camera back out to nothing over its frames.
 */
export function punchAmount(frame: number, punches: readonly Beat[]): number {
  const [punch, release] = punches;
  if (punch === undefined || frame < punch.frame) return 0;
  const rise = smooth(clamp01((frame - punch.frame) / punch.frames));
  const settle = smooth(clamp01((frame - punch.frame - punch.frames) / PUNCH_SETTLE));
  const out = release ? smooth(clamp01((frame - release.frame) / release.frames)) : 0;
  return rise * (1 - (1 - PUNCH_HOLD) * settle) * (1 - out);
}

/** Where the camera is punched in at a frame: how far (0-1) and toward which tapped point. */
export interface PunchState {
  readonly amount: number;
  readonly point: readonly [number, number] | null;
}

/** Frames between a tap and the punch it triggers; a punch with no tap this close pulls back out. */
const PUNCH_AFTER_TAP = 4;

/**
 * The camera across a run of taps: the first punch overshoots in on its point, and each later
 * tap pans the punched camera over to its own point with a fresh overshoot, so the finished ad
 * jumps from element to element. A punch that follows no tap pulls the camera back out.
 */
export function punchState(frame: number, taps: readonly Beat[], punches: readonly Beat[]): PunchState {
  const runs = punches.flatMap((punch) => {
    const tap = taps.find((t) => t.frame <= punch.frame && punch.frame - t.frame <= PUNCH_AFTER_TAP);
    const point = tap ? pointOf(tap.point) : null;
    return point ? [{ punch, point }] : [];
  });
  const release = punches.find((p) => !runs.some((r) => r.punch === p));
  const active = runs.filter((r) => r.punch.frame <= frame);
  const current = active[active.length - 1];
  if (current === undefined) {
    return { amount: 0, point: runs[0]?.point ?? null };
  }
  const level = (punch: Beat) => punchAmount(frame, [punch]);
  const previous = active[active.length - 2];
  const amount = previous ? Math.max(level(previous.punch), level(current.punch)) : level(current.punch);
  const rise = smooth(clamp01((frame - current.punch.frame) / current.punch.frames));
  const point: readonly [number, number] = previous
    ? [previous.point[0] + (current.point[0] - previous.point[0]) * rise, previous.point[1] + (current.point[1] - previous.point[1]) * rise]
    : current.point;
  const out = release && release.frame > current.punch.frame ? smooth(clamp01((frame - release.frame) / release.frames)) : 0;
  return { amount: amount * (1 - out), point };
}

/** A beat's point as two 0-1 numbers, or null when it has none. */
export function pointOf(value: unknown): readonly [number, number] | null {
  if (!Array.isArray(value) || value.length !== 2) return null;
  const [x, y] = value.map(Number) as [number, number];
  return [x, y].every((n) => Number.isFinite(n) && n >= 0 && n <= 1) ? [x, y] : null;
}

function bare(word: string): string {
  return word.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "").toLocaleLowerCase();
}
