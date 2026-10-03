/** Pure timeline maths: which scenes are on screen and when the CTA end card takes over. */
import type { CompositionSpec, SceneSpec } from "../spec/types.generated.ts";
import { CTA_CARD_MAX_FRAMES, CTA_CARD_SCENE_SHARE, TRANSITION_FRAMES } from "./tokens.ts";

export interface SceneWindow {
  readonly index: number;
  readonly scene: SceneSpec;
  /** First frame the scene is mounted. */
  readonly from: number;
  /** Frames mounted: its own length plus the overlap while the next scene transitions in. */
  readonly duration: number;
  /** Frames the next scene takes to cover this one (0 for a cut or the last scene). */
  readonly overlap: number;
}

export function sceneWindows(spec: CompositionSpec): SceneWindow[] {
  return spec.scenes.map((scene, index) => {
    const next = spec.scenes[index + 1];
    const overlap = next !== undefined && next.transition_in !== "cut" ? TRANSITION_FRAMES : 0;
    return {
      index,
      scene,
      from: scene.start_frame,
      duration: scene.end_frame - scene.start_frame + overlap,
      overlap,
    };
  });
}

/** First frame of the CTA end card: the tail of the last scene, capped so the scene still reads. */
export function ctaStartFrame(spec: CompositionSpec): number {
  const last = spec.scenes[spec.scenes.length - 1];
  if (last === undefined) throw new Error("spec has no scenes");
  const length = last.end_frame - last.start_frame;
  const card = Math.min(CTA_CARD_MAX_FRAMES, Math.max(1, Math.floor(length * CTA_CARD_SCENE_SHARE)));
  return last.end_frame - card;
}
