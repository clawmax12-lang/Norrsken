/** Command-line parsing for `node render.mjs --spec spec.json --out out.mp4`. */
import { parseArgs } from "node:util";
import path from "node:path";

export interface CliOptions {
  readonly specPath: string;
  readonly outPath: string;
  /** Directory the spec's relative screenshot/backdrop paths resolve against. */
  readonly assetsRoot: string;
  /** Explicit Chrome/Chromium binary; undefined means auto-detect, then Remotion's download. */
  readonly browser: string | undefined;
  readonly concurrency: number | undefined;
  /** Remotion composition id. Default remains Showcase ``PreflightVideo``. */
  readonly compositionId: string;
  /** Bundle entry relative to the worker package. Default is ``src/index.ts``. */
  readonly entry: string | undefined;
}

export class UsageError extends Error {
  constructor(message: string) {
    super(`${message}\nusage: node render.mjs --spec spec.json --out out.mp4 [--assets-root DIR] [--browser PATH] [--concurrency N] [--composition-id PreflightVideo] [--entry src/index.ts]`);
    this.name = "UsageError";
  }
}

export function parseCliArgs(argv: readonly string[], env: NodeJS.ProcessEnv = process.env): CliOptions {
  const { values } = parseArgs({
    args: [...argv],
    options: {
      spec: { type: "string" },
      out: { type: "string" },
      "assets-root": { type: "string" },
      browser: { type: "string" },
      concurrency: { type: "string" },
      "composition-id": { type: "string" },
      entry: { type: "string" },
    },
    strict: true,
  });
  if (values.spec === undefined || values.out === undefined) {
    throw new UsageError("--spec and --out are required");
  }
  const concurrency = values.concurrency === undefined ? undefined : Number(values.concurrency);
  if (concurrency !== undefined && (!Number.isInteger(concurrency) || concurrency < 1)) {
    throw new UsageError("--concurrency must be a positive integer");
  }
  const specPath = path.resolve(values.spec);
  return {
    specPath,
    outPath: path.resolve(values.out),
    assetsRoot: path.resolve(values["assets-root"] ?? path.dirname(specPath)),
    browser: values.browser ?? env["PREFLIGHT_CHROME"],
    concurrency,
    compositionId: values["composition-id"] ?? "PreflightVideo",
    entry: values.entry,
  };
}
