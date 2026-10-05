import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { Beat, SceneSpec, Theme } from "../spec/types.generated.ts";
import { Backdrop } from "./Backdrop.tsx";
import { ScreenImage, useImageSize } from "./DeviceFrame.tsx";
import { focusOf } from "./still.ts";
import { HOOK_SCALE, keywordOf } from "./beats.ts";
import { Headline } from "./Headline.tsx";
import { easeInOut, easeOut, progress } from "./motion.ts";
import { headlineAlign, type HeroScene } from "./shots.ts";
import { FRAME, PRODUCT_ZONE, SAFE_WIDTH, TEXT_IN_S, TYPE, TYPE_ZONE } from "./tokens.ts";
import { enterStyle, exitStyle } from "./transitions.ts";
import type { SceneWindow } from "./timeline.ts";
import type { Transition } from "../spec/types.generated.ts";

/** Frames after the scene starts before the headline begins to move. */
const HEADLINE_DELAY = 0;
/** Frames the outgoing headline takes to fade while the next one rises. */
const HEADLINE_OUT_FRAMES = 8;
/** How far the outgoing headline drifts up as it fades, in px. */
const HEADLINE_OUT_LIFT = 48;

interface SceneProps {
  readonly window: SceneWindow;
  readonly theme: Theme;
  readonly enter: Transition;
  /** How far the next scene has covered this one, and how it does so. */
  readonly exit: { readonly kind: Transition; readonly p: number };
  readonly enterProgress: number;
  /** The scene's product is drawn by the shared hero phone; this layer is only the backdrop. */
  readonly onHero: boolean;
  /** This scene's beats from the spec's shared clock. */
  readonly beats: readonly Beat[];
}

/** The scene's stage: backdrop, and for scenes off the hero phone also their own copy and product. */
export const Scene: React.FC<SceneProps> = ({ window, theme, enter, exit, enterProgress, onHero, beats }) => {
  const frame = useCurrentFrame();
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
      {onHero ? null : <SceneContent scene={scene} theme={theme} frame={frame} t={t} instant={instant} beats={beats} />}
    </AbsoluteFill>
  );
};

interface SceneHeadlineProps {
  readonly hero: HeroScene;
  readonly theme: Theme;
  readonly instant: boolean;
  /** Absolute frame at which the next scene starts, or null for the last scene before the end card. */
  readonly nextStart: number | null;
  readonly from: number;
  readonly beats: readonly Beat[];
}

/**
 * Copy for a scene on the hero phone. It sits above the device and rises word by word on the
 * cut, while the previous one drifts up and fades, so the top of the frame is never empty and
 * two headlines never stack. Only the keyword waits for the voice: it lands when it is spoken.
 */
export const SceneHeadline: React.FC<SceneHeadlineProps> = ({ hero, theme, instant, nextStart, from, beats }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const absolute = from + frame;
  const fadeIn = instant ? 1 : progress(frame, 0, HEADLINE_OUT_FRAMES, easeOut);
  const fadeOut = nextStart === null ? 0 : progress(absolute, nextStart, HEADLINE_OUT_FRAMES, easeOut);
  const align = headlineAlign(hero.shot);
  const hook = instant && beats.some((beat) => beat.kind === "hook") ? 1 + HOOK_SCALE * (1 - progress(frame, 0, 8, easeOut)) : 1;
  return (
    <AbsoluteFill
      style={{
        opacity: fadeIn * (1 - fadeOut),
        transform: [hook === 1 ? "" : `scale(${hook.toFixed(3)})`, fadeOut > 0 ? `translateY(${(-HEADLINE_OUT_LIFT * fadeOut).toFixed(1)}px)` : ""].join(" ").trim() || undefined,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: TYPE_ZONE.top,
          left: PRODUCT_ZONE.left,
          width: SAFE_WIDTH,
          height: TYPE_ZONE.height,
          display: "flex",
          alignItems: "center",
          justifyContent: align === "left" ? "flex-start" : "center",
        }}
      >
        <Headline
          text={hero.scene.text}
          color={theme.foreground}
          accent={emphasisOf(hero.scene, theme)}
          width={SAFE_WIDTH}
          align={align}
          range={TYPE.overlay}
          // The hook is readable on frame 0: its reveal has already finished.
          delay={instant ? -Math.round(TEXT_IN_S * fps) : HEADLINE_DELAY}
          frame={frame}
          byWord={!instant}
          keyword={keywordOf(hero.scene, beats)}
        />
      </div>
    </AbsoluteFill>
  );
};

interface ContentProps {
  readonly scene: SceneSpec;
  readonly theme: Theme;
  readonly frame: number;
  readonly t: number;
  readonly instant: boolean;
  readonly beats: readonly Beat[];
}

const SceneContent: React.FC<ContentProps> = (props) => {
  if (props.scene.layout === "text_only") {
    return <TextOnly {...props} />;
  }
  return <WideShot {...props} />;
};

const TextOnly: React.FC<ContentProps> = ({ scene, theme, frame, beats }) => (
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
      byWord
      keyword={keywordOf(scene, beats)}
    />
  </AbsoluteFill>
);

/** A landscape screen (dashboard, web page) shown flat in the product zone; phones use the hero device. */
const WideShot: React.FC<ContentProps> = ({ scene, theme, frame, t, instant, beats }) => {
  const image = useImageSize(scene.screenshot);
  if (image === null) return null;
  const zoneH = FRAME.height - PRODUCT_ZONE.top - PRODUCT_ZONE.bottom;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: TYPE_ZONE.top,
          left: PRODUCT_ZONE.left,
          width: SAFE_WIDTH,
          height: TYPE_ZONE.height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Headline
          text={scene.text}
          color={theme.foreground}
          accent={emphasisOf(scene, theme)}
          width={SAFE_WIDTH}
          align="center"
          range={TYPE.overlay}
          delay={instant ? 0 : HEADLINE_DELAY}
          frame={frame}
          byWord={!instant}
          keyword={keywordOf(scene, beats)}
        />
      </div>
      <div
        style={{
          position: "absolute",
          top: PRODUCT_ZONE.top,
          left: PRODUCT_ZONE.left,
          width: SAFE_WIDTH,
          height: zoneH,
          overflow: "hidden",
          borderRadius: 28,
          boxShadow: "0 40px 90px -30px rgba(20, 24, 48, 0.3)",
        }}
      >
        <ScreenImage src={scene.screenshot} image={image} crop={focusOf(scene.crop)} width={SAFE_WIDTH} height={zoneH} t={t} focus={focusOf(scene.focus)} />
      </div>
    </AbsoluteFill>
  );
};

function emphasisOf(scene: SceneSpec, theme: Theme): { word: string; color: string } | null {
  return scene.emphasis ? { word: scene.emphasis, color: theme.accent } : null;
}
