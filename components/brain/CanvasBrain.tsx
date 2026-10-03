"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { loadDemoBundle, type DemoBundle } from "../../lib/brain/backend";
import type { BrainEvent } from "../../lib/brain/events";
import type { VariantId } from "../../lib/brain/contract";
import { useBackendRun } from "../../lib/brain/useBackendRun";
import { BrainCompanion } from "./BrainCompanion";

export interface CanvasBrainProps {
  /** Backend base URL; defaults to NEXT_PUBLIC_PREFLIGHT_API_BASE (public, not a secret). */
  apiBase?: string;
  /** Backend project id of the run on the canvas. Falls back to `?project=` for verification. */
  projectId?: string;
  selectedVariant?: VariantId;
  onSelectVariant?: (variant: VariantId) => void;
  onEvent?: (event: BrainEvent) => void;
  /** Play the once-per-session entry intro on this surface. */
  entry?: boolean;
  /**
   * URL of a genuine precomputed `preflight.demo-bundle.v1` manifest (licensed, video-matched),
   * shown as "Demo example · precomputed" until the run has its own data. Optional; none exists yet.
   */
  demoBundleUrl?: string;
}

const noopSubscribe = () => () => {};

/** `?project=` for verification; project ids are opaque path segments, nothing else is accepted. */
function readProjectParam(): string | undefined {
  const p = new URLSearchParams(window.location.search).get("project");
  return p && /^[A-Za-z0-9_-]{1,128}$/.test(p) ? p : undefined;
}

/**
 * The canvas companion: the reusable brain docked top-left, driven by the backend's real
 * activity log (choreography only) and its stored TRIBE artifacts (the only source of heat).
 * No speech, scheduling or inference lives here.
 */
export function CanvasBrain({ apiBase = process.env.NEXT_PUBLIC_PREFLIGHT_API_BASE, projectId, selectedVariant, onSelectVariant, onEvent, entry = true, demoBundleUrl }: CanvasBrainProps) {
  const [demo, setDemo] = useState<{ url: string; bundle: DemoBundle | null; error: string | null } | null>(null);
  useEffect(() => {
    if (!demoBundleUrl) return;
    let cancelled = false;
    loadDemoBundle(demoBundleUrl)
      .then((bundle) => !cancelled && setDemo({ url: demoBundleUrl, bundle, error: null }))
      .catch((e: Error) => !cancelled && setDemo({ url: demoBundleUrl, bundle: null, error: e.message }));
    return () => {
      cancelled = true;
    };
  }, [demoBundleUrl]);
  const demoState = demo && demo.url === demoBundleUrl ? demo : null;
  const urlProject = useSyncExternalStore(noopSubscribe, readProjectParam, () => undefined);
  const id = projectId ?? urlProject;
  const backend = useBackendRun(apiBase, id);
  const notices = [
    ...(backend.run?.problems ?? []),
    ...(backend.error ? [`Backend: ${backend.error}`] : []),
    ...(backend.status === "error" ? ["Activity stream disconnected"] : []),
    ...(demoState?.error ? [demoState.error] : []),
  ];
  return (
    <BrainCompanion
      projectId={id}
      runId={id}
      bindings={backend.run?.bindings}
      scenesByVariant={backend.run?.scenes}
      videos={backend.run?.videos}
      workload={id && apiBase ? backend.workload : undefined}
      consumeMilestone={backend.consumeMilestone}
      dockCorner="top-left"
      entry={entry}
      selectedVariant={selectedVariant}
      onSelectVariant={onSelectVariant}
      onEvent={onEvent}
      hostNotices={notices}
      demoBundle={demoState?.bundle ?? undefined}
    />
  );
}
