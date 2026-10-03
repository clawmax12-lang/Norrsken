"use client";

import { useEffect, useRef } from "react";
import type { OrbState } from "thinking-orbs";
import { MODE_FRAMES, paintFrame, resolvePreset } from "thinking-orbs/engine";

/** Reference 10 is the library's composing sash, not its breathing/loading ring. */
export function DirectorOrb({ state, paused, label, speaking, level }: {
  state: OrbState; paused: boolean; label: string; speaking: boolean; level: () => number;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const clockRef = useRef<number | null>(null);
  const audioRef = useRef({ speaking, level });
  useEffect(() => { audioRef.current = { speaking, level }; }, [speaking, level]);
  useEffect(() => {
    const canvas = ref.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    // Preserve the reference silhouette in every phase, including disconnected/error.
    // State is communicated by status text and cadence, never a replacement spinner.
    const preset = resolvePreset("composing", 64);
    let frameId = 0;
    let alive = true;
    let envelope = 0;
    let clock = clockRef.current ?? 0.6 * preset.speed;
    let lastTime = 0;
    const paint = (time: number) => {
      const delta = lastTime ? Math.min(0.05, Math.max(0, (time - lastTime) / 1000)) : 1 / 60;
      lastTime = time;
      const audio = audioRef.current;
      const measured = audio.speaking && !paused ? audio.level() : 0;
      const target = Number.isFinite(measured) ? Math.min(1, Math.max(0, measured)) : 0;
      envelope += (target - envelope) * (1 - Math.exp(-delta / (target > envelope ? 0.06 : 0.16)));
      // Interruption/mute must reset visual speech immediately, not keep a stale pulse.
      if (!audio.speaking || paused) envelope = 0;
      canvas.style.setProperty("--voice-amplitude-scale", String(1 + envelope * 0.16));
      const pixels = Math.round(canvas.clientWidth * Math.min(2, window.devicePixelRatio || 1));
      if (canvas.width !== pixels) { canvas.width = pixels; canvas.height = pixels; }
      context.setTransform(pixels / 64, 0, 0, pixels / 64, 0, 0);
      context.clearRect(0, 0, 64, 64);
      if (!paused && !document.hidden) clock += delta * preset.speed * (state === "working" ? 0.8 : 0.45);
      clockRef.current = clock;
      const frame = MODE_FRAMES[preset.mode](64, clock, { ...preset.opts, wobMul: 0.65 + envelope * 1.8 });
      // The owner removed the white substrate: neutral light ink on black canvas.
      paintFrame(context, frame, true);
      if (alive && !paused && !document.hidden) frameId = requestAnimationFrame(paint);
    };
    const refresh = () => {
      cancelAnimationFrame(frameId);
      lastTime = 0;
      paint(performance.now());
    };
    refresh();
    const resize = new ResizeObserver(refresh);
    resize.observe(canvas);
    document.addEventListener("visibilitychange", refresh);
    return () => { alive = false; cancelAnimationFrame(frameId); resize.disconnect(); document.removeEventListener("visibilitychange", refresh); };
  }, [state, paused]);
  return <canvas ref={ref} className="director-orb-canvas" data-orb-state={state} role="img" aria-label={label} />;
}
