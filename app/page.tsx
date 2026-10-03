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

const hookVariants = [
  { label: "01", title: "Start with the blank canvas", preview: "variant-a", y: 70 },
  { label: "02", title: "Open on the finished launch", preview: "variant-b", y: 220 },
  { label: "03", title: "Lead with a founder question", preview: "variant-c", y: 370 },
];

const continuations = [
  { suffix: "01", title: "The brief arrives", preview: "refine-a", y: 55 },
  { suffix: "02", title: "Ideas begin to branch", preview: "refine-b", y: 205 },
  { suffix: "03", title: "A direction takes shape", preview: "refine-c", y: 355 },
];

const nextBeats = [
  { suffix: "01", title: "Turn the idea into motion", preview: "variant-b", y: 55 },
  { suffix: "02", title: "Reveal the first output", preview: "variant-a", y: 205 },
  { suffix: "03", title: "Compare the directions", preview: "variant-c", y: 355 },
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
  const [selectedHook, setSelectedHook] = useState("01");
  const [selectedContinuation, setSelectedContinuation] = useState("01");
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
    setSelectedHook("01");
    setSelectedContinuation("01");
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
              <span><strong>{promptTitle}</strong><small>Recursive story tree</small></span>
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
              <div className="prompt-notes"><span>50 opening hooks</span><i /><span>50 continuations each</span><i /><span>No simulation yet</span></div>
            </section>

            {isGenerating && (
              <div className="generating-overlay" role="status">
                <div className="generating-card"><span className="loading-mark" /><strong>Generating the first 50 hooks</strong><small>Starting one storyline with many possible openings…</small></div>
              </div>
            )}
          </div>
        ) : (
          <div className="canvas-workspace">
            <div className="canvas-toolbar">
              <div><strong>Story tree</strong><span>One evolving storyline · 50 branches at every step</span></div>
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
              <div className="tree-scale" style={{ width: 1900 * zoom, height: 850 * zoom }}>
                <div className="tree-stage" style={{ transform: `scale(${zoom})` }}>
                  <svg className="tree-lines" viewBox="0 0 1900 850" aria-hidden="true">
                    {hookVariants.map((hook) => <path key={hook.label} d={`M300 475 C350 475 350 ${hook.y + 52} 400 ${hook.y + 52}`} />)}
                    <path d="M300 475 C350 475 350 572 400 572" />
                    {continuations.map((continuation) => (
                      <path className="active-branch-line" key={continuation.suffix} d={`M630 ${hookVariants.find((hook) => hook.label === selectedHook)!.y + 52} C705 ${hookVariants.find((hook) => hook.label === selectedHook)!.y + 52} 705 ${continuation.y + 50} 780 ${continuation.y + 50}`} />
                    ))}
                    <path className="active-branch-line" d={`M630 ${hookVariants.find((hook) => hook.label === selectedHook)!.y + 52} C705 ${hookVariants.find((hook) => hook.label === selectedHook)!.y + 52} 705 557 780 557`} />
                    {nextBeats.map((beat) => (
                      <path className="active-branch-line" key={beat.suffix} d={`M1000 ${continuations.find((continuation) => continuation.suffix === selectedContinuation)!.y + 50} C1070 ${continuations.find((continuation) => continuation.suffix === selectedContinuation)!.y + 50} 1070 ${beat.y + 50} 1140 ${beat.y + 50}`} />
                    ))}
                    <path className="active-branch-line" d={`M1000 ${continuations.find((continuation) => continuation.suffix === selectedContinuation)!.y + 50} C1070 ${continuations.find((continuation) => continuation.suffix === selectedContinuation)!.y + 50} 1070 557 1140 557`} />
                    <path className="active-branch-line" d="M1360 105 C1430 105 1430 155 1500 155" />
                  </svg>

                  <button className="tree-node root-node" type="button" onClick={() => setSelectedNode({ eyebrow: "Source prompt", title: promptTitle, description: "The starting idea for one product-demo storyline." })}>
                    <span className="node-eyebrow">Source prompt</span><strong>{promptTitle}</strong><small>{assetCount > 0 ? `${assetCount} source assets attached` : "No source assets attached"}</small>
                  </button>

                  {hookVariants.map((hook) => (
                    <button
                      className={`tree-node path-node ${selectedHook === hook.label ? "selected-path-node" : ""}`}
                      style={{ left: 400, top: hook.y }}
                      type="button"
                      key={hook.label}
                      onClick={() => {
                        setSelectedHook(hook.label);
                        setSelectedContinuation("01");
                        setSelectedNode({ eyebrow: `Hook ${hook.label} of 50`, title: hook.title, description: "A possible opening for the same storyline. Selecting it reveals 50 ways the story could continue.", branches: "50 continuations" });
                      }}
                    >
                      <Preview kind={hook.preview} />
                      <span className="node-body"><span className="node-eyebrow">Hook {hook.label}</span><strong>{hook.title}</strong><small>{selectedHook === hook.label ? "Story path open" : "Select to continue"}</small></span>
                      <span className="branch-count">50</span>
                    </button>
                  ))}
                  <button className="tree-node collapsed-node" style={{ left: 400, top: 520 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Hook generation", title: "47 more opening hooks", description: "The remaining hook concepts are compressed into this expandable branch group.", branches: "47 hooks" })}><span className="stack-glyph"><i /><i /><i /></span><strong>+47 hooks</strong><small>Generation 01</small></button>

                  {continuations.map((continuation) => (
                    <button
                      className={`tree-node continuation-node ${selectedContinuation === continuation.suffix ? "selected-path-node" : ""}`}
                      style={{ left: 780, top: continuation.y }}
                      type="button"
                      key={continuation.suffix}
                      onClick={() => {
                        setSelectedContinuation(continuation.suffix);
                        setSelectedNode({ eyebrow: `Beat ${selectedHook}.${continuation.suffix}`, title: continuation.title, description: `One of 50 ways to continue from Hook ${selectedHook}. Selecting it opens the next generation of the storyline.`, branches: "50 next story beats" });
                      }}
                    >
                      <Preview kind={continuation.preview} /><span className="node-body"><span className="node-eyebrow">Beat {selectedHook}.{continuation.suffix}</span><strong>{continuation.title}</strong><small>{selectedContinuation === continuation.suffix ? "Story path open" : "Select to continue"}</small></span><span className="branch-count">50</span>
                    </button>
                  ))}
                  <button className="tree-node collapsed-node" style={{ left: 780, top: 505 }} type="button" onClick={() => setSelectedNode({ eyebrow: `Hook ${selectedHook} continuations`, title: "47 more ways to continue", description: `The remaining continuations generated from Hook ${selectedHook} are grouped here.`, branches: "47 continuations" })}><span className="stack-glyph"><i /><i /><i /></span><strong>+47 continuations</strong><small>Generation 02</small></button>

                  {nextBeats.map((beat) => (
                    <button className="tree-node continuation-node" style={{ left: 1140, top: beat.y }} type="button" key={beat.suffix} onClick={() => setSelectedNode({ eyebrow: `Beat ${selectedHook}.${selectedContinuation}.${beat.suffix}`, title: beat.title, description: `A third-generation story beat continuing from ${selectedHook}.${selectedContinuation}. This is an untested visual concept.`, branches: "50 deeper continuations" })}>
                      <Preview kind={beat.preview} /><span className="node-body"><span className="node-eyebrow">Beat {selectedHook}.{selectedContinuation}.{beat.suffix}</span><strong>{beat.title}</strong><small>Generation 03</small></span><span className="branch-count">50</span>
                    </button>
                  ))}
                  <button className="tree-node collapsed-node" style={{ left: 1140, top: 505 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Generation 03", title: "47 more story beats", description: "The storyline can continue recursively from every beat.", branches: "47 continuations" })}><span className="stack-glyph"><i /><i /><i /></span><strong>+47 next beats</strong><small>Generation 03</small></button>

                  <button className="tree-node generation-node" style={{ left: 1500, top: 100 }} type="button" onClick={() => setSelectedNode({ eyebrow: "Generation 04+", title: "The storyline keeps expanding", description: "Every story beat can open another set of 50 possible continuations.", branches: "50 branches per beat" })}><span className="generation-orbit"><i /><i /><i /></span><span><span className="node-eyebrow">Generation 04+</span><strong>50 ways forward</strong><small>Continue this storyline</small></span></button>

                  <div className="lane-label" style={{ left: 60 }}>Idea</div>
                  <div className="lane-label" style={{ left: 400 }}>50 hooks</div>
                  <div className="lane-label" style={{ left: 780 }}>50 continuations from hook {selectedHook}</div>
                  <div className="lane-label" style={{ left: 1140 }}>50 next beats from {selectedHook}.{selectedContinuation}</div>
                  <div className="lane-label" style={{ left: 1500 }}>Keeps branching</div>
                </div>
              </div>
            </div>

            <form className="canvas-composer" onSubmit={(event) => event.preventDefault()}>
              <button className="composer-attach" type="button" aria-label="Attach assets"><PaperclipIcon /></button>
              <input aria-label="Add a direction" placeholder="Add a direction or ask for another branch…" />
              <button className="canvas-send" type="submit" aria-label="Send direction"><SendIcon /></button>
            </form>

            <div className="canvas-minimap" aria-hidden="true"><i className="mini-root" />{hookVariants.map((hook) => <i className="mini-scene" style={{ top: 15 + Number(hook.label) * 10 }} key={hook.label} />)}<i className="mini-generation mini-generation-two" /><i className="mini-generation mini-generation-three" /><span /></div>

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
