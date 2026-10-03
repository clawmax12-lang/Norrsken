"use client";

import { PointerEvent, WheelEvent, useCallback, useEffect, useRef, useState } from "react";

type InspectorNode = {
  eyebrow: string;
  title: string;
  description: string;
  branches?: string;
};

type StoryTreeCanvasProps = {
  onInspect: (node: InspectorNode) => void;
};

type Point = { x: number; y: number };

const TAU = Math.PI * 2;
const HOOK_COUNT = 5;
const CONTINUATIONS_PER_HOOK = 5;
const BEATS_PER_CONTINUATION = 5;
const CONTINUATION_COUNT = HOOK_COUNT * CONTINUATIONS_PER_HOOK;
const BEAT_COUNT = CONTINUATION_COUNT * BEATS_PER_CONTINUATION;
const TOTAL_NODES = 1 + HOOK_COUNT + CONTINUATION_COUNT + BEAT_COUNT;
const MAX_RADIUS = 33_000;

const hookNames = [
  "Start with the blank canvas",
  "Open on the finished launch",
  "Lead with a founder question",
];

function hookAngle(hook: number) {
  return -Math.PI / 2 + (hook / HOOK_COUNT) * TAU;
}

function polar(radius: number, angle: number): Point {
  return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
}

function hookPosition(hook: number) {
  return polar(9_000, hookAngle(hook));
}

function continuationAngle(hook: number, continuation: number) {
  const sector = TAU / HOOK_COUNT;
  return hookAngle(hook) + ((continuation - (CONTINUATIONS_PER_HOOK - 1) / 2) / CONTINUATIONS_PER_HOOK) * sector * 0.82;
}

function continuationPosition(hook: number, continuation: number) {
  return polar(18_000 + (continuation % 5) * 850, continuationAngle(hook, continuation));
}

function beatPosition(hook: number, continuation: number, beat: number) {
  const sector = TAU / HOOK_COUNT;
  const column = beat % 5;
  const row = Math.floor(beat / 5);
  const angle = continuationAngle(hook, continuation) + (column - 2) * (sector / CONTINUATIONS_PER_HOOK) * 0.16;
  return polar(30_500 + row * 1_700 + (continuation % 3) * 90, angle);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function generationProgress(progress: number, start: number, end: number) {
  return clamp((progress - start) / (end - start), 0, 1);
}

export default function StoryTreeCanvas({ onInspect }: StoryTreeCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const frameRef = useRef<number | null>(null);
  const startRef = useRef(0);
  const dragRef = useRef({ active: false, moved: false, x: 0, y: 0, offsetX: 0, offsetY: 0 });
  const viewRef = useRef({ zoom: 0.008, fitZoom: 0.008, offsetX: 0, offsetY: 0 });
  const [zoomLabel, setZoomLabel] = useState("0.8%");
  const [replay, setReplay] = useState(0);
  const selectedRef = useRef({ hook: 0, continuation: 0 });
  const [isDragging, setIsDragging] = useState(false);

  const project = useCallback((point: Point) => {
    const view = viewRef.current;
    return { x: point.x * view.zoom + view.offsetX, y: point.y * view.zoom + view.offsetY };
  }, []);

  const draw = useCallback((progress: number) => {
    const canvas = canvasRef.current;
    const viewport = viewportRef.current;
    if (!canvas || !viewport) return;

    const bounds = viewport.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const targetWidth = Math.max(1, Math.floor(bounds.width * dpr));
    const targetHeight = Math.max(1, Math.floor(bounds.height * dpr));
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
      canvas.width = targetWidth;
      canvas.height = targetHeight;
      canvas.style.width = `${bounds.width}px`;
      canvas.style.height = `${bounds.height}px`;
    }

    const context = canvas.getContext("2d");
    if (!context) return;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.clearRect(0, 0, bounds.width, bounds.height);

    const visible = (point: Point, margin = 4) => point.x > -margin && point.x < bounds.width + margin && point.y > -margin && point.y < bounds.height + margin;
    const root = project({ x: 0, y: 0 });
    const hookReveal = Math.floor(generationProgress(progress, 0.04, 0.24) * HOOK_COUNT);
    const continuationReveal = Math.floor(generationProgress(progress, 0.2, 0.6) * CONTINUATION_COUNT);
    const beatReveal = Math.floor(generationProgress(progress, 0.54, 1) * BEAT_COUNT);

    context.lineCap = "round";
    context.lineWidth = 0.85;
    context.strokeStyle = "rgba(132,132,132,.62)";
    context.beginPath();
    for (let hook = 0; hook < hookReveal; hook += 1) {
      const end = project(hookPosition(hook));
      context.moveTo(root.x, root.y);
      context.lineTo(end.x, end.y);
    }
    context.stroke();

    context.lineWidth = 0.7;
    context.strokeStyle = "rgba(104,104,104,.48)";
    context.beginPath();
    for (let index = 0; index < continuationReveal; index += 1) {
      const hook = Math.floor(index / CONTINUATIONS_PER_HOOK);
      const continuation = index % CONTINUATIONS_PER_HOOK;
      const start = project(hookPosition(hook));
      const end = project(continuationPosition(hook, continuation));
      if (!visible(start, 80) && !visible(end, 80)) continue;
      context.moveTo(start.x, start.y);
      context.lineTo(end.x, end.y);
    }
    context.stroke();

    context.lineWidth = 0.5;
    context.strokeStyle = "rgba(88,88,88,.38)";
    context.beginPath();
    const outerEdgeStep = BEAT_COUNT > 5_000 && progress < 0.98 ? 10 : 1;
    for (let index = 0; index < beatReveal; index += outerEdgeStep) {
      const continuationIndex = Math.floor(index / BEATS_PER_CONTINUATION);
      const beat = index % BEATS_PER_CONTINUATION;
      const hook = Math.floor(continuationIndex / CONTINUATIONS_PER_HOOK);
      const continuation = continuationIndex % CONTINUATIONS_PER_HOOK;
      const start = project(continuationPosition(hook, continuation));
      const end = project(beatPosition(hook, continuation, beat));
      if (!visible(start, 90) && !visible(end, 90)) continue;
      context.moveTo(start.x, start.y);
      context.lineTo(end.x, end.y);
    }
    context.stroke();

    if (beatReveal > 0) {
      context.fillStyle = "rgba(168,168,168,.76)";
      const dotSize = viewRef.current.zoom < 0.01 ? 1.7 : clamp(viewRef.current.zoom * 160, 2, 5);
      for (let index = 0; index < beatReveal; index += 1) {
        const continuationIndex = Math.floor(index / BEATS_PER_CONTINUATION);
        const beat = index % BEATS_PER_CONTINUATION;
        const hook = Math.floor(continuationIndex / CONTINUATIONS_PER_HOOK);
        const continuation = continuationIndex % CONTINUATIONS_PER_HOOK;
        const point = project(beatPosition(hook, continuation, beat));
        if (!visible(point, 2)) continue;
        context.fillRect(point.x - dotSize / 2, point.y - dotSize / 2, dotSize, dotSize);
      }
    }

    context.fillStyle = "rgba(188,188,188,.9)";
    const continuationSize = clamp(viewRef.current.zoom * 260, 3.5, 8);
    for (let index = 0; index < continuationReveal; index += 1) {
      const hook = Math.floor(index / CONTINUATIONS_PER_HOOK);
      const continuation = index % CONTINUATIONS_PER_HOOK;
      const point = project(continuationPosition(hook, continuation));
      if (!visible(point, 3)) continue;
      context.fillRect(point.x - continuationSize / 2, point.y - continuationSize / 2, continuationSize, continuationSize);
    }

    for (let hook = 0; hook < hookReveal; hook += 1) {
      const point = project(hookPosition(hook));
      if (!visible(point, 8)) continue;
      const size = hook === selectedRef.current.hook ? 8 : 6;
      context.beginPath();
      context.fillStyle = hook === selectedRef.current.hook ? "#f1f1f1" : "#9a9a9a";
      context.arc(point.x, point.y, size, 0, TAU);
      context.fill();
    }

    if (progress >= 0.98) {
      const activeHook = project(hookPosition(selectedRef.current.hook));
      const activeContinuation = project(continuationPosition(selectedRef.current.hook, selectedRef.current.continuation));
      context.lineWidth = 1.2;
      context.strokeStyle = "rgba(255,255,255,.88)";
      context.beginPath();
      context.moveTo(root.x, root.y);
      context.lineTo(activeHook.x, activeHook.y);
      context.lineTo(activeContinuation.x, activeContinuation.y);
      context.stroke();

      context.lineWidth = 0.55;
      context.strokeStyle = "rgba(255,255,255,.4)";
      context.beginPath();
      for (let beat = 0; beat < BEATS_PER_CONTINUATION; beat += 1) {
        const point = project(beatPosition(selectedRef.current.hook, selectedRef.current.continuation, beat));
        context.moveTo(activeContinuation.x, activeContinuation.y);
        context.lineTo(point.x, point.y);
      }
      context.stroke();

      context.fillStyle = "#fff";
      context.beginPath();
      context.arc(activeContinuation.x, activeContinuation.y, 3.5, 0, TAU);
      context.fill();
    }

    context.fillStyle = "#fff";
    context.beginPath();
    context.arc(root.x, root.y, 6, 0, TAU);
    context.fill();
    context.strokeStyle = "rgba(255,255,255,.24)";
    context.lineWidth = 1;
    context.beginPath();
    context.arc(root.x, root.y, 11, 0, TAU);
    context.stroke();

    if (viewRef.current.zoom > 0.01) {
      const activeHook = project(hookPosition(selectedRef.current.hook));
      const activeContinuation = project(continuationPosition(selectedRef.current.hook, selectedRef.current.continuation));
      context.font = "600 10px Inter, sans-serif";
      context.fillStyle = "rgba(245,245,245,.94)";
      context.fillText(`HOOK ${String(selectedRef.current.hook + 1).padStart(2, "0")}`, activeHook.x + 10, activeHook.y - 4);
      context.font = "500 9px Inter, sans-serif";
      context.fillStyle = "rgba(180,180,180,.88)";
      context.fillText(`BEAT ${String(selectedRef.current.continuation + 1).padStart(2, "0")} · 5 NEXT VERSIONS`, activeContinuation.x + 9, activeContinuation.y - 4);
    }
  }, [project]);

  const redraw = useCallback(() => draw(1), [draw]);

  const fitAll = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const bounds = viewport.getBoundingClientRect();
    const fitZoom = Math.min(bounds.width, bounds.height) * 0.88 / (MAX_RADIUS * 2);
    viewRef.current = { zoom: fitZoom, fitZoom, offsetX: bounds.width / 2, offsetY: bounds.height / 2 };
    setZoomLabel(`${(fitZoom * 100).toFixed(2)}%`);
    redraw();
  }, [redraw]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const observer = new ResizeObserver(() => fitAll());
    observer.observe(viewport);
    fitAll();
    return () => observer.disconnect();
  }, [fitAll]);

  useEffect(() => {
    startRef.current = Date.now();
    const completionTimer = window.setTimeout(() => draw(1), 2_850);
    const animate = () => {
      const elapsed = Date.now() - startRef.current;
      const progress = clamp(elapsed / 2_800, 0, 1);
      draw(progress);
      if (progress < 1) frameRef.current = window.requestAnimationFrame(animate);
    };
    if (frameRef.current) window.cancelAnimationFrame(frameRef.current);
    frameRef.current = window.requestAnimationFrame(animate);
    return () => {
      window.clearTimeout(completionTimer);
      if (frameRef.current) window.cancelAnimationFrame(frameRef.current);
    };
  }, [draw, replay]);

  const setZoomAt = (nextZoom: number, centerX: number, centerY: number) => {
    const view = viewRef.current;
    const zoom = clamp(nextZoom, view.fitZoom * 0.62, 1.4);
    const worldX = (centerX - view.offsetX) / view.zoom;
    const worldY = (centerY - view.offsetY) / view.zoom;
    view.offsetX = centerX - worldX * zoom;
    view.offsetY = centerY - worldY * zoom;
    view.zoom = zoom;
    setZoomLabel(zoom >= 0.1 ? `${Math.round(zoom * 100)}%` : `${(zoom * 100).toFixed(2)}%`);
    redraw();
  };

  const handleWheel = (event: WheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const bounds = event.currentTarget.getBoundingClientRect();
    const factor = event.deltaY > 0 ? 0.78 : 1.28;
    setZoomAt(viewRef.current.zoom * factor, event.clientX - bounds.left, event.clientY - bounds.top);
  };

  const handlePointerDown = (event: PointerEvent<HTMLDivElement>) => {
    const view = viewRef.current;
    dragRef.current = { active: true, moved: false, x: event.clientX, y: event.clientY, offsetX: view.offsetX, offsetY: view.offsetY };
    event.currentTarget.setPointerCapture(event.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag.active) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
    viewRef.current.offsetX = drag.offsetX + dx;
    viewRef.current.offsetY = drag.offsetY + dy;
    redraw();
  };

  const inspectNearestNode = (screenX: number, screenY: number) => {
    let nearest: { distance: number; hook: number; continuation?: number; beat?: number } | null = null;
    const consider = (point: Point, hook: number, continuation?: number, beat?: number) => {
      const projected = project(point);
      const distance = Math.hypot(projected.x - screenX, projected.y - screenY);
      if (distance < (nearest?.distance ?? 14)) nearest = { distance, hook, continuation, beat };
    };

    for (let hook = 0; hook < HOOK_COUNT; hook += 1) consider(hookPosition(hook), hook);
    for (let hook = 0; hook < HOOK_COUNT; hook += 1) {
      for (let continuation = 0; continuation < CONTINUATIONS_PER_HOOK; continuation += 1) {
        consider(continuationPosition(hook, continuation), hook, continuation);
      }
    }
    for (let beat = 0; beat < BEATS_PER_CONTINUATION; beat += 1) {
      consider(beatPosition(selectedRef.current.hook, selectedRef.current.continuation, beat), selectedRef.current.hook, selectedRef.current.continuation, beat);
    }

    if (!nearest) return;
    const node = nearest as { distance: number; hook: number; continuation?: number; beat?: number };
    if (node.continuation === undefined) {
      selectedRef.current = { hook: node.hook, continuation: 0 };
      window.requestAnimationFrame(redraw);
      onInspect({
        eyebrow: `Hook ${String(node.hook + 1).padStart(2, "0")} of 5`,
        title: hookNames[node.hook] ?? `Opening direction ${String(node.hook + 1).padStart(2, "0")}`,
        description: "A complete opening branch. All 5 possible continuations are drawn directly beyond it.",
        branches: "5 visible continuations",
      });
      return;
    }

    selectedRef.current = { hook: node.hook, continuation: node.continuation };
    window.requestAnimationFrame(redraw);
    if (node.beat !== undefined) {
      onInspect({
        eyebrow: `Story beat ${String(node.hook + 1).padStart(2, "0")}.${String(node.continuation + 1).padStart(2, "0")}.${String(node.beat + 1).padStart(2, "0")}`,
        title: `Next-beat direction ${String(node.beat + 1).padStart(2, "0")}`,
        description: "One untested third-generation direction in this recursive storyline.",
        branches: "Prototype node",
      });
    } else {
      onInspect({
        eyebrow: `Continuation ${String(node.hook + 1).padStart(2, "0")}.${String(node.continuation + 1).padStart(2, "0")}`,
        title: `Continuation from Hook ${String(node.hook + 1).padStart(2, "0")}`,
        description: "One of 5 continuations from this hook. Its 5 next story beats are highlighted beyond it.",
        branches: "5 visible next beats",
      });
    }
  };

  const handlePointerUp = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    drag.active = false;
    setIsDragging(false);
    if (!drag.moved) {
      const bounds = event.currentTarget.getBoundingClientRect();
      inspectNearestNode(event.clientX - bounds.left, event.clientY - bounds.top);
    }
  };

  return (
    <div className="tree-universe-shell">
      <div
        className={`tree-universe-viewport ${isDragging ? "is-dragging" : ""}`}
        ref={viewportRef}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={() => { dragRef.current.active = false; setIsDragging(false); }}
      >
        <canvas ref={canvasRef} aria-label="A recursive storyline tree containing 5 hooks, 25 continuations, and 125 next story beats" />
      </div>

      <div className="universe-summary">
        <span className="universe-live-dot" />
        <strong>{TOTAL_NODES.toLocaleString()} nodes</strong>
        <span>Every branch rendered</span>
      </div>

      <div className="generation-legend" aria-label="Tree generations">
        <span><i />Idea <b>1</b></span>
        <span><i />Hooks <b>5</b></span>
        <span><i />Continuations <b>25</b></span>
        <span><i />Next beats <b>125</b></span>
      </div>

      <div className="universe-controls">
        <button type="button" onClick={() => setReplay((value) => value + 1)}>Replay growth</button>
        <button type="button" onClick={fitAll}>Fit all</button>
        <button type="button" aria-label="Zoom out" onClick={() => {
          const bounds = viewportRef.current?.getBoundingClientRect();
          if (bounds) setZoomAt(viewRef.current.zoom / 1.7, bounds.width / 2, bounds.height / 2);
        }}>−</button>
        <span>{zoomLabel}</span>
        <button type="button" aria-label="Zoom in" onClick={() => {
          const bounds = viewportRef.current?.getBoundingClientRect();
          if (bounds) setZoomAt(viewRef.current.zoom * 1.7, bounds.width / 2, bounds.height / 2);
        }}>+</button>
      </div>

      <div className="universe-hint">Scroll to zoom · drag to pan · click a node</div>
    </div>
  );
}
