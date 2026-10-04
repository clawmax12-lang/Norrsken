/** Speech lead matches soundtrack planning: first word after the scene has settled. */
export const SPEECH_LEAD_S = 0.3;
export const TEXT_IN_S = 0.6;
export const TEXT_HOLD_MIN_S = 1.5;

export function splitWords(text: string): string[] {
  return text.trim().split(/\s+/).filter(Boolean);
}

/** Whole line lands once, then holds. Never stagger words across the remaining shot. */
export function lineLandFrame(fps: number): number {
  return Math.round(SPEECH_LEAD_S * fps);
}

export function canAnimateIn(durationFrames: number, fps: number): boolean {
  return durationFrames / fps >= TEXT_HOLD_MIN_S;
}
