import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import type { CompositionSpec } from "../spec/types.generated.ts";
import { CtaCard } from "./CtaCard.tsx";
import { useFontsReady } from "./fonts.ts";
import { Scene } from "./Scene.tsx";
import { ctaStartFrame, sceneWindows } from "./timeline.ts";
import { progress } from "./motion.ts";
import { TRANSITION_FRAMES } from "./tokens.ts";

/** Remotion props must be a plain object type, so the spec travels under one key. */
export type PreflightVideoProps = { readonly spec: CompositionSpec };

/**
 * Renders any valid CompositionSpec: scenes stacked in order with their transitions, then the
 * CTA end card. All text comes from the spec; the template adds none of its own.
 */
export const PreflightVideo: React.FC<PreflightVideoProps> = ({ spec }) => {
  const fontsReady = useFontsReady();
  const frame = useCurrentFrame();
  const windows = sceneWindows(spec);
  const ctaStart = ctaStartFrame(spec);
  if (!fontsReady) return null;
  return (
    <AbsoluteFill style={{ backgroundColor: spec.theme.background }}>
      {windows.map((w) => {
        const next = spec.scenes[w.index + 1];
        return (
          <Sequence key={w.index} from={w.from} durationInFrames={w.duration} layout="none">
            <Scene
              window={w}
              theme={spec.theme}
              enter={w.scene.transition_in}
              enterProgress={progress(frame, w.from, TRANSITION_FRAMES)}
              exit={{ kind: next?.transition_in ?? "cut", p: next ? progress(frame, next.start_frame, TRANSITION_FRAMES) : 0 }}
            />
          </Sequence>
        );
      })}
      <Sequence from={ctaStart} durationInFrames={spec.duration_frames - ctaStart} layout="none">
        <CtaCard text={spec.cta} theme={spec.theme} />
      </Sequence>
    </AbsoluteFill>
  );
};
