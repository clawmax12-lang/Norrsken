import { useMemo } from "react";
import { useVideoConfig } from "remotion";
import { countText, slam, type Keyword } from "./beats.ts";
import { progress, easeOut } from "./motion.ts";
import { withAlpha } from "./color.ts";
import { FONT_FAMILY, TEXT_IN_S, TYPE } from "./tokens.ts";
import { layoutHeadline, measureInBrowser, type SizeRange } from "./typography.ts";

/** Frames between one line starting its reveal and the next. */
const LINE_STAGGER_S = 0.08;
/** With ``byWord``, the delay between one word starting its rise and the next. */
const WORD_STAGGER_S = 0.06;
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
  /** One word drawn heavy in the accent colour (the line's keyword). */
  readonly accent?: { readonly word: string; readonly color: string } | null;
  /** Reveal word by word instead of line by line. */
  readonly byWord?: boolean;
  /** With ``byWord``, the local frame each word starts to rise (when it is heard). */
  readonly wordDelays?: readonly number[] | null;
  /** The word that slams in on its own beat; a number counts up as it lands. */
  readonly keyword?: Keyword | null;
}

/** Large statement type whose lines (or words) slide up out of a mask, with heavy/light weight contrast. */
export const Headline: React.FC<HeadlineProps> = ({
  text,
  color,
  width,
  align,
  range,
  delay,
  frame,
  accent,
  byWord = false,
  wordDelays = null,
  keyword = null,
}) => {
  const { fps } = useVideoConfig();
  const layout = useMemo(() => layoutHeadline(text, width, range, measureInBrowser), [text, width, range]);
  const { fontSize, lines } = layout;
  const revealFrames = Math.round(TEXT_IN_S * fps);
  const lineStagger = Math.round(LINE_STAGGER_S * fps);
  const wordStagger = WORD_STAGGER_S * fps;
  const wordsBefore = lines.map((_, i) => lines.slice(0, i).reduce((n, line) => n + line.length, 0));
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
        const p = progress(frame, delay + i * lineStagger, revealFrames, easeOut);
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
            <div style={byWord ? undefined : { transform: `translateY(${(1 - p) * 112}%)`, opacity: Math.min(1, p * 2.2) }}>
              {line.map((word, w) => {
                const look =
                  accent && isWord(word.text, accent.word)
                    ? { fontWeight: Math.max(word.weight, 700), color: accent.color }
                    : { fontWeight: word.weight, color: word.weight < 500 ? withAlpha(color, LIGHT_WORD_ALPHA) : color };
                const index = wordsBefore[i]! + w;
                const start = wordDelays?.[index] ?? delay + index * wordStagger;
                const q = byWord ? progress(frame, start, revealFrames, easeOut) : 1;
                const key = keyword?.index === index ? keyword : null;
                const lift = key ? slam(frame, key.at, key.frames) : 0;
                // A number counts up from its reveal and lands on the frame it is spoken.
                const counted = key?.count ? progress(frame, Math.min(start, key.at), Math.max(1, key.at + key.frames - Math.min(start, key.at)), easeOut) : 1;
                const shown = key?.count ? countText(word.text, counted) : word.text;
                const moves = byWord || key !== null;
                return (
                  <span key={w}>
                    {w > 0 ? " " : ""}
                    <span
                      style={
                        moves
                          ? {
                              ...look,
                              display: "inline-block",
                              transformOrigin: "50% 70%",
                              transform: `translateY(${(1 - q) * 112}%) scale(${(1 + lift).toFixed(3)})`,
                              opacity: Math.min(1, q * 2.2),
                              fontVariantNumeric: key?.count ? "tabular-nums" : undefined,
                            }
                          : look
                      }
                    >
                      {shown}
                    </span>
                  </span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export function isWord(candidate: string, word: string): boolean {
  const bare = (s: string) => s.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "").toLocaleLowerCase();
  return bare(candidate) !== "" && bare(candidate) === bare(word);
}
