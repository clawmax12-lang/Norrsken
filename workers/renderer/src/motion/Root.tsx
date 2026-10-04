import { Composition } from "remotion";
import { FRAME } from "../composition/tokens.ts";
import { MOTION_COMPOSITION_ID, MOTION_FPS, MOTION_FRAMES } from "./id.ts";
import { MotionVideo } from "./MotionVideo.tsx";
import type { MotionSpec } from "./types.ts";

const PREVIEW: MotionSpec = {
  variant_id: "A",
  width: 1080,
  height: 1920,
  fps: 60,
  duration_frames: MOTION_FRAMES,
  theme: { background: "#f5f5f7", foreground: "#1d1d1f", accent: "#5b5bd6", font_family: "Inter" },
  shots: [
    {
      screenshot: "preview.png",
      start_frame: 0,
      end_frame: MOTION_FRAMES,
      text: "Preview",
      source_field: "product_name",
      t_start: 0,
      t_end: 15,
      layers: [
        { id: "panel", kind: "panel", bbox_norm: [0.12, 0.28, 0.76, 0.42], confidence: 0.9 },
        { id: "cta", kind: "button", bbox_norm: [0.28, 0.74, 0.44, 0.08], confidence: 0.88, label: "Preview" },
      ],
    },
  ],
  cta: "Preview",
  cta_source_field: "product_name",
  wordmark: "Preview",
  headline: "Preview",
  headline_source_field: "product_name",
  underlay: true,
};

export const Root: React.FC = () => (
  <Composition
    id={MOTION_COMPOSITION_ID}
    component={MotionVideo}
    width={FRAME.width}
    height={FRAME.height}
    fps={MOTION_FPS}
    durationInFrames={MOTION_FRAMES}
    defaultProps={{ spec: PREVIEW }}
    calculateMetadata={({ props }) => ({
      durationInFrames: props.spec.duration_frames,
      width: props.spec.width ?? FRAME.width,
      height: props.spec.height ?? FRAME.height,
      fps: props.spec.fps ?? MOTION_FPS,
    })}
  />
);
