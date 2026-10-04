import { Composition } from "remotion";
import type { CompositionSpec } from "../spec/types.generated.ts";
import { PreflightVideo } from "./PreflightVideo.tsx";
import { COMPOSITION_ID } from "./id.ts";
import { FRAME } from "./tokens.ts";

/** Placeholder props so the Remotion Studio can open the composition; renders always pass a real spec. */
const PREVIEW_SPEC: CompositionSpec = {
  variant_id: "A",
  width: FRAME.width,
  height: FRAME.height,
  fps: 30,
  duration_frames: 90,
  theme: { background: "#f5f5f7", foreground: "#1d1d1f", accent: "#5b5bd6", font_family: "Inter" },
  scenes: [
    {
      start_frame: 0,
      end_frame: 90,
      text: "Preview",
      source_field: "product_name",
      screenshot: "preview.png",
      layout: "text_only",
      transition_in: "cut",
    },
  ],
  cta: "Preview",
  cta_source_field: "product_name",
  wordmark: "Preview",
  headline: "Preview",
  headline_source_field: "product_name",
};

/** Dimensions, frame rate and length always come from the spec, never from constants. */
export const Root: React.FC = () => (
  <Composition
    id={COMPOSITION_ID}
    component={PreflightVideo}
    width={FRAME.width}
    height={FRAME.height}
    fps={30}
    durationInFrames={PREVIEW_SPEC.duration_frames}
    defaultProps={{ spec: PREVIEW_SPEC }}
    calculateMetadata={({ props }) => ({
      durationInFrames: props.spec.duration_frames,
      width: props.spec.width ?? FRAME.width,
      height: props.spec.height ?? FRAME.height,
      fps: props.spec.fps ?? 30,
    })}
  />
);
