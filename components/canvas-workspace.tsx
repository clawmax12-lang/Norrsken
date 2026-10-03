"use client";

import type { FunctionCall } from "@google/genai";
import { FormEvent, PointerEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ThinkingOrb, type OrbState } from "thinking-orbs";
import { VoiceBeam } from "voice-glow";

import { useLiveDirector } from "@/hooks/use-live-director";
import { briefSchema, emptyBrief, type BriefDraft, type BriefField, type SourceMap } from "@/lib/brief";
import {
  canvasDraftSchema,
  createCanvasDraft,
  reorderScenes,
  replaceScene,
  sourceFields,
  type CanvasDraft,
  type SourceField,
  type VariantId,
  variantIds,
} from "@/lib/canvas-draft";

type LocalAsset = {
  id: string;
  name: string;
  relativePath: string;
  file: File;
  previewUrl: string;
};

type Notice = { id: string; role: "user" | "director" | "system"; text: string };
type JobState = "draft" | "saving" | "queued" | "unavailable" | "error";

const PROJECT_ID = "launch-draft";
const BRIEF_STORAGE = `preflight:${PROJECT_ID}:brief`;
const DRAFT_STORAGE = `preflight:${PROJECT_ID}:canvas`;

const fieldLabels: Record<BriefField, string> = {
  product_name: "Product",
  one_liner: "Description",
  goal: "Goal",
  goal_note: "Goal detail",
  audience: "Audience",
};

const sourceLabel: Record<SourceField, string> = {
  product_name: "product name",
  one_liner: "description",
  goal: "goal",
  goal_note: "goal detail",
  audience: "audience",
};

function cleanString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeGoal(value: string): BriefDraft["goal"] | null {
  const normalized = value.toLowerCase().replace(/[\s_-]+/g, "");
  if (normalized.includes("signup")) return "signups";
  if (normalized.includes("download")) return "downloads";
  if (normalized.includes("understand") || normalized.includes("awareness")) return "understand";
  if (normalized.includes("purchase") || normalized.includes("buy")) return "purchase";
  return null;
}

function valueForSource(brief: BriefDraft, field: SourceField) {
  return String(brief[field] ?? "").trim();
}

function isGroundedCopy(text: string, source: string) {
  const normalize = (value: string) => value.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  const candidate = normalize(text);
  const evidence = normalize(source);
  if (!candidate || !evidence) return false;
  if (evidence.includes(candidate)) return true;
  const evidenceWords = new Set(evidence.split(" "));
  return candidate.split(" ").filter((word) => word.length > 2).every((word) => evidenceWords.has(word));
}

function touchDraft(draft: CanvasDraft) {
  return canvasDraftSchema.parse({ ...draft, revision: draft.revision + 1, updated_at: new Date().toISOString() });
}

function readStored<T>(key: string, parse: (value: unknown) => T): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? parse(JSON.parse(raw)) : null;
  } catch {
    return null;
  }
}

export function CanvasWorkspace() {
  const [brief, setBrief] = useState<BriefDraft>(() => emptyBrief(PROJECT_ID));
  const [sources, setSources] = useState<SourceMap>({});
  const [draft, setDraft] = useState<CanvasDraft>(() => createCanvasDraft(PROJECT_ID));
  const [assets, setAssets] = useState<LocalAsset[]>([]);
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [assetQuery, setAssetQuery] = useState("");
  const [composerText, setComposerText] = useState("");
  const [notices, setNotices] = useState<Notice[]>([]);
  const [draftState, setDraftState] = useState<"saved" | "saving" | "error">("saved");
  const [jobState, setJobState] = useState<JobState>("draft");
  const [jobMessage, setJobMessage] = useState("Draft only · no render or simulation has run");
  const [showBrief, setShowBrief] = useState(false);
  const [showAssets, setShowAssets] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [confirmSummary, setConfirmSummary] = useState<string | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, zoom: 0.82 });
  const [dragging, setDragging] = useState(false);

  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const dragRef = useRef({ x: 0, y: 0, viewX: 0, viewY: 0, moved: false });
  const assetsRef = useRef(assets);
  const selectedAssetsRef = useRef(selectedAssetIds);
  const draftRef = useRef(draft);
  const briefRef = useRef(brief);
  const shareAssetRef = useRef<((file: File, label: string, requestResponse?: boolean) => Promise<boolean>) | null>(null);

  useEffect(() => {
    folderInputRef.current?.setAttribute("webkitdirectory", "");
    folderInputRef.current?.setAttribute("directory", "");
  }, []);

  useEffect(() => { assetsRef.current = assets; }, [assets]);
  useEffect(() => { selectedAssetsRef.current = selectedAssetIds; }, [selectedAssetIds]);
  useEffect(() => { draftRef.current = draft; }, [draft]);
  useEffect(() => { briefRef.current = brief; }, [brief]);

  useEffect(() => {
    const storedBrief = readStored(BRIEF_STORAGE, (value) => {
      const record = value as { brief?: BriefDraft; sources?: SourceMap };
      return { brief: { ...emptyBrief(PROJECT_ID), ...record.brief, project_id: PROJECT_ID }, sources: record.sources ?? {} };
    });
    const storedDraft = readStored(DRAFT_STORAGE, (value) => canvasDraftSchema.parse(value));
    queueMicrotask(() => {
      if (storedBrief) {
        setBrief(storedBrief.brief);
        setSources(storedBrief.sources);
      }
      if (storedDraft) setDraft(storedDraft);
    });

    void fetch(`/api/projects/${PROJECT_ID}/draft`, { cache: "no-store" })
      .then(async (response) => response.ok ? canvasDraftSchema.parse(await response.json()) : null)
      .then((serverDraft) => {
        if (serverDraft && serverDraft.revision > (storedDraft?.revision ?? -1)) setDraft(serverDraft);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => () => {
    for (const asset of assetsRef.current) URL.revokeObjectURL(asset.previewUrl);
  }, []);

  const addNotice = useCallback((role: Notice["role"], text: string) => {
    setNotices((current) => [...current, { id: crypto.randomUUID(), role, text }].slice(-16));
  }, []);

  const persistDraft = useCallback(async (next: CanvasDraft) => {
    setDraft(next);
    draftRef.current = next;
    localStorage.setItem(DRAFT_STORAGE, JSON.stringify(next));
    setDraftState("saving");
    try {
      const response = await fetch(`/api/projects/${PROJECT_ID}/draft`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      });
      if (response.status === 409) {
        const currentResponse = await fetch(`/api/projects/${PROJECT_ID}/draft`, { cache: "no-store" });
        if (currentResponse.ok) {
          const current = canvasDraftSchema.parse(await currentResponse.json());
          setDraft(current);
          draftRef.current = current;
          localStorage.setItem(DRAFT_STORAGE, JSON.stringify(current));
        }
        setDraftState("error");
        throw new Error("This edit used a stale draft revision. The latest saved draft has been restored.");
      }
      if (!response.ok) throw new Error("Draft validation failed.");
      setDraftState("saved");
    } catch (error) {
      setDraftState("error");
      if (error instanceof Error && error.message.includes("stale draft")) throw error;
    }
    return next;
  }, []);

  const updateField = useCallback((field: BriefField, rawValue: string, source: "voice" | "typed") => {
    const value = field === "goal" ? normalizeGoal(rawValue) : rawValue.trim();
    if (value === null) throw new Error("Goal must be signups, downloads, understanding, or purchase.");
    if (field === "one_liner" && value.length > 140) throw new Error("Description must be 140 characters or fewer.");
    const nextBrief = { ...briefRef.current, [field]: value } as BriefDraft;
    const nextSources = { ...sources, [field]: source };
    setBrief(nextBrief);
    setSources(nextSources);
    briefRef.current = nextBrief;
    localStorage.setItem(BRIEF_STORAGE, JSON.stringify({ brief: nextBrief, sources: nextSources }));
    return value;
  }, [sources]);

  const selectScene = useCallback(async (variantId: VariantId, sceneId: string) => {
    const concept = draftRef.current.concepts.find((item) => item.variant_id === variantId);
    if (!concept?.scenes.some((scene) => scene.id === sceneId)) throw new Error("That scene is not in this concept.");
    const next = touchDraft({ ...draftRef.current, selected_variant_id: variantId, selected_scene_id: sceneId });
    await persistDraft(next);
    return next;
  }, [persistDraft]);

  const editSceneCopy = useCallback(async (sceneId: string, text: string, sourceField: SourceField) => {
    const sourceValue = valueForSource(briefRef.current, sourceField);
    if (!sourceValue) throw new Error(`The ${sourceLabel[sourceField]} field is empty.`);
    if (!isGroundedCopy(text, sourceValue)) throw new Error(`Copy must use words from the confirmed ${sourceLabel[sourceField]}.`);
    const next = replaceScene(draftRef.current, sceneId, { text, source_field: sourceField });
    await persistDraft(next);
    addNotice("system", `Saved ${sceneId} from ${sourceLabel[sourceField]} · revision ${next.revision}`);
    return next;
  }, [addNotice, persistDraft]);

  const handleToolCall = useCallback(async (call: FunctionCall): Promise<Record<string, unknown>> => {
    const args = call.args ?? {};
    switch (call.name) {
      case "update_brief": {
        const field = cleanString(args.field) as BriefField;
        if (!(field in fieldLabels)) throw new Error("Unknown brief field.");
        return { field, value: updateField(field, cleanString(args.value), "voice"), source: "voice" };
      }
      case "search_assets": {
        const query = cleanString(args.query).toLowerCase();
        setAssetQuery(query);
        setShowAssets(true);
        return {
          matches: assetsRef.current.filter((asset) => `${asset.name} ${asset.relativePath}`.toLowerCase().includes(query)).slice(0, 12).map(({ id, name, relativePath }) => ({ id, name, relativePath })),
          scope: "user-approved folder only",
        };
      }
      case "inspect_asset": {
        const asset = assetsRef.current.find((item) => item.id === cleanString(args.asset_id));
        if (!asset) throw new Error("Asset is outside the approved folder or no longer available.");
        setShowAssets(true);
        await shareAssetRef.current?.(asset.file, asset.name, false);
        return { asset: { id: asset.id, name: asset.name, relativePath: asset.relativePath }, evidence: "approved local screenshot" };
      }
      case "select_asset": {
        const assetId = cleanString(args.asset_id);
        const asset = assetsRef.current.find((item) => item.id === assetId);
        if (!asset) throw new Error("Asset is outside the approved folder.");
        if (!selectedAssetsRef.current.includes(assetId)) {
          if (selectedAssetsRef.current.length >= 6) throw new Error("The project already has six selected screenshots.");
          const next = [...selectedAssetsRef.current, assetId];
          selectedAssetsRef.current = next;
          setSelectedAssetIds(next);
        }
        return { selected: { id: asset.id, name: asset.name }, selected_count: selectedAssetsRef.current.length };
      }
      case "select_scene": {
        const variantId = cleanString(args.variant_id) as VariantId;
        const sceneId = cleanString(args.scene_id);
        const next = await selectScene(variantId, sceneId);
        return { selected_variant_id: next.selected_variant_id, selected_scene_id: next.selected_scene_id, revision: next.revision };
      }
      case "edit_scene_copy": {
        const sceneId = cleanString(args.scene_id);
        const sourceField = cleanString(args.source_field) as SourceField;
        if (!sourceFields.includes(sourceField)) throw new Error("Copy source is invalid.");
        const next = await editSceneCopy(sceneId, cleanString(args.text), sourceField);
        return { saved: true, scene_id: sceneId, source_field: sourceField, revision: next.revision };
      }
      case "set_scene_asset": {
        const sceneId = cleanString(args.scene_id);
        const assetId = cleanString(args.asset_id);
        if (!selectedAssetsRef.current.includes(assetId)) throw new Error("Select the approved asset before placing it.");
        const next = replaceScene(draftRef.current, sceneId, { asset_id: assetId });
        await persistDraft(next);
        const rationale = cleanString(args.rationale);
        if (rationale) addNotice("system", `${sceneId}: ${rationale}`);
        return { saved: true, scene_id: sceneId, asset_id: assetId, revision: next.revision };
      }
      case "reorder_scene": {
        const next = reorderScenes(draftRef.current, cleanString(args.variant_id) as VariantId, Number(args.from), Number(args.to));
        await persistDraft(next);
        return { saved: true, revision: next.revision };
      }
      case "record_decision": {
        const status = cleanString(args.status) as "recommended" | "rejected" | "overridden";
        if (!["recommended", "rejected", "overridden"].includes(status)) throw new Error("Decision status is invalid.");
        const next = touchDraft({
          ...draftRef.current,
          decisions: [{ id: crypto.randomUUID(), choice: cleanString(args.choice), rationale: cleanString(args.rationale), status, created_at: new Date().toISOString() }, ...draftRef.current.decisions].slice(0, 30),
        });
        await persistDraft(next);
        return { recorded: true, revision: next.revision };
      }
      case "request_run_confirmation": {
        const summary = cleanString(args.summary) || "Generate and pretest exactly three 15-second concepts from this approved draft.";
        setConfirmSummary(summary);
        return { confirmation_required: true, job_started: false, summary };
      }
      default:
        throw new Error("Unknown Director tool.");
    }
  }, [addNotice, editSceneCopy, persistDraft, selectScene, updateField]);

  const director = useLiveDirector({ onToolCall: handleToolCall });

  useEffect(() => { shareAssetRef.current = director.shareAsset; }, [director.shareAsset]);

  const selectedConcept = draft.concepts.find((concept) => concept.variant_id === draft.selected_variant_id) ?? draft.concepts[0];
  const selectedScene = selectedConcept.scenes.find((scene) => scene.id === draft.selected_scene_id) ?? selectedConcept.scenes[0];
  const visibleAssets = assets.filter((asset) => !assetQuery || `${asset.name} ${asset.relativePath}`.toLowerCase().includes(assetQuery.toLowerCase())).slice(0, 24);
  const readiness = {
    brief: Boolean(brief.product_name && brief.one_liner && brief.audience && sources.goal),
    screens: selectedAssetIds.length >= 3 && selectedAssetIds.length <= 6,
    concepts: draft.concepts.length === 3 && draft.concepts.every((concept) => concept.scenes.length >= 4 && concept.scenes.length <= 6),
  };
  const readyToConfirm = Object.values(readiness).every(Boolean);

  const loadFolder = useCallback((files: FileList | null) => {
    if (!files) return;
    for (const asset of assetsRef.current) URL.revokeObjectURL(asset.previewUrl);
    const next = Array.from(files)
      .filter((file) => file.type === "image/png" || file.type === "image/jpeg")
      .slice(0, 100)
      .map((file) => ({ id: crypto.randomUUID(), name: file.name, relativePath: file.webkitRelativePath || file.name, file, previewUrl: URL.createObjectURL(file) }));
    setAssets(next);
    setSelectedAssetIds([]);
    selectedAssetsRef.current = [];
    setShowAssets(true);
    addNotice("system", `${next.length} image filenames indexed from the folder you approved.`);
  }, [addNotice]);

  const toggleAsset = useCallback((assetId: string) => {
    const current = selectedAssetsRef.current;
    const next = current.includes(assetId) ? current.filter((id) => id !== assetId) : current.length < 6 ? [...current, assetId] : current;
    selectedAssetsRef.current = next;
    setSelectedAssetIds(next);
  }, []);

  const runTypedFallback = useCallback(async (message: string) => {
    const text = message.trim();
    let match: RegExpMatchArray | null;
    if ((match = text.match(/^(?:product|product name)\s*(?:is|to|:)\s*(.+)$/i))) {
      updateField("product_name", match[1], "typed");
      addNotice("director", "Product name saved from typed input.");
      return;
    }
    if ((match = text.match(/^(?:description|one[- ]?liner)\s*(?:is|to|:)\s*(.+)$/i))) {
      updateField("one_liner", match[1], "typed");
      addNotice("director", "Description saved and available as a copy source.");
      return;
    }
    if ((match = text.match(/^audience\s*(?:is|to|:)\s*(.+)$/i))) {
      updateField("audience", match[1], "typed");
      addNotice("director", "Audience saved from typed input.");
      return;
    }
    if ((match = text.match(/^goal\s*(?:is|to|:)\s*(.+)$/i))) {
      updateField("goal", match[1], "typed");
      addNotice("director", "Launch goal saved from typed input.");
      return;
    }
    if ((match = text.match(/^select\s+(?:concept\s+)?([abc])(?:\s+scene)?\s+(\d)$/i))) {
      const variant = match[1].toUpperCase() as VariantId;
      await selectScene(variant, `${variant}-scene-${Number(match[2])}`);
      addNotice("director", `Selected ${variant}, scene ${Number(match[2])}.`);
      return;
    }
    if ((match = text.match(/^use\s+(product name|description|goal|goal detail|audience)(?:\s+as|\s+for)?\s+(?:the\s+)?copy$/i))) {
      const map: Record<string, SourceField> = { "product name": "product_name", description: "one_liner", goal: "goal", "goal detail": "goal_note", audience: "audience" };
      const field = map[match[1].toLowerCase()];
      await editSceneCopy(draftRef.current.selected_scene_id, valueForSource(briefRef.current, field), field);
      addNotice("director", `Applied the confirmed ${sourceLabel[field]} to ${draftRef.current.selected_scene_id}.`);
      return;
    }
    if ((match = text.match(/^move\s+scene\s+(\d)\s+(?:to|before)\s+(\d)$/i))) {
      const next = reorderScenes(draftRef.current, draftRef.current.selected_variant_id, Number(match[1]), Number(match[2]));
      await persistDraft(next);
      addNotice("director", `Reordered concept ${next.selected_variant_id} and saved revision ${next.revision}.`);
      return;
    }
    if (/^(?:run|run preflight|start run)$/i.test(text)) {
      setConfirmSummary("Generate exactly three 15-second concepts, then render and pretest them using the connected pipeline.");
      addNotice("director", "I opened the run confirmation. Nothing has started yet.");
      return;
    }
    addNotice("director", "Typed fallback understands brief fields, scene selection, source-backed copy, reordering, and Run. Enable Live for open-ended creative conversation.");
  }, [addNotice, editSceneCopy, persistDraft, selectScene, updateField]);

  const submitComposer = useCallback(async (event: FormEvent) => {
    event.preventDefault();
    const text = composerText.trim();
    if (!text) return;
    setComposerText("");
    addNotice("user", text);
    if (!director.sendText(text)) await runTypedFallback(text);
  }, [addNotice, composerText, director, runTypedFallback]);

  const confirmRun = useCallback(async () => {
    if (!readyToConfirm || jobState === "saving") return;
    setConfirmSummary(null);
    setJobState("saving");
    setJobMessage("Validating and saving the approved draft…");
    const commandId = crypto.randomUUID();
    try {
      const selected = selectedAssetIds.map((id) => assets.find((asset) => asset.id === id)).filter(Boolean) as LocalAsset[];
      const form = new FormData();
      for (const asset of selected) form.append("files", asset.file, asset.name);
      const uploadResponse = await fetch(`/api/projects/${PROJECT_ID}/assets`, { method: "POST", body: form });
      const upload = await uploadResponse.json() as { assets?: Array<{ storedPath: string }>; error?: string };
      if (!uploadResponse.ok || !upload.assets) throw new Error(upload.error ?? "Screenshot upload failed.");

      const assetPathById = new Map(selected.map((asset, index) => [asset.id, upload.assets?.[index]?.storedPath]));
      let finalDraft = structuredClone(draftRef.current);
      finalDraft.concepts = finalDraft.concepts.map((concept) => ({
        ...concept,
        scenes: concept.scenes.map((scene) => scene.asset_id && assetPathById.get(scene.asset_id) ? { ...scene, asset_id: assetPathById.get(scene.asset_id) } : scene),
      }));
      finalDraft = touchDraft(finalDraft);
      await persistDraft(finalDraft);

      const finalBrief = briefSchema.parse({ ...briefRef.current, project_id: PROJECT_ID, screenshots: upload.assets.map((asset) => asset.storedPath) });
      const briefResponse = await fetch(`/api/projects/${PROJECT_ID}/brief`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(finalBrief) });
      if (!briefResponse.ok) throw new Error(((await briefResponse.json()) as { error?: string }).error ?? "Brief save failed.");

      const runResponse = await fetch(`/api/projects/${PROJECT_ID}/run`, { method: "POST", headers: { "Idempotency-Key": commandId } });
      const run = await runResponse.json() as { error?: string; status?: string; run_id?: string };
      if (!runResponse.ok) {
        setJobState(runResponse.status === 503 ? "unavailable" : "error");
        setJobMessage(run.error ?? "No job was started.");
        addNotice("system", run.error ?? "No job was started.");
        return;
      }
      setJobState("queued");
      setJobMessage(`Run ${run.run_id ?? "queued"} · waiting for genuine backend events`);
      addNotice("system", "Run accepted by the connected pipeline. Progress will only follow persisted backend events.");
    } catch (error) {
      setJobState("error");
      setJobMessage(error instanceof Error ? error.message : "No job was started.");
    }
  }, [addNotice, assets, jobState, persistDraft, readyToConfirm, selectedAssetIds]);

  const startDrag = (event: PointerEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest("button, input, select, textarea")) return;
    dragRef.current = { x: event.clientX, y: event.clientY, viewX: view.x, viewY: view.y, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragging(true);
  };
  const moveDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragging) return;
    const dx = event.clientX - dragRef.current.x;
    const dy = event.clientY - dragRef.current.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) dragRef.current.moved = true;
    setView((current) => ({ ...current, x: dragRef.current.viewX + dx, y: dragRef.current.viewY + dy }));
  };

  const allTranscript = useMemo(() => [
    ...director.transcript.map((line) => ({ id: line.id, role: line.role, text: line.text } as Notice)),
    ...notices,
  ].slice(-12), [director.transcript, notices]);

  const orbState: OrbState = director.state === "connecting" || director.state === "requesting" ? "connecting" : director.isSpeaking ? "composing" : director.state === "listening" ? "listening" : "breathing";
  const liveLabel = director.state === "listening" ? "Live · listening" : director.state === "connecting" || director.state === "requesting" ? "Connecting…" : director.state === "error" ? "Live unavailable" : "Enable Live";
  const latestLine = director.liveDirectorText || director.liveUserText || allTranscript.at(-1)?.text;
  const selectedAsset = assets.find((asset) => asset.id === selectedScene.asset_id);

  return (
    <main className="canvas-app">
      <header className="canvas-header">
        <div className="project-identity"><span className="preflight-mark">P</span><div><strong>Preflight</strong><small>{brief.product_name || "Untitled launch"} · storyboard</small></div></div>
        <div className="header-actions">
          <span className={`draft-state ${draftState}`}>{draftState === "saving" ? "Saving…" : draftState === "error" ? "Saved in browser" : `Draft r${draft.revision}`}</span>
          <button onClick={() => setShowBrief((current) => !current)}>Brief</button>
          <button className="run-top" onClick={() => setConfirmSummary("Generate exactly three 15-second concepts, then render and pretest them using the connected pipeline.")}>Run</button>
        </div>
      </header>

      <nav className="tool-rail" aria-label="Canvas tools">
        <button className="active" aria-label="Select">↖</button>
        <button onClick={() => folderInputRef.current?.click()} aria-label="Add screenshots">＋</button>
        <button onClick={() => setView({ x: 0, y: 0, zoom: 0.82 })} aria-label="Fit flow">⌂</button>
        <span />
        <button onClick={() => setShowTranscript((current) => !current)} aria-label="Transcript">≡</button>
      </nav>

      <section
        className={`flow-viewport ${dragging ? "dragging" : ""}`}
        onPointerDown={startDrag}
        onPointerMove={moveDrag}
        onPointerUp={() => setDragging(false)}
        onPointerCancel={() => setDragging(false)}
        onWheel={(event) => {
          event.preventDefault();
          setView((current) => ({ ...current, zoom: Math.min(1.22, Math.max(0.58, current.zoom * (event.deltaY > 0 ? 0.9 : 1.1))) }));
        }}
      >
        <div className="flow-plane" style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})` }}>
          <svg className="flow-lines" width="1440" height="720" viewBox="0 0 1440 720" aria-hidden="true">
            {variantIds.map((variant, index) => <path key={variant} d={`M 330 355 C 395 355, 390 ${170 + index * 185}, 462 ${170 + index * 185}`} />)}
            {selectedConcept.scenes.map((_, index) => <path className="scene-line" key={index} d={`M 720 ${170 + variantIds.indexOf(selectedConcept.variant_id) * 185} C 770 ${170 + variantIds.indexOf(selectedConcept.variant_id) * 185}, 760 ${118 + index * 116}, 820 ${118 + index * 116}`} />)}
          </svg>

          <article className="flow-card source-node">
            <div className="node-label"><span>Source</span><b>{readiness.brief ? "Confirmed" : "Incomplete"}</b></div>
            <h1>{brief.product_name || "Name your product"}</h1>
            <p>{brief.one_liner || "Tell the Director what the product actually does."}</p>
            <dl><div><dt>Audience</dt><dd>{brief.audience || "Missing"}</dd></div><div><dt>Goal</dt><dd>{sources.goal ? brief.goal : "Missing"}</dd></div></dl>
            <button onClick={() => setShowBrief(true)}>Edit confirmed facts</button>
          </article>

          <div className="concept-stack">
            {draft.concepts.map((concept) => (
              <button
                className={`concept-card ${draft.selected_variant_id === concept.variant_id ? "selected" : ""}`}
                key={concept.variant_id}
                onClick={() => void selectScene(concept.variant_id, concept.scenes[0].id)}
              >
                <span className="variant-letter">{concept.variant_id}</span>
                <span><small>Proposed · not rendered</small><strong>{concept.hypothesis.split(" — ")[0]}</strong><em>{concept.scenes.length} scenes · 15 seconds</em></span>
              </button>
            ))}
          </div>

          <div className="scene-stack">
            {selectedConcept.scenes.map((scene, index) => {
              const sceneAsset = assets.find((asset) => asset.id === scene.asset_id);
              return (
                <button className={`scene-card ${scene.id === selectedScene.id ? "selected" : ""}`} key={scene.id} onClick={() => void selectScene(selectedConcept.variant_id, scene.id)}>
                  <span className="scene-index">{String(index + 1).padStart(2, "0")}</span>
                  <span className="scene-preview">
                    {sceneAsset ? <><span className="asset-thumb" style={{ backgroundImage: `url(${sceneAsset.previewUrl})` }} /><small>{sceneAsset.name}</small></> : <span className="empty-screen">Add screen</span>}
                  </span>
                  <span className="scene-copy"><strong>{scene.text || "No copy yet"}</strong><small>{scene.source_field ? `Source · ${sourceLabel[scene.source_field]}` : `${scene.t_start}–${scene.t_end}s · draft`}</small></span>
                </button>
              );
            })}
          </div>

          <aside className="scene-inspector">
            <div><small>Editing</small><strong>{selectedScene.id.replace("-scene-", " · scene ")}</strong></div>
            <p>{selectedScene.text || "Apply a confirmed brief field as source-backed copy."}</p>
            <div className="source-buttons">
              <button disabled={!brief.one_liner} onClick={() => void editSceneCopy(selectedScene.id, brief.one_liner, "one_liner")}>Use description</button>
              <button disabled={!brief.product_name} onClick={() => void editSceneCopy(selectedScene.id, brief.product_name, "product_name")}>Use product</button>
            </div>
            <button className="asset-picker-button" onClick={() => setShowAssets(true)}>{selectedAsset ? "Change screenshot" : "Choose screenshot"}</button>
          </aside>
        </div>

        <div className="brain-placeholder"><span className="brain-glyph">◌</span><div><strong>Brain</strong><small>No brain data</small></div></div>
        <div className="zoom-control"><button onClick={() => setView((current) => ({ ...current, zoom: Math.max(0.58, current.zoom - 0.1) }))}>−</button><span>{Math.round(view.zoom * 100)}%</span><button onClick={() => setView((current) => ({ ...current, zoom: Math.min(1.22, current.zoom + 0.1) }))}>＋</button></div>
      </section>

      {showBrief && <aside className="side-drawer brief-drawer">
        <div className="drawer-heading"><div><small>Confirmed source</small><h2>Launch brief</h2></div><button onClick={() => setShowBrief(false)}>×</button></div>
        <label>Product name <span>{sources.product_name ?? "missing"}</span><input value={brief.product_name} onChange={(event) => updateField("product_name", event.target.value, "typed")} /></label>
        <label>Description <span>{sources.one_liner ?? "missing"}</span><textarea maxLength={140} value={brief.one_liner} onChange={(event) => updateField("one_liner", event.target.value, "typed")} /><small>{brief.one_liner.length}/140</small></label>
        <label>Audience <span>{sources.audience ?? "missing"}</span><input value={brief.audience} onChange={(event) => updateField("audience", event.target.value, "typed")} /></label>
        <label>Goal <span>{sources.goal ?? "missing"}</span><select value={brief.goal} onChange={(event) => updateField("goal", event.target.value, "typed")}><option value="signups">Sign ups</option><option value="downloads">Downloads</option><option value="understand">Understand product</option><option value="purchase">Purchase</option></select></label>
        <div className="drawer-note">Each visible claim keeps one of these fields as its source. Draft edits are validated before saving.</div>
      </aside>}

      {showAssets && <aside className="asset-drawer">
        <div className="drawer-heading"><div><small>User-approved folder</small><h2>Product screens</h2></div><button onClick={() => setShowAssets(false)}>×</button></div>
        <div className="asset-tools"><button onClick={() => folderInputRef.current?.click()}>Choose folder</button><input value={assetQuery} onChange={(event) => setAssetQuery(event.target.value)} placeholder="Search filenames" /></div>
        <input ref={folderInputRef} hidden type="file" accept="image/png,image/jpeg" multiple onChange={(event) => loadFolder(event.target.files)} />
        {assets.length === 0 ? <button className="empty-assets" onClick={() => folderInputRef.current?.click()}><strong>Grant one folder</strong><span>PNG/JPG filenames stay local until you confirm Run.</span></button> : <div className="asset-shelf">{visibleAssets.map((asset) => {
          const selected = selectedAssetIds.includes(asset.id);
          return <div className={`shelf-card ${selected ? "selected" : ""}`} key={asset.id}><button onClick={() => toggleAsset(asset.id)}><span style={{ backgroundImage: `url(${asset.previewUrl})` }} /><strong>{asset.name}</strong><small>{selected ? "Selected for brief" : "Select"}</small></button><button className="place-button" disabled={!selected} onClick={() => void handleToolCall({ name: "set_scene_asset", args: { scene_id: selectedScene.id, asset_id: asset.id, rationale: "Chosen by the user from the approved folder" } })}>Place in {selectedScene.id}</button></div>;
        })}</div>}
        <div className="asset-count">{selectedAssetIds.length}/3–6 selected for the run</div>
      </aside>}

      {showTranscript && <aside className="transcript-drawer">
        <div className="drawer-heading"><div><small>One shared conversation</small><h2>Director transcript</h2></div><button onClick={() => setShowTranscript(false)}>×</button></div>
        <div>{allTranscript.length ? allTranscript.map((line) => <article key={line.id} className={line.role}><span>{line.role === "director" ? "Director" : line.role === "user" ? "You" : "Canvas"}</span><p>{line.text}</p></article>) : <p className="empty-transcript">Enable Live or type a command. Transcripts appear here.</p>}</div>
      </aside>}

      <section className="composer-dock">
        {latestLine && <button className="latest-caption" onClick={() => setShowTranscript(true)}><span>{director.liveDirectorText ? "Director" : director.liveUserText ? "You" : "Session"}</span>{latestLine}</button>}
        <div className={`orb-wrap ${director.isSpeaking ? "speaking" : ""}`}>
          <ThinkingOrb state={orbState} size={64} theme="dark" color="#ff5a36" aria-label={liveLabel} />
        </div>
        <VoiceBeam
          level={director.outputLevel}
          processing={director.state === "connecting" || draftState === "saving"}
          colorVariant="sunset"
          colors={["#ff5a36", "#f2472c", "#ff773f", "#cb3828", "#ff9650", "#a82923", "#e45432"]}
          bandColors={{ core: "#ffe1c7", above: "#ff773f", mid: "#ff5a36", below: "#cb3828" }}
          staticColors
          strength={0.42}
          idle={0}
          theme="dark"
        >
          <form className="canvas-composer" onSubmit={(event) => void submitComposer(event)}>
            <button
              className={`mic-button ${director.state === "listening" ? "live" : ""}`}
              type="button"
              onClick={() => director.state === "listening" ? void director.stop() : void director.start()}
              aria-label={director.state === "listening" ? "Disconnect Live Director" : "Enable Live Director"}
            ><span>●</span></button>
            <input value={composerText} onChange={(event) => setComposerText(event.target.value)} placeholder="Ask the Director, select a scene, or type “run preflight”…" />
            <button className="send-button" type="submit" disabled={!composerText.trim()} aria-label="Send">↗</button>
          </form>
        </VoiceBeam>
        <div className="composer-meta"><button onClick={() => director.state === "listening" ? void director.stop() : void director.start()}>{liveLabel}</button>{director.state === "listening" && <><span>Mic {Math.round(director.level * 100)}%</span><button onClick={director.toggleMute}>{director.isMuted ? "Unmute Director" : "Mute Director"}</button><button onClick={() => void director.stop()}>Disconnect</button></>}<span className={`job-state ${jobState}`}>{jobMessage}</span></div>
        {director.error && <div className="composer-error" role="alert">{director.error}</div>}
      </section>

      {confirmSummary && <div className="modal-backdrop" role="presentation">
        <section className="run-modal" role="dialog" aria-modal="true" aria-labelledby="run-title">
          <small>Explicit confirmation · no job started</small><h2 id="run-title">Run this bounded preflight?</h2><p>{confirmSummary}</p>
          <ul><li className={readiness.brief ? "ready" : ""}>Confirmed brief fields</li><li className={readiness.screens ? "ready" : ""}>3–6 approved screenshots ({selectedAssetIds.length})</li><li className={readiness.concepts ? "ready" : ""}>Exactly A/B/C · five scenes each · 15 seconds</li></ul>
          <div className="modal-warning">This can start planning, rendering, Gemini panel evaluation, and TRIBE only when those services are genuinely connected.</div>
          <div className="modal-actions"><button onClick={() => setConfirmSummary(null)}>Keep editing</button><button className="confirm-run" disabled={!readyToConfirm || jobState === "saving"} onClick={() => void confirmRun()}>{readyToConfirm ? "Confirm Run" : "Complete required inputs"}</button></div>
        </section>
      </div>}
    </main>
  );
}
