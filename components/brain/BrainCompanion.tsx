"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore, type ChangeEvent } from "react";
import Link from "next/link";
import type * as THREE from "three";
import { adaptSimulationResult, computeDisplayScale, resolveCorticalValues } from "../../lib/brain/adapter";
import { METER_GROUPS, REGION_GROUPS, computeRegionStatistics, regionInfo, strongestMoment, type RegionStatistics } from "../../lib/brain/atlas";
import { loadBrainAssets, type BrainAssets } from "../../lib/brain/assets";
import { PlaybackClock } from "../../lib/brain/clock";
import type { CorticalBinding, Hemisphere, SceneRef, SimulationResult, SurfaceKind, VariantId } from "../../lib/brain/contract";
import { getBrainGeometry, type BrainGeometry } from "../../lib/brain/geometry";
import { loadHeadGeometry, type HeadObject } from "../../lib/brain/head";
import type { BrainScene, PickResult } from "../../lib/brain/scene";
import { formatTime, sampleAt, samplePeriod, seriesAt, stepSeconds } from "../../lib/brain/timeline";
import { ANALYSIS_RUN_KEY_PREFIX, BRAIN_COMMAND, ENTRY_SESSION_KEY, dispatchBrainEvent, type BrainCommand, type BrainEvent, type BrainMode, type DataMode, type RegionRef, type SelectionSnapshot } from "../../lib/brain/events";
import { useLatest } from "../../lib/brain/useLatest";
import { STEP_LABELS, statusLine, isWorking, RESULT_STEPS, type Milestone, type WorkloadState } from "../../lib/brain/workload";
import { BrainStage } from "./BrainStage";
import { useDockChoreography, type BeatRegion } from "./useDockChoreography";
import { EntrySequence } from "./EntrySequence";
import { PreflightSequence } from "./PreflightSequence";
import { RegionCard } from "./RegionCard";
import { Segmented } from "./Segmented";
import { GROUP_COLORS, Timeline, type CurveData } from "./Timeline";
import "./brain.css";

const VARIANTS: VariantId[] = ["A", "B", "C"];
const DEFAULT_DURATION_S = 15;

type DataOrigin = "file" | "url" | "mock" | "prop" | "backend";

interface VariantData {
  binding?: CorticalBinding;
  origin?: DataOrigin;
  scenes?: SceneRef[];
  videoUrl?: string;
  videoName?: string;
}

/** A genuine, precomputed example shown before the user's first run (PRD v1.4 §12.2). */
interface DemoExample {
  binding: CorticalBinding;
  title: string;
  videoUrl: string;
  scenes?: SceneRef[];
}

const DATA_LABELS: Record<DataMode, string> = {
  none: "No brain data",
  sim_off: "Brain sim off",
  demo_example: "Demo example · precomputed",
  genuine: "Genuine TRIBE result",
  genuine_precomputed: "Genuine TRIBE result · precomputed",
  mock: "MOCK test fixture",
};

const statsCache = new WeakMap<CorticalBinding, RegionStatistics>();
function statsFor(binding: CorticalBinding, assets: BrainAssets): RegionStatistics {
  let s = statsCache.get(binding);
  if (!s) {
    s = computeRegionStatistics(binding, assets.atlas);
    statsCache.set(binding, s);
  }
  return s;
}

function regionInfoName(atlasName: string): string {
  return regionInfo(atlasName)?.name ?? atlasName;
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

export interface BrainCompanionProps {
  /** Orchestrator state for this run; "off" renders the PRD fallback label. */
  brainSim?: "available" | "off";
  /** Stored results for the current run, straight from the backend (any simulator; non-cortical ones are ignored). */
  results?: SimulationResult[];
  /** CreativeConcepts for the run, used for "what is on screen" (variant_id + scenes). */
  concepts?: Array<{ variant_id: string; scenes: SceneRef[] }>;
  /** Analyzed video URL per variant (the exact bytes the result was computed from). */
  videos?: Partial<Record<VariantId, string>>;
  /** Project id echoed in selection events so the canvas/voice can map back to its nodes. */
  projectId?: string;
  /** Stable run id; the analysis sequence plays at most once per run id. */
  runId?: string;
  /** Genuine precomputed example for first arrival; must be precomputed and name its video. */
  demoExample?: SimulationResult;
  /** Controlled variant selection, e.g. from the selected canvas node. */
  selectedVariant?: VariantId;
  onSelectVariant?: (variant: VariantId) => void;
  /** Entry/analysis/selection/mode events for the canvas and voice owners. */
  onEvent?: (event: BrainEvent) => void;
  /** Initial presentation when the entry has already played this session. */
  initialMode?: Exclude<BrainMode, "entry">;
  /** Standalone /brain route: top bar, canvas placeholder, local loaders and URL parameters. */
  harness?: boolean;
  /** Pre-adapted genuine bindings per variant (e.g. from the backend adapter in lib/brain/backend.ts). */
  bindings?: Record<string, CorticalBinding>;
  /** Concept scenes per variant for "what is on screen" (backend results). */
  scenesByVariant?: Record<string, SceneRef[]>;
  /** Real backend workload, for choreography only (never cortical data). */
  workload?: WorkloadState;
  consumeMilestone?: (id: number) => void;
  /** Where the dock sits; the canvas uses top-left. */
  dockCorner?: "top-left" | "bottom-right";
  /** Play the once-per-session entry intro on this surface. */
  entry?: boolean;
  /** Extra honest notices from the host (e.g. backend artifact problems). */
  hostNotices?: string[];
}

export function BrainCompanion(props: BrainCompanionProps) {
  const { brainSim: brainSimProp = "available", projectId, results, concepts, videos, runId, demoExample, selectedVariant, onSelectVariant, onEvent, initialMode = "dock", harness = false, bindings, scenesByVariant, workload, consumeMilestone, dockCorner = "bottom-right", entry: entryEnabled = true, hostNotices } = props;
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
  const [mode, setMode] = useState<BrainMode>(initialMode);
  const [entry, setEntry] = useState<{ run: number; replay: boolean } | null>(null);
  const [demo, setDemo] = useState<DemoExample | null>(null);
  const [eventLog, setEventLog] = useState<BrainEvent[]>([]);
  const [runKey, setRunKey] = useState<string | null>(runId ?? null);
  const onEventRef = useLatest(onEvent);
  const entryChecked = useRef(false);
  const reducedMotion = usePrefersReducedMotion();
  const workspaceRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const clock = useMemo(() => new PlaybackClock(DEFAULT_DURATION_S), []);
  const clockState = useSyncExternalStore(clock.subscribe, clock.getSnapshot, clock.getSnapshot);

  const emit = useCallback(
    (event: BrainEvent) => {
      dispatchBrainEvent(event, onEventRef.current);
      if (harness) setEventLog((log) => [event, ...log].slice(0, 8));
    },
    [harness, onEventRef],
  );

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

  /** Accept only a genuine, precomputed result that names the video it analyzed. */
  const ingestDemo = useCallback(async (item: unknown) => {
    if (!isSimulationResult(item)) {
      setNotices((n) => [...n, "Demo example rejected: not a SimulationResult."]);
      return;
    }
    let fetched: Float32Array | undefined;
    try {
      fetched = await resolveCorticalValues(item);
    } catch (e) {
      setNotices((n) => [...n, `Demo example: ${(e as Error).message}`]);
      return;
    }
    const adapted = adaptSimulationResult(item, fetched);
    const meta = (item.meta?.demo_example ?? {}) as { title?: unknown; video_url?: unknown; scenes?: unknown };
    if (!adapted.ok) {
      setNotices((n) => [...n, `Demo example rejected: ${adapted.reason}.`]);
    } else if (adapted.binding.mock || !adapted.binding.precomputed || typeof meta.video_url !== "string") {
      setNotices((n) => [...n, "Demo example rejected: it must be a genuine precomputed result with meta.demo_example.video_url."]);
    } else {
      setDemo({
        binding: adapted.binding,
        title: typeof meta.title === "string" ? meta.title : "Example video",
        videoUrl: meta.video_url,
        scenes: Array.isArray(meta.scenes) ? (meta.scenes as SceneRef[]) : undefined,
      });
    }
  }, []);

  useEffect(() => {
    if (demoExample) void ingestDemo(demoExample);
  }, [demoExample, ingestDemo]);

  // URL parameters (harness only): ?result=, ?demo=, ?sim=off, ?entry=replay, ?fixture=mock (development only).
  useEffect(() => {
    if (!assets) return;
    if (!harness) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("sim") === "off") setBrainSim("off");
    const demoUrl = params.get("demo");
    if (demoUrl) {
      if (!demoUrl.startsWith("/") || demoUrl.startsWith("//")) setNotices((n) => [...n, "Only same-origin demo paths (starting with /) are accepted."]);
      else
        fetch(demoUrl)
          .then((r) => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
          })
          .then((json) => ingestDemo(json))
          .catch((e: Error) => setNotices((n) => [...n, `Could not load demo example ${demoUrl}: ${e.message}`]));
    }
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
              setRunKey((k) => k ?? `${resultUrl}:${updates[first]?.binding?.version}`);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assets, ingest]);

  // Backend-provided run data (embedded use).
  useEffect(() => {
    if (!assets) return;
    const items: unknown[] = [...(results ?? []), ...(concepts ?? [])];
    if (items.length) void ingest(items, "prop");
  }, [assets, results, concepts, ingest]);

  // Backend-adapted bindings (already validated against the worker artifact) and scenes.
  useEffect(() => {
    if (!bindings && !scenesByVariant) return;
    setData((prev) => {
      const next = { ...prev };
      for (const v of VARIANTS) {
        const b = bindings?.[v];
        const sc = scenesByVariant?.[v];
        if (b || sc) next[v] = { ...next[v], ...(b ? { binding: b, origin: "backend" as const } : {}), ...(sc ? { scenes: sc } : {}) };
      }
      return next;
    });
  }, [bindings, scenesByVariant]);

  useEffect(() => {
    if (!videos) return;
    setData((prev) => {
      const next = { ...prev };
      for (const v of Object.keys(videos) as VariantId[]) next[v] = { ...next[v], videoUrl: videos[v] };
      return next;
    });
  }, [videos]);

  useEffect(() => {
    if (runId) setRunKey(runId);
  }, [runId]);

  useEffect(() => {
    if (selectedVariant && VARIANTS.includes(selectedVariant)) setVariant(selectedVariant);
  }, [selectedVariant]);

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
  const runBindings = useMemo(() => VARIANTS.map((v) => data[v]?.binding).filter((b): b is CorticalBinding => Boolean(b)), [data]);
  // A disclosed demo example is shown only until the run has any cortical data of its own.
  const demoActive = Boolean(demo) && runBindings.length === 0;
  const runData = data[variant];
  const current: VariantData | undefined = demoActive && demo ? { binding: demo.binding, scenes: demo.scenes, videoUrl: demo.videoUrl } : runData;
  const binding = demoActive ? demo!.binding : brainSim === "off" ? null : runData?.binding ?? null;
  const allBindings = useMemo(() => (demoActive && demo ? [demo.binding] : runBindings), [demoActive, demo, runBindings]);
  const scale = useMemo(() => computeDisplayScale(allBindings), [allBindings]);
  const dataMode: DataMode = demoActive
    ? "demo_example"
    : binding
      ? binding.mock
        ? "mock"
        : binding.precomputed
          ? "genuine_precomputed"
          : "genuine"
      : brainSim === "off"
        ? "sim_off"
        : "none";
  const dataModeRef = useLatest<DataMode>(dataMode);
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
    return { stats, times: binding.times, hz: binding.hz, groupSource: stats.groupSource, yMin, yMax: yMax || 1, units: binding.units, mock: binding.mock };
  }, [binding, stats, assets, allBindings]);

  const mock = Boolean(binding?.mock);
  const precomputed = Boolean(binding?.precomputed);
  const statusLabel = DATA_LABELS[dataMode];

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
  const regionRef = (hemi: Hemisphere, atlasName: string): RegionRef => ({ hemi, atlasName, name: regionInfoName(atlasName) });
  useEffect(() => {
    if (entry || sequence !== "idle" || lastReported.current.pick === pick) return;
    lastReported.current.pick = pick;
    emit({ type: "region.selected", region: selection ? regionRef(selection.hemi, selection.atlasName) : null, time_s: clock.getSnapshot().time, dataMode });
    // Emit on selection changes only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pick]);
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
      if (sequence === "running" || entry) return;
      // Playback/fullscreen keys belong to the expanded analysis view only. In the dock they would
      // steal the host canvas's keys (e.g. space-drag pan); the focused dock has its own Enter/Space/Esc.
      if (mode !== "expanded") return;
      if (e.key === "Escape" && mode === "expanded" && !document.fullscreenElement) {
        setMode("dock");
        return;
      }
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
  }, [clock, toggleFullscreen, sequence, entry, mode]);

  // ---------------------------------------------------------------- entry
  const startEntry = useCallback(
    (replay: boolean) => {
      if (document.fullscreenElement) void document.exitFullscreen();
      setPick(null);
      setOpen(false);
      setSurface("pial");
      setMode("entry");
      setEntry((e) => ({ run: (e?.run ?? 0) + 1, replay }));
      emit({ type: "entry.started", replay, dataMode: dataModeRef.current });
    },
    [emit, dataModeRef],
  );

  // First arrival: once per browser session (FR-14); ?entry=replay forces it.
  // The hero frame shows immediately; the sequence itself starts once the mesh is ready.
  useEffect(() => {
    if (entryChecked.current) return;
    entryChecked.current = true;
    const params = new URLSearchParams(window.location.search);
    const forced = params.get("entry") === "replay";
    if (!entryEnabled || params.get("entry") === "off") return;
    if (forced || !window.sessionStorage.getItem(ENTRY_SESSION_KEY)) startEntry(forced);
  }, [entryEnabled, startEntry]);

  const finishEntry = useCallback(
    (skipped: boolean) => {
      window.sessionStorage.setItem(ENTRY_SESSION_KEY, new Date().toISOString());
      setEntry(null);
      setMode((m) => (m === "entry" ? "dock" : m));
      emit({ type: "entry.completed", skipped });
    },
    [emit],
  );

  // Expanding is a deliberate reveal: frame the reference profile instead of wherever the dock's
  // idle spin happened to stop (the scene itself skips the move under reduced motion).
  useEffect(() => {
    if (mode === "expanded") scene?.applyCameraPreset(open ? "open" : "profile", 700);
    // Only on entering the expanded view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, scene]);

  // Mode/variant/region events for the canvas and voice owners (changes only, not the initial state).
  const lastReported = useRef({ mode: initialMode as BrainMode, variant: "A" as VariantId, pick: null as PickResult | null });
  useEffect(() => {
    if (lastReported.current.mode === mode) return;
    lastReported.current.mode = mode;
    emit({ type: "mode.changed", mode });
  }, [mode, emit]);
  useEffect(() => {
    if (lastReported.current.variant === variant) return;
    lastReported.current.variant = variant;
    emit({ type: "variant.selected", variant, dataMode: dataModeRef.current });
  }, [variant, emit, dataModeRef]);

  // ------------------------------------------------------------- sequence
  const startSequence = useCallback(() => {
    if (!scene || entry) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    emit({ type: "analysis.started", runId: runKey ?? "preview", variant });
    setPick(null);
    setOpen(false);
    setSurface("pial");
    setSequence("running");
  }, [scene, entry, emit, runKey, variant]);

  // Analysis focus plays at most once per run, only for this run's genuine data.
  useEffect(() => {
    if (!runKey || !scene || entry || !binding || sequence !== "idle") return;
    if (dataMode !== "genuine" && dataMode !== "genuine_precomputed") return;
    const storageKey = `${ANALYSIS_RUN_KEY_PREFIX}${runKey}`;
    if (window.localStorage.getItem(storageKey)) return;
    window.localStorage.setItem(storageKey, new Date().toISOString());
    startSequence();
  }, [runKey, scene, entry, binding, dataMode, sequence, startSequence]);

  const finishSequence = useCallback((skipped: boolean, locked: { hemi: Hemisphere; label: number } | null) => {
    if (locked) setPick({ hemi: locked.hemi, label: locked.label, vertex: -1 });
    emit({ type: "analysis.completed", runId: runKey ?? "preview", variant, skipped });
    // Hand back to the canvas: the brain returns to its corner dock (PRD v1.4 §12.2 beat 5).
    setMode("dock");
    setSequence("idle");
    setHandoverAnim(true);
    window.setTimeout(() => setHandoverAnim(false), 700);
  }, [emit, runKey, variant]);

  const selectVariant = useCallback(
    (v: VariantId) => {
      setVariant(v);
      onSelectVariant?.(v);
    },
    [onSelectVariant],
  );

  // ---------------------------------------------------------- dock companion
  // Hover enlarges; click or Enter/Space pins; Esc unpins. Workload choreography is presentation
  // driven by real backend events and never writes cortical values or playback time.
  const [hovered, setHovered] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [motionPaused, setMotionPaused] = useState(false);
  const [manual, setManual] = useState(false);
  const pickRef = useLatest(pick);
  const resolveRegion = useCallback(
    (m: Milestone): BeatRegion | null => {
      if (!assets || !m.variantId || !RESULT_STEPS.includes(m.step) || brainSim === "off") return null;
      const vd = data[m.variantId as VariantId];
      const b = vd?.binding;
      if (!b) return null;
      const strongest = strongestMoment(statsFor(b, assets));
      if (!strongest) return null;
      const [hemi, atlasName] = strongest.key.split(":") as [Hemisphere, string];
      const info = regionInfo(atlasName);
      const label = assets.atlas.names.indexOf(atlasName);
      if (!info || label < 0) return null;
      const sampleTime = b.times[strongest.sampleIndex];
      const sc = vd?.scenes?.find((x) => sampleTime >= x.t_start && sampleTime < x.t_end);
      return {
        hemi,
        label,
        atlasName,
        name: info.name,
        knownFor: info.knownFor,
        group: REGION_GROUPS[info.group].label,
        sampleTime,
        sceneText: sc?.text ?? null,
        dataMode: b.mock ? "mock" : b.precomputed ? "genuine_precomputed" : "genuine",
      };
    },
    [assets, data, brainSim],
  );
  const beat = useDockChoreography({
    scene,
    active: mode === "dock" && !entry && sequence === "idle",
    workload,
    consumeMilestone,
    reducedMotion,
    motionPaused,
    manual,
    resolveRegion,
    dataVersion: data,
    restoreSelection: () => {
      const p = pickRef.current;
      scene?.setSelected(p ? { hemi: p.hemi, label: p.label } : null);
    },
    onBeat: (b) =>
      emit({
        type: "workload.focus",
        step: b.milestone.step,
        variant: b.milestone.variantId,
        message: b.milestone.message,
        region: b.region ? { hemi: b.region.hemi, atlasName: b.region.atlasName, name: b.region.name } : null,
        sample_time_s: b.region?.sampleTime ?? null,
        dataMode: b.region?.dataMode ?? null,
      }),
  });
  const dockLarge = mode === "dock" && (hovered || pinned || Boolean(beat));
  const working = workload ? isWorking(workload) : false;
  const onStagePick = useCallback(
    (p: PickResult | null) => {
      // In the dock, the first click pins it open; region picking starts once pinned.
      if (mode === "dock" && !pinned) {
        setPinned(true);
        return;
      }
      setPick(p);
    },
    [mode, pinned],
  );
  const onDockKey = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (mode !== "dock" || e.target !== e.currentTarget) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      setPinned((v) => !v);
    } else if (e.key === "Escape") {
      setPinned(false);
    }
  };

  // selection.changed: variant/region/mode/data changes, seeks and pauses — not every frame.
  const snapshotRef = useLatest((): SelectionSnapshot => {
    const t = clock.getSnapshot().time;
    const s = binding ? sampleAt(binding.times, t, binding.hz) : null;
    const scenes = current?.scenes;
    const idx = scenes ? scenes.findIndex((sc) => t >= sc.t_start && t < sc.t_end) : -1;
    return {
      projectId: projectId ?? null,
      runId: runKey,
      variant: demoActive ? "demo_example" : variant,
      time_s: Math.round(t * 1000) / 1000,
      sample_time_s: s?.inRange && binding ? binding.times[s.nearestIndex] : null,
      scene: scenes && idx >= 0 ? { index: idx, t_start: scenes[idx].t_start, t_end: scenes[idx].t_end, text: scenes[idx].text } : null,
      region: selection ? regionRef(selection.hemi, selection.atlasName) : null,
      dataMode,
      mode,
    };
  });
  const emitSelection = useCallback(() => emit({ type: "selection.changed", selection: snapshotRef.current() }), [emit, snapshotRef]);
  const selectionReady = useRef(false);
  useEffect(() => {
    if (!selectionReady.current) {
      selectionReady.current = true;
      return;
    }
    if (!entry && sequence === "idle") emitSelection();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [variant, pick, mode, dataMode]);
  useEffect(() => {
    let timer = 0;
    let wasPlaying = clock.getSnapshot().playing;
    let lastTime = clock.getSnapshot().time;
    return clock.subscribe(() => {
      const st = clock.getSnapshot();
      const paused = wasPlaying && !st.playing;
      const seeked = !st.playing && Math.abs(st.time - lastTime) > 1e-3;
      wasPlaying = st.playing;
      lastTime = st.time;
      if (paused || seeked) {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => emitSelection(), 200);
      }
    });
  }, [clock, emitSelection]);

  // Host commands (canvas, or the voice owner after a user-confirmed change).
  useEffect(() => {
    const onCommand = (e: Event) => {
      const cmd = (e as CustomEvent<BrainCommand>).detail;
      if (!cmd || typeof cmd !== "object") return;
      switch (cmd.type) {
        case "select_variant":
          if (VARIANTS.includes(cmd.variant as VariantId)) selectVariant(cmd.variant as VariantId);
          break;
        case "seek":
          if (Number.isFinite(cmd.time_s)) clock.seek(cmd.time_s);
          break;
        case "play":
          clock.play();
          break;
        case "pause":
          clock.pause();
          break;
        case "set_mode":
          if (!entry && (cmd.mode === "dock" || cmd.mode === "expanded")) setMode(cmd.mode);
          break;
        case "select_region": {
          const label = assets?.atlas.names.indexOf(cmd.atlasName) ?? -1;
          if (label >= 0 && (cmd.hemi === "left" || cmd.hemi === "right")) setPick({ hemi: cmd.hemi, label, vertex: -1 });
          break;
        }
        case "clear_region":
          setPick(null);
          break;
        case "replay_entry":
          if (!entry && sequence === "idle") startEntry(true);
          break;
      }
    };
    window.addEventListener(BRAIN_COMMAND, onCommand);
    return () => window.removeEventListener(BRAIN_COMMAND, onCommand);
  }, [selectVariant, clock, entry, sequence, assets, startEntry]);

  // ------------------------------------------------------------------ render
  const meterMax = curves ? Math.max(curves.yMax, 1e-6) : 1;
  const variantStatus = (v: VariantId) => {
    if (demoActive) return "Demo example shown";
    const b = data[v]?.binding;
    if (brainSim === "off") return "Brain sim off";
    if (!b) return "No brain data";
    return b.mock ? "MOCK fixture" : b.precomputed ? "Precomputed result" : "Genuine result";
  };
  const allNotices = hostNotices?.length ? [...notices, ...hostNotices] : notices;
  const emptyCopy = brainSim === "off" ? "Brain sim off · this run completed with the Gemini panel only" : "No brain data · curves appear only with genuine predictions";
  const sample = binding ? sampleAt(binding.times, clockState.time, binding.hz) : null;
  const viewLabel = demoActive && demo ? `Demo example · ${demo.title}` : `Variant ${variant}`;
  const chipClass = mock ? "bv-chip-mock" : dataMode === "demo_example" ? "bv-chip-demo" : binding ? "bv-chip-live" : "";
  const pageClass = [
    "bv-page",
    `bv-mode-${mode}`,
    harness ? "bv-harness" : "bv-embedded",
    `bv-dock-${dockCorner}`,
    dockLarge ? "bv-dock-large" : "",
    pinned && mode === "dock" ? "bv-dock-pinned" : "",
    working && mode === "dock" ? "bv-dock-working" : "",
    beat ? "bv-dock-focus" : "",
    sequence === "running" ? "bv-seq-running" : "",
    sequence === "handover" || handoverAnim ? "bv-seq-handover" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={pageClass}>
      {harness && (
        <header className="bv-topbar">
          <div className="bv-crumbs">
            <Link href="/" className="bv-brand"><span className="bv-brand-mark" aria-hidden="true" />Preflight</Link>
            <span className="bv-sep">/</span>
            <strong>Brain companion</strong>
            <span className={`bv-chip ${chipClass}`}>{statusLabel}</span>
            {precomputed && dataMode !== "demo_example" && <span className="bv-chip">Precomputed</span>}
            {demoActive && brainSim === "off" && <span className="bv-chip">Brain sim off</span>}
          </div>
          <div className="bv-topbar-actions">
            <button type="button" className="bv-button bv-button-quiet" onClick={() => startEntry(true)} disabled={!scene || Boolean(entry) || sequence !== "idle"}>
              Replay intro
            </button>
            <button type="button" className="bv-button bv-button-quiet" onClick={startSequence} disabled={!scene || Boolean(entry) || sequence !== "idle"}>
              {binding ? "Play analysis focus" : "Preview analysis focus"}
            </button>
            {mode === "expanded" ? (
              <button type="button" className="bv-button" onClick={() => setMode("dock")}>Dock brain</button>
            ) : (
              <button type="button" className="bv-button" onClick={() => setMode("expanded")} disabled={Boolean(entry)}>Expand brain</button>
            )}
          </div>
        </header>
      )}

      {harness && mode !== "expanded" && (
        <section className="bv-canvas-slot" aria-label="Flow canvas slot">
          <div className="bv-canvas-note">
            <span className="bv-eyebrow">Flow canvas slot</span>
            <h2>The canvas lives on the Dashboard branch</h2>
            <p>
              This route hosts only the reusable brain companion and its integration seam. Selecting a variant node on the canvas maps to <code>selectedVariant</code>; the
              brain reports entry, analysis, mode, variant and region events for the canvas and the voice owner.
            </p>
            <div className="bv-harness-row" role="group" aria-label="Simulate canvas node selection">
              {VARIANTS.map((v) => (
                <button key={v} type="button" className={`bv-icon-button${v === variant ? " bv-harness-active" : ""}`} onClick={() => selectVariant(v)}>
                  Select variant {v}
                </button>
              ))}
            </div>
            {allNotices.length > 0 && (
              <ul className="bv-notices" aria-live="polite">
                {allNotices.slice(-3).map((n, i) => (
                  <li key={`${i}-${n}`}>{n}</li>
                ))}
              </ul>
            )}
            <span className="bv-eyebrow">Emitted events (window &quot;preflight:brain&quot; and onEvent)</span>
            <ol className="bv-event-log bv-mono" aria-live="polite">
              {eventLog.length === 0 && <li className="bv-dim">No events yet</li>}
              {eventLog.map((e, i) => (
                <li key={`${i}-${e.type}`}>{JSON.stringify(e)}</li>
              ))}
            </ol>
          </div>
        </section>
      )}

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
                  <button type="button" className={v === variant ? "bv-variant-active" : undefined} onClick={() => selectVariant(v)} aria-pressed={v === variant}>
                    <strong>{v}</strong>
                    <span>{variantStatus(v)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
          {harness && (
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
              {runData?.videoName && <p className="bv-footnote">Video: {runData.videoName}</p>}
            </section>
          )}
          {allNotices.length > 0 && (
            <ul className="bv-notices" aria-live="polite">
              {allNotices.slice(-4).map((n, i) => (
                <li key={`${i}-${n}`}>{n}</li>
              ))}
            </ul>
          )}
        </aside>

        <div className={`bv-workspace${fullscreen ? " bv-fullscreen" : ""}`} ref={workspaceRef}>
          <div
            className="bv-stage"
            onMouseEnter={() => mode === "dock" && setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onKeyDown={onDockKey}
            tabIndex={mode === "dock" ? 0 : -1}
            role={mode === "dock" ? "group" : undefined}
            aria-label={mode === "dock" ? `Brain companion, ${viewLabel}, ${statusLabel}. Enter pins it open, Escape unpins.` : undefined}
          >
            {mock && (
              <div className="bv-mock-banner" role="status">
                <strong>MOCK</strong> Synthetic test fixture · not a simulation result · do not use as evidence
              </div>
            )}
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
                onPick={onStagePick}
                onReady={setScene}
                onHead={setHead}
                onUserInteract={() => mode === "dock" && setManual(true)}
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
                  const v = seriesAt(curves.stats.groupMeans[g], curves.times, clockState.time, curves.hz);
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

            {binding && scale && (
              <div className="bv-legend" aria-label="Activity legend">
                <span className="bv-eyebrow">Predicted cortical response</span>
                <div className="bv-heatbar" aria-hidden="true" />
                <div className="bv-heat-ticks bv-mono">
                  <span>{scale.threshold.toFixed(3)}</span>
                  <span>{scale.vmax.toFixed(3)}+</span>
                </div>
                <span className="bv-footnote" title={scale.rule}>{binding.units} · gray below threshold · shared A/B/C scale</span>
              </div>
            )}

            <div className="bv-stage-tools">
              <button type="button" className="bv-icon-button" onClick={() => setMode("dock")} title="Return the brain to its dock (Esc)">
                {harness ? "Dock" : "Back to canvas"}
              </button>
              <button type="button" className="bv-icon-button" onClick={() => scene?.resetCamera()} title="Reset camera (double-click the brain)">Reset view</button>
              <button type="button" className="bv-icon-button" onClick={toggleFullscreen} title="Fullscreen (F)" aria-pressed={fullscreen}>
                {fullscreen ? "Exit fullscreen" : "Fullscreen"}
              </button>
            </div>

            <div className="bv-controls" role="toolbar" aria-label="Brain view controls">
              <Segmented label="Variant" value={variant} onChange={selectVariant} options={VARIANTS.map((v) => ({ value: v, label: v, hint: variantStatus(v) }))} />
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
                hz={binding?.hz}
                scenes={current?.scenes}
                atlasNames={assets?.atlas.names ?? []}
                meterMax={meterMax}
                reducedMotion={reducedMotion}
                mock={mock}
                precomputed={precomputed}
                onHandOver={() => setSequence("handover")}
                onLockOn={(hemi, atlasName, time_s) => emit({ type: "analysis.lock_on", runId: runKey ?? "preview", variant, region: regionRef(hemi, atlasName), time_s })}
                onFinish={finishSequence}
              />
            )}

            {binding && (dataMode === "mock" || dataMode === "demo_example" || dataMode === "genuine_precomputed") && (
              <span className={`bv-dock-tag ${dataMode === "mock" ? "bv-dock-tag-mock" : ""}`}>
                {dataMode === "mock" ? "MOCK" : dataMode === "demo_example" ? "Demo example · precomputed" : "Precomputed"}
              </span>
            )}

            {workload && (
              <p className="bv-dock-status bv-mono" aria-live="polite">
                <i aria-hidden="true" className={working ? "bv-dot-working" : ""} />
                {statusLine(workload)}
              </p>
            )}

            <div className="bv-dock-bar" aria-label="Brain dock">
              <div className="bv-dock-meta">
                <strong>{viewLabel}</strong>
                <span className="bv-mono">
                  {formatTime(clockState.time)}
                  {sample?.inRange && binding ? ` · sample ${binding.times[sample.nearestIndex].toFixed(0)} s` : ""}
                </span>
              </div>
              <span className={`bv-chip ${chipClass}`}>{dataMode === "mock" ? "MOCK" : statusLabel}</span>
              <div className="bv-dock-actions">
                <button type="button" className="bv-icon-button" onClick={() => setMode("expanded")} disabled={Boolean(entry)}>Expand</button>
                <button type="button" className="bv-icon-button" onClick={() => startEntry(true)} disabled={Boolean(entry) || sequence !== "idle"} title="Replay the entry intro">Replay</button>
                <button type="button" className="bv-icon-button" onClick={() => setPinned((v) => !v)} aria-pressed={pinned}>{pinned ? "Unpin" : "Pin"}</button>
                {manual || motionPaused ? (
                  <button type="button" className="bv-icon-button" onClick={() => { setManual(false); setMotionPaused(false); }}>Resume motion</button>
                ) : (
                  <button type="button" className="bv-icon-button" onClick={() => setMotionPaused(true)}>Pause motion</button>
                )}
              </div>
            </div>

            {entry && scene && (
              <EntrySequence
                key={entry.run}
                scene={scene}
                head={head}
                atlasNames={assets?.atlas.names ?? []}
                reducedMotion={reducedMotion}
                dataMode={dataMode}
                dataLabel={dataMode === "demo_example" ? DATA_LABELS.demo_example : binding ? statusLabel : brainSim === "off" ? "Anatomy only · Brain sim off" : "Anatomy only · No brain data"}
                replay={entry.replay}
                onRegionFocus={(region) => emit({ type: "entry.region_focus", region, dataMode })}
                onDock={() => setMode("dock")}
                onFinish={finishEntry}
              />
            )}
          </div>

          {mode === "dock" && beat && (
            <aside className="bv-dock-callout" aria-live="polite">
              <span className="bv-eyebrow">
                {STEP_LABELS[beat.milestone.step]}
                {beat.milestone.variantId ? ` · Variant ${beat.milestone.variantId}` : ""} · backend event
              </span>
              <h3>{beat.milestone.message}</h3>
              {beat.milestone.durationS !== null && <p className="bv-mono bv-dim">Step took {beat.milestone.durationS.toFixed(1)} s</p>}
              {beat.region ? (
                <>
                  <p className="bv-callout-region">
                    {beat.region.dataMode === "mock" ? "MOCK fixture · " : "Strongest predicted response · "}
                    <strong>{beat.region.name}</strong> ({beat.region.group}, {beat.region.hemi} hemisphere) at {formatTime(beat.region.sampleTime)}
                    {beat.region.dataMode === "genuine_precomputed" ? " · precomputed" : ""}
                  </p>
                  <p>{beat.region.knownFor}</p>
                  <p className="bv-mono bv-dim">On screen: {beat.region.sceneText ?? "no scene data at this time"}</p>
                  <p className="bv-mono bv-dim">Brain colours still show playback time {formatTime(clockState.time)}; nothing was seeked.</p>
                </>
              ) : RESULT_STEPS.includes(beat.milestone.step) ? (
                <p className="bv-dim">No region shown: no genuine brain data for this video yet.</p>
              ) : null}
            </aside>
          )}

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
              hz={binding?.hz}
              units={binding?.units ?? ""}
              scenes={current?.scenes}
              noDataLabel={brainSim === "off" ? "Brain sim off" : "No brain data"}
              onClear={() => setPick(null)}
            />
            <details className="bv-card bv-about">
              <summary className="bv-eyebrow">About this view</summary>
              <p>
                Predicted cortical (fMRI-like) response for an average viewer from TRIBE v2, sampled about once per second and interpolated for display. It is
                not measured EEG and does not read emotions, desire or buying intent.
              </p>
              <p className="bv-footnote">
                Mesh: FreeSurfer fsaverage5 (normal and inflated). Scale: {scale ? scale.rule : "none until data is bound"}. Keys: space play/pause, ←/→ one second, F fullscreen, Esc dock, double-click reset.
              </p>
            </details>
          </aside>
        </div>
      </div>
    </div>
  );
}

/** @deprecated Use BrainCompanion. */
export const BrainExperience = BrainCompanion;
