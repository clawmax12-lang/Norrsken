"use client";

import { useEffect, useRef } from "react";
import type { OrbState } from "thinking-orbs";
import { MODE_FRAMES, paintFrame, resolvePreset } from "thinking-orbs/engine";

/** The library's tuned 64 geometry, painted at native dock resolution instead of stretching a bitmap. */
export function DirectorOrb({ state, paused, label }: { state: OrbState; paused: boolean; label: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    const preset = resolvePreset(state, 64);
    let frameId = 0;
    let alive = true;
    const paint = (time: number) => {
      const pixels = Math.round(canvas.clientWidth * Math.min(2, window.devicePixelRatio || 1));
      if (canvas.width !== pixels) { canvas.width = pixels; canvas.height = pixels; }
      context.setTransform(pixels / 64, 0, 0, pixels / 64, 0, 0);
      context.clearRect(0, 0, 64, 64);
      paintFrame(context, MODE_FRAMES[preset.mode](64, time / 1000 * preset.speed, preset.opts), true);
      if (alive && !paused && !document.hidden) frameId = requestAnimationFrame(paint);
    };
    const refresh = () => {
      cancelAnimationFrame(frameId);
      paint(paused ? 600 : performance.now());
    };
    refresh();
    const resize = new ResizeObserver(refresh);
    resize.observe(canvas);
    document.addEventListener("visibilitychange", refresh);
    return () => { alive = false; cancelAnimationFrame(frameId); resize.disconnect(); document.removeEventListener("visibilitychange", refresh); };
  }, [state, paused]);
  return <canvas ref={ref} className="director-orb-canvas" role="img" aria-label={label} />;
}
