"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore, type ChangeEvent } from "react";
import type * as THREE from "three";
import { adaptSimulationResult, computeDisplayScale, resolveCorticalValues } from "../../lib/brain/adapter";
import { METER_GROUPS, REGION_GROUPS, computeRegionStatistics, type RegionStatistics } from "../../lib/brain/atlas";
import { loadBrainAssets, type BrainAssets } from "../../lib/brain/assets";
import { PlaybackClock } from "../../lib/brain/clock";
import type { CorticalBinding, Hemisphere, SceneRef, SimulationResult, SurfaceKind, VariantId } from "../../lib/brain/contract";
import { getBrainGeometry, type BrainGeometry } from "../../lib/brain/geometry";
import { loadHeadGeometry, type HeadObject } from "../../lib/brain/head";
import type { BrainScene, PickResult } from "../../lib/brain/scene";
import { formatTime, samplePeriod, seriesAt, stepSeconds } from "../../lib/brain/timeline";
import { BrainStage } from "./BrainStage";
import { PreflightSequence } from "./PreflightSequence";
import { RegionCard } from "./RegionCard";
import { Segmented } from "./Segmented";
import { GROUP_COLORS, Timeline, type CurveData } from "./Timeline";

const VARIANTS: VariantId[] = ["A", "B", "C"];
const DEFAULT_DURATION_S = 15;

type DataOrigin = "file" | "url" | "mock";

interface VariantData {
  binding?: CorticalBinding;
  origin?: DataOrigin;
  scenes?: SceneRef[];
  videoUrl?: string;
  videoName?: string;
}

const statsCache = new WeakMap<CorticalBinding, RegionStatistics>();
function statsFor(binding: CorticalBinding, assets: BrainAssets): RegionStatistics {
  let s = statsCache.get(binding);
  if (!s) {
    s = computeRegionStatistics(binding, assets.atlas);
    statsCache.set(binding, s);
  }
  return s;
}

function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    () => false,
  );
}

function isConcept(value: unknown): value is { variant_id: string; scenes: SceneRef[] } {
  const v = value as { variant_id?: unknown; scenes?: unknown; hook?: unknown };
  return Boolean(v && typeof v === "object" && typeof v.variant_id === "string" && Array.isArray(v.scenes));
}

function isSimulationResult(value: unknown): value is SimulationResult {
  const v = value as { simulator?: unknown; variant_id?: unknown };
  return Boolean(v && typeof v === "object" && typeof v.simulator === "string" && v.variant_id !== undefined);
}

export interface BrainExperienceProps {
  /** Orchestrator state for this run; "off" renders the PRD fallback label. */
  brainSim?: "available" | "off";
}

export function BrainExperience({ brainSim: brainSimProp = "available" }: BrainExperienceProps) {
  const [assets, setAssets] = useState<BrainAssets | null>(null);
  const [geometry, setGeometry] = useState<BrainGeometry | null>(null);
  const [headGeometry, setHeadGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [data, setData] = useState<Partial<Record<VariantId, VariantData>>>({});
  const [notices, setNotices] = useState<string[]>([]);
  const [variant, setVariant] = useState<VariantId>("A");
  const [surface, setSurface] = useState<SurfaceKind>("pial");
  const [open, setOpen] = useState(false);
  const [pick, setPick] = useState<PickResult | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [sequence, setSequence] = useState<"idle" | "running" | "handover">("idle");
  const [brainSim, setBrainSim] = useState(brainSimProp);
  const [scene, setScene] = useState<BrainScene | null>(null);
  const [head, setHead] = useState<HeadObject | null>(null);
  const [handoverAnim, setHandoverAnim] = useState(false);
  const reducedMotion = usePrefersReducedMotion();
  const workspaceRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const autoSequenceKey = useRef<string | null>(null);
  const clock = useMemo(() => new PlaybackClock(DEFAULT_DURATION_S), []);
  const clockState = useSyncExternalStore(clock.subscribe, clock.getSnapshot, clock.getSnapshot);

  // ---------------------------------------------------------------- assets
  useEffect(() => {
    let cancelled = false;
    loadBrainAssets()
      .then((a) => {
        if (cancelled) return;
        const g = getBrainGeometry(a);
        setAssets(a);
        setGeometry(g);
        loadHeadGeometry(g.center)
          .then((h) => !cancelled && setHeadGeometry(h))
          .catch(() => setNotices((n) => [...n, "Head silhouette failed to load; the brain is unaffected."]));
      })
      .catch((e: Error) => !cancelled && setLoadError(e.message));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => () => clock.dispose(), [clock]);

  // ------------------------------------------------------------- ingestion
  const ingest = useCallback(
    async (items: unknown[], origin: DataOrigin) => {
      const messages: string[] = [];
      const updates: Partial<Record<VariantId, VariantData>> = {};
      for (const item of items) {
        if (isConcept(item)) {
          const id = item.variant_id as VariantId;
          if (!VARIANTS.includes(id)) {
            messages.push(`Concept for unknown variant ${item.variant_id} ignored.`);
            continue;
          }
          updates[id] = { ...updates[id], scenes: item.scenes.map((s) => ({ t_start: s.t_start, t_end: s.t_end, text: s.text })) };
          continue;
        }
        if (!isSimulationResult(item)) {
          messages.push("A file was neither a SimulationResult nor a CreativeConcept.");
          continue;
        }
        let fetched: Float32Array | undefined;
        try {
          fetched = await resolveCorticalValues(item);
        } catch (e) {
          messages.push(`Variant ${String(item.variant_id)}: ${(e as Error).message}`);
          continue;
        }
        const result = adaptSimulationResult(item, fetched);
        if (!result.ok) {
          messages.push(`Variant ${String(item.variant_id)} (${item.simulator}): ${result.reason}.`);
          continue;
        }
        const id = result.binding.variantId as VariantId;
        if (!VARIANTS.includes(id)) {
          messages.push(`Result for unknown variant ${id} ignored.`);
          continue;
        }
        if (result.binding.mock && origin !== "mock") {
          messages.push(`Variant ${id}: result is flagged as a test MOCK and is shown with a MOCK banner.`);
        }
        updates[id] = { ...updates[id], binding: result.binding, origin, videoUrl: updates[id]?.videoUrl ?? result.binding.video?.url };
      }
      setData((prev) => {
        const next = { ...prev };
        for (const id of Object.keys(updates) as VariantId[]) next[id] = { ...prev[id], ...updates[id] };
        return next;
      });
      if (messages.length) setNotices((n) => [...n, ...messages]);
      return updates;
    },
    [],
  );

  // URL parameters: ?result=/same-origin.json, ?sim=off, ?fixture=mock (development only).
  useEffect(() => {
    if (!assets) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("sim") === "off") setBrainSim("off");
    const resultUrl = params.get("result");
    if (resultUrl) {
      if (!resultUrl.startsWith("/") || resultUrl.startsWith("//")) {
        setNotices((n) => [...n, "Only same-origin result paths (starting with /) are accepted."]);
      } else {
        fetch(resultUrl)
          .then((r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          })
          .then((json) => ingest(Array.isArray(json) ? json : [json], "url"))
          .then((updates) => {
            const first = VARIANTS.find((v) => updates[v]?.binding);
            if (first) {
              setVariant(first);
              autoSequenceKey.current = `${resultUrl}:${updates[first]?.binding?.version}`;
            }
          })
          .catch((e: Error) => setNotices((n) => [...n, `Could not load ${resultUrl}: ${e.message}`]));
      }
    }
    if (params.get("fixture") === "mock") {
      if (process.env.NODE_ENV !== "production") {
        import("../../tests/brain/fixtures/mockCortical").then((m) => {
          const results = VARIANTS.map((v) => m.buildMockResult(v, assets.atlas, { left: assets.left.sulc, right: assets.right.sulc }));
          void ingest(results, "mock");
          setData((prev) => {
            const next = { ...prev };
            for (const v of VARIANTS) next[v] = { ...next[v], scenes: m.MOCK_SCENES[v] };
            return next;
          });
        });
      } else {
        setNotices((n) => [...n, "Test fixtures are not available in production builds."]);
      }
    }
  }, [assets, ingest]);

  const onFiles = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    const items: unknown[] = [];
    for (const f of files) {
      try {
        const json = JSON.parse(await f.text());
        items.push(...(Array.isArray(json) ? json : [json]));
      } catch {
        setNotices((n) => [...n, `${f.name} is not valid JSON.`]);
      }
    }
    await ingest(items, "file");
  };

  const onVideo = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const url = URL.createObjectURL(file);
    setData((prev) => {
      const old = prev[variant]?.videoUrl;
      if (old?.startsWith("blob:")) URL.revokeObjectURL(old);
      return { ...prev, [variant]: { ...prev[variant], videoUrl: url, videoName: file.name } };
    });
  };

  // ------------------------------------------------------------ derivations
  const current = data[variant];
  const binding = brainSim === "off" ? null : current?.binding ?? null;
  const allBindings = useMemo(() => VARIANTS.map((v) => data[v]?.binding).filter((b): b is CorticalBinding => Boolean(b)), [data]);
  const scale = useMemo(() => computeDisplayScale(allBindings), [allBindings]);
  const stats = binding && assets ? statsFor(binding, assets) : null;

  const curves: CurveData | null = useMemo(() => {
    if (!binding || !stats || !assets) return null;
    let yMin = 0;
    let yMax = 0;
    for (const b of allBindings) {
      const s = statsFor(b, assets);
      for (const g of METER_GROUPS) for (const v of s.groupMeans[g]) {
        yMin = Math.min(yMin, v);
        yMax = Math.max(yMax, v);
      }
    }
    return { stats, times: binding.times, yMin, yMax: yMax || 1, units: binding.units, mock: binding.mock };
  }, [binding, stats, assets, allBindings]);

  const mock = Boolean(binding?.mock);
  const precomputed = Boolean(binding?.precomputed);
  const statusLabel = brainSim === "off" ? "Brain sim off" : binding ? (mock ? "MOCK test fixture" : "Genuine TRIBE result") : "No brain data";

  // Duration: the video when attached, otherwise the predicted range, otherwise 15 s.
  useEffect(() => {
    if (current?.videoUrl) return; // set from video metadata by the clock
    if (binding) clock.setDuration(binding.times[binding.nTimesteps - 1] + samplePeriod(binding.times));
    else clock.setDuration(DEFAULT_DURATION_S);
  }, [binding, current?.videoUrl, clock]);

  useEffect(() => {
    clock.attachVideo(current?.videoUrl ? videoRef.current : null);
  }, [current?.videoUrl, clock]);

  // Selections are anatomical, so they persist across variants and surfaces.
  const selection = pick && assets ? { hemi: pick.hemi, atlasName: assets.atlas.names[pick.label] ?? "unknown" } : null;
  const selectedForScene = useMemo(() => (pick ? { hemi: pick.hemi as Hemisphere, label: pick.label } : null), [pick]);

  // ---------------------------------------------------------- fullscreen/keys
  const toggleFullscreen = useCallback(() => {
    const el = workspaceRef.current;
    if (!el) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else void el.requestFullscreen?.().catch(() => setNotices((n) => [...n, "Fullscreen was refused by the browser."]));
  }, []);

  useEffect(() => {
    const onChange = () => setFullscreen(document.fullscreenElement === workspaceRef.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement;
      const tag = target.tagName;
      const isRange = tag === "INPUT" && (target as HTMLInputElement).type === "range";
      if ((tag === "INPUT" && !isRange) || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable) return;
      if (sequence === "running") return;
      if (e.key === " " || e.code === "Space") {
        if (tag === "BUTTON") return;
        e.preventDefault();
        clock.toggle();
      } else if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        if (isRange) return;
        e.preventDefault();
        clock.seek(stepSeconds(clock.getSnapshot().time, e.key === "ArrowRight" ? 1 : -1, clock.getSnapshot().duration));
      } else if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        toggleFullscreen();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clock, toggleFullscreen, sequence]);

  // ------------------------------------------------------------- sequence
  const startSequence = useCallback(() => {
    if (!scene) return;
    setPick(null);
    setOpen(false);
    setSurface("pial");
    setSequence("running");
  }, [scene]);

  // Plays once per run when a genuine result arrives via ?result=.
  useEffect(() => {
    const key = autoSequenceKey.current;
    if (!key || !scene || !binding || binding.mock || sequence !== "idle") return;
    const storageKey = `preflight.sequence.played:${key}`;
    if (window.localStorage.getItem(storageKey)) return;
    window.localStorage.setItem(storageKey, new Date().toISOString());
    autoSequenceKey.current = null;
    startSequence();
  }, [scene, binding, sequence, startSequence]);

  const finishSequence = useCallback((_skipped: boolean, locked: { hemi: Hemisphere; label: number } | null) => {
    if (locked) setPick({ hemi: locked.hemi, label: locked.label, vertex: -1 });
    setSequence("idle");
    setHandoverAnim(true);
    window.setTimeout(() => setHandoverAnim(false), 700);
  }, []);

  // ------------------------------------------------------------------ render
  const meterMax = curves ? Math.max(curves.yMax, 1e-6) : 1;
  const variantStatus = (v: VariantId) => {
    const b = data[v]?.binding;
    if (brainSim === "off") return "Brain sim off";
    if (!b) return "No brain data";
    return b.mock ? "MOCK fixture" : b.precomputed ? "Precomputed result" : "Genuine result";
  };
  const emptyCopy = brainSim === "off" ? "Brain sim off · this run completed with the Gemini panel only" : "No brain data · curves appear only with genuine predictions";

  return (
    <div className={`bv-page${sequence === "running" ? " bv-seq-running" : ""}${sequence === "handover" || handoverAnim ? " bv-seq-handover" : ""}`}>
      <header className="bv-topbar">
        <div className="bv-crumbs">
          <a href="/" className="bv-brand"><span className="brand-mark" aria-hidden="true" />Preflight</a>
          <span className="bv-sep">/</span>
          <strong>Brain viewer</strong>
          <span className={`bv-chip ${mock ? "bv-chip-mock" : binding ? "bv-chip-live" : ""}`}>{statusLabel}</span>
          {precomputed && <span className="bv-chip">Precomputed</span>}
        </div>
        <div className="bv-topbar-actions">
          <button type="button" className="bv-button" onClick={startSequence} disabled={!scene || sequence !== "idle"}>
            {binding ? "Play Preflight sequence" : "Preview sequence"}
          </button>
          <a className="bv-button bv-button-quiet" href="/">Dashboard</a>
        </div>
      </header>

      <div className="bv-layout">
        <aside className="bv-side bv-side-left" aria-label="Variants and recommendation">
          <section className="bv-card bv-reco">
            <span className="bv-eyebrow">Recommendation</span>
            <h2>No ranking yet</h2>
            <p className="bv-muted">The verdict (launch one, A/B test it against the runner up) appears here once scoring runs. Brain activity alone is not a ranking.</p>
          </section>
          <section className="bv-card">
            <span className="bv-eyebrow">Variants</span>
            <ul className="bv-variant-list">
              {VARIANTS.map((v) => (
                <li key={v}>
                  <button type="button" className={v === variant ? "bv-variant-active" : undefined} onClick={() => setVariant(v)} aria-pressed={v === variant}>
                    <strong>{v}</strong>
                    <span>{variantStatus(v)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
          <section className="bv-card">
            <span className="bv-eyebrow">Data</span>
            <p className="bv-muted">Bind a stored SimulationResult (tribe_v2 with meta.cortical) or CreativeConcept JSON. Files stay in this browser; nothing is uploaded or inferred.</p>
            <label className="bv-file">
              <input type="file" accept="application/json,.json" multiple onChange={onFiles} />
              Load result / concept JSON
            </label>
            <label className="bv-file">
              <input type="file" accept="video/mp4,video/*" onChange={onVideo} />
              Attach analyzed video to {variant}
            </label>
            {current?.videoName && <p className="bv-footnote">Video: {current.videoName}</p>}
            {notices.length > 0 && (
              <ul className="bv-notices" aria-live="polite">
                {notices.slice(-4).map((n, i) => (
                  <li key={`${i}-${n}`}>{n}</li>
                ))}
              </ul>
            )}
          </section>
        </aside>

        <div className={`bv-workspace${fullscreen ? " bv-fullscreen" : ""}`} ref={workspaceRef}>
          <div className="bv-stage">
            {mock && (
              <div className="bv-mock-banner" role="status">
                <strong>MOCK</strong> Synthetic test fixture · not a simulation result · do not use as evidence
              </div>
            )}
            <div className="bv-hud" aria-hidden="true"><i /><i /><i /><i /></div>
            {loadError && <p className="bv-stage-error">Brain mesh failed to load: {loadError}</p>}
            {!geometry && !loadError && <p className="bv-stage-loading bv-mono">Loading fsaverage5 cortex…</p>}
            {geometry && (
              <BrainStage
                geometry={geometry}
                headGeometry={headGeometry}
                clock={clock}
                binding={binding}
                scale={scale}
                surface={surface}
                open={open}
                selected={selectedForScene}
                reducedMotion={reducedMotion}
                onPick={setPick}
                onReady={setScene}
                onHead={setHead}
                label={`Interactive 3D cortex, variant ${variant}, ${statusLabel}. Drag to orbit, scroll to zoom, double-click to reset.`}
              />
            )}

            <figure className={`bv-video${current?.videoUrl ? "" : " bv-video-empty"}`}>
              {current?.videoUrl ? (
                <video ref={videoRef} src={current.videoUrl} playsInline preload="auto" aria-label={`Variant ${variant} video`} />
              ) : (
                <div className="bv-video-placeholder">
                  <span className="bv-mono">Variant {variant}</span>
                  <strong>{mock ? "MOCK · no video" : "No variant video"}</strong>
                  {current?.scenes && <em>{current.scenes.find((s) => clockState.time >= s.t_start && clockState.time < s.t_end)?.text}</em>}
                </div>
              )}
              <figcaption className="bv-mono">{formatTime(clockState.time)}</figcaption>
            </figure>

            {binding && curves && sequence === "idle" && (
              <div className="bv-meters" aria-label="Group meters at the current time">
                {METER_GROUPS.map((g) => {
                  const v = seriesAt(curves.stats.groupMeans[g], curves.times, clockState.time);
                  const w = Number.isFinite(v) ? Math.max(0, Math.min(1, v / meterMax)) : 0;
                  return (
                    <div className="bv-meter" key={g}>
                      <span><i style={{ background: GROUP_COLORS[g] }} aria-hidden="true" />{REGION_GROUPS[g].label}</span>
                      <b className="bv-mono">{Number.isFinite(v) ? v.toFixed(3) : "—"}</b>
                      <em><s style={{ width: `${w * 100}%`, background: GROUP_COLORS[g] }} /></em>
                    </div>
                  );
                })}
              </div>
            )}

            {!binding && sequence === "idle" && (
              <div className="bv-empty" role="status">
                <strong>{brainSim === "off" ? "Brain sim off" : "No brain data"}</strong>
                <span>
                  {brainSim === "off"
                    ? "TRIBE was unavailable for this run. Results use the Gemini viewer panel only; no brain activity is shown."
                    : `Variant ${variant} has no genuine TRIBE prediction bound. The anatomy is interactive; activity appears only from real results.`}
                </span>
              </div>
            )}

            <div className="bv-legend" aria-label="Activity legend">
              {binding && scale ? (
                <>
                  <span className="bv-eyebrow">Predicted cortical response</span>
                  <div className="bv-heatbar" aria-hidden="true" />
                  <div className="bv-heat-ticks bv-mono">
                    <span>{scale.threshold.toFixed(3)}</span>
                    <span>{scale.vmax.toFixed(3)}+</span>
                  </div>
                  <span className="bv-footnote" title={scale.rule}>{binding.units} · gray below threshold · shared A/B/C scale</span>
                </>
              ) : (
                <>
                  <span className="bv-eyebrow">Activity scale</span>
                  <span className="bv-legend-empty">{brainSim === "off" ? "Brain sim off" : "No brain data"}</span>
                </>
              )}
            </div>

            <div className="bv-stage-tools">
              <button type="button" className="bv-icon-button" onClick={() => scene?.resetCamera()} title="Reset camera (double-click the brain)">Reset view</button>
              <button type="button" className="bv-icon-button" onClick={toggleFullscreen} title="Fullscreen (F)" aria-pressed={fullscreen}>
                {fullscreen ? "Exit fullscreen" : "Fullscreen"}
              </button>
            </div>

            <div className="bv-controls" role="toolbar" aria-label="Brain view controls">
              <Segmented label="Variant" value={variant} onChange={setVariant} options={VARIANTS.map((v) => ({ value: v, label: v, hint: variantStatus(v) }))} />
              <Segmented label="Surface" value={surface} onChange={setSurface} options={[{ value: "pial", label: "Normal" }, { value: "inflated", label: "Inflated" }]} />
              <Segmented label="View" value={open ? "open" : "closed"} onChange={(v) => setOpen(v === "open")} options={[{ value: "closed", label: "Closed" }, { value: "open", label: "Open" }]} />
            </div>

            {sequence !== "idle" && scene && (
              <PreflightSequence
                scene={scene}
                head={head}
                clock={clock}
                variant={variant}
                stats={stats}
                times={binding?.times ?? null}
                scenes={current?.scenes}
                atlasNames={assets?.atlas.names ?? []}
                meterMax={meterMax}
                reducedMotion={reducedMotion}
                mock={mock}
                precomputed={precomputed}
                onHandOver={() => setSequence("handover")}
                onFinish={finishSequence}
              />
            )}
          </div>

          <Timeline
            time={clockState.time}
            duration={clockState.duration}
            playing={clockState.playing}
            onSeek={(t) => clock.seek(t)}
            onToggle={() => clock.toggle()}
            curves={curves}
            scenes={current?.scenes}
            emptyLabel={emptyCopy}
          />

          <aside className="bv-side bv-side-right" aria-label="Region details">
            <RegionCard
              selection={selection}
              time={clockState.time}
              stats={stats}
              times={binding?.times ?? null}
              units={binding?.units ?? ""}
              scenes={current?.scenes}
              noDataLabel={brainSim === "off" ? "Brain sim off" : "No brain data"}
              onClear={() => setPick(null)}
            />
            <section className="bv-card bv-about">
              <span className="bv-eyebrow">About this view</span>
              <p>
                Predicted cortical (fMRI-like) response for an average viewer from TRIBE v2, sampled about once per second and interpolated for display. It is
                not measured EEG and does not read emotions, desire or buying intent.
              </p>
              <p className="bv-footnote">
                Mesh: FreeSurfer fsaverage5 (normal and inflated). Scale: {scale ? scale.rule : "none until data is bound"}. Keys: space play/pause, ←/→ one second, F fullscreen, double-click reset.
              </p>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
