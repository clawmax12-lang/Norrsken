import { useEffect, useState } from "react";
import { AbsoluteFill, Img, cancelRender, continueRender, delayRender, staticFile } from "remotion";
import { getImageDimensions } from "@remotion/media-utils";
import { coverLayout, stageTransform, type FocusBox, type ImageSize } from "./still.ts";
import { pointOf, tapMark, type TapMark } from "./beats.ts";
import { contentFocus, screenLayers, type HeroScene, type Pose } from "./shots.ts";
import { DEVICE, PRODUCT_ZONE, TYPE_ZONE } from "./tokens.ts";

/** Natural pixel size of a staged screenshot; waits for it before rendering. */
export function useImageSize(path: string): ImageSize | null {
  const [size, setSize] = useState<ImageSize | null>(null);
  useEffect(() => {
    const handle = delayRender(`Measuring ${path}`);
    getImageDimensions(staticFile(path))
      .then(({ width, height }) => setSize({ width, height }))
      .catch((error: unknown) => cancelRender(error))
      .finally(() => continueRender(handle));
  }, [path]);
  return size;
}

/** Natural sizes of every staged screenshot, keyed by path; null until all are measured. */
export function useImageSizes(paths: readonly string[]): Readonly<Record<string, ImageSize>> | null {
  const key = [...new Set(paths)].join("\n");
  const [sizes, setSizes] = useState<Readonly<Record<string, ImageSize>> | null>(null);
  useEffect(() => {
    const unique = key === "" ? [] : key.split("\n");
    const handle = delayRender(`Measuring ${unique.length} screenshots`);
    Promise.all(unique.map(async (path) => [path, await getImageDimensions(staticFile(path))] as const))
      .then((entries) => setSizes(Object.fromEntries(entries.map(([path, { width, height }]) => [path, { width, height }]))))
      .catch((error: unknown) => cancelRender(error))
      .finally(() => continueRender(handle));
  }, [key]);
  return sizes;
}

/** Natural aspect ratio (width / height) of a staged screenshot; waits for it before rendering. */
export function useImageAspect(path: string): number | null {
  const size = useImageSize(path);
  return size === null ? null : size.width / size.height;
}

interface ScreenImageProps {
  readonly src: string;
  readonly image: ImageSize;
  /** The part of the image to show (a mockup's display), or null for all of it. */
  readonly crop: FocusBox | null;
  readonly width: number;
  readonly height: number;
  /** Scene progress 0-1. */
  readonly t: number;
  readonly focus: FocusBox | null;
  /** Keep the punch-in centred across (phone screens), so neither side of the screen is cut. */
  readonly centreX?: boolean;
  /** A fingertip on ``point`` (a share of the shown region), moving with the screen. */
  readonly tap?: { readonly point: readonly [number, number]; readonly mark: TapMark } | null | undefined;
}

/** A screenshot (or the display cut out of a mockup) filling a box, moving within the upscale cap. */
export const ScreenImage: React.FC<ScreenImageProps> = ({ src, image, crop, width, height, t, focus, centreX = false, tap = null }) => {
  const layout = coverLayout(image, crop, width, height);
  const [cx, cy, cw, ch] = crop ?? [0, 0, 1, 1];
  return (
    <div style={{ position: "absolute", inset: 0, transform: stageTransform(t, focus, layout.scale, centreX), transformOrigin: "50% 50%" }}>
      <Img
        src={staticFile(src)}
        style={{
          position: "absolute",
          left: layout.left,
          top: layout.top,
          width: layout.width,
          height: layout.height,
          maxWidth: "none",
          display: "block",
        }}
      />
      {tap ? (
        <Fingertip
          x={layout.left + (cx + tap.point[0] * cw) * layout.width}
          y={layout.top + (cy + tap.point[1] * ch) * layout.height}
          size={width * FINGERTIP_SHARE}
          mark={tap.mark}
        />
      ) : null}
    </div>
  );
};

/** Fingertip diameter as a share of the glass width: about a real thumb on a phone. */
const FINGERTIP_SHARE = 0.15;

/** A touch indicator: a soft disc that comes down, presses, and leaves a ripple. */
const Fingertip: React.FC<{ x: number; y: number; size: number; mark: TapMark }> = ({ x, y, size, mark }) => (
  <>
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        border: `${Math.max(2, size * 0.04)}px solid rgba(255, 255, 255, 0.95)`,
        boxShadow: "0 0 0 2px rgba(10, 12, 20, 0.25)",
        transform: `scale(${mark.ripple.toFixed(3)})`,
        opacity: mark.rippleOpacity,
      }}
    />
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255,255,255,0.92) 0%, rgba(255,255,255,0.7) 55%, rgba(255,255,255,0.35) 100%)",
        border: "2px solid rgba(10, 12, 20, 0.22)",
        boxShadow: "0 10px 28px rgba(10, 12, 20, 0.35)",
        transform: `scale(${mark.scale.toFixed(3)})`,
        opacity: mark.touch,
      }}
    />
  </>
);

/** Below the headline the device fades in over this many px instead of meeting a hard edge. */
const MASK_FADE_PX = 60;

interface HeroDeviceProps {
  readonly pose: Pose;
  readonly track: readonly HeroScene[];
  readonly frame: number;
}

/**
 * The one brand-neutral phone shared by every product scene, drawn from ``pose``: metal edge,
 * black bezel and the real screenshots, each pushing the previous one up inside the glass.
 * Nothing clips the device except the frame itself; above the product zone it fades out so a
 * close-up or a takeover never covers the headline.
 */
export const HeroDevice: React.FC<HeroDeviceProps> = ({ pose, track, frame }) => {
  if (pose.opacity <= 0 || pose.glassW <= 0) return null;
  const outerW = pose.glassW + 2 * pose.bezel;
  const outerH = pose.glassH + 2 * pose.bezel;
  const unit = pose.bezel / (DEVICE.edge + DEVICE.bezel || 1);
  const edge = DEVICE.edge * unit;
  const outerRadius = pose.radius + pose.bezel;
  const fadeTop = TYPE_ZONE.top + TYPE_ZONE.height;
  const mask = `linear-gradient(180deg, transparent ${fadeTop}px, #000 ${Math.max(fadeTop + MASK_FADE_PX, PRODUCT_ZONE.top)}px)`;
  const layers = screenLayers(frame, track);
  return (
    <AbsoluteFill style={{ maskImage: mask, WebkitMaskImage: mask, opacity: pose.opacity }}>
      <div
        style={{
          position: "absolute",
          left: pose.cx - outerW / 2,
          top: pose.cy - outerH / 2,
          width: outerW,
          height: outerH,
          transform: `perspective(2400px) rotateY(${pose.rotateY.toFixed(3)}deg) rotateZ(${pose.rotateZ.toFixed(3)}deg)`,
          transformOrigin: "50% 50%",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: outerRadius,
            opacity: pose.frame,
            background: "linear-gradient(145deg, #eceef2 0%, #9a9da6 22%, #d9dbe0 50%, #80838c 78%, #cfd1d6 100%)",
            boxShadow: [
              "0 80px 140px -30px rgba(20, 24, 48, 0.34)",
              "0 30px 60px -18px rgba(20, 24, 48, 0.24)",
              "0 0 0 1px rgba(255, 255, 255, 0.35) inset",
            ].join(", "),
          }}
        >
          <div style={{ position: "absolute", inset: edge, borderRadius: Math.max(0, outerRadius - edge), background: "#08080a" }} />
          <SideButtons height={outerH} />
        </div>
        <div
          style={{
            position: "absolute",
            left: pose.bezel,
            top: pose.bezel,
            width: pose.glassW,
            height: pose.glassH,
            borderRadius: pose.radius,
            overflow: "hidden",
            background: "#fff",
          }}
        >
          {layers.map(({ scene, t, shift }) =>
            scene.image ? (
              <div key={scene.index} style={{ position: "absolute", inset: 0, transform: shift ? `translateY(${(shift * 100).toFixed(2)}%)` : undefined }}>
                <ScreenImage
                  src={scene.scene.screenshot}
                  image={scene.image}
                  crop={scene.crop}
                  width={pose.glassW}
                  height={pose.glassH}
                  t={t}
                  focus={contentFocus(scene)}
                  centreX
                  tap={tapOn(scene, frame)}
                />
              </div>
            ) : null,
          )}
          <Glare t={layers.at(-1)?.t ?? 0} strength={pose.frame} />
        </div>
        {layers.at(-1)?.scene.crop === null ? (
          <div
            style={{
              position: "absolute",
              top: pose.bezel + 16 * unit,
              left: "50%",
              width: outerW * 0.27,
              height: outerW * 0.055,
              marginLeft: -outerW * 0.135,
              borderRadius: outerW,
              background: "#050506",
              opacity: pose.frame,
            }}
          />
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/** The fingertip of the latest tap still on screen at ``frame``. */
function tapOn(scene: HeroScene, frame: number): ScreenImageProps["tap"] {
  for (const tap of [...scene.taps].reverse()) {
    const point = pointOf(tap.point);
    const mark = point ? tapMark(frame, tap.frame) : null;
    if (mark && point) return { point, mark };
  }
  return null;
}

const Glare: React.FC<{ t: number; strength: number }> = ({ t, strength }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: strength,
      background: `linear-gradient(112deg, rgba(255,255,255,0) ${t * 120 - 40}%, rgba(255,255,255,0.14) ${t * 120 - 25}%, rgba(255,255,255,0) ${t * 120 - 8}%)`,
      mixBlendMode: "screen",
    }}
  />
);

const SideButtons: React.FC<{ height: number }> = ({ height }) => {
  const button = (top: number, h: number, side: "left" | "right") => (
    <div
      style={{
        position: "absolute",
        top: height * top,
        height: height * h,
        width: 5,
        [side]: -4,
        borderRadius: 3,
        background: "linear-gradient(90deg, #8a8d96, #c9cbd1)",
      }}
    />
  );
  return (
    <>
      {button(0.16, 0.035, "left")}
      {button(0.215, 0.06, "left")}
      {button(0.29, 0.06, "left")}
      {button(0.24, 0.1, "right")}
    </>
  );
};
