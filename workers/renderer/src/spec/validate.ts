/** Validation of incoming spec JSON against the schema exported from the Python model. */
import { readFile } from "node:fs/promises";
import { Ajv2020 } from "ajv/dist/2020.js";
import type { CompositionSpec } from "./types.generated.ts";

const SCHEMA_URL = new URL("../../schema/composition-spec.schema.json", import.meta.url);

export class SpecValidationError extends Error {
  constructor(details: string) {
    super(`Invalid CompositionSpec: ${details}`);
    this.name = "SpecValidationError";
  }
}

async function loadValidator() {
  const schema: object = JSON.parse(await readFile(SCHEMA_URL, "utf8"));
  return new Ajv2020({ allErrors: true, strict: false }).compile<CompositionSpec>(schema);
}

/** Returns the spec typed, or throws a SpecValidationError listing every violation. */
export async function parseSpec(json: string): Promise<CompositionSpec> {
  let value: unknown;
  try {
    value = JSON.parse(json);
  } catch (error) {
    throw new SpecValidationError(`not JSON (${(error as Error).message})`);
  }
  const validate = await loadValidator();
  if (!validate(value)) {
    const details = (validate.errors ?? []).map((e) => `${e.instancePath || "/"} ${e.message}`);
    throw new SpecValidationError(details.join("; "));
  }
  assertTimeline(value);
  return value;
}

/** The invariants JSON Schema cannot express: scenes tile the timeline exactly. */
function assertTimeline(spec: CompositionSpec): void {
  let cursor = 0;
  for (const scene of spec.scenes) {
    if (scene.start_frame !== cursor || scene.end_frame <= scene.start_frame) {
      throw new SpecValidationError(`scene starting at ${scene.start_frame} breaks the timeline`);
    }
    cursor = scene.end_frame;
  }
  if (cursor !== spec.duration_frames) {
    throw new SpecValidationError("last scene must end at duration_frames");
  }
}
