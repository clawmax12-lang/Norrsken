import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { Theme } from "../spec/types.generated.ts";
import { withAlpha } from "./color.ts";
import { Headline } from "./Headline.tsx";
import { easeInOut, lerp, progress, springIn } from "./motion.ts";
import { SAFE_WIDTH, TYPE } from "./tokens.ts";

const WASH_FRAMES = 22;
const TEXT_DELAY = 10;
const ARROW_DELAY = 24;
const ARROW_SIZE = 150;

interface CtaCardProps {
  readonly text: string;
  readonly theme: Theme;
}

/**
 * Closing card. The wash uses the foreground colour with the stage colour as type, so the
 * contrast between the two is the theme's own text contrast whatever the brand colour is.
 */
export const CtaCard: React.FC<CtaCardProps> = ({ text, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const wash = progress(frame, 0, WASH_FRAMES, easeInOut);
  const arrow = springIn(frame, fps, ARROW_DELAY);
  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.foreground,
        clipPath: `circle(${lerp(0, 150, wash)}% at 50% 88%)`,
      }}
    >
      <AbsoluteFill
        style={{
          background: `radial-gradient(1100px 1100px at 50% ${lerp(70, 55, wash)}%, ${withAlpha(theme.accent, 0.5)}, transparent 68%)`,
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 160 }}>
        <Headline text={text} color={theme.background} width={SAFE_WIDTH} align="center" range={TYPE.cta} delay={TEXT_DELAY} frame={frame} />
        <div
          style={{
            marginTop: 88,
            width: ARROW_SIZE,
            height: ARROW_SIZE,
            borderRadius: ARROW_SIZE,
            background: theme.accent,
            display: "grid",
            placeItems: "center",
            transform: `scale(${arrow})`,
            opacity: Math.min(1, arrow * 2),
            boxShadow: `0 30px 80px ${withAlpha(theme.accent, 0.55)}`,
          }}
        >
          <svg width={ARROW_SIZE * 0.42} height={ARROW_SIZE * 0.42} viewBox="0 0 24 24" fill="none" stroke={theme.background} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
