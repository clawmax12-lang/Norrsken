import { AbsoluteFill, Sequence } from "remotion";
import { CtaCard } from "../composition/CtaCard.tsx";
import { useFontsReady } from "../composition/fonts.ts";
import { ctaStartFrameFor } from "../composition/tokens.ts";
import type { Theme } from "../spec/types.generated.ts";
import { MotionShotView } from "./MotionShot.tsx";
import { OVERLAP_FRAMES, shotWindow } from "./overlap.ts";
import type { MotionSpec } from "./types.ts";

export type MotionVideoProps = { readonly spec: MotionSpec };

export const MotionVideo: React.FC<MotionVideoProps> = ({ spec }) => {
  const fontsReady = useFontsReady();
  if (!fontsReady) return null;
  const fps = spec.fps ?? 60;
  const ctaStart = ctaStartFrameFor(spec.duration_frames, fps);
  return (
    <AbsoluteFill style={{ backgroundColor: spec.theme.background }}>
      {spec.shots.map((shot, index) => {
        if (shot.start_frame >= ctaStart) return null;
        const clippedEnd = Math.min(shot.end_frame, ctaStart);
        const hasNext = index < spec.shots.length - 1 && (spec.shots[index + 1]?.start_frame ?? 0) < ctaStart;
        const overlap = hasNext ? OVERLAP_FRAMES : 0;
        const { duration } = shotWindow(shot.start_frame, clippedEnd, spec.duration_frames, overlap);
        return (
          <Sequence
            key={`${shot.screenshot}-${shot.start_frame}`}
            from={shot.start_frame}
            durationInFrames={Math.max(1, duration)}
            layout="none"
          >
            <MotionShotView
              shot={{ ...shot, end_frame: clippedEnd }}
              theme={spec.theme}
              shotIndex={index}
              overlap={overlap}
              underlay={spec.underlay !== false}
            />
          </Sequence>
        );
      })}
      <Sequence from={ctaStart} durationInFrames={spec.duration_frames - ctaStart} layout="none">
        <CtaCard
          headline={spec.headline ?? spec.cta}
          wordmark={spec.wordmark ?? spec.cta}
          button={spec.cta}
          theme={spec.theme as Theme}
          logo={spec.logo ?? null}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
