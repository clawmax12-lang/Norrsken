"use client";

import { useEffect, useRef, useState } from "react";
import { REGION_GROUPS, regionInfo } from "../../lib/brain/atlas";
import type { Hemisphere } from "../../lib/brain/contract";
import type { DataMode, RegionRef } from "../../lib/brain/events";
import type { HeadObject } from "../../lib/brain/head";
import type { BrainScene } from "../../lib/brain/scene";
import { useLatest } from "../../lib/brain/useLatest";

/** First-arrival hero (PRD v1.4 §12.2), milliseconds. */
export const ENTRY_BEATS = { reveal: 900, orbit: 3600, focus: 7600, release: 10200, dock: 10900, end: 12000 } as const;

/** Atlas region the entry camera moves toward (fixed, atlas-backed, not data). */
export const ENTRY_FOCUS_REGION: { hemi: Hemisphere; atlasName: string } = { hemi: "right", atlasName: "superiortemporal" };

type Phase = "reveal" | "orbit" | "focus" | "release";

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

export interface EntrySequenceProps {
  scene: BrainScene;
  head: HeadObject | null;
  atlasNames: string[];
  reducedMotion: boolean;
  dataMode: DataMode;
  /** Shown under the title, e.g. "Anatomy only · No brain data". */
  dataLabel: string;
  replay: boolean;
  onRegionFocus: (region: RegionRef) => void;
  /** Begin the move into the corner dock (the canvas becomes visible). */
  onDock: () => void;
  onFinish: (skipped: boolean) => void;
}

export function EntrySequence(props: EntrySequenceProps) {
  const { scene, head, atlasNames, reducedMotion, dataLabel } = props;
  const [phase, setPhase] = useState<Phase>("reveal");
  const propsRef = useLatest(props);
  const skipRef = useRef<() => void>(() => {});
  const focus = regionInfo(ENTRY_FOCUS_REGION.atlasName);

  useEffect(() => {
    const start = performance.now();
    const label = atlasNames.indexOf(ENTRY_FOCUS_REGION.atlasName);
    let raf = 0;
    let last: Phase | null = null;
    let docked = false;
    let done = false;

    scene.setInteractive(false);
    scene.setSelected(null);
    scene.setAutoRotate(0);
    scene.setAssembly({ reveal: reducedMotion ? 1 : 0, wire: 0, opacity: reducedMotion ? 0 : 1, dim: 0 });
    if (head) head.setOpacity(0);
    scene.applyCameraPreset(reducedMotion ? "profile" : "intro-start", 0);

    const enter = (p: Phase) => {
      setPhase(p);
      if (p === "reveal" && !reducedMotion) scene.applyCameraPreset("profile", ENTRY_BEATS.orbit - 200);
      if (p === "orbit") scene.setAutoRotate(0.42);
      if (p === "focus") {
        scene.setAutoRotate(0);
        if (label >= 0) {
          scene.setSelected({ hemi: ENTRY_FOCUS_REGION.hemi, label });
          if (!reducedMotion) scene.focusRegion(ENTRY_FOCUS_REGION.hemi, label, 1800);
          if (focus) propsRef.current.onRegionFocus({ hemi: ENTRY_FOCUS_REGION.hemi, atlasName: focus.key, name: focus.name });
        }
      }
      if (p === "release") {
        scene.setSelected(null);
        if (!reducedMotion) scene.applyCameraPreset("profile", 1400);
      }
    };

    const frame = () => {
      const ms = performance.now() - start;
      const p: Phase = ms < ENTRY_BEATS.orbit ? "reveal" : ms < ENTRY_BEATS.focus ? "orbit" : ms < ENTRY_BEATS.release ? "focus" : "release";
      if (p !== last) {
        last = p;
        enter(p);
      }
      if (head) head.setOpacity(smooth(0, 1600, ms));
      if (reducedMotion) {
        scene.setAssembly({ opacity: smooth(300, 2200, ms) });
      } else {
        scene.setAssembly({ wire: smooth(ENTRY_BEATS.reveal - 400, ENTRY_BEATS.reveal + 500, ms) * (1 - smooth(2600, 3400, ms)) * 0.5, reveal: smooth(ENTRY_BEATS.reveal, 3300, ms) });
      }
      if (!docked && ms >= ENTRY_BEATS.dock) {
        docked = true;
        propsRef.current.onDock();
      }
      if (ms >= ENTRY_BEATS.end) {
        complete(false);
        return;
      }
      raf = requestAnimationFrame(frame);
    };

    const complete = (skipped: boolean) => {
      if (done) return;
      done = true;
      cancelAnimationFrame(raf);
      scene.setAutoRotate(0);
      scene.setSelected(null);
      scene.setAssembly({ reveal: 1, wire: 0, opacity: 1, dim: 0 });
      if (head) head.setOpacity(1);
      scene.setInteractive(true);
      scene.applyCameraPreset("profile", skipped ? 0 : 600);
      if (!docked) propsRef.current.onDock();
      propsRef.current.onFinish(skipped);
    };
    skipRef.current = () => complete(true);
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
    // Runs once per mount; replay remounts the component.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className={`bv-entry bv-entry-${phase}${reducedMotion ? " bv-entry-reduced" : ""}`} role="dialog" aria-modal="false" aria-label="Preflight entry">
      <button type="button" className="bv-skip" onClick={() => skipRef.current()} autoFocus>
        Skip <span aria-hidden="true">→</span>
      </button>
      <div className="bv-entry-title">
        <span className="bv-entry-mark" aria-hidden="true" />
        <h1>Preflight</h1>
        <p className="bv-mono">Simulated viewers for launch videos</p>
        <span className="bv-chip">{dataLabel}</span>
      </div>
      {phase === "focus" && focus && (
        <aside className="bv-seq-card bv-entry-card" aria-live="polite">
          <span className="bv-eyebrow">{REGION_GROUPS[focus.group].label} · Right hemisphere · atlas region</span>
          <h2>{focus.name}</h2>
          <p>{focus.knownFor}</p>
          <p className="bv-mono bv-dim">Desikan-Killiany atlas on fsaverage5 · anatomy, not a response</p>
        </aside>
      )}
    </div>
  );
}
