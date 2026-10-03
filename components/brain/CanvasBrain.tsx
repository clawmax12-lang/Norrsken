"use client";

import { useSyncExternalStore } from "react";
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
export function CanvasBrain({ apiBase = process.env.NEXT_PUBLIC_PREFLIGHT_API_BASE, projectId, selectedVariant, onSelectVariant, onEvent, entry = true }: CanvasBrainProps) {
  const urlProject = useSyncExternalStore(noopSubscribe, readProjectParam, () => undefined);
  const id = projectId ?? urlProject;
  const backend = useBackendRun(apiBase, id);
  const notices = [
    ...(backend.run?.problems ?? []),
    ...(backend.error ? [`Backend: ${backend.error}`] : []),
    ...(backend.status === "error" ? ["Activity stream disconnected"] : []),
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
    />
  );
}
