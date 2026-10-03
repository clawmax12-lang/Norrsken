"use client";

import { useEffect, useState } from "react";
import { REGION_GROUPS, regionInfo } from "../../lib/brain/atlas";
import type { Hemisphere } from "../../lib/brain/contract";
import type { RegionRef } from "../../lib/brain/events";
import type { HeadObject } from "../../lib/brain/head";
import type { BrainScene } from "../../lib/brain/scene";
import { useLatest } from "../../lib/brain/useLatest";

/**
 * First-arrival hero: five deliberate anatomical shots on the shared renderer, then dock.
 * Camera and material motion only; it never draws activity that the data does not contain.
 * Times are milliseconds from the moment the mesh is ready.
 */
export const ENTRY_SHOTS = { lateral: 2600, dorsal: 5200, focus: 7800, release: 10400, dock: 11200, end: 12400 } as const;

/** Atlas region the entry camera moves toward (fixed, atlas-backed, not data). */
export const ENTRY_FOCUS_REGION: { hemi: Hemisphere; atlasName: string } = { hemi: "right", atlasName: "superiortemporal" };

type Phase = "reveal" | "lateral" | "dorsal" | "focus" | "release";

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export interface EntrySequenceProps {
  scene: BrainScene;
  head: HeadObject | null;
  atlasNames: string[];
  reducedMotion: boolean;
  onRegionFocus: (region: RegionRef) => void;
  /** Begin the move into the corner dock (the canvas becomes visible). */
  onDock: () => void;
  onFinish: (skipped: boolean) => void;
  /** Receives the function that ends the sequence immediately (the host owns the Skip button). */
  registerSkip: (skip: (() => void) | null) => void;
}

export function EntrySequence(props: EntrySequenceProps) {
  const { scene, head, atlasNames, reducedMotion } = props;
  const [phase, setPhase] = useState<Phase>("reveal");
  const propsRef = useLatest(props);
  const focus = regionInfo(ENTRY_FOCUS_REGION.atlasName);

  useEffect(() => {
    const start = performance.now();
    const label = atlasNames.indexOf(ENTRY_FOCUS_REGION.atlasName);
    let raf = 0;
    let last: Phase | null = null;
    let docked = false;
    let done = false;
    const still = reducedMotion;

    scene.setInteractive(false);
    scene.setSelected(null);
    scene.setAutoRotate(0);
    scene.setAssembly({ reveal: still ? 1 : 0, wire: 0, opacity: still ? 0 : 1, dim: 0 });
    if (head) head.setOpacity(0);
    // Shot 1: low front-left three-quarter, close. Reduced motion holds the profile throughout.
    if (still) scene.applyCameraPreset("profile", 0);
    else scene.flyToDirection([-0.62, 0.02, -0.78], 2.55, 0);

    const enter = (p: Phase) => {
      setPhase(p);
      if (still) {
        if (p === "focus" && label >= 0) scene.setSelected({ hemi: ENTRY_FOCUS_REGION.hemi, label });
        if (p === "release") scene.setSelected(null);
      } else if (p === "lateral") {
        // Shot 2: glide along the right lateral surface, front to back.
        scene.flyToDirection([0.92, 0.12, -0.38], 3.0, 1100);
        window.setTimeout(() => !done && scene.flyToDirection([0.9, 0.2, 0.36], 2.85, 1500), 1100);
      } else if (p === "dorsal") {
        // Shot 3: crane up to a dorsal-posterior oblique across the longitudinal fissure.
        scene.flyToDirection([0.28, 0.86, 0.42], 3.05, 2000);
      } else if (p === "focus") {
        // Shot 4: push in to the superior temporal gyrus (anatomy, not a response).
        if (label >= 0) {
          scene.setSelected({ hemi: ENTRY_FOCUS_REGION.hemi, label });
          scene.focusRegion(ENTRY_FOCUS_REGION.hemi, label, 1700);
        }
      } else if (p === "release") {
        // Shot 5: release to the reference profile, then the same renderer docks.
        scene.setSelected(null);
        scene.applyCameraPreset("profile", 1300);
      }
      if (p === "focus" && focus && label >= 0) propsRef.current.onRegionFocus({ hemi: ENTRY_FOCUS_REGION.hemi, atlasName: focus.key, name: focus.name });
    };

    const frame = () => {
      const ms = performance.now() - start;
      const p: Phase = ms < ENTRY_SHOTS.lateral ? "reveal" : ms < ENTRY_SHOTS.dorsal ? "lateral" : ms < ENTRY_SHOTS.focus ? "dorsal" : ms < ENTRY_SHOTS.release ? "focus" : "release";
      if (p !== last) {
        last = p;
        enter(p);
      }
      if (head) head.setOpacity(smooth(200, 1800, ms));
      if (still) scene.setAssembly({ opacity: smooth(150, 1600, ms) });
      else scene.setAssembly({ wire: smooth(100, 700, ms) * (1 - smooth(1900, 2600, ms)) * 0.45, reveal: smooth(350, 2400, ms) });
      if (!docked && ms >= ENTRY_SHOTS.dock) {
        docked = true;
        propsRef.current.onDock();
      }
      if (ms >= ENTRY_SHOTS.end) {
        complete(false);
        return;
      }
      raf = requestAnimationFrame(frame);
    };

    const complete = (skipped: boolean) => {
      if (done) return;
      done = true;
      cancelAnimationFrame(raf);
      scene.setSelected(null);
      scene.setAssembly({ reveal: 1, wire: 0, opacity: 1, dim: 0 });
      if (head) head.setOpacity(1);
      scene.setInteractive(true);
      scene.applyCameraPreset("profile", skipped ? 0 : 600);
      if (!docked) propsRef.current.onDock();
      propsRef.current.onFinish(skipped);
    };
    const register = propsRef.current.registerSkip;
    register(() => complete(true));
    raf = requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(raf);
      register(null);
    };
    // Runs once per mount; replay remounts the component.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (phase !== "focus" || !focus) return null;
  return (
    <aside className="bv-entry-caption" aria-live="polite">
      <span className="bv-eyebrow">{REGION_GROUPS[focus.group].label} · right hemisphere · atlas region</span>
      <strong>{focus.name}</strong>
      <span>{focus.knownFor}</span>
    </aside>
  );
}
