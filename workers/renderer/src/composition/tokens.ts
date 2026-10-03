/**
 * Design tokens for the single Preflight template family.
 *
 * Everything the scenes position, size or time comes from here, so the look can be tuned in
 * one place. Colours come from the spec's theme, never from this file.
 */

export const FRAME = { width: 1080, height: 1920 } as const;

/**
 * Pixels reserved for the UI that vertical platforms draw over a video (profile/caption at the
 * bottom, search and title bar at the top). Text and the key part of the product stay inside.
 */
export const SAFE_AREA = { top: 250, bottom: 420, left: 80, right: 80 } as const;

export const SAFE_WIDTH = FRAME.width - SAFE_AREA.left - SAFE_AREA.right;

/** Frames a scene transition takes (about 0.45 s at 30 fps). */
export const TRANSITION_FRAMES = 14;

/** The CTA end card takes at most this many frames, and never more than the share below of the last scene. */
export const CTA_CARD_MAX_FRAMES = 60;
export const CTA_CARD_SCENE_SHARE = 0.6;

export const FONT_FAMILY = "Inter Variable";

/** Weight contrast: emphasised words are heavy, connecting words are light. */
export const WEIGHT = { heavy: 780, light: 320 } as const;

export const TYPE = {
  /** Headline size ranges in px, chosen per layout; text is fitted inside the range. */
  hook: { max: 176, min: 84, maxLines: 5 },
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
