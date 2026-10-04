/**
 * Design tokens for the single Preflight template family.
 *
 * Everything the scenes position, size or time comes from here, so the look can be tuned in
 * one place. Colours come from the spec's theme, never from this file.
 */

export const FRAME = { width: 1080, height: 1920 } as const;

/**
 * Pixels reserved for platform chrome on 9:16 social UI:
 * top 12% (230), bottom 18% (346), right 14% (151). Left stays a narrow gutter.
 * Text and the key part of the product stay inside.
 */
export const SAFE_AREA = { top: 230, bottom: 346, left: 80, right: 151 } as const;

export const SAFE_WIDTH = FRAME.width - SAFE_AREA.left - SAFE_AREA.right;

/**
 * Two bands that never share pixels. Type ends, then a gap, then the product.
 * Both wrappers clip overflow, so animation cannot cross the gap.
 */
export const TYPE_ZONE = { top: 220, height: 280 } as const;
export const PRODUCT_ZONE = {
  top: TYPE_ZONE.top + TYPE_ZONE.height + 40,
  bottom: SAFE_AREA.bottom,
  left: SAFE_AREA.left,
  right: SAFE_AREA.right,
} as const;

/** Frames a scene transition takes (about 0.67 s at 30 fps; keep equal to compose.TRANSITION_FRAMES). */
export const TRANSITION_FRAMES = 20;

/** Locked end-card window, in seconds. Both 30 fps Showcase and 60 fps motion use this. */
export const END_CARD_S = 3;
export const TEXT_IN_S = 0.6;
export const TEXT_HOLD_MIN_S = 1.5;
export const SPEECH_LEAD_S = 0.3;

export function endCardFrames(fps: number): number {
  return Math.round(END_CARD_S * fps);
}

export function ctaStartFrameFor(durationFrames: number, fps: number): number {
  return Math.max(0, durationFrames - endCardFrames(fps));
}

export const FONT_FAMILY = "Inter Variable";

/** Weight contrast: emphasised words are heavy, connecting words are light. */
export const WEIGHT = { heavy: 780, light: 320 } as const;

export const TYPE = {
  /** Headline size ranges in px, chosen per layout; text is fitted inside the range. */
  hook: { max: 176, min: 84, maxLines: 5 },
  /** Overlay copy above the product. Two lines, sized to stay inside TYPE_ZONE. */
  overlay: { max: 84, min: 40, maxLines: 2 },
  statement: { max: 116, min: 64, maxLines: 4 },
  cta: { max: 150, min: 72, maxLines: 4 },
  lineHeight: 1.04,
  letterSpacingEm: -0.04,
} as const;

export const DEVICE = {
  /** Width of a phone-shaped frame, and of a wide (tablet/desktop) frame, in px. */
  phoneWidth: 640,
  wideWidth: 900,
  /** Screenshots at or below this width/height ratio are drawn in a phone frame. */
  phoneMaxAspect: 0.62,
  minAspect: 0.4,
  maxAspect: 1.8,
  bezel: 13,
} as const;
