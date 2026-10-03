import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { SceneSpec, Theme } from "../spec/types.generated.ts";
import { Backdrop } from "./Backdrop.tsx";
import { DeviceFrame, deviceGeometry, useImageAspect } from "./DeviceFrame.tsx";
import { Headline } from "./Headline.tsx";
import { easeInOut, lerp, progress, springIn, SOFT_SPRING } from "./motion.ts";
import { FRAME, SAFE_AREA, SAFE_WIDTH, TYPE } from "./tokens.ts";
import { enterStyle, exitStyle } from "./transitions.ts";
import type { SceneWindow } from "./timeline.ts";
import type { Transition } from "../spec/types.generated.ts";

/** Frames after the scene starts before the headline and device begin to move. */
const HEADLINE_DELAY = 4;
const DEVICE_DELAY = 8;
/** Camera push-in: scale gained over a scene. */
const PUSH_IN = 0.07;

interface SceneProps {
  readonly window: SceneWindow;
  readonly theme: Theme;
  readonly enter: Transition;
  /** How far the next scene has covered this one, and how it does so. */
  readonly exit: { readonly kind: Transition; readonly p: number };
  readonly enterProgress: number;
}

export const Scene: React.FC<SceneProps> = ({ window, theme, enter, exit, enterProgress }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { scene, index } = window;
  const length = scene.end_frame - scene.start_frame;
  const t = progress(frame, 0, length, easeInOut);
  const entering = enterStyle(enter, enterProgress);
  const leaving = exitStyle(exit.kind, exit.p);
  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        opacity: entering.opacity * leaving.opacity,
        transform: [entering.transform, leaving.transform].filter((s) => s !== "none").join(" ") || "none",
      }}
    >
      <Backdrop theme={theme} asset={scene.backdrop} sceneIndex={index} t={t} />
      <SceneContent scene={scene} theme={theme} frame={frame} fps={fps} t={t} />
    </AbsoluteFill>
  );
};

interface ContentProps {
  readonly scene: SceneSpec;
  readonly theme: Theme;
  readonly frame: number;
  readonly fps: number;
  readonly t: number;
}

const SceneContent: React.FC<ContentProps> = ({ scene, theme, frame, fps, t }) => {
  switch (scene.layout) {
    case "text_only":
      return <TextOnly scene={scene} theme={theme} frame={frame} />;
    case "device_center":
      return <DeviceCenter scene={scene} theme={theme} frame={frame} fps={fps} t={t} />;
    case "device_float":
      return <DeviceFloat scene={scene} theme={theme} frame={frame} fps={fps} t={t} />;
  }
};

const TextOnly: React.FC<Omit<ContentProps, "fps" | "t">> = ({ scene, theme, frame }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 120 }}>
    <Headline text={scene.text} color={theme.foreground} width={SAFE_WIDTH} align="center" range={TYPE.hook} delay={HEADLINE_DELAY} frame={frame} />
  </AbsoluteFill>
);

const DeviceCenter: React.FC<ContentProps> = ({ scene, theme, frame, fps, t }) => {
  const aspect = useImageAspect(scene.screenshot);
  if (aspect === null) return null;
  const geometry = deviceGeometry(aspect);
  const enter = springIn(frame, fps, DEVICE_DELAY, SOFT_SPRING);
  const top = geometry.isPhone ? 700 : 820;
  return (
    <>
      <div style={{ position: "absolute", top: SAFE_AREA.top, left: SAFE_AREA.left }}>
        <Headline text={scene.text} color={theme.foreground} width={SAFE_WIDTH} align="center" range={TYPE.statement} delay={HEADLINE_DELAY} frame={frame} />
      </div>
      <div
        style={{
          position: "absolute",
          top,
          left: (FRAME.width - geometry.width) / 2,
          opacity: Math.min(1, enter * 1.6),
          transform: `translateY(${(1 - enter) * 220}px) scale(${lerp(0.94, 1, enter) * (1 + PUSH_IN * t)})`,
          transformOrigin: "50% 12%",
        }}
      >
        <DeviceFrame src={scene.screenshot} geometry={geometry} glare={t} />
      </div>
    </>
  );
};

const DeviceFloat: React.FC<ContentProps> = ({ scene, theme, frame, fps, t }) => {
  const aspect = useImageAspect(scene.screenshot);
  if (aspect === null) return null;
  const geometry = deviceGeometry(aspect);
  const enter = springIn(frame, fps, DEVICE_DELAY, SOFT_SPRING);
  const bob = Math.sin((frame / fps) * 1.2) * 10;
  return (
    <>
      <div style={{ position: "absolute", top: SAFE_AREA.top, left: SAFE_AREA.left }}>
        <Headline text={scene.text} color={theme.foreground} width={SAFE_WIDTH * 0.86} align="left" range={TYPE.statement} delay={HEADLINE_DELAY} frame={frame} />
      </div>
      <div
        style={{
          position: "absolute",
          top: 760,
          left: FRAME.width - geometry.width * 0.9,
          opacity: Math.min(1, enter * 1.6),
          transform: `perspective(2600px) translateY(${(1 - enter) * 260 + bob}px) rotateY(${lerp(-26, -14, t)}deg) rotateX(${lerp(8, 4, t)}deg) rotateZ(${lerp(-8, -4, t)}deg) scale(${1 + PUSH_IN * t})`,
          transformOrigin: "50% 30%",
        }}
      >
        <DeviceFrame src={scene.screenshot} geometry={geometry} glare={t} />
      </div>
    </>
  );
};
