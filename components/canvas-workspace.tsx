"use client";

import type { FunctionCall } from "@google/genai";
import Link from "next/link";
import { FormEvent, PointerEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ThinkingOrb } from "thinking-orbs";

import { CanvasBrain } from "@/components/brain/CanvasBrain";
import { VoiceBeam } from "@/components/voice-beam";
import { DirectorVoicePresence, VoiceIcon } from "@/components/director-voice-presence";
import { DirectorConsole, type ConsoleEvent, type ConsoleEventKind, type JourneyStep } from "@/components/director-console";
import { PictureTrackCards } from "@/components/picture-track-cards";
import { RunResults, type PlannedVariant, type RunState } from "@/components/run-results";
import { useLiveDirector } from "@/hooks/use-live-director";
import {
  applyBriefFieldInput,
  BRIEF_EXTRA_MAX,
  briefSchema,
  emptyBrief,
  type BriefDraft,
  type BriefExtraField,
  type BriefField,
  type BriefTextField,
  type RenderMode,
  type SourceMap,
} from "@/lib/brief";
import { isGroundedCopy, normalizeGoal, parseTypedCommand, type TypedBriefField } from "@/lib/canvas-commands";
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
import { buildDirectorContext } from "@/lib/director-context";
import { assertEditableScene } from "@/lib/director-edit";
import { DirectorRunBoundary, isExplicitRunConsent } from "@/lib/director-run";
import { publicErrorMessage, readJson } from "@/lib/public-error";
import type { DirectorUserTurn } from "@/lib/director-tool-queue";

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
const BACKEND_PROJECT_STORAGE = `preflight:${PROJECT_ID}:backend-project`;

const fieldLabels: Record<BriefField, string> = {
  product_name: "Product",
  one_liner: "Description",
  goal: "Goal",
  goal_note: "Call to action",
  audience: "Audience",
};

const sourceLabel: Record<SourceField, string> = {
  product_name: "product name",
  one_liner: "description",
  goal: "goal",
  goal_note: "call to action",
  audience: "audience",
};

function cleanString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

const typedFieldSaved: Record<TypedBriefField, string> = {
  product_name: "Product name saved from typed input.",
  one_liner: "Description saved and available as a copy source.",
  audience: "Audience saved from typed input.",
  goal: "Launch goal saved from typed input.",
};

function valueForSource(brief: BriefDraft, field: SourceField) {
  return String(brief[field] ?? "").trim();
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
  const [backendProjectId, setBackendProjectId] = useState<string | undefined>();
  const [jobState, setJobState] = useState<JobState>("draft");
  const [jobMessage, setJobMessage] = useState("Draft only · no render or simulation has run");
  const [showBrief, setShowBrief] = useState(false);
  const [showAssets, setShowAssets] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [confirmSummary, setConfirmSummary] = useState<string | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, zoom: 0.82 });
  const [dragging, setDragging] = useState(false);
  const [visualsPaused, setVisualsPaused] = useState(false);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [runNonce, setRunNonce] = useState(0);
  const [runState, setRunState] = useState<RunState | null>(null);
  const [showConsole, setShowConsole] = useState(false);
  const [consoleEvents, setConsoleEvents] = useState<ConsoleEvent[]>([]);
  const lastTypedRef = useRef("");
  const loggedTranscriptRef = useRef(new Set<string>());

  const folderInputRef = useRef<HTMLInputElement | null>(null);
  const voiceButtonRef = useRef<HTMLButtonElement | null>(null);
  const filesInputRef = useRef<HTMLInputElement | null>(null);
  const dragRef = useRef({ x: 0, y: 0, viewX: 0, viewY: 0, moved: false });
  const assetsRef = useRef(assets);
  const selectedAssetsRef = useRef(selectedAssetIds);
  const draftRef = useRef(draft);
  const briefRef = useRef(brief);
  const sourcesRef = useRef(sources);
  const draftStateRef = useRef(draftState);
  const jobRef = useRef({ status: jobState as string, message: jobMessage, project_id: backendProjectId });
  const runBoundaryRef = useRef(new DirectorRunBoundary());
  const runApprovalRef = useRef<string | null>(null);
  const voiceApprovalTurnRef = useRef<number | null>(null);
  const confirmRunRef = useRef<((id: string) => Promise<Record<string, unknown>>) | null>(null);
  const shareAssetRef = useRef<((file: File, label: string, requestResponse?: boolean) => Promise<boolean>) | null>(null);

  useEffect(() => {
    folderInputRef.current?.setAttribute("webkitdirectory", "");
    folderInputRef.current?.setAttribute("directory", "");
  }, []);

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setVisualsPaused(motion.matches || document.hidden);
    update();
    motion.addEventListener("change", update);
    document.addEventListener("visibilitychange", update);
    return () => {
      motion.removeEventListener("change", update);
      document.removeEventListener("visibilitychange", update);
    };
  }, []);

  useEffect(() => { assetsRef.current = assets; }, [assets]);
  useEffect(() => { selectedAssetsRef.current = selectedAssetIds; }, [selectedAssetIds]);
  useEffect(() => { draftRef.current = draft; }, [draft]);
  useEffect(() => { briefRef.current = brief; }, [brief]);
  useEffect(() => { sourcesRef.current = sources; }, [sources]);
  useEffect(() => { draftStateRef.current = draftState; }, [draftState]);
  useEffect(() => { jobRef.current = { status: jobState, message: jobMessage, project_id: backendProjectId }; }, [jobState, jobMessage, backendProjectId]);

  useEffect(() => {
    const storedBrief = readStored(BRIEF_STORAGE, (value) => {
      const record = value as { brief?: BriefDraft; sources?: SourceMap };
      return { brief: { ...emptyBrief(PROJECT_ID), ...record.brief, project_id: PROJECT_ID }, sources: record.sources ?? {} };
    });
    const storedDraft = readStored(DRAFT_STORAGE, (value) => canvasDraftSchema.parse(value));
    const storedBackendProject = localStorage.getItem(BACKEND_PROJECT_STORAGE);
    queueMicrotask(() => {
      if (storedBrief) {
        setBrief(storedBrief.brief);
        setSources(storedBrief.sources);
      }
      if (storedDraft) setDraft(storedDraft);
      if (storedBackendProject && /^[A-Za-z0-9_-]{1,128}$/.test(storedBackendProject)) setBackendProjectId(storedBackendProject);
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

  const logEvent = useCallback((kind: ConsoleEventKind, title: string, detail?: unknown) => {
    const text = detail === undefined ? undefined : typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
    setConsoleEvents((current) => [...current, { id: crypto.randomUUID(), at: Date.now(), kind, title, detail: text }].slice(-200));
  }, []);

  const addNotice = useCallback((role: Notice["role"], text: string) => {
    setNotices((current) => [...current, { id: crypto.randomUUID(), role, text }].slice(-16));
    if (role !== "user") logEvent("canvas", text);
  }, [logEvent]);

  const reportAction = useCallback((action: Promise<unknown>) => {
    void action.catch((error) => addNotice("system", error instanceof Error ? error.message : "Action could not be confirmed."));
  }, [addNotice]);

  const persistDraft = useCallback(async (next: CanvasDraft) => {
    setDraft(next);
    draftRef.current = next;
    localStorage.setItem(DRAFT_STORAGE, JSON.stringify(next));
    setDraftState("saving");
    draftStateRef.current = "saving";
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
      if (!response.ok) throw new Error("The server did not save this edit. The browser preview is not a confirmed saved draft.");
      setDraftState("saved");
      draftStateRef.current = "saved";
    } catch (error) {
      setDraftState("error");
      draftStateRef.current = "error";
      addNotice("system", error instanceof Error ? error.message : "Server save failed; this edit is browser-only.");
      throw error;
    }
    return next;
  }, [addNotice]);

  const updateField = useCallback((
    field: BriefField,
    rawValue: string,
    source: "voice" | "typed",
    mode: "live" | "commit" = "commit",
  ) => {
    const value = field === "goal"
      ? normalizeGoal(rawValue)
      : applyBriefFieldInput(field as BriefTextField, rawValue, mode);
    if (value === null) throw new Error("Goal must be signups, downloads, understanding, or purchase.");
    const nextBrief = { ...briefRef.current, [field]: value } as BriefDraft;
    const nextSources = { ...sourcesRef.current, [field]: source };
    setBrief(nextBrief);
    setSources(nextSources);
    briefRef.current = nextBrief;
    sourcesRef.current = nextSources;
    localStorage.setItem(BRIEF_STORAGE, JSON.stringify({ brief: nextBrief, sources: nextSources }));
    return value;
  }, []);

  const updateExtra = useCallback((field: BriefExtraField, rawValue: string, mode: "live" | "commit") => {
    const value = (mode === "commit" ? rawValue.trim() : rawValue).slice(0, BRIEF_EXTRA_MAX[field]);
    const nextBrief = { ...briefRef.current, [field]: value };
    setBrief(nextBrief);
    briefRef.current = nextBrief;
    localStorage.setItem(BRIEF_STORAGE, JSON.stringify({ brief: nextBrief, sources: sourcesRef.current }));
  }, []);

  const updateRenderMode = useCallback((render_mode: RenderMode) => {
    const nextBrief = { ...briefRef.current, render_mode };
    setBrief(nextBrief);
    briefRef.current = nextBrief;
    localStorage.setItem(BRIEF_STORAGE, JSON.stringify({ brief: nextBrief, sources: sourcesRef.current }));
  }, []);

  const commitBriefEdits = useCallback(() => {
    for (const field of ["product_name", "one_liner", "audience", "goal_note"] as const) {
      const raw = String(briefRef.current[field] ?? "");
      const trimmed = applyBriefFieldInput(field, raw, "commit");
      if (trimmed !== raw) updateField(field, trimmed, "typed", "commit");
    }
  }, [updateField]);

  const getProjectContext = useCallback(() => buildDirectorContext({
    brief: briefRef.current, sources: sourcesRef.current, draft: draftRef.current,
    assets: assetsRef.current, selectedAssetIds: selectedAssetsRef.current,
    persistence: draftStateRef.current, job: jobRef.current,
  }), []);

  const runSignature = useCallback(() => JSON.stringify({
    brief: briefRef.current, sources: sourcesRef.current,
    revision: draftRef.current.revision, assets: selectedAssetsRef.current,
  }), []);

  const requestRunConfirmation = useCallback(() => {
    commitBriefEdits();
    const current = getProjectContext();
    const ready = current.missing_brief_fields.length === 0 && selectedAssetsRef.current.length >= 3 && selectedAssetsRef.current.length <= 6;
    const summary = `Upload ${selectedAssetsRef.current.length} selected screenshots and submit one run of exactly three 15-second A/B/C candidate videos for ${briefRef.current.product_name || "this project"}, aimed at ${briefRef.current.audience || "the unconfirmed audience"}. Rendering and pretesting require the connected backend. Existing-video baseline analysis is not connected in this build.`;
    const approval = runBoundaryRef.current.request(runSignature(), summary);
    runApprovalRef.current = approval.id;
    setConfirmSummary(summary);
    return { confirmation_id: approval.id, revision: draftRef.current.revision, summary, ready, job_started: false, missing_brief_fields: current.missing_brief_fields };
  }, [commitBriefEdits, getProjectContext, runSignature]);

  const cancelRunConfirmation = useCallback(() => {
    setConfirmSummary(null);
    runBoundaryRef.current.cancel();
    runApprovalRef.current = null;
    voiceApprovalTurnRef.current = null;
  }, []);

  const selectScene = useCallback(async (variantId: VariantId, sceneId: string) => {
    const concept = draftRef.current.concepts.find((item) => item.variant_id === variantId);
    if (!concept?.scenes.some((scene) => scene.id === sceneId)) throw new Error("That scene is not in this concept.");
    const next = touchDraft({ ...draftRef.current, selected_variant_id: variantId, selected_scene_id: sceneId });
    await persistDraft(next);
    return next;
  }, [persistDraft]);

  const editSceneCopy = useCallback(async (sceneId: string, text: string, sourceField: SourceField) => {
    assertEditableScene(draftRef.current, sceneId, ["saving", "queued"].includes(jobRef.current.status));
    if (!sourcesRef.current[sourceField]) throw new Error("That brief field has not been confirmed by the user.");
    const sourceValue = valueForSource(briefRef.current, sourceField);
    if (!sourceValue) throw new Error(`The ${sourceLabel[sourceField]} field is empty.`);
    if (!isGroundedCopy(text, sourceValue)) throw new Error(`Copy must use words from the confirmed ${sourceLabel[sourceField]}.`);
    const next = replaceScene(draftRef.current, sceneId, { text, source_field: sourceField });
    await persistDraft(next);
    addNotice("system", `Saved ${sceneId} from ${sourceLabel[sourceField]} · revision ${next.revision}`);
    return next;
  }, [addNotice, persistDraft]);

  const handleToolCall = useCallback(async (call: FunctionCall, userTurn?: DirectorUserTurn | null): Promise<Record<string, unknown>> => {
    const args = call.args ?? {};
    switch (call.name) {
      case "get_project_context":
        return getProjectContext();
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
        const shared = await shareAssetRef.current?.(asset.file, asset.name, false);
        if (!shared) throw new Error("The image was not shared with Live. Check connection, PNG/JPG format and the 10 MB limit.");
        logEvent("sent", `Screenshot ${asset.name} sent to the AI (${Math.round(asset.file.size / 1024)} KB)`);
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
        assertEditableScene(draftRef.current, sceneId, ["saving", "queued"].includes(jobRef.current.status));
        const assetId = cleanString(args.asset_id);
        if (!selectedAssetsRef.current.includes(assetId)) throw new Error("Select the approved asset before placing it.");
        const next = replaceScene(draftRef.current, sceneId, { asset_id: assetId });
        await persistDraft(next);
        const rationale = cleanString(args.rationale);
        if (rationale) addNotice("system", `${sceneId}: ${rationale}`);
        return { saved: true, scene_id: sceneId, asset_id: assetId, revision: next.revision };
      }
      case "reorder_scene": {
        assertEditableScene(draftRef.current, draftRef.current.selected_scene_id, ["saving", "queued"].includes(jobRef.current.status));
        if (cleanString(args.variant_id) !== draftRef.current.selected_variant_id) throw new Error("Select this concept before reordering its scenes.");
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
        voiceApprovalTurnRef.current = userTurn?.number ?? null;
        return { confirmation_required: true, ...requestRunConfirmation() };
      }
      case "confirm_run": {
        if (!userTurn || voiceApprovalTurnRef.current === null || userTurn.number <= voiceApprovalTurnRef.current || !isExplicitRunConsent(userTurn.text)) {
          throw new Error("A new explicit user confirmation after the bounded summary is required. No job was started.");
        }
        if (!confirmRunRef.current) throw new Error("The run controller is not ready. Ask for a fresh summary.");
        return confirmRunRef.current(cleanString(args.confirmation_id));
      }
      default:
        throw new Error("Unknown Director tool.");
    }
  }, [addNotice, editSceneCopy, getProjectContext, logEvent, persistDraft, requestRunConfirmation, selectScene, updateField]);

  const loggedToolCall = useCallback(async (call: FunctionCall, userTurn?: DirectorUserTurn | null) => {
    const args = call.args ?? {};
    const rationale = cleanString((args as Record<string, unknown>).rationale);
    const summary = Object.entries(args).filter(([key]) => key !== "rationale" && key !== "summary").map(([key, value]) => `${key}: ${String(value).slice(0, 60)}`).join(", ");
    logEvent("action", `${call.name}${summary ? ` (${summary})` : ""}${rationale ? ` · why: ${rationale}` : ""}`, args);
    try {
      const output = await handleToolCall(call, userTurn);
      logEvent("result", `${call.name} done`, output);
      return output;
    } catch (error) {
      logEvent("error", `${call.name}: ${error instanceof Error ? error.message : "failed"}`);
      throw error;
    }
  }, [handleToolCall, logEvent]);

  const director = useLiveDirector({ onToolCall: loggedToolCall, getProjectContext });

  const startVoice = director.start;
  const stopVoice = director.stop;
  const openVoice = useCallback(() => {
    setVoiceOpen(true);
    void startVoice();
  }, [startVoice]);

  const closeVoice = useCallback(() => {
    setVoiceOpen(false);
    void stopVoice();
    window.setTimeout(() => {
      const button = voiceButtonRef.current;
      if (button?.isConnected && !button.closest("[inert]")) button.focus();
    }, 250);
  }, [stopVoice]);

  useEffect(() => {
    for (const line of director.transcript) {
      if (loggedTranscriptRef.current.has(line.id)) continue;
      loggedTranscriptRef.current.add(line.id);
      if (line.role === "user" && line.text.trim() === lastTypedRef.current) continue;
      logEvent(line.role === "director" ? "said" : "heard", line.text);
    }
  }, [director.transcript, logEvent]);

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
  const missingBrief = (["product_name", "one_liner", "audience"] as const).filter((field) => !brief[field]).map((field) => fieldLabels[field]);
  if (!sources.goal) missingBrief.push(fieldLabels.goal);

  const loadFolder = useCallback((files: FileList | null) => {
    if (!files) return;
    for (const asset of assetsRef.current) URL.revokeObjectURL(asset.previewUrl);
    const next = Array.from(files)
      .filter((file) => file.type === "image/png" || file.type === "image/jpeg")
      .slice(0, 100)
      .map((file) => ({ id: crypto.randomUUID(), name: file.name, relativePath: file.webkitRelativePath || file.name, file, previewUrl: URL.createObjectURL(file) }));
    const selected = next.slice(0, 6).map((asset) => asset.id);
    setAssets(next);
    setSelectedAssetIds(selected);
    selectedAssetsRef.current = selected;
    setShowAssets(true);
    addNotice("system", `${next.length} screenshots loaded · ${selected.length} selected for the run.`);
  }, [addNotice]);

  const toggleAsset = useCallback((assetId: string) => {
    const current = selectedAssetsRef.current;
    const next = current.includes(assetId) ? current.filter((id) => id !== assetId) : current.length < 6 ? [...current, assetId] : current;
    selectedAssetsRef.current = next;
    setSelectedAssetIds(next);
  }, []);

  const runTypedFallback = useCallback(async (message: string) => {
    const command = parseTypedCommand(message);
    switch (command?.kind) {
      case "brief":
        updateField(command.field, command.value, "typed");
        addNotice("director", typedFieldSaved[command.field]);
        return;
      case "select":
        await selectScene(command.variant, `${command.variant}-scene-${command.scene}`);
        addNotice("director", `Selected ${command.variant}, scene ${command.scene}.`);
        return;
      case "use-copy":
        await editSceneCopy(draftRef.current.selected_scene_id, valueForSource(briefRef.current, command.field), command.field);
        addNotice("director", `Applied the confirmed ${sourceLabel[command.field]} to ${draftRef.current.selected_scene_id}.`);
        return;
      case "move": {
        assertEditableScene(draftRef.current, draftRef.current.selected_scene_id, ["saving", "queued"].includes(jobRef.current.status));
        const next = reorderScenes(draftRef.current, draftRef.current.selected_variant_id, command.from, command.to);
        await persistDraft(next);
        addNotice("director", `Reordered concept ${next.selected_variant_id} and saved revision ${next.revision}.`);
        return;
      }
      case "run":
        requestRunConfirmation();
        addNotice("director", "I opened the run confirmation. Nothing has started yet.");
        return;
      default:
        addNotice("director", "Typed fallback understands brief fields, scene selection, source-backed copy, reordering, and Run. Enable Live for open-ended creative conversation.");
    }
  }, [addNotice, editSceneCopy, persistDraft, requestRunConfirmation, selectScene, updateField]);

  const submitComposer = useCallback(async (event: FormEvent) => {
    event.preventDefault();
    const text = composerText.trim();
    if (!text) return;
    setComposerText("");
    addNotice("user", text);
    lastTypedRef.current = text;
    const live = director.sendText(text);
    logEvent("typed", text, live ? undefined : "Live is off: handled by the canvas command parser, not sent to the AI.");
    if (!live) {
      try {
        await runTypedFallback(text);
      } catch (error) {
        addNotice("system", error instanceof Error ? error.message : "That command failed.");
      }
    }
  }, [addNotice, composerText, director, logEvent, runTypedFallback]);

  const submitRun = useCallback(async (commandId: string): Promise<Record<string, unknown>> => {
    commitBriefEdits();
    setConfirmSummary(null);
    setJobState("saving");
    setJobMessage("Validating and saving the approved draft…");
    jobRef.current = { ...jobRef.current, status: "saving", message: "Validating and saving the approved draft…" };
    try {
      const selected = selectedAssetIds.map((id) => assets.find((asset) => asset.id === id)).filter(Boolean) as LocalAsset[];
      const form = new FormData();
      for (const asset of selected) form.append("files", asset.file, asset.name);
      const uploadResponse = await fetch(`/api/projects/${PROJECT_ID}/assets`, { method: "POST", body: form });
      const upload = await readJson(uploadResponse) as { assets?: Array<{ storedPath: string }>; error?: unknown };
      if (!uploadResponse.ok || !upload.assets) throw new Error(publicErrorMessage(upload.error, "Screenshot upload failed."));
      logEvent("sent", `${selected.length} screenshots uploaded to the backend`, upload.assets.map((asset) => asset.storedPath));

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
      if (!briefResponse.ok) throw new Error(publicErrorMessage((await readJson(briefResponse)).error, "Brief save failed."));
      logEvent("sent", "Brief sent to the backend (brief.json)", finalBrief);

      const runResponse = await fetch(`/api/projects/${PROJECT_ID}/run`, { method: "POST", headers: { "Idempotency-Key": commandId } });
      const run = await readJson(runResponse) as { error?: unknown; status?: string; run_id?: string; project_id?: string };
      logEvent(runResponse.ok ? "backend" : "error", runResponse.ok ? "Run accepted by the backend" : `Run refused (${runResponse.status})`, run);
      if (!runResponse.ok) {
        const message = publicErrorMessage(run.error, "No job was started.");
        setJobState(runResponse.status === 503 ? "unavailable" : "error");
        setJobMessage(message);
        addNotice("system", message);
        return { accepted: false, job_started: false, error: message };
      }
      const acceptedProjectId = run.project_id && /^[A-Za-z0-9_-]{1,128}$/.test(run.project_id) ? run.project_id : PROJECT_ID;
      setBackendProjectId(acceptedProjectId);
      localStorage.setItem(BACKEND_PROJECT_STORAGE, acceptedProjectId);
      setJobState("queued");
      jobRef.current = { status: "queued", message: "Backend accepted the run; awaiting genuine events", project_id: acceptedProjectId };
      setJobMessage("Run started · follow progress in Results");
      setRunState(null);
      setRunNonce((current) => current + 1);
      setShowResults(true);
      setShowBrief(false);
      setShowAssets(false);
      addNotice("system", "Run started. Progress and results are in the Results panel.");
      return { accepted: true, status: run.status ?? "queued", run_id: run.run_id, project_id: acceptedProjectId };
    } catch (error) {
      setJobState("error");
      setJobMessage(error instanceof Error ? error.message : "No job was started.");
      logEvent("error", error instanceof Error ? error.message : "No job was started.");
      throw new Error("Run submission could not be confirmed. Inspect the canvas before attempting another run.");
    }
  }, [addNotice, assets, commitBriefEdits, logEvent, persistDraft, selectedAssetIds]);

  const confirmRun = useCallback(async (id: string) => {
    if (!readyToConfirm) throw new Error("Required confirmed brief fields and 3–6 selected screenshots are missing.");
    return runBoundaryRef.current.confirm(id, runSignature(), submitRun);
  }, [readyToConfirm, runSignature, submitRun]);

  useEffect(() => { confirmRunRef.current = confirmRun; }, [confirmRun]);

  const onRunProgress = useCallback((state: RunState, variants: PlannedVariant[]) => {
    setRunState(state);
    const messages: Partial<Record<RunState, string>> = {
      BRIEF_RECEIVED: "Brief received · Gemini is planning three concepts",
      PLANNED: "Planned A, B and C · rendering the videos",
      RENDERED: "Rendered three 15 s videos · simulated viewers are watching",
      SIMULATED: "Viewer panel finished · scoring",
      SCORED: "Ranked · writing the explanations",
      EXPLAINED: "Explanations written",
      DONE: "Run complete · results are ready",
      FAILED: "Run failed · press Run to resume",
    };
    if (messages[state]) logEvent(state === "FAILED" ? "error" : "backend", messages[state], state === "PLANNED" ? variants.map((variant) => ({ variant: variant.variant_id, hypothesis: variant.concept.hypothesis, hook: variant.concept.hook, scenes: variant.concept.scenes.map((scene) => scene.text) })) : undefined);
    if (variants.length !== 3) return;
    const status = state === "DONE" || state === "EXPLAINED" || state === "SCORED" || state === "SIMULATED" ? "tested" : state === "RENDERED" ? "rendered" : state === "FAILED" ? "failed" : "rendering";
    const assetIdFor = (screenshot: string) => {
      const fileName = screenshot.split("/").pop()?.replace(/^[0-9a-f-]{36}-/, "");
      return assetsRef.current.find((asset) => asset.name === fileName)?.id;
    };
    const next = structuredClone(draftRef.current);
    next.concepts = next.concepts.map((concept) => {
      const planned = variants.find((variant) => variant.variant_id === concept.variant_id)?.concept;
      if (!planned || planned.scenes.length < 4 || planned.scenes.length > 6) return concept;
      return {
        ...concept,
        hypothesis: planned.hypothesis.slice(0, 180) || concept.hypothesis,
        hook: planned.hook.slice(0, 80),
        status,
        scenes: planned.scenes.map((scene, index) => {
          const sourceField = sourceFields.find((field) => field === scene.source_field);
          return {
            id: `${concept.variant_id}-scene-${index + 1}`,
            asset_id: assetIdFor(scene.screenshot),
            text: sourceField ? scene.text.slice(0, 120) : "",
            source_field: sourceField,
            t_start: scene.t_start,
            t_end: scene.t_end,
          };
        }),
      };
    });
    const selected = next.concepts.find((concept) => concept.variant_id === next.selected_variant_id);
    if (!selected?.scenes.some((scene) => scene.id === next.selected_scene_id)) next.selected_scene_id = `${next.selected_variant_id}-scene-1`;
    try {
      void persistDraft(touchDraft(next)).catch(() => undefined);
    } catch {
      // A plan that does not fit the canvas draft stays visible in Results only.
    }
  }, [logEvent, persistDraft]);

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

  const liveLabel = director.isSpeaking ? "Live · Director speaking" : director.isProcessing ? "Live · working" : director.state === "listening" ? "Live · listening" : director.state === "connecting" || director.state === "requesting" ? "Connecting…" : director.state === "error" ? "Live unavailable" : "Enable Live";
  const latestLine = director.liveDirectorText || director.liveUserText || allTranscript.at(-1)?.text;
  const selectedAsset = assets.find((asset) => asset.id === selectedScene.asset_id);
  const hasProjectContent = Boolean(brief.product_name || brief.one_liner || brief.audience || assets.length || selectedAssetIds.length || Object.keys(sources).length);

  const openFilePicker = useCallback(() => filesInputRef.current?.click(), []);
  const order: RunState[] = ["BRIEF_RECEIVED", "PLANNED", "RENDERED", "SIMULATED", "SCORED", "EXPLAINED", "ITERATED", "DONE"];
  const runIndex = runNonce > 0 && runState && runState !== "FAILED" ? order.indexOf(runState) : -1;
  const runStep = (reachedAt: RunState, startsAt: RunState): JourneyStep["state"] => {
    if (runNonce === 0) return "todo";
    if (runState === "FAILED") return "failed";
    if (runIndex >= order.indexOf(reachedAt)) return "done";
    return runIndex >= order.indexOf(startsAt) || (startsAt === "BRIEF_RECEIVED" && runIndex === -1) ? "active" : "todo";
  };
  const journey: JourneyStep[] = [
    { id: "screens", label: "Add screenshots", hint: readiness.screens ? `${selectedAssetIds.length} selected` : `${selectedAssetIds.length}/3–6 selected`, state: readiness.screens ? "done" : "active", action: openFilePicker, actionLabel: "Choose" },
    { id: "brief", label: "Fill in the brief", hint: readiness.brief ? `${brief.product_name} · goal ${brief.goal}` : `Missing: ${missingBrief.join(", ")}`, state: readiness.brief ? "done" : readiness.screens ? "active" : "todo", action: () => { setShowResults(false); setShowBrief(true); }, actionLabel: "Open" },
    { id: "run", label: "Confirm the run", hint: runNonce > 0 ? "Run started" : "Nothing runs until you confirm", state: runNonce > 0 ? "done" : readyToConfirm ? "active" : "todo", action: () => { try { requestRunConfirmation(); } catch (error) { addNotice("system", error instanceof Error ? error.message : "Run unavailable."); } }, actionLabel: "Run" },
    { id: "plan", label: "Plan A, B and C", hint: "Gemini writes three concepts from your facts", state: runStep("PLANNED", "BRIEF_RECEIVED") },
    { id: "render", label: "Render the videos", hint: "Three 15 s vertical videos", state: runStep("RENDERED", "PLANNED") },
    { id: "test", label: "Simulated viewers watch", hint: "Gemini viewer panel via Condense", state: runStep("SIMULATED", "RENDERED") },
    { id: "results", label: "Results ready", hint: "Winner, reasons, downloads", state: runStep("DONE", "SIMULATED"), action: () => { setShowBrief(false); setShowResults(true); }, actionLabel: "View" },
  ];
  const journeyStates = [readiness.screens, readiness.brief, runNonce > 0, runStep("PLANNED", "BRIEF_RECEIVED") === "done", runStep("RENDERED", "PLANNED") === "done", runStep("SIMULATED", "RENDERED") === "done", runStep("DONE", "SIMULATED") === "done"];
  const journeyDone = journeyStates.filter(Boolean).length;

  return (
    <main className="canvas-app preflight-theme pf-canvas" data-voice-open={voiceOpen}>
      <header className="canvas-header">
        <div className="project-identity"><span className="preflight-mark">P</span><div><strong>Preflight</strong><small>{brief.product_name || "Untitled launch"} · storyboard</small></div></div>
        <div className="header-actions">
          <span className={`draft-state ${draftState}`}>{draftState === "saving" ? "Saving…" : draftState === "error" ? "Saved in browser" : `Draft r${draft.revision}`}</span>
          <Link href="/admin">Dashboard</Link>
          <button onClick={() => { setShowResults(false); setShowBrief((current) => !current); }}>Brief</button>
          {backendProjectId && <button onClick={() => { setShowBrief(false); setShowResults((current) => !current); }}>Results</button>}
          <button className="run-top" onClick={() => { try { requestRunConfirmation(); } catch (error) { addNotice("system", error instanceof Error ? error.message : "Run unavailable."); } }}>Run</button>
        </div>
      </header>

      <nav className="tool-rail" aria-label="Canvas tools">
        <button className="active" aria-label="Select">↖</button>
        <button onClick={() => filesInputRef.current?.click()} aria-label="Add screenshots">＋</button>
        <button onClick={() => setView({ x: 0, y: 0, zoom: 0.82 })} aria-label="Fit flow">⌂</button>
        <span />
        <button onClick={() => setShowTranscript((current) => !current)} aria-label="Transcript">≡</button>
      </nav>
      <input ref={folderInputRef} hidden type="file" accept="image/png,image/jpeg" multiple onChange={(event) => { loadFolder(event.target.files); event.target.value = ""; }} />
      <input ref={filesInputRef} hidden type="file" accept="image/png,image/jpeg" multiple data-testid="screenshot-files" onChange={(event) => { loadFolder(event.target.files); event.target.value = ""; }} />

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
        {!hasProjectContent && <section className="empty-canvas-invite" aria-labelledby="empty-canvas-title">
          <small>New preflight</small>
          <h1 id="empty-canvas-title">Bring your launch screens.</h1>
          <p>Choose 3–6 screenshots, or enable Live and describe what you are shipping.</p>
          <div><button onClick={() => filesInputRef.current?.click()}>Choose screenshots</button><button className="enable-live-empty" onClick={openVoice}>Talk to Director</button></div>
        </section>}

        {hasProjectContent && <div className="flow-plane" style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})` }}>
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
                onClick={() => reportAction(selectScene(concept.variant_id, concept.scenes[0].id))}
              >
                <span className="variant-letter">{concept.variant_id}</span>
                <span><small>{concept.status === "tested" ? "Rendered · tested" : concept.status === "rendered" ? "Rendered · testing" : concept.status === "rendering" ? "Planned · rendering" : concept.status === "failed" ? "Run failed" : "Proposed · not rendered"}</small><strong>{concept.hypothesis.split(" — ")[0]}</strong><em>{concept.scenes.length} scenes · 15 seconds</em></span>
              </button>
            ))}
          </div>

          <div className="scene-stack">
            {selectedConcept.scenes.map((scene, index) => {
              const sceneAsset = assets.find((asset) => asset.id === scene.asset_id);
              return (
                <button className={`scene-card ${scene.id === selectedScene.id ? "selected" : ""}`} key={scene.id} onClick={() => reportAction(selectScene(selectedConcept.variant_id, scene.id))}>
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
              <button disabled={!brief.one_liner} onClick={() => reportAction(editSceneCopy(selectedScene.id, brief.one_liner, "one_liner"))}>Use description</button>
              <button disabled={!brief.product_name} onClick={() => reportAction(editSceneCopy(selectedScene.id, brief.product_name, "product_name"))}>Use product</button>
            </div>
            <button className="asset-picker-button" onClick={() => setShowAssets(true)}>{selectedAsset ? "Change screenshot" : "Choose screenshot"}</button>
          </aside>
        </div>}

        <div className="canvas-brain-layer">
          <CanvasBrain
            key={runNonce}
            projectId={backendProjectId}
            selectedVariant={draft.selected_variant_id}
            onSelectVariant={(variant) => {
              const concept = draftRef.current.concepts.find((item) => item.variant_id === variant);
              if (concept) reportAction(selectScene(variant, concept.scenes[0].id));
            }}
            entry
          />
        </div>
        <div className="zoom-control"><button onClick={() => setView((current) => ({ ...current, zoom: Math.max(0.58, current.zoom - 0.1) }))}>−</button><span>{Math.round(view.zoom * 100)}%</span><button onClick={() => setView((current) => ({ ...current, zoom: Math.min(1.22, current.zoom + 0.1) }))}>＋</button></div>
      </section>

      {showBrief && <aside className="side-drawer brief-drawer">
        <div className="drawer-heading"><div><small>Confirmed source</small><h2>Launch brief</h2></div><button onClick={() => { commitBriefEdits(); setShowBrief(false); }}>×</button></div>
        <label>Product name <span>{sources.product_name ?? "missing"}</span><input maxLength={80} value={brief.product_name} onChange={(event) => updateField("product_name", event.target.value, "typed", "live")} onBlur={(event) => updateField("product_name", event.target.value, "typed")} /></label>
        <label>Description <span>{sources.one_liner ?? "missing"}</span><textarea maxLength={140} value={brief.one_liner} onChange={(event) => updateField("one_liner", event.target.value, "typed", "live")} onBlur={(event) => updateField("one_liner", event.target.value, "typed")} /><small>{brief.one_liner.length}/140</small></label>
        <label>Audience <span>{sources.audience ?? "missing"}</span><input maxLength={300} value={brief.audience} onChange={(event) => updateField("audience", event.target.value, "typed", "live")} onBlur={(event) => updateField("audience", event.target.value, "typed")} /></label>
        <label>Goal <span>{sources.goal ?? "missing"}</span><select value={sources.goal ? brief.goal : ""} onChange={(event) => updateField("goal", event.target.value, "typed")}><option value="" disabled>Choose a goal</option><option value="signups">Sign ups</option><option value="downloads">Downloads</option><option value="understand">Understand product</option><option value="purchase">Purchase</option></select></label>
        <label>Call to action <span>{sources.goal_note ?? "optional"}</span><textarea maxLength={240} value={brief.goal_note ?? ""} placeholder="Start selling today" onChange={(event) => updateField("goal_note", event.target.value, "typed", "live")} onBlur={(event) => updateField("goal_note", event.target.value, "typed")} /><small>{(brief.goal_note ?? "").length}/240</small></label>
        <label>Button for your customers <span>optional</span><input maxLength={40} value={brief.buyer_cta ?? ""} placeholder="Book a table" onChange={(event) => updateExtra("buyer_cta", event.target.value, "live")} onBlur={(event) => updateExtra("buyer_cta", event.target.value, "commit")} /><small>{(brief.buyer_cta ?? "").length}/40</small></label>
        <label>Facts you can back up <span>optional</span><textarea maxLength={400} value={brief.proof_points ?? ""} placeholder="Setup takes 5 minutes. Works with Swish." onChange={(event) => updateExtra("proof_points", event.target.value, "live")} onBlur={(event) => updateExtra("proof_points", event.target.value, "commit")} /><small>{(brief.proof_points ?? "").length}/400</small></label>
        <div className="drawer-note">The videos may phrase copy freely, but every number, name and claim must come from these fields. The button uses &ldquo;Button for your customers&rdquo; when set; a call to action aimed at someone else (for example investors) is replaced and explained in the report. Picture track is chosen when you confirm Run.</div>
      </aside>}

      {showAssets && <aside className="asset-drawer">
        <div className="drawer-heading"><div><small>User-approved folder</small><h2>Product screens</h2></div><button onClick={() => setShowAssets(false)}>×</button></div>
        <div className="asset-tools"><button onClick={() => filesInputRef.current?.click()}>Choose files</button><button onClick={() => folderInputRef.current?.click()}>Choose folder</button><input value={assetQuery} onChange={(event) => setAssetQuery(event.target.value)} placeholder="Search filenames" /></div>
        {assets.length === 0 ? <button className="empty-assets" onClick={() => filesInputRef.current?.click()}><strong>Choose 3–6 screenshots</strong><span>PNG/JPG files stay in this browser until you confirm Run.</span></button> : <div className="asset-shelf">{visibleAssets.map((asset) => {
          const selected = selectedAssetIds.includes(asset.id);
          return <div className={`shelf-card ${selected ? "selected" : ""}`} key={asset.id}><button onClick={() => toggleAsset(asset.id)}><span style={{ backgroundImage: `url(${asset.previewUrl})` }} /><strong>{asset.name}</strong><small>{selected ? "Selected for brief" : "Select"}</small></button><button className="place-button" disabled={!selected} onClick={() => reportAction(handleToolCall({ name: "set_scene_asset", args: { scene_id: selectedScene.id, asset_id: asset.id, rationale: "Chosen by the user from the approved folder" } }))}>Place in {selectedScene.id}</button></div>;
        })}</div>}
        <div className="asset-count">{selectedAssetIds.length}/3–6 selected for the run</div>
      </aside>}

      {(showResults || runNonce > 0) && backendProjectId && <RunResults visible={showResults} apiBase={process.env.NEXT_PUBLIC_PREFLIGHT_API_BASE} projectId={backendProjectId} runNonce={runNonce} onClose={() => setShowResults(false)} onProgress={onRunProgress} />}

      {showTranscript && <aside className="transcript-drawer">
        <div className="drawer-heading"><div><small>One shared conversation</small><h2>Director transcript</h2></div><button onClick={() => setShowTranscript(false)}>×</button></div>
        <div>{allTranscript.length ? allTranscript.map((line) => <article key={line.id} className={line.role}><span>{line.role === "director" ? "Director" : line.role === "user" ? "You" : "Canvas"}</span><p>{line.text}</p></article>) : <p className="empty-transcript">Enable Live or type a command. Transcripts appear here.</p>}</div>
      </aside>}

      {showConsole && <DirectorConsole
        events={consoleEvents}
        steps={journey}
        liveUserText={director.liveUserText}
        liveDirectorText={director.liveDirectorText}
        liveState={liveLabel}
        onClose={() => setShowConsole(false)}
        narrow={showResults || showBrief || showAssets}
      />}

      <section className={`composer-dock ${voiceOpen ? "is-voice-mode" : ""}`}>
        <div className="composer-text-mode" aria-hidden={voiceOpen} inert={voiceOpen}
          onTransitionEnd={(event) => { if (!voiceOpen && event.target === event.currentTarget && event.propertyName === "opacity") voiceButtonRef.current?.focus(); }}>
        {latestLine && !voiceOpen && <button className="latest-caption" onClick={() => setShowTranscript(true)}><span>{director.liveDirectorText ? "Director" : director.liveUserText ? "You" : "Session"}</span>{latestLine}</button>}
        <VoiceBeam
          className="director-beam"
          level={() => director.isSpeaking ? director.outputLevel : director.state === "listening" ? director.inputLevel : 0}
          processing={director.isProcessing}
          active={!voiceOpen && (director.isSpeaking || director.state === "listening" || director.isProcessing)}
          paused={visualsPaused || voiceOpen}
          type="default"
          colorVariant="sunset"
          colors={["#FF5A36", "#F2472C", "#FF773F", "#CB3828", "#FF9650", "#A82923", "#E45432"]}
          bandColors={{ core: "#FFE1C7", above: "#FF773F", mid: "#FF5A36", below: "#CB3828" }}
          staticColors
          strength={0.45}
          idle={0}
          theme="dark"
        >
          <form className="canvas-composer" onSubmit={(event) => void submitComposer(event)}>
            <input value={composerText} onChange={(event) => setComposerText(event.target.value)} placeholder="Ask the Director…" aria-label="Message the Director" />
            <button
              ref={voiceButtonRef}
              className={`mic-button ${director.state === "listening" ? "live" : ""}`}
              type="button"
              onClick={voiceOpen ? closeVoice : openVoice}
              aria-label={voiceOpen ? "Close voice conversation" : "Start voice conversation"}
              aria-expanded={voiceOpen}
              aria-controls="director-voice-mode"
              title="Talk to Director"
            >{director.state === "listening" ? <ThinkingOrb state={director.isSpeaking ? "composing" : director.isProcessing ? "working" : "listening"} size={20} theme="dark" color="#FF9B80" paused={visualsPaused} aria-label="Live voice active" /> : <VoiceIcon />}</button>
            <button className="send-button" type="submit" disabled={!composerText.trim()} aria-label="Send">↗</button>
          </form>
        </VoiceBeam>
        {director.error && !voiceOpen && <div className="composer-error" role="alert">{director.error}</div>}
        </div>
        <DirectorVoicePresence open={voiceOpen} director={director} paused={visualsPaused} anchorRef={voiceButtonRef}
          onClose={closeVoice} onRetry={openVoice} onTranscript={() => setShowTranscript(true)} />
        <div className="composer-meta"><span>{voiceOpen ? "Gemini Live · voice mode" : "Gemini Live"}</span><button className="console-toggle" onClick={() => setShowConsole((current) => !current)}>{showConsole ? "▾ Hide console" : `▴ Console · ${journeyDone}/${journeyStates.length}`}</button><span className={`job-state ${jobState}`}>{jobMessage}</span></div>
      </section>

      {confirmSummary && <div className="modal-backdrop" role="presentation">
        <section className="run-modal" role="dialog" aria-modal="true" aria-labelledby="run-title">
          <small>Nothing starts until you confirm</small><h2 id="run-title">{readyToConfirm ? "Which picture?" : "Almost ready"}</h2>
          <p>Choose how the three 15-second videos are built, then start the run. One mode per run.</p>
          <PictureTrackCards
            mode={brief.render_mode ?? "showcase"}
            photoUrl={assets.find((asset) => selectedAssetIds.includes(asset.id))?.previewUrl}
            onChange={(next) => {
              updateRenderMode(next);
              requestRunConfirmation();
            }}
          />
          <ul>
            <li className={readiness.brief ? "ready" : ""}><span>{readiness.brief ? `Brief: ${brief.product_name} · goal ${brief.goal}` : `Brief is missing: ${missingBrief.join(", ")}`}</span>{!readiness.brief && <button onClick={() => { cancelRunConfirmation(); setShowBrief(true); }}>Fill in brief</button>}</li>
            <li className={readiness.screens ? "ready" : ""}><span>{readiness.screens ? `${selectedAssetIds.length} screenshots selected` : `Screenshots: ${selectedAssetIds.length} selected, need 3–6`}</span>{!readiness.screens && <button onClick={() => { cancelRunConfirmation(); filesInputRef.current?.click(); }}>Add screenshots</button>}</li>
            <li className={readiness.concepts ? "ready" : ""}><span>Three variants · A, B, C · 15 seconds each</span></li>
          </ul>
          <div className="modal-warning">Planning, rendering, Gemini evaluation and TRIBE require their connected services. No neural or audience result is guaranteed.{brief.render_mode === "generative_motion" ? " Generative motion uses Vision and falls back to exact photos if it is unsure." : ""}</div>
          <div className="modal-actions"><button onClick={cancelRunConfirmation}>Keep editing</button><button className="confirm-run" disabled={!readyToConfirm || jobState === "saving"} onClick={() => reportAction(confirmRun(runApprovalRef.current ?? ""))}>{jobState === "saving" ? "Starting…" : readyToConfirm ? "Start run" : "Fix the items above"}</button></div>
        </section>
      </div>}
    </main>
  );
}
