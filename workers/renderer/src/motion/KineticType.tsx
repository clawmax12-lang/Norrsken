import { Headline } from "../composition/Headline.tsx";
import { SAFE_WIDTH, TYPE, TYPE_ZONE } from "../composition/tokens.ts";
import { canAnimateIn, lineLandFrame } from "./kinetic.ts";

interface KineticTypeProps {
  readonly text: string;
  readonly color: string;
  readonly frame: number;
  readonly fps: number;
  readonly durationFrames: number;
}

/** Overlay type in the reserved band. Fits and wraps; never ellipsizes source copy. */
export const KineticType: React.FC<KineticTypeProps> = ({ text, color, frame, fps, durationFrames }) => {
  const delay = canAnimateIn(durationFrames, fps) ? lineLandFrame(fps) : 0;
  return (
    <div
      style={{
        position: "absolute",
        top: TYPE_ZONE.top,
        left: 80,
        width: SAFE_WIDTH,
        height: TYPE_ZONE.height,
        overflow: "hidden",
        zIndex: 2,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Headline text={text} color={color} width={SAFE_WIDTH} align="center" range={TYPE.overlay} delay={delay} frame={frame} />
    </div>
  );
};
