"use client";

import { FormEvent, PointerEvent, useEffect, useRef, useState } from "react";

type IconName = "create" | "canvas" | "asset" | "activity" | "settings" | "brain";
type SelectedNode = { eyebrow: string; title: string; description: string; branches?: string } | null;

const navigation: Array<{ label: string; icon: IconName }> = [
  { label: "Create", icon: "create" },
  { label: "Canvases", icon: "canvas" },
  { label: "Assets", icon: "asset" },
  { label: "Activity", icon: "activity" },
];

const scenes = [
  { number: "01", title: "Hook", note: "Open on the strongest idea", preview: "hook", y: 70 },
  { number: "02", title: "Problem", note: "Make the pain concrete", preview: "problem", y: 230 },
  { number: "03", title: "Product reveal", note: "Introduce the real interface", preview: "reveal", y: 390 },
  { number: "04", title: "Core workflow", note: "Show the product in motion", preview: "workflow", y: 550 },
  { number: "05", title: "CTA", note: "End on the launch goal", preview: "cta", y: 710 },
];

const variants = [
  { label: "A", title: "Question hook", preview: "variant-a", y: 25 },
  { label: "B", title: "Outcome hook", preview: "variant-b", y: 150 },
  { label: "C", title: "Product-first hook", preview: "variant-c", y: 275 },
];

const refinements = [
  { label: "A1", title: "Faster reveal", preview: "refine-a", y: 25 },
  { label: "A2", title: "Larger headline", preview: "refine-b", y: 150 },
  { label: "A3", title: "Motion intro", preview: "refine-c", y: 275 },
];

function AppIcon({ name }: { name: IconName }) {
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  if (name === "create") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M9 2.5v13M2.5 9h13" {...stroke} /></svg>;
  if (name === "canvas") return <svg viewBox="0 0 18 18" aria-hidden="true"><rect x="2.5" y="3" width="13" height="12" rx="2" {...stroke} /><path d="M6 3v12" {...stroke} /></svg>;
  if (name === "asset") return <svg viewBox="0 0 18 18" aria-hidden="true"><rect x="2.5" y="3" width="13" height="12" rx="2" {...stroke} /><circle cx="6" cy="6.5" r="1" {...stroke} /><path d="m4.5 12 3-3 2.2 2.2 1.3-1.3 2.5 2.1" {...stroke} /></svg>;
  if (name === "activity") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2.5 9h3l1.6-4 3 8 1.5-4h3.9" {...stroke} /></svg>;
  if (name === "brain") return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M7 3.2A2.4 2.4 0 0 0 3.8 5.5a2.5 2.5 0 0 0-.3 4.7A2.5 2.5 0 0 0 7 14.7M11 3.2a2.4 2.4 0 0 1 3.2 2.3 2.5 2.5 0 0 1 .3 4.7 2.5 2.5 0 0 1-3.5 4.5M9 2.5v13M6.4 6.5c.7.1 1.2.5 1.5 1.1M11.6 6.5c-.7.1-1.2.5-1.5 1.1" {...stroke} /></svg>;
  return <svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="2.4" {...stroke} /><path d="M9 2.5v2M9 13.5v2M2.5 9h2M13.5 9h2M4.4 4.4l1.4 1.4M12.2 12.2l1.4 1.4M13.6 4.4l-1.4 1.4M5.8 12.2l-1.4 1.4" {...stroke} /></svg>;
}

function PlusIcon() {
  return <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>;
}

function MenuIcon() {
  return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="M3 5h12M3 9h12M3 13h12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>;
}

function SendIcon() {
  return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="m4 10 5-5 5 5M9 5v9" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

function PaperclipIcon() {
  return <svg viewBox="0 0 18 18" aria-hidden="true"><path d="m6.2 9.5 4.4-4.4a2.2 2.2 0 0 1 3.1 3.1l-5.5 5.5a3.2 3.2 0 0 1-4.5-4.5l5-5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg>;
}

function VoiceIcon() {
  return <svg viewBox="0 0 18 18" aria-hidden="true"><rect x="6.5" y="2.5" width="5" height="8" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.4" /><path d="M4.5 8.5a4.5 4.5 0 0 0 9 0M9 13v2.5M6.5 15.5h5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></svg>;
}

function Preview({ kind }: { kind: string }) {
  return (
    <div className={`node-preview preview-${kind}`} aria-hidden="true">
      <span className="preview-window"><i /><i /><i /></span>
      <span className="preview-copy"><i /><i /></span>
      <b />
    </div>
  );
}

export default function DashboardPage() {
  const [prompt, setPrompt] = useState("");
  const [hasCanvas, setHasCanvas] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [assetCount, setAssetCount] = useState(0);
  const [zoom, setZoom] = useState(0.82);
  const [selectedNode, setSelectedNode] = useState<SelectedNode>(null);
  const [isPanning, setIsPanning] = useState(false);
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef({ x: 0, y: 0, left: 0, top: 0 });

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("demo") === "1") {
      setPrompt("Create a launch demo that shows how the product turns a brief into tested video concepts.");
      setHasCanvas(true);
    }
  }, []);

  useEffect(() => {
    document.body.style.overflow = isSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [isSidebarOpen]);

  const startCanvas = (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    window.setTimeout(() => {
      setIsGenerating(false);
      setHasCanvas(true);
      window.history.replaceState(null, "", "?demo=1");
    }, 1150);
  };

  const resetCanvas = () => {
    setHasCanvas(false);
    setIsGenerating(false);
    setPrompt("");
    setAssetCount(0);
    setSelectedNode(null);
    setIsSidebarOpen(false);
    window.history.replaceState(null, "", window.location.pathname);
  };

  const beginPan = (event: PointerEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    dragRef.current = { x: event.clientX, y: event.clientY, left: canvas.scrollLeft, top: canvas.scrollTop };
    setIsPanning(true);
    canvas.setPointerCapture(event.pointerId);
  };

  const movePan = (event: PointerEvent<HTMLDivElement>) => {
    if (!isPanning || !canvasRef.current) return;
    canvasRef.current.scrollLeft = dragRef.current.left - (event.clientX - dragRef.current.x);
    canvasRef.current.scrollTop = dragRef.current.top - (event.clientY - dragRef.current.y);
  };

  const endPan = () => setIsPanning(false);
  const promptTitle = prompt.trim() || "Untitled product demo";

  return (
    <main className="studio-shell">
      <aside className={`studio-sidebar ${isSidebarOpen ? "sidebar-open" : ""}`} aria-label="Primary navigation">
        <div className="studio-brand"><span className="brand-mark" aria-hidden="true" /><span>Preflight</span></div>
        <button className="new-canvas-button" type="button" onClick={resetCanvas}><PlusIcon />New canvas</button>

        <nav className="studio-nav">
          <p>Workspace</p>
          {navigation.map((item, index) => (
            <button className={`studio-nav-item ${index === 0 ? "nav-active" : ""}`} type="button" key={item.label} onClick={() => setIsSidebarOpen(false)}>
              <AppIcon name={item.icon} /><span>{item.label}</span>
            </button>
          ))}
        </nav>

        {hasCanvas && (
          <div className="recent-canvases">
            <p>Recent</p>
            <button type="button" className="recent-canvas active-canvas">
              <span className="canvas-dot" />
              <span><strong>{promptTitle}</strong><small>Concept tree</small></span>
            </button>
          </div>
        )}

        <div className="sidebar-footer">
          <div className="brain-status"><AppIcon name="brain" /><span><strong>Brain sim off</strong><small>Connect later</small></span></div>
          <button className="studio-nav-item" type="button"><AppIcon name="settings" /><span>Settings</span></button>
        </div>
      </aside>

      {isSidebarOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setIsSidebarOpen(false)} />}

      <section className="studio-main">
        <header className="studio-topbar">
          <div className="topbar-path">
            <button className="menu-button" type="button" onClick={() => setIsSidebarOpen(true)} aria-label="Open navigation"><MenuIcon /></button>
            <span>Personal</span><i>/</i><strong>{hasCanvas ? "Product demo canvas" : "Create"}</strong>
          </div>
          <div className="topbar-actions">
            <span className="prototype-badge">Prototype</span>
            {hasCanvas && <button className="reset-button" type="button" onClick={resetCanvas}>New canvas</button>}
          </div>
        </header>

        {!hasCanvas ? (
          <div className="empty-canvas">
            <div className="canvas-grid" />
            <section className="prompt-stage" aria-labelledby="prompt-title">
              <span className="prompt-kicker">Product demo canvas</span>
              <h1 id="prompt-title">What should the demo show?</h1>
              <p>Describe the product, who it is for, and what a viewer should understand.</p>
              <form className="prompt-composer" onSubmit={startCanvas}>
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      event.currentTarget.form?.requestSubmit();
                    }
                  }}
                  placeholder="Create a product demo for…"
                  aria-label="Describe your product demo"
                  autoFocus
                />
                <div className="composer-footer">
                  <div className="composer-tools">
                    <label className="tool-button" title="Add product screenshots">
                      <PaperclipIcon /><span>{assetCount > 0 ? `${assetCount} assets` : "Add assets"}</span>
                      <input type="file" accept="image/png,image/jpeg" multiple onChange={(event) => setAssetCount(event.target.files?.length ?? 0)} />
                    </label>
                    <button className="tool-button voice-button" type="button" disabled title="Voice input will be added later"><VoiceIcon /><span>Voice soon</span></button>
                  </div>
                  <div className="composer-submit-group"><span>↵ to create</span><button className="send-button" type="submit" disabled={!prompt.trim() || isGenerating} aria-label="Create demo canvas"><SendIcon /></button></div>
                </div>
              </form>
              <div className="prompt-notes"><span>5 scenes</span><i /><span>50 branches per scene</span><i /><span>No simulation yet</span></div>
            </section>

            {isGenerating && (
              <div className="generating-overlay" role="status">
                <div className="generating-card"><span className="loading-mark" /><strong>Building the concept tree</strong><small>Mapping scenes and first-pass branches…</small></div>
              </div>
            )}
          </div>
        ) : (
          <div className="canvas-workspace">
            <div className="canvas-toolbar">
              <div><strong>Concept tree</strong><span>5 scenes · 50 branches per scene</span></div>
              <div className="canvas-controls">
                <button type="button" onClick={() => setZoom((value) => Math.max(0.55, value - 0.1))} aria-label="Zoom out">−</button>
                <span>{Math.round(zoom * 100)}%</span>
                <button type="button" onClick={() => setZoom((value) => Math.min(1.2, value + 0.1))} aria-label="Zoom in">+</button>
              </div>
            </div>

            <div
              className={`tree-viewport ${isPanning ? "is-panning" : ""}`}
              ref={canvasRef}
              onPointerDown={beginPan}
              onPointerMove={movePan}
              onPointerUp={endPan}
              onPointerCancel={endPan}
            >
              <div className="tree-scale" style={{ width: 1840 * zoom, height: 930 * zoom }}>
                <div className="tree-stage" style={{ transform: `scale(${zoom})` }}>
                  <svg className="tree-lines" viewBox="0 0 1840 930" aria-hidden="true">
                    {scenes.map((scene) => <path key={scene.number} d={`M300 485 C360 485 360 ${scene.y + 60} 420 ${scene.y + 60}`} />)}
                    {variants.map((variant) => <path key={variant.label} d={`M640 130 C700 130 700 ${variant.y + 50} 760 ${variant.y + 50}`} />)}
                    <path d="M640 130 C700 130 700 470 760 470" />
                    {refinements.map((variant) => <path key={variant.label} d={`M970 75 C1030 75 1030 ${variant.y + 50} 1090 ${variant.y + 50}`} />)}
                    <path d="M970 75 C1030 75 1030 470 1090 470" />
                    <path d="M1300 75 C1370 75 1370 160 1430 160" />
                  </svg>

                  <button className="tree-node root-node" type="button" onClick={() => setSelectedNode({ eyebrow: "Source prompt", title: promptTitle, description: "The product-demo direction that anchors every scene and branch." })}>
                    <span className="node-eyebrow">Source prompt</span><strong>{promptTitle}</strong><small>{assetCount > 0 ? `${assetCount} source assets attached` : "No source assets attached"}</small>
                  </button>

                  {scenes.map((scene, index) => (
                    <button
                      className={`tree-node scene-node ${index === 0 ? "expanded-node" : ""}`}
                      style={{ left: 420, top: scene.y }}
                      type="button"
                      key={scene.number}
                      onClick={() => setSelectedNode({ eyebrow: `Scene ${scene.number}`, title: scene.title, description: scene.note, branches: "50 first-pass branches" })}
                    >
                      <Preview kind={scene.preview} />
                      <span className="node-body"><span className="node-eyebrow">Scene {scene.number}</span><strong>{scene.title}</strong><small>{scene.note}</small></span>
                      <span className="branch-count">50</span>
                    </button>
                  ))}

                  {variants.map((variant) => (
                    <button className="tree-node variant-node" style={{ left: 760, top: variant.y }} type="button" key={variant.label} onClick={() => setSelectedNode({ eyebrow: `Hook variant ${variant.label}`, title: variant.title, description: "A visual direction within Scene 01. This is a front-end concept, not a tested result.", branches: "50 refinement branches" })}>
                      <Preview kind={variant.preview} /><span className="node-body"><span className="node-eyebrow">Variant {variant.label}</span><strong>{variant.title}</strong><small>Concept preview</small></span>
                    </button>
                  ))}
                  <button className="tree-node collapsed-node" style={{ left: 760, top: 420 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Collapsed branches", title: "47 more hook variants", description: "The canvas compresses large generations into expandable branch groups.", branches: "47 branches" })}><span className="stack-glyph"><i /><i /><i /></span><strong>+47 variants</strong><small>Expand branch group</small></button>

                  {refinements.map((variant) => (
                    <button className="tree-node refinement-node" style={{ left: 1090, top: variant.y }} type="button" key={variant.label} onClick={() => setSelectedNode({ eyebrow: `Refinement ${variant.label}`, title: variant.title, description: "A second-generation direction branching from Hook A.", branches: "50 next-pass branches" })}>
                      <Preview kind={variant.preview} /><span className="node-body"><span className="node-eyebrow">Refinement {variant.label}</span><strong>{variant.title}</strong><small>Generation 02</small></span>
                    </button>
                  ))}
                  <button className="tree-node collapsed-node" style={{ left: 1090, top: 420 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Collapsed branches", title: "47 more refinements", description: "More second-generation concepts are grouped here.", branches: "47 branches" })}><span className="stack-glyph"><i /><i /><i /></span><strong>+47 refinements</strong><small>Generation 02</small></button>

                  <button className="tree-node generation-node" style={{ left: 1430, top: 105 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Generation 03", title: "50 next-pass directions", description: "Each selected refinement can open another set of visual directions.", branches: "50 branches" })}><span className="generation-orbit"><i /><i /><i /></span><span><span className="node-eyebrow">Generation 03</span><strong>50 next-pass directions</strong><small>Continue branching</small></span></button>

                  <div className="lane-label" style={{ left: 420 }}>Scenes</div>
                  <div className="lane-label" style={{ left: 760 }}>Hook branches</div>
                  <div className="lane-label" style={{ left: 1090 }}>Refinements</div>
                  <div className="lane-label" style={{ left: 1430 }}>Next generation</div>
                </div>
              </div>
            </div>

            <form className="canvas-composer" onSubmit={(event) => event.preventDefault()}>
              <button className="composer-attach" type="button" aria-label="Attach assets"><PaperclipIcon /></button>
              <input aria-label="Add a direction" placeholder="Add a direction or ask for another branch…" />
              <button className="canvas-send" type="submit" aria-label="Send direction"><SendIcon /></button>
            </form>

            <div className="canvas-minimap" aria-hidden="true"><i className="mini-root" />{scenes.map((scene) => <i className="mini-scene" style={{ top: 10 + Number(scene.number) * 9 }} key={scene.number} />)}<span /></div>

            {selectedNode && (
              <aside className="node-inspector">
                <button className="inspector-close" type="button" onClick={() => setSelectedNode(null)} aria-label="Close inspector">×</button>
                <span className="section-label">{selectedNode.eyebrow}</span>
                <h2>{selectedNode.title}</h2>
                <p>{selectedNode.description}</p>
                {selectedNode.branches && <div className="inspector-row"><span>Branch group</span><strong>{selectedNode.branches}</strong></div>}
                <div className="inspector-row"><span>Simulation</span><strong>Not run</strong></div>
                <div className="inspector-note">Prototype view only. Brain simulation and scoring will connect later.</div>
              </aside>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
