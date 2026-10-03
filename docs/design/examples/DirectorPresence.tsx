"use client";

// Controlled presentation example; the existing Live owner supplies real state.
import type { ReactNode } from "react";
import { ThinkingOrb, type OrbState } from "thinking-orbs";
import { VoiceBeam } from "voice-glow";

export type DirectorPhase = "idle" | "connecting" | "listening" | "thinking" | "speaking" | "error";

export type DirectorPresenceProps = {
  phase: DirectorPhase;
  micActive: boolean;
  outputMuted: boolean;
  inputLevel: () => number;
  outputLevel: () => number;
  // Host supplies reduced-motion, hidden-tab and manual visual-pause state.
  paused: boolean;
  children: ReactNode;
};

const PHASE_COPY: Record<DirectorPhase, string> = {
  idle: "Director offline",
  connecting: "Connecting to Gemini",
  listening: "Listening",
  thinking: "Working on your request",
  speaking: "Director speaking",
  error: "Connection needs attention",
};

function normalizedLevel(read: () => number) {
  const level = read();
  return Number.isFinite(level) ? Math.max(0, Math.min(1, level)) : 0;
}

export function DirectorPresence({
  phase, micActive, outputMuted, inputLevel, outputLevel, paused, children,
}: DirectorPresenceProps) {
  const speaking = phase === "speaking" && !outputMuted;
  const listening = phase === "listening" && micActive;
  const processing = phase === "thinking";
  const frozen = paused;
  const orbState: OrbState = phase === "connecting" ? "connecting"
    : speaking ? "composing" : processing ? "working" : listening ? "listening" : "breathing";
  const status = phase === "speaking" && outputMuted ? "Director output muted"
    : phase === "listening" && !micActive ? "Microphone off" : PHASE_COPY[phase];

  return (
    <div className="pf-director-presence">
      <div className="pf-director-orb-space" aria-hidden="true">
        <div className="pf-director-orb" data-speaking={speaking && !frozen}>
          <ThinkingOrb
            state={orbState}
            size={64}
            theme="dark"
            color="#FF5A36"
            paused={frozen || phase === "idle" || phase === "error"}
          />
        </div>
      </div>
      <span className="pf-director-status" role="status">{status}</span>
      <VoiceBeam
        className="pf-director-prompt"
        type="default"
        theme="dark"
        colorVariant="sunset"
        colors={["#FF5A36", "#F2472C", "#FF773F", "#CB3828", "#FF9650", "#A82923", "#E45432"]}
        bandColors={{ core: "#FFE1C7", above: "#FF773F", mid: "#FF5A36", below: "#CB3828" }}
        staticColors
        strength={0.45}
        idle={0}
        active={speaking || listening || processing}
        paused={frozen}
        processing={processing}
        level={() => speaking ? normalizedLevel(outputLevel) : listening ? normalizedLevel(inputLevel) : 0}
      >
        {children}
      </VoiceBeam>
    </div>
  );
}
