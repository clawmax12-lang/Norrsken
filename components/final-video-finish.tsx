"use client";

import { useEffect, useRef, useState } from "react";

type FinalStatus = "queued" | "composing" | "rendering" | "audio" | "simulating" | "done" | "failed";
type FinalRecord = {
  command_id: string;
  status: FinalStatus;
  opus_attempts: number;
  error: string | null;
  brain_sim: boolean;
  files: Record<string, string>;
  usage: { model: string; route: string; input_tokens: number; output_tokens: number } | null;
};
const PHASES: Record<FinalStatus, string> = {
  queued: "Final video queued", composing: "Opus is directing the final motion",
  rendering: "Rendering the Opus composition", audio: "Finishing the sound",
  simulating: "Pretesting the exact finished video", done: "Final video ready", failed: "Finalization stopped",
};

export function FinalVideoFinish({ apiBase, projectId, variantId, sourceHash }: {
  apiBase: string; projectId: string; variantId: string; sourceHash: string;
}) {
  const [record, setRecord] = useState<FinalRecord | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const command = useRef<string | null>(null);
  const endpoint = `${apiBase.replace(/\/+$/, "")}/api/projects/${encodeURIComponent(projectId)}/finalization`;

  useEffect(() => {
    let stopped = false;
    let timer = 0;
    const abort = new AbortController();
    async function poll() {
      try {
        const response = await fetch(endpoint, { cache: "no-store", signal: abort.signal });
        if (!response.ok) throw new Error("Final-video status unavailable. Check the backend deployment.");
        const next = await response.json() as FinalRecord | null;
        if (stopped) return;
        setRecord(next);
        if (next) setError(null);
        if (!next || next.status === "done" || next.status === "failed") return;
      } catch (e) {
        if (stopped) return;
        setError(e instanceof Error ? e.message : "Final-video status unavailable.");
      }
      if (!stopped) timer = window.setTimeout(() => void poll(), 2000);
    }
    void poll();
    return () => { stopped = true; abort.abort(); window.clearTimeout(timer); };
  }, [endpoint, refresh]);

  async function finish() {
    if (sending) return;
    setSending(true);
    setError(null);
    command.current ??= record?.command_id ?? crypto.randomUUID();
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/finalization`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command_id: command.current, confirmed: true, variant_id: variantId, source_video_sha256: sourceHash }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.error === "string" ? payload.error : payload.error?.message ?? "Finalization unavailable.");
      setRecord(payload as FinalRecord);
      setConfirming(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to start finalization.");
    } finally {
      setSending(false);
      setRefresh((n) => n + 1);
    }
  }

  const busy = sending || (record && record.status !== "done" && record.status !== "failed");
  const limitReached = record?.status === "failed" && !record.usage && record.opus_attempts >= 2;
  return <section className="results-next final-finish" aria-label="Finish selected video with Opus">
    <small>Final motion video</small>
    {record && <p role="status">{PHASES[record.status]}</p>}
    {(error || record?.error) && <p className="results-error" role="alert">{error ?? record?.error}</p>}
    {record?.status === "done" ? <>
      <video className="results-video" src={`${apiBase.replace(/\/+$/, "")}${record.files.video}`} controls playsInline preload="metadata" />
      <p className="results-muted">This final file has its own pretest. The A/B/C ranking above still belongs to the original videos. {record.brain_sim ? "Final brain simulation available in its report." : "Final brain sim off."}</p>
      {record.usage && <p className="results-muted">{record.usage.model} · {record.usage.route} · {record.usage.input_tokens.toLocaleString()} input / {record.usage.output_tokens.toLocaleString()} output tokens</p>}
      <div className="results-exports">
        <a href={`${apiBase.replace(/\/+$/, "")}${record.files.video}`} download>Finished MP4</a>
        <a href={`${apiBase.replace(/\/+$/, "")}${record.files.report}`} download>Final evidence (JSON)</a>
      </div>
    </> : confirming ? <div role="group" aria-label="Confirm final-video budget">
      <p className="results-muted">Finish winner {variantId}: one bounded Opus composition, one render and a new pretest. Sound is added when configured. Render/testing may retry once; a failed Opus call needs another confirmation (maximum two attempts). Original videos stay available.</p>
      <button className="chip active" disabled={!!busy} onClick={() => void finish()}>{sending ? "Submitting…" : "Confirm paid finish"}</button>{" "}
      <button className="chip" disabled={sending} onClick={() => setConfirming(false)}>Keep original</button>
    </div> : <button className="chip" disabled={!!busy || limitReached} onClick={() => setConfirming(true)}>{busy ? "Finishing…" : record?.status === "failed" ? "Confirm resume" : "Finish with Opus"}</button>}
  </section>;
}
