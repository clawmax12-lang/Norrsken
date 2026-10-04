import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TemplateBackdrop } from "../composition/Backdrop.tsx";
import { useImageAspect } from "../composition/DeviceFrame.tsx";
import { FRAME } from "../composition/tokens.ts";
import type { Theme } from "../spec/types.generated.ts";
import { largestLayer, productRect, punchIn } from "./crop.ts";
import { KineticType } from "./KineticType.tsx";
import type { MotionLayer, MotionShot, MotionTheme } from "./types.ts";

const ENTER_SPRING = { damping: 13, stiffness: 150, mass: 0.7 } as const;

export { OVERLAP_FRAMES } from "./overlap.ts";

interface ShotProps {
  readonly shot: MotionShot;
  readonly theme: MotionTheme;
  readonly shotIndex: number;
  readonly overlap: number;
  readonly underlay: boolean;
}

export const MotionShotView: React.FC<ShotProps> = ({ shot, theme, shotIndex, overlap }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const aspect = useImageAspect(shot.screenshot);
  const length = shot.end_frame - shot.start_frame;
  const t = interpolate(frame, [0, Math.max(1, length - 1)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitP =
    overlap > 0
      ? interpolate(frame, [length, length + overlap], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
      : 0;
  const enterP = interpolate(frame, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (aspect === null) return null;
  const hero = largestLayer(shot.layers);
  return (
    <AbsoluteFill style={{ backgroundColor: theme.background, perspective: 1800, opacity: (1 - exitP * 0.35) * Math.min(1, enterP * 2) }}>
      <TemplateBackdrop theme={theme as Theme} sceneIndex={shotIndex} drift={(t - 0.5) * 40} />
      {hero ? (
        <HeroView
          layer={hero}
          screenshot={shot.screenshot}
          frame={frame}
          fps={fps}
          t={t}
          exitP={exitP}
          imageAspect={aspect}
          gentle={shotIndex === 0}
        />
      ) : null}
      <KineticType text={shot.text} color={theme.foreground} frame={frame} fps={fps} durationFrames={length} />
    </AbsoluteFill>
  );
};

interface HeroProps {
  readonly layer: MotionLayer;
  readonly screenshot: string;
  readonly frame: number;
  readonly fps: number;
  readonly t: number;
  readonly exitP: number;
  readonly imageAspect: number;
  readonly gentle: boolean;
}

const HeroView: React.FC<HeroProps> = ({ layer, screenshot, frame, fps, t, exitP, imageAspect, gentle }) => {
  const crop = punchIn(layer.bbox_norm, imageAspect, productRect(FRAME.width, FRAME.height));
  if (crop === null) return null;
  const enter = spring({ frame, fps, config: ENTER_SPRING });
  const yaw = gentle ? interpolate(t, [0, 1], [-2, 2]) : interpolate(t, [0, 1], [-5, 3]);
  const pitch = gentle ? interpolate(t, [0, 1], [2, 0]) : interpolate(t, [0, 1], [3, 1]);
  return (
    <div
      style={{
        position: "absolute",
        left: crop.box.left,
        top: crop.box.top,
        width: crop.box.width,
        height: crop.box.height,
        overflow: "hidden",
        zIndex: 1,
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: 36,
          overflow: "hidden",
          transform: `translate3d(0, ${(1 - enter) * 16}px, 0) rotateY(${yaw}deg) rotateX(${pitch}deg)`,
          transformOrigin: "50% 50%",
          opacity: Math.min(1, enter * 1.4) * (1 - exitP * 0.35),
          boxShadow: "0 36px 70px rgba(0,0,0,0.22)",
        }}
      >
      <Img
        src={staticFile(screenshot)}
        style={{
          position: "absolute",
          left: crop.image.left - crop.box.left,
          top: crop.image.top - crop.box.top,
          width: crop.image.width,
          height: crop.image.height,
          maxWidth: "none",
          objectFit: "fill",
        }}
      />
      </div>
    </div>
  );
};
