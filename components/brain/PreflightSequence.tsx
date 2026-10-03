"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { METER_GROUPS, REGION_GROUPS, regionInfo, strongestMoment, type GroupId, type RegionStatistics } from "../../lib/brain/atlas";
import type { PlaybackClock } from "../../lib/brain/clock";
import type { Hemisphere, SceneRef } from "../../lib/brain/contract";
import type { HeadObject } from "../../lib/brain/head";
import type { BrainScene } from "../../lib/brain/scene";
import { useLatest } from "../../lib/brain/useLatest";
import { formatTime, sceneAt, seriesAt } from "../../lib/brain/timeline";
import { GROUP_COLORS } from "./Timeline";

/** PRD §12.2 beats, in milliseconds. */
export const SEQUENCE_BEATS = { dim: 0, assemble: 1500, watch: 4000, lockOn: 9000, handOver: 12000, end: 15000 } as const;

type Beat = "dim" | "assemble" | "watch" | "lockOn" | "handOver";

/** Right-hemisphere anchor regions for the HUD lines (visible in profile). */
const ANCHORS: Record<"visual" | "auditory" | "language", string> = {
  visual: "lateraloccipital",
  auditory: "superiortemporal",
  language: "parsopercularis",
};

export interface SequenceProps {
  scene: BrainScene;
  head: HeadObject | null;
  clock: PlaybackClock;
  variant: string;
  stats: RegionStatistics | null;
  times: Float64Array | null;
  hz?: number;
  scenes?: SceneRef[];
  atlasNames: string[];
  meterMax: number;
  reducedMotion: boolean;
  mock: boolean;
  precomputed: boolean;
  /** Called when the hand-over begins, so the Results layout can slide in. */
  onHandOver: () => void;
  /** The lock-on beat chose this genuine strongest region/time. */
  onLockOn?: (hemi: Hemisphere, atlasName: string, time_s: number) => void;
  /** `locked` is the lock-on region left selected for the Results view. */
  onFinish: (skipped: boolean, locked: { hemi: Hemisphere; label: number } | null) => void;
}

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function beatAt(ms: number): Beat {
  if (ms < SEQUENCE_BEATS.assemble) return "dim";
  if (ms < SEQUENCE_BEATS.watch) return "assemble";
  if (ms < SEQUENCE_BEATS.lockOn) return "watch";
  if (ms < SEQUENCE_BEATS.handOver) return "lockOn";
  return "handOver";
}

export function PreflightSequence(props: SequenceProps) {
  const { scene, head, clock, variant, stats, times, scenes, atlasNames, meterMax, reducedMotion, mock, precomputed } = props;
  const [beat, setBeat] = useState<Beat>("dim");
  const rootRef = useRef<HTMLDivElement>(null);
  const lineRefs = useRef<Record<string, SVGLineElement | null>>({});
  const meterRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const handedOver = useRef(false);
  const skipRef = useRef<() => void>(() => {});
  const propsRef = useLatest(props);
  const clockState = useSyncExternalStore(clock.subscribe, clock.getSnapshot, clock.getSnapshot);
  const hasData = Boolean(stats && times);
  const strongest = stats ? strongestMoment(stats) : null;
  const strongestTime = strongest && times ? times[strongest.sampleIndex] : null;
  const strongestRegion = strongest ? { hemi: strongest.key.split(":")[0] as Hemisphere, name: strongest.key.split(":")[1] } : null;

  useEffect(() => {
    handedOver.current = false;
    const start = performance.now();
    const labelOf = (name: string) => atlasNames.indexOf(name);
    let raf = 0;
    let lastBeat: Beat | null = null;

    // Initial state: hidden brain, start pose.
    clock.pause();
    clock.seek(0);
    scene.setInteractive(false);
    scene.setSelected(null);
    scene.setAssembly({ reveal: reducedMotion ? 1 : 0, wire: 0, opacity: reducedMotion ? 0 : 1, dim: 0 });
    if (head) head.setOpacity(0);
    scene.applyCameraPreset(reducedMotion ? "profile" : "intro-start", 0);

    const enter = (b: Beat) => {
      setBeat(b);
      if (b === "assemble") {
        if (!reducedMotion) {
          scene.applyCameraPreset("profile", SEQUENCE_BEATS.watch - SEQUENCE_BEATS.assemble);
        }
      } else if (b === "watch") {
        clock.seek(0);
        clock.play();
      } else if (b === "lockOn") {
        clock.pause();
        if (strongestTime !== null && strongestRegion) {
          clock.seek(strongestTime);
          const label = labelOf(strongestRegion.name);
          locked = { hemi: strongestRegion.hemi, label };
          scene.setSelected(locked);
          propsRef.current.onLockOn?.(strongestRegion.hemi, strongestRegion.name, strongestTime);
          if (!reducedMotion) scene.focusRegion(strongestRegion.hemi, label, 1600);
        }
      } else if (b === "handOver") {
        if (!reducedMotion) scene.applyCameraPreset("profile", 1800);
      }
    };

    const frame = () => {
      const ms = performance.now() - start;
      const b = beatAt(ms);
      if (b !== lastBeat) {
        lastBeat = b;
        enter(b);
      }
      // Beat 1: dim to black (a stage layer beneath the canvas, so the brain stays visible).
      const dim = smooth(0, SEQUENCE_BEATS.assemble, ms) * (1 - smooth(SEQUENCE_BEATS.handOver + 1200, SEQUENCE_BEATS.end, ms));
      rootRef.current?.parentElement?.style.setProperty("--bv-dim", dim.toFixed(3));
      // Beat 2: head fades in, wireframe builds into the shaded mesh (fades when reduced).
      if (head) head.setOpacity(smooth(1500, 3000, ms));
      if (reducedMotion) {
        scene.setAssembly({ opacity: smooth(1500, 3500, ms) });
      } else {
        scene.setAssembly({
          wire: smooth(1500, 2300, ms) * (1 - smooth(3300, 4000, ms)) * 0.55,
          reveal: smooth(2100, 3900, ms),
        });
      }
      // Beat 3: HUD lines from meters to their anchor regions.
      for (const g of Object.keys(ANCHORS) as (keyof typeof ANCHORS)[]) {
        const line = lineRefs.current[g];
        const meter = meterRefs.current[g];
        if (!line || !meter) continue;
        const p = scene.projectRegion("right", labelOf(ANCHORS[g]));
        const host = scene.renderer.domElement.getBoundingClientRect();
        const m = meter.getBoundingClientRect();
        if (p) {
          line.setAttribute("x1", String(m.left - host.left));
          line.setAttribute("y1", String(m.top - host.top + m.height / 2));
          line.setAttribute("x2", String(p.x));
          line.setAttribute("y2", String(p.y));
        }
      }
      if (ms >= SEQUENCE_BEATS.handOver + 1000 && !handedOver.current) {
        handedOver.current = true;
        propsRef.current.onHandOver();
      }
      if (ms >= SEQUENCE_BEATS.end) {
        complete(false);
        return;
      }
      raf = requestAnimationFrame(frame);
    };

    let locked: { hemi: Hemisphere; label: number } | null = null;
    const complete = (skipped: boolean) => {
      cancelAnimationFrame(raf);
      rootRef.current?.parentElement?.style.removeProperty("--bv-dim");
      clock.pause();
      if (skipped) clock.seek(0);
      scene.setAssembly({ reveal: 1, wire: 0, opacity: 1, dim: 0 });
      if (head) head.setOpacity(1);
      scene.setInteractive(true);
      if (skipped) {
        scene.setSelected(null);
        scene.applyCameraPreset("profile", 0);
      }
      propsRef.current.onFinish(skipped, skipped ? null : locked);
    };
    skipRef.current = () => complete(true);
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
    // The sequence runs once per mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const t = clockState.time;
  const scene_ = sceneAt(scenes, t);
  const showMeters = hasData && (beat === "watch" || beat === "lockOn");
  const strongestInfo = strongestRegion ? regionInfo(strongestRegion.name) : undefined;
  const lockScene = strongestTime !== null ? sceneAt(scenes, strongestTime) : undefined;

  return (
    <div ref={rootRef} className={`bv-seq bv-seq-${beat}${reducedMotion ? " bv-seq-reduced" : ""}`} role="dialog" aria-modal="false" aria-label="Preflight sequence">
      <button type="button" className="bv-skip" onClick={() => skipRef.current()} autoFocus>
        Skip <span aria-hidden="true">→</span>
      </button>
      <p className="bv-seq-status bv-mono" aria-live="polite">
        {beat === "dim" || beat === "assemble" ? `Running simulated viewers · Variant ${variant}` : beat === "watch" ? `Brain sim · Variant ${variant} · ${formatTime(t)}` : beat === "lockOn" ? "Strongest predicted response" : "Opening results"}
        {mock && <span className="bv-chip bv-chip-mock">MOCK</span>}
        {precomputed && <span className="bv-chip">Precomputed</span>}
      </p>

      {!hasData && beat !== "dim" && (
        <p className="bv-seq-nodata">
          <strong>No brain data</strong>
          <span>Preview only. The response beats play when a genuine TRIBE result for this video is available.</span>
        </p>
      )}

      {showMeters && stats && times && (
        <>
          <svg className="bv-seq-lines" aria-hidden="true">
            {(Object.keys(ANCHORS) as GroupId[]).map((g) => (
              <line key={g} ref={(el) => { lineRefs.current[g] = el; }} stroke={GROUP_COLORS[g]} />
            ))}
          </svg>
          <div className="bv-seq-meters" aria-label="Live meters">
            {METER_GROUPS.map((g) => {
              const v = seriesAt(stats.groupMeans[g], times, t, props.hz);
              const w = Number.isFinite(v) && meterMax > 0 ? Math.max(0, Math.min(1, v / meterMax)) : 0;
              return (
                <div className="bv-meter" key={g} ref={(el) => { meterRefs.current[g] = el; }}>
                  <span><i style={{ background: GROUP_COLORS[g] }} aria-hidden="true" />{REGION_GROUPS[g].label}</span>
                  <b className="bv-mono">{Number.isFinite(v) ? v.toFixed(3) : "—"}</b>
                  <em><s style={{ width: `${w * 100}%`, background: GROUP_COLORS[g] }} /></em>
                </div>
              );
            })}
          </div>
        </>
      )}

      {beat === "watch" && scene_ && <p className="bv-seq-scene bv-mono">{formatTime(t)} · {scene_.text}</p>}

      {beat === "lockOn" && (
        <aside className="bv-seq-card" aria-live="polite">
          {strongestInfo && strongestTime !== null ? (
            <>
              <span className="bv-eyebrow">{REGION_GROUPS[strongestInfo.group].label} · {strongestRegion?.hemi === "left" ? "Left" : "Right"} hemisphere</span>
              <h2>{strongestInfo.name}</h2>
              <p>{strongestInfo.knownFor}</p>
              <p className="bv-mono">{formatTime(strongestTime)} · {lockScene ? lockScene.text : "No scene data at this time"}</p>
            </>
          ) : (
            <>
              <span className="bv-eyebrow">Lock on</span>
              <h2>No brain data</h2>
              <p>There is no genuine response to lock on to. Nothing is generated in its place.</p>
            </>
          )}
        </aside>
      )}
    </div>
  );
}
