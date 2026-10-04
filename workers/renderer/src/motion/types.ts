/** Hand-checked types matching backend MotionSpec. Isolated from CompositionSpec. */

export type LayerKind = "panel" | "button" | "chart" | "text" | "icon" | "other";

export interface MotionLayer {
  readonly id: string;
  readonly kind: LayerKind;
  readonly bbox_norm: readonly [number, number, number, number];
  readonly confidence: number;
  readonly path?: string | null;
  readonly label?: string | null;
}

export interface MotionShot {
  readonly screenshot: string;
  readonly start_frame: number;
  readonly end_frame: number;
  readonly text: string;
  readonly source_field: string;
  readonly layers: readonly MotionLayer[];
  readonly t_start: number;
  readonly t_end: number;
}

export interface MotionTheme {
  readonly background: string;
  readonly foreground: string;
  readonly accent: string;
  readonly font_family: string;
}

export interface MotionSpec {
  readonly variant_id: string;
  readonly width: 1080;
  readonly height: 1920;
  readonly fps: 60;
  readonly duration_frames: 900;
  readonly theme: MotionTheme;
  readonly shots: readonly MotionShot[];
  readonly cta: string;
  readonly cta_source_field: string;
  readonly wordmark?: string;
  readonly headline?: string;
  readonly headline_source_field?: string;
  readonly logo?: string | null;
  readonly underlay?: boolean;
}
