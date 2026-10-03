/**
 * Mapping from the single playback position to genuine samples.
 *
 * Between two source samples the viewer linearly interpolates for smooth
 * presentation (PRD §12.2); the source timestamps are preserved and reported.
 * Outside the sampled range the edge sample is held for at most one sample
 * period; beyond that there is no prediction to show.
 */

export interface FrameSample {
  /** False when the time is outside the predicted range: show no activity. */
  inRange: boolean;
  i0: number;
  i1: number;
  /** Interpolation weight toward i1 (0..1). */
  alpha: number;
  /** Source timestamp of the nearest genuine sample. */
  nearestIndex: number;
}

const OUT_OF_RANGE: FrameSample = { inRange: false, i0: 0, i1: 0, alpha: 0, nearestIndex: 0 };

export function samplePeriod(times: ArrayLike<number>): number {
  if (times.length < 2) return 1;
  return (times[times.length - 1] - times[0]) / (times.length - 1);
}

/**
 * With `hz`, consecutive samples further apart than 1.5 periods are a gap (e.g. a silent
 * stretch the producer skipped): the earlier sample is held for one period, then nothing.
 */
export function sampleAt(times: ArrayLike<number>, t: number, hz?: number): FrameSample {
  const n = times.length;
  if (n === 0 || !Number.isFinite(t)) return OUT_OF_RANGE;
  const period = hz && hz > 0 ? 1 / hz : samplePeriod(times);
  const first = times[0];
  const last = times[n - 1];
  if (t < first) return t >= first - period ? { inRange: true, i0: 0, i1: 0, alpha: 0, nearestIndex: 0 } : OUT_OF_RANGE;
  if (t >= last) {
    return t <= last + period ? { inRange: true, i0: n - 1, i1: n - 1, alpha: 0, nearestIndex: n - 1 } : OUT_OF_RANGE;
  }
  // Binary search for times[lo] <= t < times[lo + 1].
  let lo = 0;
  let hi = n - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (times[mid] <= t) lo = mid;
    else hi = mid;
  }
  if (hz && times[hi] - times[lo] > 1.5 * period) {
    return t <= times[lo] + period ? { inRange: true, i0: lo, i1: lo, alpha: 0, nearestIndex: lo } : OUT_OF_RANGE;
  }
  const alpha = (t - times[lo]) / (times[hi] - times[lo]);
  return { inRange: true, i0: lo, i1: hi, alpha, nearestIndex: alpha < 0.5 ? lo : hi };
}

/** Linear interpolation of a per-sample series at time t (NaN when out of range). */
export function seriesAt(series: ArrayLike<number>, times: ArrayLike<number>, t: number, hz?: number): number {
  const s = sampleAt(times, t, hz);
  if (!s.inRange) return Number.NaN;
  return series[s.i0] * (1 - s.alpha) + series[s.i1] * s.alpha;
}

export function clampTime(t: number, duration: number): number {
  if (!Number.isFinite(t)) return 0;
  return Math.min(Math.max(t, 0), Math.max(duration, 0));
}

/** Arrow-key step: whole seconds, landing on integer boundaries. */
export function stepSeconds(t: number, direction: 1 | -1, duration: number): number {
  const next = direction > 0 ? Math.floor(t + 1e-6) + 1 : Math.ceil(t - 1e-6) - 1;
  return clampTime(next, duration);
}

export function formatTime(t: number): string {
  const safe = Math.max(0, Number.isFinite(t) ? t : 0);
  const m = Math.floor(safe / 60);
  const s = Math.floor(safe % 60);
  const tenths = Math.floor((safe * 10) % 10);
  return `${m}:${String(s).padStart(2, "0")}.${tenths}`;
}

export function sceneAt<T extends { t_start: number; t_end: number }>(scenes: readonly T[] | undefined, t: number): T | undefined {
  if (!scenes) return undefined;
  return scenes.find((s) => t >= s.t_start && t < s.t_end);
}
