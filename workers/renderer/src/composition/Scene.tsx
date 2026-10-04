import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { SceneSpec, Theme } from "../spec/types.generated.ts";
import { Backdrop } from "./Backdrop.tsx";
import { DeviceFrame, deviceGeometry, useImageAspect } from "./DeviceFrame.tsx";
import { fullBleedStyle, isPhoneAspect } from "./still.ts";
import { Headline } from "./Headline.tsx";
import { easeInOut, lerp, progress, springIn, SHOWCASE_SPRING } from "./motion.ts";
import { FRAME, PRODUCT_ZONE, SAFE_WIDTH, TYPE, TYPE_ZONE } from "./tokens.ts";
import { enterStyle, exitStyle } from "./transitions.ts";
import type { SceneWindow } from "./timeline.ts";
import type { Transition } from "../spec/types.generated.ts";

/** Frames after the scene starts before the headline and device begin to move. */
const HEADLINE_DELAY = 4;
const DEVICE_DELAY = 8;

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
  if (scene.layout === "text_only") {
    return <TextOnly scene={scene} theme={theme} frame={frame} />;
  }
  return <ProductShot scene={scene} theme={theme} frame={frame} fps={fps} t={t} float={scene.layout === "device_float"} />;
};

const TextOnly: React.FC<Omit<ContentProps, "fps" | "t">> = ({ scene, theme, frame }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 120 }}>
    <Headline text={scene.text} color={theme.foreground} width={SAFE_WIDTH} align="center" range={TYPE.hook} delay={HEADLINE_DELAY} frame={frame} />
  </AbsoluteFill>
);

const ProductShot: React.FC<ContentProps & { float: boolean }> = ({ scene, theme, frame, fps, t, float }) => {
  const aspect = useImageAspect(scene.screenshot);
  if (aspect === null) return null;
  const zoneW = SAFE_WIDTH;
  const zoneH = FRAME.height - PRODUCT_ZONE.top - PRODUCT_ZONE.bottom;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: TYPE_ZONE.top,
          left: PRODUCT_ZONE.left,
          width: zoneW,
          height: TYPE_ZONE.height,
          overflow: "hidden",
          zIndex: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Headline text={scene.text} color={theme.foreground} width={zoneW} align="center" range={TYPE.overlay} delay={HEADLINE_DELAY} frame={frame} />
      </div>
      <div
        style={{
          position: "absolute",
          top: PRODUCT_ZONE.top,
          left: PRODUCT_ZONE.left,
          width: zoneW,
          height: zoneH,
          overflow: "hidden",
          zIndex: 1,
        }}
      >
        {isPhoneAspect(aspect) ? (
          <PhoneInBand scene={scene} zoneW={zoneW} zoneH={zoneH} aspect={aspect} frame={frame} fps={fps} t={t} float={float} />
        ) : (
          <Img src={staticFile(scene.screenshot)} style={fullBleedStyle(t)} />
        )}
      </div>
    </AbsoluteFill>
  );
};

const PhoneInBand: React.FC<{
  scene: SceneSpec;
  zoneW: number;
  zoneH: number;
  aspect: number;
  frame: number;
  fps: number;
  t: number;
  float: boolean;
}> = ({ scene, zoneW, zoneH, aspect, frame, fps, t, float }) => {
  const geometry = deviceGeometry(aspect);
  const fit = Math.min(zoneW / geometry.width, zoneH / geometry.height);
  const drawnW = geometry.width * fit;
  const drawnH = geometry.height * fit;
  const enter = springIn(frame, fps, DEVICE_DELAY, SHOWCASE_SPRING);
  const yaw = float ? lerp(-3, 2, t) : lerp(-2, 2, t);
  return (
    <div
      style={{
        position: "absolute",
        top: (zoneH - drawnH) / 2,
        left: (zoneW - drawnW) / 2,
        width: drawnW,
        height: drawnH,
        opacity: Math.min(1, enter * 1.6),
        transform: `translateY(${(1 - enter) * 16}px) rotateY(${yaw}deg)`,
        transformOrigin: "50% 50%",
      }}
    >
      <DeviceFrame
        src={scene.screenshot}
        geometry={{ ...geometry, width: drawnW, height: drawnH, radius: geometry.radius * fit }}
        glare={t}
        kenBurns={t}
      />
    </div>
  );
};
