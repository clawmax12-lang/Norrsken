/**
 * Workload choreography state, derived only from real backend activity events.
 *
 * This drives presentation (spin speed, halo, status line, short focus beats). It never
 * produces cortical values, never picks a region on its own and never touches playback
 * time: a focus beat's region comes only from genuine TRIBE samples for the event's variant.
 */

import type { ActivityEvent, BackendRunState, BackendStep } from "./backend";

/** Steps whose successful completion is a meaningful milestone worth a focus beat. */
export const MILESTONE_STEPS: readonly BackendStep[] = ["plan", "render", "simulate", "score", "explain", "export"];

/** Steps after which genuine per-variant brain data may exist (results are re-fetched). */
export const RESULT_STEPS: readonly BackendStep[] = ["simulate", "score", "explain", "export"];

/** Events older than this when received are history (replay on connect), not live milestones. */
export const LIVE_WINDOW_MS = 30_000;

export const FOCUS_BEAT_MS = 3_000;
/** A result-step beat waits at most this long for the variant's genuine data to load. */
export const RESULT_WAIT_MS = 2_500;
export const MAX_QUEUED_BEATS = 2;

export const STEP_LABELS: Record<BackendStep, string> = {
  plan: "Planning concepts",
  generate: "Generating composition",
  render: "Rendering",
  simulate: "Simulating viewers",
  score: "Scoring",
  explain: "Explaining",
  iterate: "Revising winner",
  export: "Exporting",
};

export interface Milestone {
  id: number;
  step: BackendStep;
  variantId: string | null;
  /** Backend-authored message, shown verbatim. */
  message: string;
  durationS: number | null;
  at: string;
  /** Client receive time, used to briefly wait for that step's results before the beat. */
  receivedAtMs: number;
}

export interface WorkloadState {
  /** Highest SSE id applied; replays at or below it are ignored. */
  lastId: number;
  /** Steps currently started and not yet finished, keyed "step" or "step:variant". */
  running: string[];
  /** Latest event, for the status line. */
  latest: ActivityEvent | null;
  /** Live milestones waiting for a focus beat (bounded). */
  queue: Milestone[];
  /** Terminal run state from the stream's `end` frame. */
  ended: BackendRunState | null;
  failed: ActivityEvent | null;
}

export const INITIAL_WORKLOAD: WorkloadState = { lastId: -1, running: [], latest: null, queue: [], ended: null, failed: null };

function key(e: ActivityEvent): string {
  return e.variant_id ? `${e.step}:${e.variant_id}` : e.step;
}

export function applyActivity(state: WorkloadState, id: number, event: ActivityEvent, receivedAtMs: number): WorkloadState {
  if (!Number.isInteger(id) || id <= state.lastId) return state;
  const k = key(event);
  let running = state.running.filter((r) => r !== k);
  if (event.status === "started") running = [...running, k];
  const live = receivedAtMs - Date.parse(event.at) <= LIVE_WINDOW_MS;
  let queue = state.queue;
  if (live && event.status === "succeeded" && MILESTONE_STEPS.includes(event.step)) {
    const milestone: Milestone = { id, step: event.step, variantId: event.variant_id, message: event.message, durationS: event.duration_s, at: event.at, receivedAtMs };
    // Keep the newest few: a burst of completions should not queue a minute of beats.
    queue = [...queue, milestone].slice(-MAX_QUEUED_BEATS);
  }
  return {
    lastId: id,
    running,
    latest: event,
    queue,
    ended: state.ended,
    failed: event.status === "failed" ? event : state.failed,
  };
}

export function applyEnd(state: WorkloadState, runState: BackendRunState): WorkloadState {
  return { ...state, running: [], ended: runState };
}

/** Remove a milestone once its focus beat has started. */
export function consumeMilestone(state: WorkloadState, id: number): WorkloadState {
  return state.queue.some((m) => m.id === id) ? { ...state, queue: state.queue.filter((m) => m.id !== id) } : state;
}

export function shiftMilestone(state: WorkloadState): [Milestone | undefined, WorkloadState] {
  if (state.queue.length === 0) return [undefined, state];
  const [next, ...rest] = state.queue;
  return [next, { ...state, queue: rest }];
}

export function isWorking(state: WorkloadState): boolean {
  return state.running.length > 0 && !state.ended;
}

/** One-line, factual status for the dock (no invented numbers or claims). */
export function statusLine(state: WorkloadState): string {
  if (state.ended === "DONE") return "Run complete";
  if (state.ended === "FAILED") return state.failed ? state.failed.message : "Run failed";
  const e = state.latest;
  if (!e) return "No active run";
  const variant = e.variant_id ? ` · Variant ${e.variant_id}` : "";
  if (e.status === "started") return `${STEP_LABELS[e.step]}${variant}`;
  return e.message;
}
