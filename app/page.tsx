"use client";

import { useEffect, useState } from "react";

const overview = [
  { value: "3", label: "concepts", detail: "Distinct creative hypotheses" },
  { value: "15s", label: "per video", detail: "Focused motion graphics" },
  { value: "3–6", label: "screenshots", detail: "Your product is the source" },
];

const pipeline = [
  { number: "01", title: "Brief", detail: "Add the product, audience, launch goal, and screenshots." },
  { number: "02", title: "Plan", detail: "Shape three concepts with different creative hypotheses." },
  { number: "03", title: "Render", detail: "Turn each concept into a 15-second motion graphics video." },
  { number: "04", title: "Pretest", detail: "Run every variant through the available simulated viewers." },
  { number: "05", title: "Decide", detail: "Review the winner, runner-up, reasons, and launch brief." },
];

const requirements = [
  { tag: "01", title: "A focused product brief", detail: "Product name, one-line description, audience, and launch goal." },
  { tag: "02", title: "3–6 product screenshots", detail: "Real screens from the product you are preparing to launch." },
  { tag: "03", title: "One clear goal", detail: "Choose signups, downloads, understanding, or purchase." },
];

function ArrowIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16">
      <path d="M4 12 12 4M6 4h6v6" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16">
      <path d="M8 3v10M3 8h10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function DashboardPage() {
  const [isBriefOpen, setIsBriefOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = isBriefOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isBriefOpen]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsBriefOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  return (
    <main className="page-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <div className="dashboard">
        <header className="topbar">
          <div className="brand-lockup">
            <span className="mark" aria-hidden="true" />
            <span className="brand-name">Preflight</span>
            <span className="route">/ Dashboard</span>
          </div>
          <div className="run-state"><span />No active run</div>
        </header>

        <section className="hero" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="eyebrow">Launch decision system</p>
            <h1 id="page-title">Know what to launch<br />before you launch.</h1>
            <p className="lede">Turn a focused product brief into three motion graphics videos, pretest every variant, and leave with a winner and a launch brief.</p>
          </div>
          <button className="primary-button" onClick={() => setIsBriefOpen(true)}>
            <span>New preflight</span><ArrowIcon />
          </button>
        </section>

        <section className="section" aria-labelledby="overview-title">
          <div className="section-heading">
            <h2 id="overview-title">Project overview</h2>
            <span>What you&apos;ll make</span>
          </div>
          <div className="overview-grid">
            {overview.map((item) => (
              <article className="panel overview-card" key={item.label}>
                <div className="metric"><strong>{item.value}</strong><span>{item.label}</span></div>
                <p>{item.detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section" aria-labelledby="pipeline-title">
          <div className="section-heading">
            <h2 id="pipeline-title">How a preflight works</h2>
            <span>The pipeline</span>
          </div>
          <div className="pipeline-grid">
            {pipeline.map((step) => (
              <article className="panel pipeline-card" key={step.number}>
                <div className="step-meta"><span>{step.number}</span><i /></div>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.detail}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="section" aria-labelledby="briefs-title">
          <div className="section-heading">
            <h2 id="briefs-title">Recent briefs</h2>
            <span>Projects</span>
          </div>
          <div className="panel empty-state">
            <div className="empty-copy">
              <div className="document-icon" aria-hidden="true"><span /><span /><span /></div>
              <div>
                <h3>No briefs yet</h3>
                <p>Your first brief will appear here after you start a preflight.</p>
              </div>
            </div>
            <button className="secondary-button" onClick={() => setIsBriefOpen(true)}><PlusIcon />Create first brief</button>
          </div>
        </section>

        <footer>
          <span>Preflight</span>
          <span>Pretest before you spend</span>
        </footer>
      </div>

      {isBriefOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setIsBriefOpen(false)}>
          <section className="brief-modal" role="dialog" aria-modal="true" aria-labelledby="brief-modal-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-topbar">
              <span className="eyebrow">New preflight</span>
              <button className="close-button" onClick={() => setIsBriefOpen(false)} aria-label="Close new preflight">Close</button>
            </div>
            <div className="modal-copy">
              <h2 id="brief-modal-title">Start with the brief.</h2>
              <p>Bring the source material below. Preflight uses it to plan three truthful concepts without inventing product claims.</p>
            </div>
            <div className="requirement-list">
              {requirements.map((requirement) => (
                <article className="requirement" key={requirement.tag}>
                  <span>{requirement.tag}</span>
                  <div><h3>{requirement.title}</h3><p>{requirement.detail}</p></div>
                </article>
              ))}
            </div>
            <p className="modal-note">Brief intake is the next product step. No simulation runs from this dashboard.</p>
          </section>
        </div>
      )}
    </main>
  );
}
