"use client";

import { useEffect, useRef, useState } from "react";

type FinalStatus = "queued" | "composing" | "rendering" | "audio" | "simulating" | "done" | "failed";
type Director = "opus" | "gemini";
type FinalRecord = {
  command_id: string;
  status: FinalStatus;
  director?: Director;
  opus_attempts: number;
  error: string | null;
  brain_sim: boolean;
  files: Record<string, string>;
  usage: { model: string; route: string; input_tokens: number; output_tokens: number } | null;
  comparison?: { original: number; final: number; original_hook: number; final_hook: number; keep_original: boolean } | null;
};
const DIRECTORS: Record<Director, { name: string; offer: string }> = {
  opus: { name: "Opus", offer: "one bounded Opus composition of the motion and pacing" },
  gemini: { name: "Gemini", offer: "one Gemini pass that turns the winner into an ad cut: close, readable shots and a finger tapping through two or three elements per screen, the camera jumping to each with its own sound, all in sync with the voice" },
};
function phase(status: FinalStatus, director: Director): string {
  const name = DIRECTORS[director].name;
  return {
    queued: "Final video queued", composing: `${name} is directing the final motion`,
    rendering: `Rendering the ${name} composition`, audio: "Finishing the sound",
    simulating: "Pretesting the exact finished video", done: "Final video ready", failed: "Finalization stopped",
  }[status];
}

export function FinalVideoFinish({ apiBase, projectId, variantId, sourceHash }: {
  apiBase: string; projectId: string; variantId: string; sourceHash: string;
}) {
  const [record, setRecord] = useState<FinalRecord | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [chosen, setChosen] = useState<Director>("opus");
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
    const director = record?.director ?? chosen;
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/finalization`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command_id: command.current, confirmed: true, variant_id: variantId, source_video_sha256: sourceHash, director }),
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
  // A started finish resumes with the director it began with.
  const director = record?.director ?? chosen;
  return <section className="results-next final-finish" aria-label="Finish the selected video">
    <small>Final motion video</small>
    {record && <p role="status">{phase(record.status, director)}</p>}
    {(error || record?.error) && <p className="results-error" role="alert">{error ?? record?.error}</p>}
    {record?.status === "done" ? <>
      <video className="results-video" src={`${apiBase.replace(/\/+$/, "")}${record.files.video}`} controls playsInline preload="metadata" />
      <p className="results-muted">This final file has its own pretest. The A/B/C ranking above still belongs to the original videos. {record.brain_sim ? "Final brain simulation available in its report." : "Final brain sim off."}</p>
      {record.comparison && <PretestComparison variantId={variantId} comparison={record.comparison} />}
      {record.usage && <p className="results-muted">{record.usage.model} · {record.usage.route} · {record.usage.input_tokens.toLocaleString()} input / {record.usage.output_tokens.toLocaleString()} output tokens</p>}
      <div className="results-exports">
        <a href={`${apiBase.replace(/\/+$/, "")}${record.files.video}`} download>Finished MP4</a>
        <a href={`${apiBase.replace(/\/+$/, "")}${record.files.report}`} download>Final evidence (JSON)</a>
      </div>
    </> : confirming ? <div role="group" aria-label="Confirm final-video budget">
      <p className="results-muted">Finish winner {variantId}: {DIRECTORS[director].offer}, one render and a new pretest. Sound is added when configured. Render/testing may retry once; a failed {DIRECTORS[director].name} call needs another confirmation (maximum two attempts). Original videos stay available.</p>
      <button className="chip active" disabled={!!busy} onClick={() => void finish()}>{sending ? "Submitting…" : "Confirm paid finish"}</button>{" "}
      <button className="chip" disabled={sending} onClick={() => setConfirming(false)}>Keep original</button>
    </div> : record ? <button className="chip" disabled={!!busy || limitReached} onClick={() => setConfirming(true)}>{busy ? "Finishing…" : record.status === "failed" ? `Confirm resume with ${DIRECTORS[director].name}` : `Finish with ${DIRECTORS[director].name}`}</button>
      : <div role="group" aria-label="Choose who directs the finish">
        {(Object.keys(DIRECTORS) as Director[]).map((option) => (
          <button key={option} className={`chip${chosen === option ? " active" : ""}`} aria-pressed={chosen === option} onClick={() => { setChosen(option); setConfirming(true); }}>
            Finish with {DIRECTORS[option].name}
          </button>
        ))}
      </div>}
  </section>;
}

function PretestComparison({ variantId, comparison }: { variantId: string; comparison: NonNullable<FinalRecord["comparison"]> }) {
  const pct = (n: number) => `${Math.round(n * 100)}%`;
  return <>
    <p className="results-muted">Pretest: original {variantId} {pct(comparison.original)} → finished {pct(comparison.final)} · first 3 s {pct(comparison.original_hook)} → {pct(comparison.final_hook)}</p>
    {comparison.keep_original && <p className="results-error" role="alert">The finished cut tested lower than the original winner. Publish the original {variantId} instead.</p>}
  </>;
}
