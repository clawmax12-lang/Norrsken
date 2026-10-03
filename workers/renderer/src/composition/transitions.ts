/** Scene transitions as pure style functions of progress `p` in [0, 1]. */
import type { Transition } from "../spec/types.generated.ts";
import { FRAME } from "./tokens.ts";
import { easeInOut, easeOut, lerp } from "./motion.ts";

export interface LayerStyle {
  readonly opacity: number;
  readonly transform: string;
}

const REST: LayerStyle = { opacity: 1, transform: "none" };

/** Style of a scene while it enters (p: 0 = not yet visible, 1 = settled). */
export function enterStyle(kind: Transition, p: number): LayerStyle {
  switch (kind) {
    case "cut":
      return REST;
    case "fade":
      return { opacity: easeOut(p), transform: "none" };
    case "push":
      return { opacity: 1, transform: `translate3d(0, ${lerp(FRAME.height, 0, easeInOut(p))}px, 0)` };
    case "scale":
      return { opacity: easeOut(p), transform: `scale(${lerp(1.12, 1, easeOut(p))})` };
  }
}

/**
 * Style of a scene while the next one enters over it, keyed by the *next* scene's transition
 * (p: 0 = untouched, 1 = fully covered). Outgoing layers recede slightly for depth.
 */
export function exitStyle(kind: Transition, p: number): LayerStyle {
  switch (kind) {
    case "cut":
    case "fade":
      return REST;
    case "push":
      return { opacity: 1, transform: `translate3d(0, ${lerp(0, -FRAME.height * 0.28, easeInOut(p))}px, 0)` };
    case "scale":
      return { opacity: 1, transform: `scale(${lerp(1, 0.94, easeOut(p))})` };
  }
}
