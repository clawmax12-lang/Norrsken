import { FRAME, PRODUCT_ZONE, SAFE_WIDTH } from "../composition/tokens.ts";

export type CropBox = {
  readonly left: number;
  readonly top: number;
  readonly width: number;
  readonly height: number;
};

export type LayerCrop = {
  readonly box: CropBox;
  readonly image: CropBox;
};

/** Letterbox an image of ``imageAspect`` (width/height) inside the stage. */
export function containedRect(
  imageAspect: number,
  frameW: number = FRAME.width,
  frameH: number = FRAME.height,
): CropBox {
  const stageAspect = frameW / frameH;
  if (imageAspect > stageAspect) {
    const width = frameW;
    const height = frameW / imageAspect;
    return { left: 0, top: (frameH - height) / 2, width, height };
  }
  const height = frameH;
  const width = frameH * imageAspect;
  return { left: (frameW - width) / 2, top: 0, width, height };
}

export function productRect(
  frameW: number = FRAME.width,
  frameH: number = FRAME.height,
): CropBox {
  const width = Math.min(SAFE_WIDTH, frameW);
  return {
    left: Math.max(0, (frameW - width) / 2),
    top: PRODUCT_ZONE.top,
    width,
    height: frameH - PRODUCT_ZONE.top - PRODUCT_ZONE.bottom,
  };
}

/** Cover ``dest`` with the image region ``bbox`` (unit square of the source). Uniform scale. */
export function punchIn(
  bbox: readonly [number, number, number, number],
  imageAspect: number,
  dest: CropBox = productRect(),
): LayerCrop | null {
  const [x, y, w, h] = bbox;
  if (w <= 0.02 || h <= 0.02) return null;
  const iw = 1000 * imageAspect;
  const ih = 1000;
  const sw = w * iw;
  const sh = h * ih;
  const scale = Math.max(dest.width / sw, dest.height / sh);
  return {
    box: dest,
    image: {
      left: dest.left + (dest.width - sw * scale) / 2 - x * iw * scale,
      top: dest.top + (dest.height - sh * scale) / 2 - y * ih * scale,
      width: iw * scale,
      height: ih * scale,
    },
  };
}

export function largestLayer<T extends { bbox_norm: readonly [number, number, number, number] }>(
  layers: readonly T[],
): T | null {
  if (layers.length === 0) return null;
  return layers.reduce((best, layer) => {
    const area = layer.bbox_norm[2] * layer.bbox_norm[3];
    const bestArea = best.bbox_norm[2] * best.bbox_norm[3];
    return area > bestArea ? layer : best;
  });
}

/** Map a unit-square bbox of the source image onto the contained stage rect. */
export function cropLayer(
  bbox: readonly [number, number, number, number],
  frameW: number = FRAME.width,
  frameH: number = FRAME.height,
  imageAspect: number = frameW / frameH,
): LayerCrop | null {
  const [x, y, w, h] = bbox;
  if (w <= 0.02 || h <= 0.02) return null;
  const stage = containedRect(imageAspect, frameW, frameH);
  return {
    box: {
      left: stage.left + x * stage.width,
      top: stage.top + y * stage.height,
      width: w * stage.width,
      height: h * stage.height,
    },
    image: {
      left: -x * stage.width,
      top: -y * stage.height,
      width: stage.width,
      height: stage.height,
    },
  };
}
