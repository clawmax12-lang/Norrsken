import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import type { CompositionSpec, Transition } from "../spec/types.generated.ts";
import { CtaCard } from "./CtaCard.tsx";
import { HeroDevice, useImageSizes } from "./DeviceFrame.tsx";
import { useFontsReady } from "./fonts.ts";
import { Scene, SceneHeadline } from "./Scene.tsx";
import { firstBeat, sceneBeats } from "./beats.ts";
import { heroPose, heroTrack } from "./shots.ts";
import { ctaStartFrame, sceneWindows } from "./timeline.ts";
import { progress } from "./motion.ts";
import { TRANSITION_FRAMES } from "./tokens.ts";

/** Remotion props must be a plain object type, so the spec travels under one key. */
export type PreflightVideoProps = { readonly spec: CompositionSpec };

/**
 * Renders any valid CompositionSpec: scene backdrops stacked in order, one hero phone that
 * carries every portrait screen from shot to shot, the scene copy above it, then the CTA end
 * card. All text comes from the spec; the template adds none of its own.
 */
export const PreflightVideo: React.FC<PreflightVideoProps> = ({ spec }) => {
  const fontsReady = useFontsReady();
  const frame = useCurrentFrame();
  const sizes = useImageSizes(spec.scenes.map((scene) => scene.screenshot));
  const windows = sceneWindows(spec);
  const ctaStart = ctaStartFrame(spec);
  if (!fontsReady || sizes === null) return null;
  const track = heroTrack(spec, sizes);
  const onHero = (index: number) => track[index]?.on ?? false;
  // Under the hero phone a backdrop only dissolves: a push would slide the stage out from under it.
  const kindOf = (index: number, kind: Transition): Transition =>
    onHero(index) && onHero(index - 1) && kind !== "cut" ? "fade" : kind;
  return (
    <AbsoluteFill style={{ backgroundColor: spec.theme.background }}>
      {windows.map((w) => {
        const next = spec.scenes[w.index + 1];
        return (
          <Sequence key={`stage-${w.index}`} from={w.from} durationInFrames={w.duration} layout="none">
            <Scene
              window={w}
              theme={spec.theme}
              enter={kindOf(w.index, w.scene.transition_in)}
              enterProgress={progress(frame, w.from, TRANSITION_FRAMES)}
              exit={{
                kind: next ? kindOf(w.index + 1, next.transition_in) : "cut",
                p: next ? progress(frame, next.start_frame, TRANSITION_FRAMES) : 0,
              }}
              onHero={onHero(w.index)}
              beats={sceneBeats(spec, w.index)}
            />
          </Sequence>
        );
      })}
      <HeroDevice pose={heroPose(frame, track)} track={track} frame={frame} />
      {windows.map((w) => {
        const hero = track[w.index];
        if (!hero?.on) return null;
        const next = spec.scenes[w.index + 1];
        const nextStart = next && next.start_frame < ctaStart ? next.start_frame : null;
        return (
          <Sequence key={`copy-${w.index}`} from={w.from} durationInFrames={w.duration} layout="none">
            <SceneHeadline
              hero={hero}
              theme={spec.theme}
              instant={w.index === 0 && w.scene.transition_in === "cut"}
              nextStart={nextStart}
              from={w.from}
              beats={sceneBeats(spec, w.index)}
            />
          </Sequence>
        );
      })}
      <Sequence from={ctaStart} durationInFrames={spec.duration_frames - ctaStart} layout="none">
        <CtaCard
          headline={spec.headline ?? spec.cta}
          wordmark={spec.wordmark ?? spec.cta}
          button={spec.cta}
          theme={spec.theme}
          logo={spec.logo ?? null}
          chips={spec.chips ?? []}
          hint={spec.cta_hint ?? null}
          pressAt={ctaPress(spec, ctaStart)}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

/** Card-local frame of the finger pressing the end card's button, or null. */
function ctaPress(spec: CompositionSpec, ctaStart: number): number | null {
  const tap = firstBeat(sceneBeats(spec, spec.scenes.length - 1), "tap");
  return tap ? tap.frame - ctaStart : null;
}
