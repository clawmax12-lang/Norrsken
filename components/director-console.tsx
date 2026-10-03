"use client";

import { useEffect, useRef } from "react";

export type ConsoleEventKind = "heard" | "said" | "typed" | "action" | "result" | "error" | "sent" | "backend" | "canvas";
export type ConsoleEvent = { id: string; at: number; kind: ConsoleEventKind; title: string; detail?: string };
export type JourneyStep = { id: string; label: string; hint: string; state: "done" | "active" | "todo" | "failed"; action?: () => void; actionLabel?: string };

const kindLabel: Record<ConsoleEventKind, string> = {
  heard: "You said",
  typed: "You typed",
  said: "AI said",
  action: "AI action",
  result: "Tool result",
  error: "Tool error",
  sent: "Sent",
  backend: "Backend",
  canvas: "Canvas",
};

function time(at: number) {
  return new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function DirectorConsole({ events, steps, liveUserText, liveDirectorText, liveState, onClose, narrow }: {
  events: ConsoleEvent[];
  steps: JourneyStep[];
  liveUserText: string;
  liveDirectorText: string;
  liveState: string;
  onClose: () => void;
  narrow: boolean;
}) {
  const logRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length, liveUserText, liveDirectorText]);

  const done = steps.filter((step) => step.state === "done").length;
  const next = steps.find((step) => step.state !== "done");

  return (
    <section className={`director-console ${narrow ? "narrow" : ""}`} aria-label="AI console">
      <div className="console-progress">
        <div className="console-heading"><small>Progress</small><strong>{done}/{steps.length} · {next ? next.label : "Done"}</strong><button onClick={onClose} aria-label="Close console">×</button></div>
        <div className="console-bar"><i style={{ width: `${Math.round((done / steps.length) * 100)}%` }} /></div>
        <ol>
          {steps.map((step, index) => <li key={step.id} className={step.state}>
            <span className="console-dot">{step.state === "done" ? "●" : step.state === "failed" ? "×" : step.state === "active" ? "◌" : "○"}</span>
            <span><b>{index + 1}. {step.label}</b><em>{step.hint}</em></span>
            {step.action && step.state !== "done" && <button onClick={step.action}>{step.actionLabel ?? "Go"}</button>}
          </li>)}
        </ol>
      </div>

      <div className="console-log">
        <div className="console-heading"><small>Everything said, done and sent</small><strong>Live: {liveState}</strong></div>
        <div className="console-lines" ref={logRef}>
          {events.length === 0 && !liveUserText && !liveDirectorText && <p className="console-empty">Nothing yet. Type below, or press Enable Live and talk. Every message, AI action and file sent shows up here.</p>}
          {events.map((event) => <article key={event.id} className={`console-line ${event.kind}`}>
            <span className="console-meta">{time(event.at)} · {kindLabel[event.kind]}</span>
            <p>{event.title}</p>
            {event.detail && <details><summary>Show data</summary><pre>{event.detail}</pre></details>}
          </article>)}
          {liveUserText && <article className="console-line heard pending"><span className="console-meta">now · You are saying</span><p>{liveUserText}…</p></article>}
          {liveDirectorText && <article className="console-line said pending"><span className="console-meta">now · AI is saying</span><p>{liveDirectorText}…</p></article>}
        </div>
      </div>
    </section>
  );
}
