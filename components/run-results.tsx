"use client";

import { useEffect, useRef, useState } from "react";
import { FinalVideoFinish } from "@/components/final-video-finish";

import { RunReport } from "@/components/run-report";
import { CLOSE_CALL_POINTS, leadOf, measuredScores, points, productionFactor, usesPanelScoreScale, type Production, type RenderRecord, type SimulationResult } from "@/lib/run-report";

type VariantId = "A" | "B" | "C";
export type RunState = "BRIEF_RECEIVED" | "PLANNED" | "RENDERED" | "SIMULATED" | "SCORED" | "EXPLAINED" | "ITERATED" | "DONE" | "FAILED";

type Reason = { t: number; scene_index: number; text: string };
export type PlannedScene = { t_start: number; t_end: number; screenshot: string; text: string; source_field: string };
export type PlannedVariant = {
  variant_id: VariantId;
  concept: { hypothesis: string; hook: string; scenes: PlannedScene[] };
  render?: (RenderRecord & { video_sha256: string | null }) | null;
  simulations?: SimulationResult[];
  files: Record<string, string>;
};
type Results = {
  state: RunState;
  ranking: {
    order: VariantId[];
    scores: Record<string, number>;
    per_simulator?: Record<string, Record<string, number>>;
    confidence: "low" | "medium" | "high";
    rule: string;
    excluded?: Record<string, string>;
  } | null;
  report: {
    winner: VariantId;
    runner_up: VariantId;
    reasons: Record<string, Reason[]>;
    next_time: string[];
    token_savings: { calls: number; input_tokens_original: number; input_tokens_sent: number; tokens_saved: number; percent: number } | null;
    brain_sim: boolean;
    production?: Production | null;
  } | null;
  variants: PlannedVariant[];
};
type ProjectRun = { run: { state: RunState; error: string | null; failed_after: RunState | null } };

const STEPS: Array<{ after: RunState; label: string }> = [
  { after: "BRIEF_RECEIVED", label: "Plan three concepts from your brief" },
  { after: "PLANNED", label: "Render A, B and C as 15-second videos" },
  { after: "RENDERED", label: "Simulated viewers watch each video" },
  { after: "SIMULATED", label: "Score and rank the variants" },
  { after: "SCORED", label: "Explain the drop-offs" },
];
const ORDER: RunState[] = ["BRIEF_RECEIVED", "PLANNED", "RENDERED", "SIMULATED", "SCORED", "EXPLAINED", "ITERATED", "DONE"];
const EXPORTS = [
  { name: "winner.mp4", label: "Winner video" },
  { name: "runner_up.mp4", label: "Runner-up video" },
  { name: "report.json", label: "Report (JSON)" },
  { name: "launch_brief.md", label: "Launch brief" },
];

function url(apiBase: string, path: string) {
  return `${apiBase.replace(/\/+$/, "")}${path}`;
}

function clock(seconds: number) {
  return `0:${String(Math.floor(seconds)).padStart(2, "0")}`;
}

export function RunResults({ apiBase, projectId, runNonce, onClose, onProgress, onResume, visible = true }: {
  visible?: boolean;
  apiBase: string | undefined;
  projectId: string;
  runNonce: number;
  onClose: () => void;
  onProgress?: (state: RunState, variants: PlannedVariant[]) => void;
  /** Resume a failed run from its last completed step. */
  onResume?: () => void;
}) {
  const [results, setResults] = useState<Results | null>(null);
  const [failure, setFailure] = useState<ProjectRun["run"] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());
  const [picked, setPicked] = useState<VariantId | null>(null);
  const [accepted, setAccepted] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const acceptKey = `preflight.accepted.${projectId}`;

  useEffect(() => {
    queueMicrotask(() => setAccepted(localStorage.getItem(acceptKey)));
  }, [acceptKey, runNonce]);

  useEffect(() => {
    if (!apiBase) return;
    let cancelled = false;
    let timer = 0;
    queueMicrotask(() => {
      setResults(null);
      setFailure(null);
      setError(null);
      setPicked(null);
      setShowReport(false);
      setStartedAt(Date.now());
    });
    const poll = async () => {
      try {
        const response = await fetch(url(apiBase, `/api/projects/${encodeURIComponent(projectId)}/results`), { cache: "no-store" });
        if (!response.ok) throw new Error(response.status === 404 ? "Waiting for the run to be created…" : `Backend answered ${response.status}`);
        const next = (await response.json()) as Results;
        if (cancelled) return;
        setResults(next);
        setError(null);
        if (next.state === "FAILED") {
          const project = await fetch(url(apiBase, `/api/projects/${encodeURIComponent(projectId)}`), { cache: "no-store" });
          if (project.ok && !cancelled) setFailure(((await project.json()) as ProjectRun).run);
          return;
        }
        if (next.state === "DONE") return;
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Backend unreachable");
      }
      if (!cancelled) timer = window.setTimeout(() => void poll(), 2000);
    };
    void poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [apiBase, projectId, runNonce]);

  const progressRef = useRef(onProgress);
  useEffect(() => { progressRef.current = onProgress; }, [onProgress]);
  const reportedState = results?.state;
  useEffect(() => {
    if (reportedState && results) progressRef.current?.(reportedState, results.variants);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- report once per state change, not per poll
  }, [reportedState]);

  const running = !results || (results.state !== "DONE" && results.state !== "FAILED");
  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [running]);

  if (!visible) return null;
  if (!apiBase) {
    return <aside className="side-drawer results-drawer"><Heading onClose={onClose} title="Results" /><p className="results-muted">NEXT_PUBLIC_PREFLIGHT_API_BASE is not set, so this page cannot read results from the backend.</p></aside>;
  }

  const report = results?.report ?? null;
  const ranking = results?.ranking ?? null;
  const reached = results ? ORDER.indexOf(results.state === "FAILED" ? (failure?.failed_after ?? "BRIEF_RECEIVED") : results.state) : -1;
  const shown: VariantId | null = picked ?? report?.winner ?? null;
  const variant = results?.variants.find((item) => item.variant_id === shown);
  const winnerSourceHash = results?.variants.find((item) => item.variant_id === report?.winner)?.render?.video_sha256;
  const elapsed = Math.max(0, Math.round((now - startedAt) / 1000));
  const isMeasured = Boolean(ranking && results && usesPanelScoreScale(ranking, results.variants));
  const factor = isMeasured ? productionFactor(report) : 1;
  const measured = new Map((results?.variants ?? []).map((item) => {
    const score = measuredScores(item).score;
    return [item.variant_id, score == null ? null : score * factor];
  }));
  const scoreOf = (id: VariantId) => points((isMeasured ? measured.get(id) : ranking?.scores[id]) ?? 0);
  const lead = isMeasured && report?.runner_up ? leadOf(measured.get(report.winner), measured.get(report.runner_up)) : null;
  const closeThreshold = Math.round(CLOSE_CALL_POINTS * factor * 10) / 10;
  const closeCall = lead != null && lead < closeThreshold;

  return (
    <aside className="side-drawer results-drawer" aria-live="polite">
      <Heading onClose={onClose} title={report ? `Launch ${report.winner}` : results?.state === "FAILED" ? "Run failed" : "Running preflight"} />

      {(!report || results?.state === "FAILED") && <ol className="results-steps">
        {STEPS.map((step, index) => {
          const done = reached > ORDER.indexOf(step.after);
          const active = !done && reached === ORDER.indexOf(step.after) && results?.state !== "FAILED";
          const failed = results?.state === "FAILED" && reached === ORDER.indexOf(step.after);
          return <li key={step.after} className={done ? "done" : active ? "active" : failed ? "failed" : ""}><span>{done ? "●" : failed ? "×" : active ? "◌" : "○"}</span>{index + 1}. {step.label}</li>;
        })}
      </ol>}
      {running && <p className="results-muted">{error ?? `Working · ${elapsed}s elapsed · usually 2–3 minutes`}</p>}
      {results?.state === "FAILED" && <p className="results-error">{failure?.error ?? "The backend stopped this run."} Resume to continue from the last completed step.{onResume && <>{" "}<button className="chip active" onClick={onResume}>Resume run</button></>}</p>}

      {report && ranking && <>
        <p className="results-verdict">Launch <b>{report.winner}</b>. A/B test it against <b>{report.runner_up}</b>.<span className={`confidence ${ranking.confidence}`}>{ranking.confidence} confidence</span>{closeCall && <span className="confidence close-call">close call</span>}</p>
        {closeCall && <p className="results-muted">{report.winner} leads {report.runner_up} by only {lead} of 100 points. Our display flags gaps below {closeThreshold} points for live A/B follow-up; this is not a statistical tie.</p>}
        {factor < 1 && <p className="results-error">Not ready to publish. {report.production?.reasons.join(" ")}</p>}
        <div className="results-argument">
          <small>Where they leave</small>
          <p>The moments below are simulated hold/drop signals, not observed viewer retention. Use this recommendation to choose a live A/B test, not as proof of consumer behaviour.</p>
        </div>

        <div className="results-board">
          {ranking.order.map((id, index) => {
            const concept = results?.variants.find((item) => item.variant_id === id)?.concept;
            return <button key={id} className={id === shown ? "selected" : ""} onClick={() => setPicked(id)}>
              <span className="variant-letter">{id}</span>
              <span><strong>{index === 0 ? "Winner" : index === 1 ? "Runner-up" : "Third"} · {concept?.hypothesis ?? ""}</strong><em>{concept?.hook}</em></span>
              <span className="results-score" title={isMeasured ? `Mean simulated-viewer score, out of 100${factor < 1 ? `, capped at ${Math.round(factor * 100)} % for production quality` : ""}` : "Relative to these variants only"}><i style={{ width: `${scoreOf(id)}%` }} />{scoreOf(id)}</span>
            </button>;
          })}
        </div>

        {playbackSrc(variant?.files) && <video key={playbackSrc(variant?.files)} ref={videoRef} className="results-video" src={url(apiBase, playbackSrc(variant?.files)!)} controls playsInline preload="metadata" />}

        {shown && <div className="results-reasons">
          <small>Why {shown} scored this way</small>
          {(report.reasons[shown] ?? []).map((reason) => <button key={`${reason.t}-${reason.text}`} onClick={() => { if (videoRef.current) { videoRef.current.currentTime = reason.t; void videoRef.current.play(); } }}>
            <span>{clock(reason.t)}</span>{reason.text}
          </button>)}
        </div>}

        {report.next_time.length > 0 && <div className="results-next"><small>Next time</small><ul>{report.next_time.map((line) => <li key={line}>{line}</li>)}</ul></div>}

        <div className="results-facts">
          {report.token_savings && <p><b>Condense</b> saved {report.token_savings.tokens_saved.toLocaleString()} input tokens ({report.token_savings.percent}%) across {report.token_savings.calls} Gemini calls.</p>}
          <p><b>Brain simulation</b> {report.brain_sim ? "on: TRIBE v2 contributed to the score." : "off: ranked by the simulated viewer panel only."}</p>
        </div>

        {results?.state === "DONE" && <div className="results-accept">
          {accepted === report.winner
            ? <><p>You accepted <b>{report.winner}</b> as the launch video.</p><button onClick={() => setShowReport(true)}>See this run’s report</button></>
            : <button className="primary" onClick={() => { localStorage.setItem(acceptKey, report.winner); setAccepted(report.winner); setShowReport(true); }}>Accept {report.winner} and see the report</button>}
        </div>}

        <div className="results-exports">
          {EXPORTS.map((item) => <a key={item.name} href={url(apiBase, `/api/projects/${encodeURIComponent(projectId)}/export/${item.name}`)} download>{item.label}</a>)}
        </div>
        {results?.state === "DONE" && winnerSourceHash && <FinalVideoFinish
          key={`${projectId}-${report.winner}`}
          apiBase={apiBase}
          projectId={projectId}
          variantId={report.winner}
          sourceHash={winnerSourceHash}
        />}
      </>}
      {showReport && results && report && <RunReport apiBase={apiBase} projectId={projectId} results={results} onClose={() => setShowReport(false)} />}
    </aside>
  );
}

function Heading({ title, onClose }: { title: string; onClose: () => void }) {
  return <div className="drawer-heading"><div><small>Preflight results</small><h2>{title}</h2></div><button onClick={onClose} aria-label="Close results">×</button></div>;
}

function playbackSrc(files: Record<string, string> | undefined) {
  if (!files) return undefined;
  return files["video-final"] ?? files.video;
}
