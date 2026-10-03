/**
 * Events the brain companion exposes to the canvas (Dashboard) and the voice
 * owner (FR-16). The brain never speaks or schedules jobs itself; consumers
 * decide what to narrate or reveal. Delivered to the `onEvent` prop and as a
 * `window` CustomEvent named BRAIN_EVENT for loosely coupled listeners.
 *
 * Payloads describe presentation state only. `dataMode` tells consumers what
 * the visible activity is, so narration never presents a demo example, MOCK
 * fixture or empty anatomy as the user's tested result.
 */

import type { Hemisphere } from "./contract.ts";

export const BRAIN_EVENT = "preflight:brain";

export type BrainMode = "entry" | "dock" | "expanded";

/** What the cortex is showing right now. */
export type DataMode = "none" | "sim_off" | "demo_example" | "genuine" | "genuine_precomputed" | "mock";

export interface RegionRef {
  hemi: Hemisphere;
  /** FreeSurfer aparc key, e.g. "superiortemporal". */
  atlasName: string;
  /** Display name from the fixed atlas list. */
  name: string;
}

export interface SceneSnapshot {
  index: number;
  t_start: number;
  t_end: number;
  text: string;
}

/** Everything a canvas/voice consumer needs to describe "what is selected now". */
export interface SelectionSnapshot {
  projectId: string | null;
  runId: string | null;
  variant: string;
  time_s: number;
  /** Nearest genuine sample time, or null without data / outside the sampled range. */
  sample_time_s: number | null;
  scene: SceneSnapshot | null;
  region: RegionRef | null;
  dataMode: DataMode;
  mode: BrainMode;
}

export type BrainEvent =
  | { type: "entry.started"; replay: boolean; dataMode: DataMode }
  | { type: "entry.region_focus"; region: RegionRef; dataMode: DataMode }
  | { type: "entry.completed"; skipped: boolean }
  | { type: "analysis.started"; runId: string; variant: string }
  | { type: "analysis.lock_on"; runId: string; variant: string; region: RegionRef; time_s: number }
  | { type: "analysis.completed"; runId: string; variant: string; skipped: boolean }
  | { type: "mode.changed"; mode: BrainMode }
  | { type: "variant.selected"; variant: string; dataMode: DataMode }
  | { type: "region.selected"; region: RegionRef | null; time_s: number; dataMode: DataMode }
  /** Emitted on variant/region/mode change, seek and pause (never per animation frame). */
  | { type: "selection.changed"; selection: SelectionSnapshot };

/**
 * Commands a host (canvas, voice owner after the user confirms a change) can
 * send without prop drilling: `window.dispatchEvent(new CustomEvent(BRAIN_COMMAND, { detail }))`.
 * In controlled use, prefer passing `selectedVariant` from the canvas's own state;
 * the brain then reports `onSelectVariant` requests instead of owning selection.
 */
export const BRAIN_COMMAND = "preflight:brain-command";

export type BrainCommand =
  | { type: "select_variant"; variant: string }
  | { type: "seek"; time_s: number }
  | { type: "play" }
  | { type: "pause" }
  | { type: "set_mode"; mode: Exclude<BrainMode, "entry"> }
  | { type: "select_region"; hemi: Hemisphere; atlasName: string }
  | { type: "clear_region" }
  | { type: "replay_entry" };

export function dispatchBrainEvent(event: BrainEvent, onEvent?: (e: BrainEvent) => void): void {
  onEvent?.(event);
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent<BrainEvent>(BRAIN_EVENT, { detail: event }));
}

/** Session-scoped "entry played" flag (FR-14: once per browser session). */
export const ENTRY_SESSION_KEY = "preflight.entry.played";
/** Run-scoped "analysis played" flag prefix (FR-14: once per run). */
export const ANALYSIS_RUN_KEY_PREFIX = "preflight.analysis.played:";
