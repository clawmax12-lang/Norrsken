"use client";

/**
 * Workload choreography for the docked brain (FR-12 dock, PRD v1.5 canvas companion).
 *
 * - Idle: slow spin. Backend work running: brisk spin plus a halo/status (presentation only).
 * - A live milestone event: ~3 s slower focus beat with the backend's own message. The
 *   camera moves to a region ONLY when the event's variant has genuine TRIBE samples; the
 *   region is the strongest genuine response, the time is its sample time and the text is
 *   the concept scene at that time. Otherwise a neutral detail view, no region.
 * - Never changes playback time or speed. Reduced motion, Pause motion and manual orbit
 *   suppress all camera/spin motion; the text still appears.
 */

import { useEffect, useRef, useState } from "react";
import type { Hemisphere } from "../../lib/brain/contract";
import type { DataMode } from "../../lib/brain/events";
import type { BrainScene } from "../../lib/brain/scene";
import { FOCUS_BEAT_MS, RESULT_STEPS, RESULT_WAIT_MS, isWorking, type Milestone, type WorkloadState } from "../../lib/brain/workload";
import { useLatest } from "../../lib/brain/useLatest";

export const SPIN_IDLE = 0.16;
export const SPIN_WORKING = 0.85;

export interface BeatRegion {
  hemi: Hemisphere;
  label: number;
  atlasName: string;
  name: string;
  knownFor: string;
  group: string;
  /** Source timestamp of the genuine sample the region was chosen from. */
  sampleTime: number;
  sceneText: string | null;
  dataMode: DataMode;
}

export interface FocusBeat {
  milestone: Milestone;
  region: BeatRegion | null;
  /** True when the camera actually moved (false for reduced motion / paused / manual). */
  moved: boolean;
}

interface Options {
  scene: BrainScene | null;
  /** Dock visible and no entry/analysis sequence running. */
  active: boolean;
  workload: WorkloadState | undefined;
  /** Called with a milestone id once its beat starts. */
  consumeMilestone: ((id: number) => void) | undefined;
  reducedMotion: boolean;
  motionPaused: boolean;
  manual: boolean;
  /** Region for a milestone from genuine data, or null. Must not invent one. */
  resolveRegion: (m: Milestone) => BeatRegion | null;
  /** Changes whenever bound data changes, so a waiting result beat re-checks. */
  dataVersion: unknown;
  /** Selection to restore after the beat. */
  restoreSelection: () => void;
  onBeat?: (beat: FocusBeat) => void;
}

export function useDockChoreography(opts: Options): FocusBeat | null {
  const { scene, active, workload, reducedMotion, motionPaused, manual } = opts;
  const [beat, setBeat] = useState<FocusBeat | null>(null);
  const beatRef = useRef<FocusBeat | null>(null);
  const timerRef = useRef(0);
  const optsRef = useLatest(opts);
  const still = reducedMotion || motionPaused || manual;
  const working = workload ? isWorking(workload) : false;

  // Spin: brisk while real work runs, slow when idle, none during a beat or when still.
  // Outside the dock (entry, analysis, expanded) other code owns the camera; only stop on exit.
  const wasActive = useRef(false);
  useEffect(() => {
    if (!scene) return;
    if (!active) {
      if (wasActive.current) scene.setAutoRotate(0);
      wasActive.current = false;
      return;
    }
    wasActive.current = true;
    scene.setAutoRotate(still || beat ? 0 : working ? SPIN_WORKING : SPIN_IDLE);
  }, [scene, active, still, beat, working]);

  useEffect(() => {
    if (!scene) return;
    return () => scene.setAutoRotate(0);
  }, [scene]);

  // Start the next focus beat when one is queued and none is playing. The queue head is read
  // from this render's props (never a stale ref), then consumed by id.
  const head = workload?.queue[0];
  const [tick, setTick] = useState(0);
  const dataVersion = opts.dataVersion;
  useEffect(() => {
    const o = optsRef.current;
    if (!scene || !active || beatRef.current || !head) return;
    const milestone = head;
    let region = o.resolveRegion(milestone);
    // Results for a simulate/score/explain step are fetched when the event arrives; give the
    // genuine artifact a moment to load so the beat can show its real region.
    const waited = Date.now() - milestone.receivedAtMs;
    if (!region && RESULT_STEPS.includes(milestone.step) && milestone.variantId && waited < RESULT_WAIT_MS) {
      const retry = window.setTimeout(() => setTick((n) => n + 1), Math.min(400, RESULT_WAIT_MS - waited));
      return () => window.clearTimeout(retry);
    }
    region = region ?? null;
    o.consumeMilestone?.(milestone.id);
    const moved = !(o.reducedMotion || o.motionPaused || o.manual);
    const next: FocusBeat = { milestone, region, moved };
    beatRef.current = next;
    setBeat(next);
    o.onBeat?.(next);
    if (region) scene.setSelected({ hemi: region.hemi, label: region.label });
    if (moved) {
      if (region) scene.focusRegion(region.hemi, region.label, 1100);
      else scene.applyCameraPreset("detail", 1100);
    }
    timerRef.current = window.setTimeout(() => {
      const current = optsRef.current;
      if (region) current.restoreSelection();
      if (moved) scene.applyCameraPreset("profile", 900);
      beatRef.current = null;
      setBeat(null);
    }, FOCUS_BEAT_MS);
  }, [scene, active, head, beat, tick, dataVersion, optsRef]);

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  return beat;
}
