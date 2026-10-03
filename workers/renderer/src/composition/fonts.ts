/**
 * Bundled Inter (SIL OFL 1.1, @fontsource-variable/inter) so renders never touch the network.
 * The variable font carries weight (100-900) and optical size axes, which gives the large,
 * high-contrast display type the template relies on.
 */
import { useEffect, useState } from "react";
import { cancelRender, continueRender, delayRender } from "remotion";
import latin from "@fontsource-variable/inter/files/inter-latin-opsz-normal.woff2";
import latinExt from "@fontsource-variable/inter/files/inter-latin-ext-opsz-normal.woff2";
import { FONT_FAMILY } from "./tokens.ts";

const FACES: ReadonlyArray<{ url: string; range: string }> = [
  { url: latin, range: "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD" },
  { url: latinExt, range: "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF" },
];

/** Loads the faces once per page; the promise resolves when every face is registered. */
let loading: Promise<void> | undefined;

function loadFonts(): Promise<void> {
  loading ??= Promise.all(
    FACES.map(async ({ url, range }) => {
      const face = new FontFace(FONT_FAMILY, `url(${url}) format("woff2-variations")`, {
        weight: "100 900",
        unicodeRange: range,
      });
      document.fonts.add(await face.load());
    }),
  ).then(() => undefined);
  return loading;
}

/**
 * True once Inter is usable. Rendering must wait: headline fitting measures text, and
 * measuring with a fallback font would silently pick the wrong size for the whole video.
 */
export function useFontsReady(): boolean {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const handle = delayRender("Loading Inter");
    loadFonts()
      .then(() => setReady(true))
      .catch((error: unknown) => cancelRender(error))
      .finally(() => continueRender(handle));
  }, []);
  return ready;
}
