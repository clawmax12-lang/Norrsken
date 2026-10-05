import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Theme } from "../spec/types.generated.ts";
import { tapMark } from "./beats.ts";
import { withAlpha } from "./color.ts";
import { Headline } from "./Headline.tsx";
import { SHOWCASE_SPRING, easeInOut, lerp, progress, springIn } from "./motion.ts";
import { FONT_FAMILY, SAFE_WIDTH, TYPE, WEIGHT } from "./tokens.ts";

const WASH_S = 0.4;
const TEXT_DELAY_S = 0;
/** The card's content settles from this scale as it lands, so the cut to the card still moves. */
const SETTLE_FROM = 0.94;
/** Keep equal to the backend's sound/plan._CTA_BUTTON_S: the soundtrack pops here. */
const ARROW_DELAY_S = 0.28;
const LOGO_MAX = 160;
const MAX_CHIPS = 3;
const CHIP_DELAY_S = 0.12;
const CHIP_STAGGER_S = 0.1;

export interface CtaCardProps {
  readonly headline: string;
  readonly wordmark: string;
  readonly button: string;
  readonly theme: Theme;
  readonly logo?: string | null | undefined;
  /** Up to three short grounded benefits shown as pills under the headline. */
  readonly chips?: readonly string[];
  /** A short line under the button that makes acting feel easy. */
  readonly hint?: string | null | undefined;
  /** Card-local frame a finger presses the button, or null for no press. */
  readonly pressAt?: number | null | undefined;
}

/** How far the button sinks under the finger. */
const PRESS_DEPTH = 0.06;

/** Closing card: logo/wordmark, grounded headline, benefit chips, button. Holds for 3 s. */
export const CtaCard: React.FC<CtaCardProps> = ({ headline, wordmark, button, theme, logo, chips = [], hint = null, pressAt = null }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const washFrames = Math.round(WASH_S * fps);
  const wash = progress(frame, 0, washFrames, easeInOut);
  const textDelay = Math.round(TEXT_DELAY_S * fps);
  const arrow = springIn(frame, fps, Math.round(ARROW_DELAY_S * fps), SHOWCASE_SPRING);
  const mark = pressAt === null ? null : tapMark(frame, pressAt);
  const pressed = mark && frame >= pressAt! ? 1 - PRESS_DEPTH * (1 - mark.scale) / 0.18 : 1;
  const hintIn = springIn(frame, fps, Math.round((ARROW_DELAY_S + 0.25) * fps));
  // Opaque from the first frame: the card lands on the beat, so the phone never shows through.
  return (
    <AbsoluteFill style={{ backgroundColor: theme.background }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(900px 700px at 50% 42%, ${withAlpha(theme.accent, 0.28)}, transparent 70%)`,
          opacity: lerp(0.35, 1, wash),
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          gap: 44,
          padding: "160px 72px 200px",
          transform: `scale(${lerp(SETTLE_FROM, 1, wash).toFixed(4)})`,
        }}
      >
        {logo ? (
          <Img
            src={staticFile(logo)}
            style={{ maxWidth: LOGO_MAX, maxHeight: LOGO_MAX, objectFit: "contain", opacity: Math.min(1, 0.5 + wash) }}
          />
        ) : (
          <div
            style={{
              fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
              fontSize: 56,
              fontWeight: WEIGHT.heavy,
              letterSpacing: "-0.04em",
              color: theme.foreground,
              opacity: Math.min(1, 0.5 + wash),
            }}
          >
            {wordmark}
          </div>
        )}
        <Headline text={headline} color={theme.foreground} width={SAFE_WIDTH} align="center" range={TYPE.cta} delay={textDelay} frame={frame} />
        {chips.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 14, maxWidth: SAFE_WIDTH }}>
            {chips.slice(0, MAX_CHIPS).map((chip, i) => {
              const p = springIn(frame, fps, textDelay + Math.round((CHIP_DELAY_S + i * CHIP_STAGGER_S) * fps));
              return (
                <div
                  key={chip}
                  style={{
                    padding: "14px 28px",
                    borderRadius: 999,
                    border: `2px solid ${withAlpha(theme.foreground, 0.16)}`,
                    background: withAlpha(theme.foreground, 0.05),
                    color: theme.foreground,
                    fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
                    fontSize: 34,
                    fontWeight: WEIGHT.heavy,
                    letterSpacing: "-0.02em",
                    whiteSpace: "nowrap",
                    opacity: Math.min(1, p * 1.5),
                    transform: `translateY(${(1 - p) * 18}px)`,
                  }}
                >
                  {chip}
                </div>
              );
            })}
          </div>
        ) : null}
        <div
          style={{
            marginTop: 20,
            minWidth: 480,
            padding: "32px 60px",
            borderRadius: 999,
            background: theme.accent,
            color: theme.background,
            fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
            fontSize: 44,
            fontWeight: WEIGHT.heavy,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            transform: `scale(${arrow * pressed})`,
            opacity: Math.min(1, Math.max(0, arrow) * 2),
            boxShadow: `0 24px 60px ${withAlpha(theme.accent, 0.45)}`,
            position: "relative",
          }}
        >
          <span>{button}</span>
          <svg width={40} height={40} viewBox="0 0 24 24" fill="none" stroke={theme.background} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
          {mark ? <Press mark={mark} color={theme.background} /> : null}
        </div>
        {hint ? (
          <div
            style={{
              marginTop: -16,
              color: withAlpha(theme.foreground, 0.72),
              fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
              fontSize: 34,
              fontWeight: WEIGHT.heavy,
              letterSpacing: "-0.01em",
              opacity: Math.min(1, hintIn * 1.5),
              transform: `translateY(${(1 - hintIn) * 12}px)`,
            }}
          >
            {hint}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** The fingertip and ripple pressing the button, centred a little right of its middle. */
const Press: React.FC<{ mark: NonNullable<ReturnType<typeof tapMark>>; color: string }> = ({ mark, color }) => {
  const size = 84;
  return (
    <div style={{ position: "absolute", left: "62%", top: "50%", width: 0, height: 0, pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: -size * mark.ripple / 2,
          top: -size * mark.ripple / 2,
          width: size * mark.ripple,
          height: size * mark.ripple,
          borderRadius: "50%",
          border: `4px solid ${withAlpha(color, mark.rippleOpacity)}`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: -size / 2,
          top: -size / 2,
          width: size,
          height: size,
          borderRadius: "50%",
          background: withAlpha(color, 0.55 * mark.touch),
          boxShadow: `0 6px 18px rgba(0,0,0,${0.25 * mark.touch})`,
          transform: `scale(${mark.scale})`,
        }}
      />
    </div>
  );
};
