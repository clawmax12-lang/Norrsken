"use client";

/**
 * Subscribes to the backend activity log (SSE) and loads genuine results when a
 * result-bearing step finishes. Read-only: it never starts runs or inference.
 */

import { useCallback, useEffect, useReducer, useState } from "react";
import { loadBackendRun, parseActivityEvent, backendUrl, type AdaptedRun, type BackendRunState } from "./backend";
import { INITIAL_WORKLOAD, RESULT_STEPS, applyActivity, applyEnd, consumeMilestone, type WorkloadState } from "./workload";

export type StreamStatus = "off" | "connecting" | "open" | "reconnecting" | "ended" | "error";

type Action =
  | { type: "activity"; key: string; id: number; data: string; at: number }
  | { type: "end"; key: string; state: BackendRunState }
  | { type: "consume"; key: string; id: number };

interface Keyed {
  key: string;
  workload: WorkloadState;
}

/** Workload is keyed by "apiBase|projectId": switching projects starts from a clean state. */
function reducer(state: Keyed, action: Action): Keyed {
  const base = state.key === action.key ? state.workload : INITIAL_WORKLOAD;
  switch (action.type) {
    case "activity": {
      const event = parseActivityEvent(action.data);
      return { key: action.key, workload: event ? applyActivity(base, action.id, event, action.at) : base };
    }
    case "end":
      return { key: action.key, workload: applyEnd(base, action.state) };
    case "consume":
      return { key: action.key, workload: consumeMilestone(base, action.id) };
  }
}

export interface BackendRun {
  status: StreamStatus;
  workload: WorkloadState;
  run: AdaptedRun | null;
  error: string | null;
  /** Mark a queued milestone as shown (the caller plays its focus beat from `workload.queue`). */
  consumeMilestone: (id: number) => void;
}

export function useBackendRun(apiBase: string | undefined, projectId: string | undefined): BackendRun {
  const key = apiBase && projectId ? `${apiBase}|${projectId}` : "";
  const [keyed, dispatch] = useReducer(reducer, { key: "", workload: INITIAL_WORKLOAD });
  const [conn, setConn] = useState<{ key: string; status: StreamStatus }>({ key: "", status: "off" });
  const [loaded, setLoaded] = useState<{ key: string; run: AdaptedRun | null; error: string | null }>({ key: "", run: null, error: null });
  const workload = keyed.key === key ? keyed.workload : INITIAL_WORKLOAD;
  const status: StreamStatus = !key ? "off" : conn.key === key ? conn.status : "connecting";
  const run = loaded.key === key ? loaded.run : null;
  const error = loaded.key === key ? loaded.error : null;

  useEffect(() => {
    if (!apiBase || !projectId) return;
    let cancelled = false;
    let refreshTimer = 0;
    const refresh = () => {
      window.clearTimeout(refreshTimer);
      refreshTimer = window.setTimeout(() => {
        loadBackendRun(apiBase, projectId)
          .then((r) => !cancelled && setLoaded({ key, run: r, error: null }))
          .catch((e: Error) => !cancelled && setLoaded((prev) => ({ key, run: prev.key === key ? prev.run : null, error: e.message })));
      }, 150);
    };
    refresh();
    const source = new EventSource(backendUrl(apiBase, `/api/projects/${encodeURIComponent(projectId)}/log`));
    source.onopen = () => setConn({ key, status: "open" });
    // EventSource reconnects by itself and resends Last-Event-ID, so the backend replays only what was missed.
    source.onerror = () => setConn({ key, status: source.readyState === EventSource.CLOSED ? "error" : "reconnecting" });
    source.addEventListener("activity", (e) => {
      const msg = e as MessageEvent<string>;
      const id = Number(msg.lastEventId);
      dispatch({ type: "activity", key, id, data: msg.data, at: Date.now() });
      const parsed = parseActivityEvent(msg.data);
      if (parsed && parsed.status === "succeeded" && RESULT_STEPS.includes(parsed.step)) refresh();
    });
    source.addEventListener("end", (e) => {
      // The backend's terminal frame: close so the browser does not reconnect.
      source.close();
      let state: BackendRunState = "DONE";
      try {
        state = (JSON.parse((e as MessageEvent<string>).data) as { state: BackendRunState }).state;
      } catch {
        // keep DONE
      }
      dispatch({ type: "end", key, state });
      setConn({ key, status: "ended" });
      refresh();
    });
    return () => {
      cancelled = true;
      window.clearTimeout(refreshTimer);
      source.close();
    };
  }, [apiBase, projectId, key]);

  const consume = useCallback((id: number) => dispatch({ type: "consume", key, id }), [key]);

  return { status, workload, run, error, consumeMilestone: consume };
}
