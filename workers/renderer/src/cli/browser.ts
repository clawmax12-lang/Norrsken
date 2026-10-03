/** Locating a Chrome for Remotion. Order: explicit option/env, PATH, else Remotion's own download. */
import { accessSync, constants } from "node:fs";
import path from "node:path";

const CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"];

function isExecutable(file: string): boolean {
  try {
    accessSync(file, constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

/** First Chrome-like binary on PATH, or undefined (Remotion then downloads Chrome Headless Shell). */
export function findBrowserOnPath(pathVariable: string = process.env["PATH"] ?? ""): string | undefined {
  for (const dir of pathVariable.split(path.delimiter)) {
    for (const name of CANDIDATES) {
      const candidate = path.join(dir, name);
      if (dir !== "" && isExecutable(candidate)) return candidate;
    }
  }
  return undefined;
}
