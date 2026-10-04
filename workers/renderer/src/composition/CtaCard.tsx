import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Theme } from "../spec/types.generated.ts";
import { withAlpha } from "./color.ts";
import { Headline } from "./Headline.tsx";
import { easeInOut, lerp, progress, springIn } from "./motion.ts";
import { FONT_FAMILY, SAFE_WIDTH, TYPE, WEIGHT } from "./tokens.ts";

const WASH_S = 0.4;
const TEXT_DELAY_S = 0.15;
const ARROW_DELAY_S = 0.28;
const LOGO_MAX = 160;

export interface CtaCardProps {
  readonly headline: string;
  readonly wordmark: string;
  readonly button: string;
  readonly theme: Theme;
  readonly logo?: string | null | undefined;
}

/** Closing card: logo/wordmark, grounded headline, button. Holds for the locked 3 s window. */
export const CtaCard: React.FC<CtaCardProps> = ({ headline, wordmark, button, theme, logo }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const washFrames = Math.round(WASH_S * fps);
  const wash = progress(frame, 0, washFrames, easeInOut);
  const textDelay = Math.round(TEXT_DELAY_S * fps);
  const arrow = springIn(frame, fps, Math.round(ARROW_DELAY_S * fps));
  return (
    <AbsoluteFill
      style={{
        backgroundColor: theme.background,
        opacity: lerp(0.35, 1, wash),
      }}
    >
      <AbsoluteFill
        style={{
          background: `radial-gradient(900px 700px at 50% 42%, ${withAlpha(theme.accent, 0.28)}, transparent 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          gap: 36,
          padding: "160px 72px 200px",
        }}
      >
        {logo ? (
          <Img
            src={staticFile(logo)}
            style={{ maxWidth: LOGO_MAX, maxHeight: LOGO_MAX, objectFit: "contain", opacity: Math.min(1, wash * 1.4) }}
          />
        ) : (
          <div
            style={{
              fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
              fontSize: 42,
              fontWeight: WEIGHT.heavy,
              letterSpacing: "-0.04em",
              color: theme.foreground,
              opacity: Math.min(1, wash * 1.4),
            }}
          >
            {wordmark}
          </div>
        )}
        <Headline text={headline} color={theme.foreground} width={SAFE_WIDTH} align="center" range={TYPE.cta} delay={textDelay} frame={frame} />
        <div
          style={{
            marginTop: 12,
            minWidth: 280,
            padding: "22px 40px",
            borderRadius: 999,
            background: theme.accent,
            color: theme.background,
            fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
            fontSize: 28,
            fontWeight: WEIGHT.heavy,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            transform: `scale(${arrow})`,
            opacity: Math.min(1, arrow * 2),
            boxShadow: `0 24px 60px ${withAlpha(theme.accent, 0.45)}`,
          }}
        >
          <span>{button}</span>
          <svg width={28} height={28} viewBox="0 0 24 24" fill="none" stroke={theme.background} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
