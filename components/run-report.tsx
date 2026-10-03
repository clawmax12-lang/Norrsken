"use client";

import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import { buildRunReport, clock, parseActivityLog, points, simulatorLabel, type ActivityEvent, type Outcome, type Results } from "@/lib/run-report";

const EXPORTS = [
  { name: "winner.mp4", label: "Winner video" },
  { name: "runner_up.mp4", label: "Runner-up video" },
  { name: "report.json", label: "Report (JSON)" },
  { name: "launch_brief.md", label: "Launch brief" },
];

const OUTCOME_LABEL: Record<Outcome, string> = {
  winner: "Final video",
  "runner-up": "A/B challenger",
  "not chosen": "Not chosen",
  excluded: "Excluded",
  "render failed": "Render failed",
  "not simulated": "Not simulated",
};

function url(apiBase: string, path: string) {
  return `${apiBase.replace(/\/+$/, "")}${path}`;
}

function duration(seconds: number | null) {
  if (seconds == null) return null;
  if (seconds < 60) return `${Math.round(seconds)}s`;
  return `${Math.floor(seconds / 60)}m ${String(Math.round(seconds % 60)).padStart(2, "0")}s`;
}

export function RunReport({ apiBase, projectId, results, onClose }: {
  apiBase: string;
  projectId: string;
  results: Results;
  onClose: () => void;
}) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [logState, setLogState] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    fetch(url(apiBase, `/api/projects/${encodeURIComponent(projectId)}/log`), { cache: "no-store", signal: controller.signal })
      .then((response) => (response.ok ? response.text() : Promise.reject(new Error(String(response.status)))))
      .then((text) => { setEvents(parseActivityLog(text)); setLogState("ready"); })
      .catch(() => setLogState("missing"))
      .finally(() => window.clearTimeout(timer));
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [apiBase, projectId]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const report = useMemo(() => buildRunReport(results, events), [results, events]);
  if (!report) return null;

  const winnerVariant = results.variants.find((variant) => variant.variant_id === report.winner);
  const winner = report.variants.find((variant) => variant.outcome === "winner");
  const n = report.numbers;
  const stats: Array<{ value: string; label: string; hot?: boolean }> = [
    { value: `${n.planned} → ${n.ranked}`, label: "Films planned, then ranked by simulated viewers" },
    { value: String(n.notBoosted), label: n.notBoosted === 1 ? "Film that never takes ad money" : "Films that never take ad money" },
    ...(n.winnerMargin != null ? [{
      value: report.closeCall ? "Tie" : `+${n.winnerMargin}`,
      label: report.closeCall
        ? `${report.winner} leads ${report.runnerUp} by only ${n.winnerMargin} of 100 points. Too close to call: test both live`
        : `Points of 100 that ${report.winner} leads ${report.runnerUp} by, as the simulated viewers scored them`,
      hot: true,
    }] : []),
    ...(n.earliestOtherDrop != null ? [{ value: clock(n.earliestOtherDrop), label: `Earliest drop in a film that lost${n.winnerFirstDrop != null ? `. ${report.winner} first drops at ${clock(n.winnerFirstDrop)}` : `. ${report.winner} has no drop recorded`}` }] : []),
    ...(n.runSeconds != null ? [{ value: duration(n.runSeconds)!, label: "Brief to verdict, from the run log" }] : []),
    ...(n.renderSeconds != null ? [{ value: duration(n.renderSeconds)!, label: `Render time across ${n.rendered} films` }] : []),
    { value: String(n.simulators.length), label: n.simulators.length ? n.simulators.map(simulatorLabel).join(" + ") : "No simulator returned a result" },
    ...(n.tokensSaved != null ? [{ value: n.tokensSaved.toLocaleString(), label: `Input tokens Condense did not send (${n.tokenPercent}%)` }] : []),
  ];

  return createPortal(
    <div className="run-report preflight-theme" role="dialog" aria-modal="true" aria-labelledby="run-report-title">
      <div className="run-report-frame">
        <header className="run-report-bar">
          <div><small>Run report · {projectId}</small><h1 id="run-report-title">Launch {report.winner}{report.runnerUp ? `. Test it against ${report.runnerUp}.` : "."}</h1></div>
          <button onClick={onClose} aria-label="Close report">×</button>
        </header>

        <section className="run-report-hero">
          {winnerVariant?.files.video
            ? <video className="run-report-video" src={url(apiBase, winnerVariant.files.video)} controls playsInline preload="metadata" />
            : <div className="run-report-video empty">No video file for {report.winner}</div>}
          <div>
            <p className="run-report-kicker">Final video · {winner?.hypothesis}</p>
            <h2>“{winner?.hook}”</h2>
            <p className="run-report-why">{winner?.why}</p>
            <p className="run-report-tags">
              {report.closeCall && <span className="close-call">Close call</span>}
              <span className={`confidence ${report.confidence}`}>{report.confidence} confidence</span>
              <span>Brain sim {report.brainSim ? "on" : "off"}</span>
            </p>
            <p className="run-report-rule">{report.rule}</p>
          </div>
        </section>

        <section className="run-report-stats" aria-label="This run in numbers">
          {stats.map((stat) => <article key={stat.label} className={stat.hot ? "hot" : undefined}><b>{stat.value}</b><span>{stat.label}</span></article>)}
        </section>

        <section className="run-report-panel">
          <p className="run-report-kicker">Every film, and why</p>
          <h2>How {report.winner} became the last video standing</h2>
          <ol className="run-report-variants">
            {report.variants.map((variant) => (
              <li key={variant.id} className={`outcome-${variant.outcome.replace(" ", "-")}`}>
                <div className="run-report-variant-id"><b>{variant.id}</b><span>{OUTCOME_LABEL[variant.outcome]}</span>{variant.rank && <em>Rank {variant.rank}</em>}</div>
                <div>
                  <h3>{variant.hypothesis}<small>“{variant.hook}”</small></h3>
                  {variant.score != null && <div className="run-report-score"><i style={{ width: `${points(variant.score)}%` }} /><span>{points(variant.score)}{report.scoreScale === "measured" ? " / 100" : " relative"}</span></div>}
                  <p className="run-report-why">{variant.why}</p>
                  <dl>
                    {variant.perSimulator.map((sim) => <div key={sim.simulator}><dt>{simulatorLabel(sim.simulator)}</dt><dd>{points(sim.score)}</dd></div>)}
                    <div><dt>Holds</dt><dd>{variant.holds}</dd></div>
                    <div><dt>Drops</dt><dd>{variant.drops}</dd></div>
                    {variant.renderSeconds != null && <div><dt>Render</dt><dd>{duration(variant.renderSeconds)}</dd></div>}
                  </dl>
                  {variant.reasons.length > 0 && <ul className="run-report-reasons">{variant.reasons.map((reason) => <li key={`${reason.t}-${reason.text}`}><span>{clock(reason.t)}</span>{reason.text}</li>)}</ul>}
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="run-report-panel">
          <p className="run-report-kicker">Every step</p>
          <h2>What the agent did on this run</h2>
          {logState === "loading" && <p className="run-report-muted">Reading the run log…</p>}
          {logState === "missing" && <p className="run-report-muted">The run log could not be read, so step times are not shown.</p>}
          {logState === "ready" && report.steps.length === 0 && <p className="run-report-muted">The run log is empty.</p>}
          <ol className="run-report-steps">
            {report.steps.map((step, index) => (
              <li key={step.step} className={step.status}>
                <span className="run-report-step-index">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <strong>{step.label}</strong>
                  <ul>{step.lines.filter((line) => line.status !== "started").map((line, lineIndex) => <li key={`${line.at}-${lineIndex}`} className={line.status === "failed" ? "failed" : undefined}>{line.variant_id && <b>{line.variant_id}</b>}{line.message}</li>)}</ul>
                </div>
                <em>{step.status}{step.seconds != null ? ` · ${duration(step.seconds)}` : ""}</em>
              </li>
            ))}
          </ol>
        </section>

        {report.nextTime.length > 0 && <section className="run-report-panel">
          <p className="run-report-kicker">Next launch</p>
          <h2>What this run teaches</h2>
          <ul className="run-report-next">{report.nextTime.map((line) => <li key={line}>{line}</li>)}</ul>
        </section>}

        <div className="run-report-exports">
          {EXPORTS.map((item) => <a key={item.name} href={url(apiBase, `/api/projects/${encodeURIComponent(projectId)}/export/${item.name}`)} download>{item.label}</a>)}
        </div>
        <p className="run-report-muted">Scores compare these films with each other. They are not a forecast of reach, downloads or revenue. Holds and drops are simulation signals, not observed retention. Close call is a five-point display heuristic, not statistical significance. Confirm the recommendation with a live A/B test.</p>
      </div>
    </div>,
    document.body,
  );
}
