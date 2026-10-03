/**
 * CLI entry: validate the spec against the exported JSON Schema, then render.
 *
 * Exit codes: 0 rendered, 2 bad usage or invalid spec/assets (retrying cannot help), 1 render
 * failure. stdout carries one JSON summary line; everything else goes to stderr.
 */
import { readFile } from "node:fs/promises";
import { parseCliArgs, UsageError } from "./args.ts";
import { renderSpec } from "./render.ts";
import { AssetPathError } from "./stage.ts";
import { parseSpec, SpecValidationError } from "../spec/validate.ts";

const EXIT_RENDER_FAILED = 1;
const EXIT_INVALID_INPUT = 2;

export async function main(argv: readonly string[]): Promise<number> {
  try {
    const options = parseCliArgs(argv);
    const spec = await parseSpec(await readFile(options.specPath, "utf8"));
    const summary = await renderSpec({ ...options, spec });
    console.log(JSON.stringify({ output: options.outPath, ...summary }));
    return 0;
  } catch (error) {
    console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
    const invalid = error instanceof UsageError || error instanceof SpecValidationError || error instanceof AssetPathError;
    return invalid ? EXIT_INVALID_INPUT : EXIT_RENDER_FAILED;
  }
}
