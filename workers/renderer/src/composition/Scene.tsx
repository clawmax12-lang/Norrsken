import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { SceneSpec, Theme } from "../spec/types.generated.ts";
import { Backdrop } from "./Backdrop.tsx";
import { DeviceFrame, ScreenImage, deviceGeometry, useImageSize } from "./DeviceFrame.tsx";
import { focusOf, isPhoneAspect, regionAspect, type FocusBox, type ImageSize } from "./still.ts";
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
  // The opening cut shows the product on frame 0: the scroll-stopper is the product itself.
  const instant = index === 0 && enter === "cut";
  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        opacity: entering.opacity * leaving.opacity,
        transform: [entering.transform, leaving.transform].filter((s) => s !== "none").join(" ") || "none",
      }}
    >
      <Backdrop theme={theme} asset={scene.backdrop} sceneIndex={index} t={t} />
      <SceneContent scene={scene} theme={theme} frame={frame} fps={fps} t={t} instant={instant} />
    </AbsoluteFill>
  );
};

interface ContentProps {
  readonly scene: SceneSpec;
  readonly theme: Theme;
  readonly frame: number;
  readonly fps: number;
  readonly t: number;
  readonly instant: boolean;
}

const SceneContent: React.FC<ContentProps> = (props) => {
  if (props.scene.layout === "text_only") {
    return <TextOnly {...props} />;
  }
  return <ProductShot {...props} float={props.scene.layout === "device_float"} />;
};

const TextOnly: React.FC<ContentProps> = ({ scene, theme, frame }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 120 }}>
    <Headline
      text={scene.text}
      color={theme.foreground}
      accent={emphasisOf(scene, theme)}
      width={SAFE_WIDTH}
      align="center"
      range={TYPE.hook}
      delay={HEADLINE_DELAY}
      frame={frame}
    />
  </AbsoluteFill>
);

const ProductShot: React.FC<ContentProps & { float: boolean }> = ({ scene, theme, frame, fps, t, float, instant }) => {
  const image = useImageSize(scene.screenshot);
  if (image === null) return null;
  const zoneW = SAFE_WIDTH;
  const zoneH = FRAME.height - PRODUCT_ZONE.top - PRODUCT_ZONE.bottom;
  const focus = focusOf(scene.focus);
  const crop = focusOf(scene.crop);
  const aspect = regionAspect(image, crop);
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
        <Headline
          text={scene.text}
          color={theme.foreground}
          accent={emphasisOf(scene, theme)}
          width={zoneW}
          align="center"
          range={TYPE.overlay}
          delay={instant ? 0 : HEADLINE_DELAY}
          frame={frame}
        />
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
          <PhoneInBand
            scene={scene}
            image={image}
            crop={crop}
            zoneW={zoneW}
            zoneH={zoneH}
            aspect={aspect}
            frame={frame}
            fps={fps}
            t={t}
            float={float}
            instant={instant}
          />
        ) : (
          <ScreenImage src={scene.screenshot} image={image} crop={crop} width={zoneW} height={zoneH} t={t} focus={focus} />
        )}
      </div>
    </AbsoluteFill>
  );
};

const PhoneInBand: React.FC<{
  scene: SceneSpec;
  image: ImageSize;
  crop: FocusBox | null;
  zoneW: number;
  zoneH: number;
  aspect: number;
  frame: number;
  fps: number;
  t: number;
  float: boolean;
  instant: boolean;
}> = ({ scene, image, crop, zoneW, zoneH, aspect, frame, fps, t, float, instant }) => {
  const geometry = deviceGeometry(aspect);
  const fit = Math.min(zoneW / geometry.width, zoneH / geometry.height);
  const drawnW = geometry.width * fit;
  const drawnH = geometry.height * fit;
  const enter = instant ? 1 : springIn(frame, fps, DEVICE_DELAY, SHOWCASE_SPRING);
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
        image={image}
        crop={crop}
        geometry={{ ...geometry, width: drawnW, height: drawnH, radius: geometry.radius * fit }}
        glare={t}
        kenBurns={t}
        focus={focusOf(scene.focus)}
      />
    </div>
  );
};

function emphasisOf(scene: SceneSpec, theme: Theme): { word: string; color: string } | null {
  return scene.emphasis ? { word: scene.emphasis, color: theme.accent } : null;
}
