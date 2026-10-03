"use client";

import type { FunctionCall } from "@google/genai";
import { FormEvent, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import { briefSchema, emptyBrief, goals, type BriefDraft, type BriefField, type SourceMap } from "@/lib/brief";
import { useLiveDirector } from "@/hooks/use-live-director";

type LocalAsset = {
  id: string;
  name: string;
  relativePath: string;
  file: File;
  previewUrl: string;
};

type Scene = {
  assetId?: string;
  rationale?: string;
};

type Decision = {
  id: string;
  choice: string;
  rationale: string;
  status: "recommended" | "rejected" | "overridden";
};

const fieldLabels: Record<BriefField, string> = {
  product_name: "Product",
  one_liner: "One-line truth",
  goal: "Launch goal",
  goal_note: "Goal detail",
  audience: "Audience",
};

const statusCopy = {
  idle: "Director offline",
  requesting: "Waiting for microphone",
  connecting: "Opening live channel",
  listening: "Listening — interrupt anytime",
  error: "Connection needs attention",
};

function normalizeGoal(value: string): BriefDraft["goal"] | null {
  const compact = value.toLowerCase().replace(/[\s_-]+/g, "");
  if (compact.includes("signup")) return "signups";
  if (compact.includes("download")) return "downloads";
  if (compact.includes("understand") || compact.includes("awareness")) return "understand";
  if (compact.includes("purchase") || compact.includes("buy") || compact.includes("sale")) return "purchase";
  return goals.includes(value as BriefDraft["goal"]) ? (value as BriefDraft["goal"]) : null;
}

function asString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

export function DirectorStudio() {
  const reactId = useId();
  const projectId = useMemo(() => `project-${reactId.replace(/[^a-zA-Z0-9_-]/g, "") || "draft"}`, [reactId]);
  const [brief, setBrief] = useState<BriefDraft>(() => emptyBrief(projectId));
  const [sources, setSources] = useState<SourceMap>({});
  const [assets, setAssets] = useState<LocalAsset[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [assetQuery, setAssetQuery] = useState("");
  const [scenes, setScenes] = useState<Scene[]>(() => Array.from({ length: 6 }, () => ({})));
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [message, setMessage] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const assetsRef = useRef(assets);
  const selectedRef = useRef(selectedIds);
  const shareAssetRef = useRef<((file: File, label: string, requestResponse?: boolean) => Promise<boolean>) | null>(null);

  useEffect(() => {
    folderInputRef.current?.setAttribute("webkitdirectory", "");
    folderInputRef.current?.setAttribute("directory", "");
  }, []);

  useEffect(() => {
    assetsRef.current = assets;
  }, [assets]);

  useEffect(() => {
    selectedRef.current = selectedIds;
  }, [selectedIds]);

  useEffect(
    () => () => {
      for (const asset of assetsRef.current) URL.revokeObjectURL(asset.previewUrl);
    },
    [],
  );

  const updateField = useCallback((field: BriefField, rawValue: string, source: "voice" | "typed") => {
    const value = field === "goal" ? normalizeGoal(rawValue) : rawValue.trim();
    if (value === null) throw new Error("Goal must be signups, downloads, understanding, or purchase.");
    if (field === "one_liner" && value.length > 140) throw new Error("The one-line description must be 140 characters or fewer.");
    setBrief((current) => ({ ...current, [field]: value }));
    setSources((current) => ({ ...current, [field]: source }));
    return value;
  }, []);

  const handleToolCall = useCallback(
    async (call: FunctionCall): Promise<Record<string, unknown>> => {
      const args = call.args ?? {};
      switch (call.name) {
        case "update_brief": {
          const field = asString(args.field) as BriefField;
          if (!(field in fieldLabels)) throw new Error("Unknown brief field.");
          const value = updateField(field, asString(args.value), "voice");
          return { updated: field, value, source: "voice" };
        }
        case "search_assets": {
          const query = asString(args.query).toLowerCase();
          setAssetQuery(query);
          const matches = assetsRef.current
            .filter((asset) => !query || `${asset.name} ${asset.relativePath}`.toLowerCase().includes(query))
            .slice(0, 12)
            .map(({ id, name, relativePath }) => ({ id, name, relativePath }));
          return matches.length
            ? { matches, note: "Only filenames and approved relative paths were searched." }
            : { matches: [], note: "No approved image filenames matched. Ask the user to choose a folder or another term." };
        }
        case "select_asset": {
          const assetId = asString(args.asset_id);
          const asset = assetsRef.current.find((candidate) => candidate.id === assetId);
          if (!asset) throw new Error("That asset is not in the approved folder.");
          if (!selectedRef.current.includes(assetId)) {
            if (selectedRef.current.length >= 6) throw new Error("The brief already has six screenshots.");
            setSelectedIds((current) => [...current, assetId]);
            setScenes((current) => {
              const next = [...current];
              const emptyIndex = next.findIndex((scene) => !scene.assetId);
              if (emptyIndex >= 0) next[emptyIndex] = { assetId, rationale: "Selected during Director session" };
              return next;
            });
          }
          queueMicrotask(() => void shareAssetRef.current?.(asset.file, asset.name, false));
          return { selected: { id: asset.id, name: asset.name }, count: selectedRef.current.length + 1 };
        }
        case "set_scene": {
          const scene = Number(args.scene);
          const assetId = asString(args.asset_id);
          const rationale = asString(args.rationale);
          if (!Number.isInteger(scene) || scene < 1 || scene > 6) throw new Error("Scene must be between 1 and 6.");
          if (!selectedRef.current.includes(assetId)) throw new Error("Select the asset before placing it in the storyboard.");
          setScenes((current) => current.map((item, index) => (index === scene - 1 ? { assetId, rationale } : item)));
          return { scene, assetId, rationale };
        }
        case "record_decision": {
          const status = asString(args.status) as Decision["status"];
          if (!(["recommended", "rejected", "overridden"] as const).includes(status)) throw new Error("Invalid decision status.");
          const decision = {
            id: crypto.randomUUID(),
            choice: asString(args.choice),
            rationale: asString(args.rationale),
            status,
          };
          setDecisions((current) => [decision, ...current].slice(0, 12));
          return { recorded: decision };
        }
        default:
          throw new Error("Unknown Director tool.");
      }
    },
    [updateField],
  );

  const director = useLiveDirector({ onToolCall: handleToolCall });

  useEffect(() => {
    shareAssetRef.current = director.shareAsset;
  }, [director.shareAsset]);

  const visibleAssets = useMemo(() => {
    const query = assetQuery.toLowerCase().trim();
    return assets
      .filter((asset) => !query || `${asset.name} ${asset.relativePath}`.toLowerCase().includes(query))
      .slice(0, 24);
  }, [assetQuery, assets]);

  const readiness = useMemo(
    () => ({
      product: Boolean(brief.product_name),
      truth: Boolean(brief.one_liner && brief.one_liner.length <= 140),
      audience: Boolean(brief.audience),
      goal: Boolean(sources.goal),
      screens: selectedIds.length >= 3 && selectedIds.length <= 6,
    }),
    [brief, selectedIds.length, sources.goal],
  );
  const isReady = Object.values(readiness).every(Boolean);

  const loadFolder = useCallback((files: FileList | null) => {
    if (!files) return;
    for (const asset of assetsRef.current) URL.revokeObjectURL(asset.previewUrl);
    const images = Array.from(files)
      .filter((file) => file.type === "image/png" || file.type === "image/jpeg")
      .slice(0, 100)
      .map((file) => ({
        id: crypto.randomUUID(),
        name: file.name,
        relativePath: file.webkitRelativePath || file.name,
        file,
        previewUrl: URL.createObjectURL(file),
      }));
    setAssets(images);
    setSelectedIds([]);
    setScenes(Array.from({ length: 6 }, () => ({})));
    setAssetQuery("");
  }, []);

  const toggleAsset = useCallback(
    (asset: LocalAsset) => {
      const isSelected = selectedRef.current.includes(asset.id);
      if (isSelected) {
        setSelectedIds((current) => current.filter((id) => id !== asset.id));
        setScenes((current) => current.map((scene) => (scene.assetId === asset.id ? {} : scene)));
        return;
      }
      if (selectedRef.current.length >= 6) return;
      setSelectedIds((current) => [...current, asset.id]);
      setScenes((current) => {
        const next = [...current];
        const emptyIndex = next.findIndex((scene) => !scene.assetId);
        if (emptyIndex >= 0) next[emptyIndex] = { assetId: asset.id, rationale: "Chosen from approved product screens" };
        return next;
      });
      void director.shareAsset(asset.file, asset.name);
    },
    [director],
  );

  const submitText = useCallback(
    (event: FormEvent) => {
      event.preventDefault();
      if (director.sendText(message)) setMessage("");
    },
    [director, message],
  );

  const runPreflight = useCallback(async () => {
    if (!isReady || saveState === "saving") return;
    setSaveState("saving");
    setSaveError(null);
    try {
      const selectedAssets = selectedIds.map((id) => assets.find((asset) => asset.id === id)).filter(Boolean) as LocalAsset[];
      const form = new FormData();
      for (const asset of selectedAssets) form.append("files", asset.file, asset.name);
      const uploadResponse = await fetch(`/api/projects/${projectId}/assets`, { method: "POST", body: form });
      const uploadPayload = (await uploadResponse.json()) as {
        assets?: Array<{ storedPath: string }>;
        error?: string;
      };
      if (!uploadResponse.ok || !uploadPayload.assets) throw new Error(uploadPayload.error ?? "Unable to upload screenshots.");

      const finalBrief = briefSchema.parse({
        ...brief,
        project_id: projectId,
        screenshots: uploadPayload.assets.map((asset) => asset.storedPath),
      });
      const briefResponse = await fetch(`/api/projects/${projectId}/brief`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finalBrief),
      });
      const briefPayload = (await briefResponse.json()) as { error?: string };
      if (!briefResponse.ok) throw new Error(briefPayload.error ?? "Unable to save brief.");
      setBrief(finalBrief);
      setSaveState("saved");
      director.sendText("The brief is now locked. State clearly that planning, rendering, and simulation are not connected in this build yet.");
    } catch (runError) {
      setSaveError(runError instanceof Error ? runError.message : "Unable to save the brief.");
      setSaveState("error");
    }
  }, [assets, brief, director, isReady, projectId, saveState, selectedIds]);

  const orbStyle = { "--signal": director.inputLevel.toFixed(3) } as React.CSSProperties;

  return (
    <main className="studio-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">P</span>
          <div><strong>Preflight</strong><span>Director</span></div>
        </div>
        <div className="session-status"><span className={`status-dot ${director.state}`} />{statusCopy[director.state]}</div>
        <div className="truth-label">Creative rationale · no simulation yet</div>
      </header>

      <section className="hero-grid">
        <div className="director-panel glass-panel">
          <div className="panel-kicker">Live creative session</div>
          <div className={`signal-stage ${director.state}`} style={orbStyle}>
            <div className="signal-orbit orbit-one" />
            <div className="signal-orbit orbit-two" />
            <div className="signal-core"><span>{director.state === "listening" ? "LIVE" : "PREFLIGHT"}</span></div>
            <div className="signal-bars" aria-hidden="true">
              {Array.from({ length: 18 }, (_, index) => <i key={index} style={{ "--bar": index } as React.CSSProperties} />)}
            </div>
          </div>
          <h1>Build the story.<br /><span>Defend every frame.</span></h1>
          <p className="hero-copy">Talk through the launch video with an opinionated Director that can inspect only the screens you approve.</p>
          <div className="director-actions">
            {director.state === "idle" || director.state === "error" ? (
              <button className="primary-action" onClick={() => void director.start()}>
                <span className="mic-icon" aria-hidden="true" /> Start Director
              </button>
            ) : (
              <button className="secondary-action" onClick={() => void director.stop()}>End session</button>
            )}
            <span className="permission-note">One click is required for microphone permission.</span>
          </div>
          {director.error && <div className="error-banner" role="alert">{director.error}</div>}

          <div className="transcript" aria-live="polite">
            {director.transcript.length === 0 && !director.liveUserText && !director.liveDirectorText ? (
              <p className="empty-copy">The live transcript and every Director decision will appear here.</p>
            ) : (
              <>
                {director.transcript.slice(-6).map((line) => (
                  <div className={`transcript-line ${line.role}`} key={line.id}>
                    <span>{line.role === "director" ? "Director" : "You"}</span><p>{line.text}</p>
                  </div>
                ))}
                {director.liveUserText && <div className="transcript-line user live"><span>You</span><p>{director.liveUserText}</p></div>}
                {director.liveDirectorText && <div className="transcript-line director live"><span>Director</span><p>{director.liveDirectorText}</p></div>}
              </>
            )}
          </div>
          <form className="message-box" onSubmit={submitText}>
            <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Type to the Director…" disabled={director.state !== "listening"} />
            <button type="submit" disabled={director.state !== "listening" || !message.trim()} aria-label="Send message">↗</button>
          </form>
        </div>

        <div className="workspace-column">
          <section className="glass-panel brief-panel">
            <div className="panel-heading"><div><span className="step-number">01</span><div><h2>Launch brief</h2><p>Confirmed facts only</p></div></div><span className="completion-count">{Object.values(readiness).filter(Boolean).length}/5 ready</span></div>
            <div className="brief-fields">
              <label>Product name <span className={`source-chip ${sources.product_name ?? "empty"}`}>{sources.product_name ?? "missing"}</span>
                <input value={brief.product_name} onChange={(event) => updateField("product_name", event.target.value, "typed")} placeholder="What are you launching?" />
              </label>
              <label className="wide-field">One-line truth <span className={`source-chip ${sources.one_liner ?? "empty"}`}>{sources.one_liner ?? "missing"}</span>
                <input value={brief.one_liner} maxLength={140} onChange={(event) => updateField("one_liner", event.target.value, "typed")} placeholder="Describe only what the product actually does" />
                <small>{brief.one_liner.length}/140</small>
              </label>
              <label>Goal <span className={`source-chip ${sources.goal ?? "typed"}`}>{sources.goal ?? "default"}</span>
                <select value={brief.goal} onChange={(event) => updateField("goal", event.target.value, "typed")}>
                  <option value="signups">Sign ups</option><option value="downloads">Downloads</option><option value="understand">Understand product</option><option value="purchase">Purchase</option>
                </select>
              </label>
              <label>Audience <span className={`source-chip ${sources.audience ?? "empty"}`}>{sources.audience ?? "missing"}</span>
                <input value={brief.audience} onChange={(event) => updateField("audience", event.target.value, "typed")} placeholder="Who should understand this?" />
              </label>
            </div>
          </section>

          <section className="glass-panel assets-panel">
            <div className="panel-heading"><div><span className="step-number">02</span><div><h2>Approved screens</h2><p>{assets.length ? `${assets.length} images indexed locally` : "Choose a product folder"}</p></div></div><span className={`completion-count ${readiness.screens ? "complete" : ""}`}>{selectedIds.length}/3–6 selected</span></div>
            <div className="asset-toolbar">
              <button className="folder-button" onClick={() => folderInputRef.current?.click()}>Choose folder</button>
              <input ref={folderInputRef} type="file" accept="image/png,image/jpeg" multiple hidden onChange={(event) => loadFolder(event.target.files)} />
              <input className="asset-search" value={assetQuery} onChange={(event) => setAssetQuery(event.target.value)} placeholder="Search approved filenames" />
            </div>
            {assets.length === 0 ? (
              <button className="folder-drop" onClick={() => folderInputRef.current?.click()}>
                <span className="folder-glyph" aria-hidden="true" />
                <strong>Grant access to one product folder</strong>
                <small>Preflight indexes PNG and JPG filenames locally. Nothing uploads until you select Run Preflight.</small>
              </button>
            ) : (
              <div className="asset-grid">
                {visibleAssets.map((asset) => {
                  const selectedIndex = selectedIds.indexOf(asset.id);
                  return <button className={`asset-card ${selectedIndex >= 0 ? "selected" : ""}`} key={asset.id} onClick={() => toggleAsset(asset)}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={asset.previewUrl} alt={asset.name} />
                    <span>{asset.name}</span>{selectedIndex >= 0 && <b>{selectedIndex + 1}</b>}
                  </button>;
                })}
              </div>
            )}
          </section>
        </div>
      </section>

      <section className="lower-grid">
        <div className="glass-panel storyboard-panel">
          <div className="panel-heading"><div><span className="step-number">03</span><div><h2>15-second spine</h2><p>Six equal scene slots · draft only</p></div></div><span className="evidence-badge">Creative rationale</span></div>
          <div className="storyboard-track">
            {scenes.map((scene, index) => {
              const asset = assets.find((candidate) => candidate.id === scene.assetId);
              return <div className={`scene-slot ${asset ? "filled" : ""}`} key={index}>
                <div className="scene-time">{(index * 2.5).toFixed(1)}–{((index + 1) * 2.5).toFixed(1)}s</div>
                {asset ? <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={asset.previewUrl} alt="" />
                  <strong>{asset.name}</strong><p>{scene.rationale}</p>
                </> : <span>Scene {index + 1}</span>}
              </div>;
            })}
          </div>
        </div>

        <aside className="glass-panel decisions-panel">
          <div className="panel-heading"><div><span className="step-number">04</span><div><h2>Decision thread</h2><p>Pushback stays inspectable</p></div></div></div>
          <div className="decision-list">
            {decisions.length === 0 ? <p className="empty-copy">Recommendations, rejections, and overrides will be recorded here.</p> : decisions.map((decision) => <article key={decision.id} className={decision.status}><span>{decision.status}</span><strong>{decision.choice}</strong><p>{decision.rationale}</p></article>)}
          </div>
        </aside>
      </section>

      <footer className="run-dock">
        <div className="readiness-list">
          {Object.entries(readiness).map(([name, ready]) => <span className={ready ? "ready" : ""} key={name}><i />{name}</span>)}
        </div>
        <div className="run-message">
          {saveState === "saved" ? <><strong>Brief locked</strong><span>Planning, rendering, and simulation are not connected yet.</span></> : <><strong>{isReady ? "Ready to lock the brief" : "Complete the preflight checks"}</strong><span>{saveError ?? "Only selected screenshots will be uploaded."}</span></>}
        </div>
        <button className="run-button" disabled={!isReady || saveState === "saving" || saveState === "saved"} onClick={() => void runPreflight()}>{saveState === "saving" ? "Saving…" : saveState === "saved" ? "Brief saved" : "Run Preflight"}</button>
      </footer>
    </main>
  );
}
