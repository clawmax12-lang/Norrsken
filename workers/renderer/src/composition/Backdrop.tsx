import { AbsoluteFill, Img, OffthreadVideo, staticFile } from "remotion";
import type { GeneratedAsset, Theme } from "../spec/types.generated.ts";
import { withAlpha } from "./color.ts";
import { FRAME } from "./tokens.ts";

/** Parallax: the backdrop drifts this many px over the scene, far less than the device. */
const DRIFT_PX = 70;
const SCENE_HUES = [
  { x: 18, y: 12 },
  { x: 86, y: 30 },
  { x: 24, y: 78 },
  { x: 82, y: 64 },
];

interface BackdropProps {
  readonly theme: Theme;
  readonly asset: GeneratedAsset | null | undefined;
  readonly sceneIndex: number;
  /** 0-1 position through the scene, drives the slow drift. */
  readonly t: number;
}

/** Generated studies when present, otherwise soft accent light on the stage colour. */
export const Backdrop: React.FC<BackdropProps> = ({ theme, asset, sceneIndex, t }) => {
  const drift = (t - 0.5) * DRIFT_PX;
  if (asset === null || asset === undefined) {
    return <TemplateBackdrop theme={theme} sceneIndex={sceneIndex} drift={drift} />;
  }
  const media = { width: FRAME.width, height: FRAME.height, objectFit: "cover", transform: `scale(1.14) translateY(${drift}px)` } as const;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {asset.kind === "video" ? (
        <OffthreadVideo src={staticFile(asset.path)} muted style={media} />
      ) : (
        <Img src={staticFile(asset.path)} style={media} />
      )}
      <AbsoluteFill
        style={{ background: `linear-gradient(180deg, ${withAlpha(theme.background, 0.18)} 0%, ${withAlpha(theme.background, 0.04)} 42%, transparent 100%)` }}
      />
    </AbsoluteFill>
  );
};

export const TemplateBackdrop: React.FC<{ theme: Theme; sceneIndex: number; drift: number }> = ({ theme, sceneIndex, drift }) => {
  const a = SCENE_HUES[sceneIndex % SCENE_HUES.length]!;
  const b = SCENE_HUES[(sceneIndex + 2) % SCENE_HUES.length]!;
  return (
    <AbsoluteFill
      style={{
        transform: `translateY(${drift}px) scale(1.1)`,
        background: [
          `radial-gradient(900px 900px at ${a.x}% ${a.y}%, ${withAlpha(theme.accent, 0.2)}, transparent 70%)`,
          `radial-gradient(760px 760px at ${b.x}% ${b.y}%, ${withAlpha(theme.accent, 0.11)}, transparent 70%)`,
          `radial-gradient(420px 280px at 50% 18%, ${withAlpha(theme.foreground, 0.08)}, transparent 72%)`,
        ].join(", "),
      }}
    />
  );
};
