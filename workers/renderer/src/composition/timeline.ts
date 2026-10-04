/** Pure timeline maths: which scenes are on screen and when the CTA end card takes over. */
import type { CompositionSpec, SceneSpec } from "../spec/types.generated.ts";
import { ctaStartFrameFor, TRANSITION_FRAMES } from "./tokens.ts";

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
  const ctaStart = ctaStartFrame(spec);
  return spec.scenes
    .map((scene, index) => {
      const next = spec.scenes[index + 1];
      const overlap =
        next !== undefined && next.transition_in !== "cut" && next.start_frame < ctaStart
          ? TRANSITION_FRAMES
          : 0;
      const from = scene.start_frame;
      if (from >= ctaStart) return null;
      const end = Math.min(scene.end_frame, ctaStart);
      return {
        index,
        scene,
        from,
        duration: end - from + overlap,
        overlap,
      };
    })
    .filter((window): window is SceneWindow => window !== null);
}

/** First frame of the locked 3 s end card. */
export function ctaStartFrame(spec: CompositionSpec): number {
  const fps = spec.fps ?? 30;
  return ctaStartFrameFor(spec.duration_frames, fps);
}
