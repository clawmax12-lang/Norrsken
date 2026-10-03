import { useMemo } from "react";
import { useVideoConfig } from "remotion";
import { progress, easeOut } from "./motion.ts";
import { withAlpha } from "./color.ts";
import { FONT_FAMILY, TYPE } from "./tokens.ts";
import { layoutHeadline, measureInBrowser, type SizeRange } from "./typography.ts";

/** Frames between one line starting its reveal and the next. */
const LINE_STAGGER = 5;
const REVEAL_FRAMES = 26;
/** Light words keep enough contrast for large text (WCAG 1.4.3 requires 3:1). */
const LIGHT_WORD_ALPHA = 0.62;

interface HeadlineProps {
  readonly text: string;
  readonly color: string;
  readonly width: number;
  readonly align: "left" | "center";
  readonly range: SizeRange;
  /** Local frame at which the reveal starts. */
  readonly delay: number;
  readonly frame: number;
}

/** Large statement type whose lines slide up out of a mask, with heavy/light weight contrast. */
export const Headline: React.FC<HeadlineProps> = ({ text, color, width, align, range, delay, frame }) => {
  useVideoConfig();
  const layout = useMemo(() => layoutHeadline(text, width, range, measureInBrowser), [text, width, range]);
  const { fontSize, lines } = layout;
  return (
    <div
      style={{
        width,
        textAlign: align,
        fontFamily: `"${FONT_FAMILY}", system-ui, sans-serif`,
        fontSize,
        lineHeight: TYPE.lineHeight,
        letterSpacing: `${TYPE.letterSpacingEm}em`,
        fontOpticalSizing: "auto",
        color,
      }}
    >
      {lines.map((line, i) => {
        const p = progress(frame, delay + i * LINE_STAGGER, REVEAL_FRAMES, easeOut);
        return (
          <div
            key={i}
            style={{
              overflow: "hidden",
              padding: "0.06em 0.05em 0.18em",
              margin: "-0.06em -0.05em -0.18em",
              whiteSpace: "nowrap",
            }}
          >
            <div style={{ transform: `translateY(${(1 - p) * 112}%)`, opacity: Math.min(1, p * 2.2) }}>
              {line.map((word, w) => (
                <span
                  key={w}
                  style={{
                    fontWeight: word.weight,
                    color: word.weight < 500 ? withAlpha(color, LIGHT_WORD_ALPHA) : color,
                  }}
                >
                  {w > 0 ? " " : ""}
                  {word.text}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
