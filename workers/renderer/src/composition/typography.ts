/**
 * Headline layout: weight contrast, balanced line breaks and fit-to-box sizing.
 *
 * The text is never altered or truncated (it is source-backed copy); instead the type size
 * shrinks until the words fit the box. `layoutHeadline` is pure: callers inject the measurer,
 * so it is unit-tested without a browser.
 */
import { measureText } from "@remotion/layout-utils";
import { FONT_FAMILY, TYPE, WEIGHT } from "./tokens.ts";

export interface SizeRange {
  readonly max: number;
  readonly min: number;
  readonly maxLines: number;
}

export interface HeadlineWord {
  readonly text: string;
  readonly weight: number;
}

export interface HeadlineLayout {
  readonly lines: ReadonlyArray<ReadonlyArray<HeadlineWord>>;
  readonly fontSize: number;
}

/** Width in px of `text` set at `fontSize` and `weight`. */
export type Measure = (text: string, fontSize: number, weight: number) => number;

/** Words that connect ideas are set light so the content words carry the weight contrast. */
const CONNECTORS = new Set([
  "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "at", "by", "from",
  "as", "is", "are", "be", "it", "its", "that", "this", "your", "you", "our", "my", "into",
]);

const SIZE_STEP = 4;
const SPACE_EM = 0.24;
/** Fit inside this share of the box so rounding in the browser can never overflow it. */
const FIT_MARGIN = 0.98;
const HARD_MIN_SIZE = 32;

const bareWord = (word: string): string => word.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

export function weighWords(text: string): HeadlineWord[] {
  const words = text.split(/\s+/).filter((w) => w.length > 0);
  const hasContent = words.some((w) => !CONNECTORS.has(bareWord(w)));
  return words.map((word) => ({
    text: word,
    weight: hasContent && CONNECTORS.has(bareWord(word)) ? WEIGHT.light : WEIGHT.heavy,
  }));
}

function breakLines(
  words: readonly HeadlineWord[],
  limit: number,
  measure: Measure,
  size: number,
): HeadlineWord[][] {
  const space = size * SPACE_EM;
  const lines: HeadlineWord[][] = [];
  let current: HeadlineWord[] = [];
  let width = 0;
  for (const word of words) {
    const w = measure(word.text, size, word.weight);
    if (current.length > 0 && width + space + w > limit) {
      lines.push(current);
      current = [];
      width = 0;
    }
    width += (current.length > 0 ? space : 0) + w;
    current.push(word);
  }
  if (current.length > 0) lines.push(current);
  return lines;
}

/** Narrowest limit that keeps the greedy line count, which balances ragged lines. */
function balance(
  words: readonly HeadlineWord[],
  maxWidth: number,
  measure: Measure,
  size: number,
): HeadlineWord[][] {
  const target = breakLines(words, maxWidth, measure, size).length;
  let low = maxWidth * 0.4;
  let high = maxWidth;
  for (let i = 0; i < 12; i++) {
    const mid = (low + high) / 2;
    if (breakLines(words, mid, measure, size).length > target) low = mid;
    else high = mid;
  }
  return breakLines(words, high, measure, size);
}

const widestWord = (words: readonly HeadlineWord[], size: number, measure: Measure): number =>
  Math.max(...words.map((w) => measure(w.text, size, w.weight)));

export function layoutHeadline(
  text: string,
  maxWidth: number,
  range: SizeRange,
  measure: Measure,
): HeadlineLayout {
  const words = weighWords(text);
  const limit = maxWidth * FIT_MARGIN;
  for (let size = range.max; size >= HARD_MIN_SIZE; size -= SIZE_STEP) {
    if (widestWord(words, size, measure) > limit) continue;
    const lines = balance(words, limit, measure, size);
    if (lines.length <= range.maxLines || size <= range.min) return { lines, fontSize: size };
  }
  return { lines: words.map((w) => [w]), fontSize: HARD_MIN_SIZE };
}

/** The browser measurer, using the bundled Inter at the template's tracking. */
export const measureInBrowser: Measure = (text, fontSize, weight) =>
  measureText({
    text,
    fontFamily: FONT_FAMILY,
    fontSize,
    fontWeight: weight,
    letterSpacing: `${TYPE.letterSpacingEm * fontSize}px`,
    validateFontIsLoaded: true,
    additionalStyles: { fontOpticalSizing: "auto" },
  }).width;
