"use client";

import { REGION_GROUPS, regionInfo, regionKey, regionSeries, type RegionStatistics } from "../../lib/brain/atlas";
import type { Hemisphere, SceneRef } from "../../lib/brain/contract";
import { formatTime, sampleAt, sceneAt, seriesAt } from "../../lib/brain/timeline";

interface RegionCardProps {
  selection: { hemi: Hemisphere; atlasName: string } | null;
  time: number;
  stats: RegionStatistics | null;
  times: Float64Array | null;
  units: string;
  scenes?: SceneRef[];
  noDataLabel: string;
  onClear: () => void;
}

export function RegionCard({ selection, time, stats, times, units, scenes, noDataLabel, onClear }: RegionCardProps) {
  const scene = sceneAt(scenes, time);
  if (!selection) {
    return (
      <section className="bv-card bv-region-card" aria-label="Region information">
        <span className="bv-eyebrow">Region</span>
        <h2>Select a region</h2>
        <p className="bv-muted">Click the cortex to identify an atlas region and see what it is known for, at the current video time.</p>
        <dl className="bv-facts">
          <div><dt>Time</dt><dd className="bv-mono">{formatTime(time)}</dd></div>
          <div><dt>On screen</dt><dd>{scene ? scene.text : scenes ? "No scene at this time" : "No scene data for this variant"}</dd></div>
        </dl>
      </section>
    );
  }
  const info = regionInfo(selection.atlasName);
  const key = regionKey(selection.hemi, selection.atlasName);
  const series = stats ? regionSeries(stats, key) : undefined;
  const value = series && times ? seriesAt(series, times, time) : Number.NaN;
  const nearest = times ? sampleAt(times, time) : null;
  const hemiLabel = selection.hemi === "left" ? "Left hemisphere" : "Right hemisphere";

  let spark: string | null = null;
  let playheadX = 0;
  if (series && times && times.length > 1) {
    let min = Infinity;
    let max = -Infinity;
    for (const v of series) {
      min = Math.min(min, v);
      max = Math.max(max, v);
    }
    const span = max - min || 1;
    const t0 = times[0];
    const t1 = times[times.length - 1];
    spark = Array.from(series)
      .map((v, i) => `${i ? "L" : "M"}${(((times[i] - t0) / (t1 - t0)) * 200).toFixed(1)},${(4 + (1 - (v - min) / span) * 32).toFixed(1)}`)
      .join("");
    playheadX = Math.min(200, Math.max(0, ((time - t0) / (t1 - t0)) * 200));
  }

  return (
    <section className="bv-card bv-region-card" aria-label="Region information" aria-live="polite">
      <div className="bv-card-head">
        <span className="bv-eyebrow">{info ? REGION_GROUPS[info.group].label : "Unlabelled"} · {hemiLabel}</span>
        <button type="button" className="bv-text-button" onClick={onClear} aria-label="Clear region selection">Clear</button>
      </div>
      <h2>{info ? info.name : "Medial wall (no atlas region)"}</h2>
      <p className="bv-known">{info ? info.knownFor : "Vertices on the medial wall are not assigned a cortical region by the atlas."}</p>
      <dl className="bv-facts">
        <div><dt>Time</dt><dd className="bv-mono">{formatTime(time)}{nearest?.inRange && times ? <span className="bv-dim"> · sample {times[nearest.nearestIndex].toFixed(1)} s</span> : null}</dd></div>
        <div><dt>On screen</dt><dd>{scene ? scene.text : scenes ? "No scene at this time" : "No scene data for this variant"}</dd></div>
        <div>
          <dt>Region mean</dt>
          <dd className="bv-mono">{stats ? (Number.isFinite(value) ? `${value.toFixed(3)} ${units}` : "No sample at this time") : noDataLabel}</dd>
        </div>
      </dl>
      {spark && (
        <svg className="bv-spark" viewBox="0 0 200 40" preserveAspectRatio="none" aria-label={`Region mean over time for ${info?.name ?? "region"}`}>
          <path d={spark} vectorEffect="non-scaling-stroke" />
          <line x1={playheadX} x2={playheadX} y1="0" y2="40" vectorEffect="non-scaling-stroke" />
        </svg>
      )}
      <p className="bv-footnote">Desikan-Killiany atlas (FreeSurfer aparc) on fsaverage5. Describes what the region is commonly studied for, not what a viewer feels or wants.</p>
    </section>
  );
}
