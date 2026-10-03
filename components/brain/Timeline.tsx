"use client";

import { useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { METER_GROUPS, REGION_GROUPS, type GroupId, type RegionStatistics } from "../../lib/brain/atlas";
import type { SceneRef } from "../../lib/brain/contract";
import { formatTime, sceneAt, seriesAt } from "../../lib/brain/timeline";

/** Validated categorical slots (dataviz reference palette, dark, all-pairs pass on #111). */
export const GROUP_COLORS: Record<GroupId, string> = {
  visual: "#3987e5",
  auditory: "#d95926",
  language: "#199e70",
  somatomotor: "#888",
  parietal: "#888",
  frontal: "#888",
  medial_temporal: "#888",
  cingulate_insula: "#888",
};

export interface CurveData {
  stats: RegionStatistics;
  times: Float64Array;
  /** Shared y-range across every variant shown (consistent scale). */
  yMin: number;
  yMax: number;
  units: string;
  /** Test fixture: never describe its samples as genuine. */
  mock: boolean;
}

interface TimelineProps {
  time: number;
  duration: number;
  playing: boolean;
  onSeek: (t: number) => void;
  onToggle: () => void;
  curves: CurveData | null;
  scenes?: SceneRef[];
  emptyLabel: string;
}

const H = 88;

export function Timeline({ time, duration, playing, onSeek, onToggle, curves, scenes, emptyLabel }: TimelineProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [hoverT, setHoverT] = useState<number | null>(null);
  const safeDuration = Math.max(duration, 0.001);
  const x = (t: number) => (t / safeDuration) * 1000;
  const y = (v: number) => {
    if (!curves) return H / 2;
    const span = curves.yMax - curves.yMin || 1;
    return 8 + (1 - (v - curves.yMin) / span) * (H - 16);
  };

  const paths = useMemo(() => {
    if (!curves) return [];
    return METER_GROUPS.map((g) => {
      const series = curves.stats.groupMeans[g];
      let d = "";
      for (let i = 0; i < curves.times.length; i++) {
        const t = curves.times[i];
        if (t < 0 || t > safeDuration) continue;
        d += `${d ? "L" : "M"}${x(t).toFixed(2)},${y(series[i]).toFixed(2)}`;
      }
      return { g, d, end: series[curves.times.length - 1], labelY: y(series[curves.times.length - 1]) };
    }).sort((a, b) => a.labelY - b.labelY).map((p, i, arr) => {
      // Keep direct labels at least 13px apart.
      if (i > 0) p.labelY = Math.max(p.labelY, arr[i - 1].labelY + 13);
      return p;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curves, safeDuration]);

  const handleHover = (e: ReactPointerEvent) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHoverT(Math.min(safeDuration, Math.max(0, ((e.clientX - rect.left) / rect.width) * safeDuration)));
  };

  const readoutT = hoverT ?? time;
  const values = curves ? METER_GROUPS.map((g) => ({ g, v: seriesAt(curves.stats.groupMeans[g], curves.times, readoutT) })) : [];
  const currentScene = sceneAt(scenes, time);

  return (
    <section className="bv-timeline" aria-label="Playback timeline">
      <div className="bv-timeline-bar">
        <button type="button" className="bv-play" onClick={onToggle} aria-label={playing ? "Pause (space)" : "Play (space)"}>
          {playing ? (
            <svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3.5" y="3" width="3" height="10" rx="1" /><rect x="9.5" y="3" width="3" height="10" rx="1" /></svg>
          ) : (
            <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 2.8v10.4L13 8z" /></svg>
          )}
        </button>
        <span className="bv-mono bv-time" aria-live="off">
          {formatTime(time)} <span className="bv-dim">/ {formatTime(duration)}</span>
        </span>
        <span className="bv-mono bv-dim bv-scene-now">{currentScene ? currentScene.text : scenes ? "No scene at this time" : "No scene data"}</span>
        {curves && (
          <div className="bv-legend-inline" aria-label="Curve legend">
            {values.map(({ g, v }) => (
              <span key={g}>
                <i style={{ background: GROUP_COLORS[g] }} aria-hidden="true" />
                {REGION_GROUPS[g].label}
                <b className="bv-mono">{Number.isFinite(v) ? v.toFixed(3) : "—"}</b>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="bv-track" ref={wrapRef} onPointerMove={handleHover} onPointerLeave={() => setHoverT(null)}>
        {scenes && (
          <div className="bv-scenes" aria-hidden="true">
            {scenes.map((s) => (
              <span key={`${s.t_start}-${s.text}`} style={{ left: `${(s.t_start / safeDuration) * 100}%`, width: `${((s.t_end - s.t_start) / safeDuration) * 100}%` }}>
                {s.text}
              </span>
            ))}
          </div>
        )}
        <svg className="bv-curves" viewBox={`0 0 1000 ${H}`} preserveAspectRatio="none" aria-hidden="true">
          {curves && curves.yMin < 0 && curves.yMax > 0 && <line x1="0" x2="1000" y1={y(0)} y2={y(0)} className="bv-zero" vectorEffect="non-scaling-stroke" />}
          {paths.map((p) => (
            <path key={p.g} d={p.d} stroke={GROUP_COLORS[p.g]} className="bv-curve" vectorEffect="non-scaling-stroke" />
          ))}
          {curves &&
            Array.from(curves.times).map((t) => (t >= 0 && t <= safeDuration ? <line key={t} x1={x(t)} x2={x(t)} y1={H - 4} y2={H} className="bv-tick" vectorEffect="non-scaling-stroke" /> : null))}
          {hoverT !== null && <line x1={x(hoverT)} x2={x(hoverT)} y1="0" y2={H} className="bv-hoverline" vectorEffect="non-scaling-stroke" />}
          <line x1={x(time)} x2={x(time)} y1="0" y2={H} className="bv-playhead" vectorEffect="non-scaling-stroke" />
        </svg>
        {curves &&
          paths.map((p) => (
            <span key={p.g} className="bv-direct-label" style={{ top: `${(p.labelY / H) * 100}%`, color: "var(--bv-text-2)" }}>
              <i style={{ background: GROUP_COLORS[p.g] }} aria-hidden="true" />
              {REGION_GROUPS[p.g].label}
            </span>
          ))}
        {!curves && <p className="bv-track-empty">{emptyLabel}</p>}
        {hoverT !== null && curves && (
          <div className="bv-tooltip bv-mono" style={{ left: `${(hoverT / safeDuration) * 100}%` }} role="presentation">
            <strong>{formatTime(hoverT)}</strong>
            {values.map(({ g, v }) => (
              <span key={g}>
                <i style={{ background: GROUP_COLORS[g] }} />
                {REGION_GROUPS[g].label} {Number.isFinite(v) ? v.toFixed(3) : "no sample"}
              </span>
            ))}
          </div>
        )}
        <input
          className="bv-scrub"
          type="range"
          min={0}
          max={safeDuration}
          step={0.05}
          value={Math.min(time, safeDuration)}
          onChange={(e) => onSeek(Number(e.target.value))}
          aria-label="Scrub video time"
          aria-valuetext={formatTime(time)}
        />
      </div>
      <div className="bv-axis bv-mono bv-dim" aria-hidden="true">
        {Array.from({ length: Math.floor(safeDuration) + 1 }, (_, i) => i)
          .filter((i) => i % (safeDuration > 20 ? 5 : 1) === 0)
          .map((i) => (
            <span key={i} style={{ left: `${(i / safeDuration) * 100}%` }}>
              {i}s
            </span>
          ))}
      </div>
      {curves && (
        <details className="bv-table">
          <summary>Sample table ({curves.times.length} {curves.mock ? "MOCK fixture" : "genuine"} samples, {curves.units})</summary>
          <table>
            <thead>
              <tr>
                <th scope="col">Source time</th>
                {METER_GROUPS.map((g) => (
                  <th scope="col" key={g}>{REGION_GROUPS[g].label} mean</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from(curves.times).map((t, i) => (
                <tr key={t}>
                  <td>{t.toFixed(2)} s</td>
                  {METER_GROUPS.map((g) => (
                    <td key={g}>{curves.stats.groupMeans[g][i].toFixed(4)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </section>
  );
}
