import { useEffect, useState, type ReactNode } from "react";
import { Img, cancelRender, continueRender, delayRender, staticFile } from "remotion";
import { getImageDimensions } from "@remotion/media-utils";
import { focusImageStyle, kenBurnsImageStyle, type FocusBox } from "./still.ts";
import { DEVICE } from "./tokens.ts";

/** Natural aspect ratio (width / height) of a staged screenshot; waits for it before rendering. */
export function useImageAspect(path: string): number | null {
  const [aspect, setAspect] = useState<number | null>(null);
  useEffect(() => {
    const handle = delayRender(`Measuring ${path}`);
    getImageDimensions(staticFile(path))
      .then(({ width, height }) => setAspect(width / height))
      .catch((error: unknown) => cancelRender(error))
      .finally(() => continueRender(handle));
  }, [path]);
  return aspect;
}

export interface DeviceGeometry {
  readonly width: number;
  readonly height: number;
  readonly radius: number;
  readonly isPhone: boolean;
}

/** A generic frame sized to the screenshot: phone-shaped for portrait, window-shaped otherwise. */
export function deviceGeometry(aspect: number): DeviceGeometry {
  const isPhone = aspect <= DEVICE.phoneMaxAspect;
  const clamped = Math.min(Math.max(aspect, DEVICE.minAspect), DEVICE.maxAspect);
  const width = isPhone ? DEVICE.phoneWidth : DEVICE.wideWidth;
  return { width, height: Math.round(width / clamped), radius: isPhone ? width * 0.15 : 44, isPhone };
}

interface DeviceFrameProps {
  readonly src: string;
  readonly geometry: DeviceGeometry;
  /** Moves the glare across the glass over time (0-1). */
  readonly glare: number;
  /** Scene progress 0–1; drives Ken Burns (or the focus punch-in) on the screenshot. */
  readonly kenBurns: number;
  /** Region to punch into instead of the generic Ken Burns drift. */
  readonly focus?: FocusBox | null;
  /** Optional caption drawn over the lower screen (scrim lives in the caller). */
  readonly caption?: ReactNode;
}

/** Brand-neutral device drawn in CSS: titanium-style edge, black bezel, the real screenshot. */
export const DeviceFrame: React.FC<DeviceFrameProps> = ({ src, geometry, glare, kenBurns, focus, caption }) => {
  const { width, height, radius, isPhone } = geometry;
  const edge = 4;
  const bezel = DEVICE.bezel;
  const screenRadius = radius - edge - bezel * 0.55;
  return (
    <div
      style={{
        position: "relative",
        width,
        height,
        borderRadius: radius,
        padding: edge,
        boxSizing: "border-box",
        background: "linear-gradient(145deg, #eceef2 0%, #9a9da6 22%, #d9dbe0 50%, #80838c 78%, #cfd1d6 100%)",
        boxShadow: [
          "0 80px 140px -30px rgba(20, 24, 48, 0.34)",
          "0 30px 60px -18px rgba(20, 24, 48, 0.24)",
          "0 0 0 1px rgba(255, 255, 255, 0.35) inset",
        ].join(", "),
      }}
    >
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          borderRadius: radius - edge,
          padding: bezel,
          boxSizing: "border-box",
          background: "#08080a",
        }}
      >
        <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: screenRadius, overflow: "hidden", background: "#fff" }}>
          <Img src={staticFile(src)} style={focus ? focusImageStyle(kenBurns, focus) : kenBurnsImageStyle(kenBurns)} />
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: `linear-gradient(112deg, rgba(255,255,255,0) ${glare * 120 - 40}%, rgba(255,255,255,0.14) ${glare * 120 - 25}%, rgba(255,255,255,0) ${glare * 120 - 8}%)`,
              mixBlendMode: "screen",
            }}
          />
          {caption}
        </div>
        {isPhone ? (
          <div
            style={{
              position: "absolute",
              top: bezel + 16,
              left: "50%",
              width: width * 0.27,
              height: width * 0.055,
              marginLeft: -width * 0.135,
              borderRadius: width,
              background: "#050506",
            }}
          />
        ) : null}
      </div>
      {isPhone ? <SideButtons height={height} /> : null}
    </div>
  );
};

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
