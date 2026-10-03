import type { OrbState } from "thinking-orbs";

export type DirectorPresenceState = "idle" | "requesting" | "connecting" | "listening" | "error";

export function directorOrbState(
  state: DirectorPresenceState,
  isSpeaking: boolean,
  isProcessing: boolean,
): OrbState {
  if (state === "requesting" || state === "connecting") return "connecting";
  if (isSpeaking) return "composing";
  if (isProcessing) return "working";
  if (state === "listening") return "listening";
  return "breathing";
}
