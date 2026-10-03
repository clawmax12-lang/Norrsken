"use client";

import { useEffect, useState } from "react";

type IconName = "dashboard" | "brief" | "activity" | "brain" | "export" | "settings";

const navigation: Array<{ label: string; href: string; icon: IconName; active?: boolean }> = [
  { label: "Overview", href: "#overview", icon: "dashboard", active: true },
  { label: "Briefs", href: "#briefs", icon: "brief" },
  { label: "Activity", href: "#workflow", icon: "activity" },
  { label: "Exports", href: "#briefs", icon: "export" },
  { label: "Brain viewer", href: "/brain", icon: "brain" },
];

const priorities = [
  { number: "1", title: "Write the product brief", detail: "Name, one-line description, and audience" },
  { number: "2", title: "Add 3–6 screenshots", detail: "Use real product screens" },
  { number: "3", title: "Choose the launch goal", detail: "Signups, downloads, understanding, or purchase" },
];

const workflow = ["Brief", "Plan", "Render", "Pretest", "Decision"];

const requirements = [
  { tag: "01", title: "A focused product brief", detail: "Product name, one-line description, audience, and launch goal." },
  { tag: "02", title: "3–6 product screenshots", detail: "Real screens from the product you are preparing to launch." },
  { tag: "03", title: "One clear goal", detail: "Choose signups, downloads, understanding, or purchase." },
];

function NavIcon({ name }: { name: IconName }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

  if (name === "dashboard") {
    return <svg viewBox="0 0 18 18" aria-hidden="true"><rect x="2.5" y="2.5" width="5" height="5" rx="1" {...common} /><rect x="10.5" y="2.5" width="5" height="5" rx="1" {...common} /><rect x="2.5" y="10.5" width="5" height="5" rx="1" {...common} /><rect x="10.5" y="10.5" width="5" height="5" rx="1" {...common} /></svg>;
  }
  if (name === "brief") {
    return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M5 2.5h5.5l3 3v10H5z" {...common} /><path d="M10.5 2.5v3h3M7.5 9h3.5M7.5 12h3.5" {...common} /></svg>;
  }
  if (name === "activity") {
    return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2.5 9h3l1.6-4 3 8 1.5-4h3.9" {...common} /></svg>;
  }
  if (name === "brain") {
    return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M9 3.2c-1-1.1-3.4-.9-4 .9-1.6.2-2.4 1.9-1.7 3.2-1 1-.8 2.9.6 3.5 0 1.8 1.9 3 3.5 2.2.5.8 1 1.2 1.6 1.2M9 3.2c1-1.1 3.4-.9 4 .9 1.6.2 2.4 1.9 1.7 3.2 1 1 .8 2.9-.6 3.5 0 1.8-1.9 3-3.5 2.2-.5.8-1 1.2-1.6 1.2M9 3.2v11" {...common} /></svg>;
  }
  if (name === "export") {
    return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M9 2.5v9M5.8 8.5 9 11.7l3.2-3.2M3 14.5h12" {...common} /></svg>;
  }
  return <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="2.5" {...common} /><path d="M9 2.5v2M9 13.5v2M2.5 9h2M13.5 9h2M4.4 4.4l1.4 1.4M12.2 12.2l1.4 1.4M13.6 4.4l-1.4 1.4M5.8 12.2l-1.4 1.4" {...common} /></svg>;
}

function PlusIcon() {
  return <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>;
}

function MenuIcon() {
  return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M3 5h12M3 9h12M3 13h12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>;
}

export default function DashboardPage() {
  const [isBriefOpen, setIsBriefOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = isBriefOpen || isSidebarOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isBriefOpen, isSidebarOpen]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsBriefOpen(false);
        setIsSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const openBrief = () => {
    setIsSidebarOpen(false);
    setIsBriefOpen(true);
  };

  return (
    <main className="app-shell">
      <aside className={`sidebar ${isSidebarOpen ? "sidebar-open" : ""}`} aria-label="Primary navigation">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span>Preflight</span>
        </div>

        <button className="workspace-switcher" type="button">
          <span className="workspace-avatar">P</span>
          <span><strong>Personal</strong><small>Workspace</small></span>
          <span className="workspace-chevron" aria-hidden="true">⌄</span>
        </button>

        <nav className="nav-list">
          <p>Workspace</p>
          {navigation.map((item) => (
            <a
              className={`nav-item ${item.active ? "nav-item-active" : ""}`}
              href={item.href}
              key={item.label}
              aria-current={item.active ? "page" : undefined}
              onClick={() => setIsSidebarOpen(false)}
            >
              <NavIcon name={item.icon} />
              <span>{item.label}</span>
            </a>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <a className="nav-item" href="#settings" onClick={() => setIsSidebarOpen(false)}><NavIcon name="settings" /><span>Settings</span></a>
          <div className="sidebar-meta"><span>Preflight</span><span>v0.1</span></div>
        </div>
      </aside>

      {isSidebarOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setIsSidebarOpen(false)} />}

      <div className="app-main">
        <header className="app-topbar">
          <div className="topbar-title">
            <button className="menu-button" type="button" onClick={() => setIsSidebarOpen(true)} aria-label="Open navigation"><MenuIcon /></button>
            <span className="topbar-workspace">Personal</span>
            <span className="topbar-separator">/</span>
            <strong>Overview</strong>
          </div>
          <button className="topbar-action" type="button" onClick={openBrief}><PlusIcon /><span>New preflight</span></button>
        </header>

        <div className="content" id="overview">
          <div className="page-heading">
            <div>
              <h1>Overview</h1>
              <p>What needs your attention right now.</p>
            </div>
            <span className="status-pill"><i />No active run</span>
          </div>

          <section className="priority-card" aria-labelledby="priority-title">
            <div className="priority-copy">
              <span className="section-label">Next priority</span>
              <h2 id="priority-title">Create your first preflight</h2>
              <p>Start with the source material. Once the brief is complete, Preflight can plan the three concepts.</p>
              <button className="primary-button" type="button" onClick={openBrief}>Start brief <span aria-hidden="true">→</span></button>
            </div>
            <ol className="priority-list">
              {priorities.map((priority, index) => (
                <li className={index === 0 ? "priority-active" : ""} key={priority.number}>
                  <span className="priority-number">{priority.number}</span>
                  <span><strong>{priority.title}</strong><small>{priority.detail}</small></span>
                  <em>{index === 0 ? "Start here" : "Required"}</em>
                </li>
              ))}
            </ol>
          </section>

          <section className="summary-grid" aria-label="Workspace summary">
            <article className="summary-card"><span>Briefs</span><strong>0</strong><small>No briefs created</small></article>
            <article className="summary-card"><span>Active runs</span><strong>0</strong><small>Nothing processing</small></article>
            <article className="summary-card"><span>Exports</span><strong>0</strong><small>No launch files yet</small></article>
          </section>

          <section className="dashboard-panel workflow-panel" id="workflow" aria-labelledby="workflow-title">
            <div className="panel-heading">
              <div><h2 id="workflow-title">Workflow</h2><p>Every preflight follows the same five steps.</p></div>
              <span>Not started</span>
            </div>
            <ol className="workflow-list">
              {workflow.map((step, index) => (
                <li key={step}>
                  <span>{index + 1}</span>
                  <strong>{step}</strong>
                  {index < workflow.length - 1 && <i />}
                </li>
              ))}
            </ol>
          </section>

          <section className="dashboard-panel briefs-panel" id="briefs" aria-labelledby="briefs-title">
            <div className="panel-heading">
              <div><h2 id="briefs-title">Recent briefs</h2><p>Your latest projects will appear here.</p></div>
              <button type="button" className="text-button" onClick={openBrief}>New brief</button>
            </div>
            <div className="table-heading" aria-hidden="true"><span>Project</span><span>Status</span><span>Updated</span></div>
            <div className="table-empty">
              <div className="empty-icon"><NavIcon name="brief" /></div>
              <strong>No briefs yet</strong>
              <p>Create a brief to begin your first preflight.</p>
              <button className="secondary-button" type="button" onClick={openBrief}><PlusIcon />Create brief</button>
            </div>
          </section>
        </div>
      </div>

      {isBriefOpen && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setIsBriefOpen(false)}>
          <section className="brief-modal" role="dialog" aria-modal="true" aria-labelledby="brief-modal-title" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-topbar">
              <span className="section-label">New preflight</span>
              <button className="close-button" onClick={() => setIsBriefOpen(false)} aria-label="Close new preflight">Close</button>
            </div>
            <div className="modal-copy">
              <h2 id="brief-modal-title">Start with the brief</h2>
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
