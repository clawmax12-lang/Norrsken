/** Bundles the composition and renders a validated spec to H.264 MP4 with Remotion. */
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import type { CompositionSpec } from "../spec/types.generated.ts";
import { COMPOSITION_ID } from "../composition/id.ts";
import { stageMotionAssets } from "../motion/stage.ts";
import type { MotionSpec } from "../motion/types.ts";
import { findBrowserOnPath } from "./browser.ts";
import { stageAssets } from "./stage.ts";

const PACKAGE_ROOT = fileURLToPath(new URL("../..", import.meta.url));
const ENTRY_POINT = fileURLToPath(new URL("../index.ts", import.meta.url));
const PROGRESS_LOG_EVERY = 0.1;

export interface RenderOptions {
  readonly spec: CompositionSpec | MotionSpec;
  readonly assetsRoot: string;
  readonly outPath: string;
  readonly browser: string | undefined;
  readonly concurrency: number | undefined;
  readonly compositionId?: string | undefined;
  readonly entry?: string | undefined;
}

export interface RenderSummary {
  readonly frames: number;
  readonly bundleSeconds: number;
  readonly renderSeconds: number;
}

const seconds = (since: number): number => Math.round((performance.now() - since)) / 1000;

function isMotionSpec(spec: CompositionSpec | MotionSpec): spec is MotionSpec {
  return "shots" in spec;
}

export async function renderSpec(options: RenderOptions): Promise<RenderSummary> {
  const workDir = await mkdtemp(path.join(tmpdir(), "preflight-render-"));
  try {
    const publicDir = path.join(workDir, "public");
    if (isMotionSpec(options.spec)) {
      await stageMotionAssets(options.spec, options.assetsRoot, publicDir);
    } else {
      await stageAssets(options.spec, options.assetsRoot, publicDir);
    }

    const entryPoint = options.entry ? path.join(PACKAGE_ROOT, options.entry) : ENTRY_POINT;
    const compositionId = options.compositionId ?? COMPOSITION_ID;
    const bundleStart = performance.now();
    const serveUrl = await bundle({ entryPoint, publicDir });
    const bundleSeconds = seconds(bundleStart);

    const browserExecutable = options.browser ?? findBrowserOnPath() ?? null;
    const inputProps = { spec: options.spec };
    const composition = await selectComposition({ serveUrl, id: compositionId, inputProps, browserExecutable });

    const renderStart = performance.now();
    let nextLog = PROGRESS_LOG_EVERY;
    await renderMedia({
      composition,
      serveUrl,
      inputProps,
      browserExecutable,
      codec: "h264",
      crf: 16,
      pixelFormat: "yuv420p",
      concurrency: options.concurrency ?? null,
      outputLocation: options.outPath,
      overwrite: true,
      onProgress: ({ progress }) => {
        if (progress >= nextLog) {
          console.error(`render ${Math.round(progress * 100)}%`);
          nextLog += PROGRESS_LOG_EVERY;
        }
      },
    });
    return { frames: composition.durationInFrames, bundleSeconds, renderSeconds: seconds(renderStart) };
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }
}
