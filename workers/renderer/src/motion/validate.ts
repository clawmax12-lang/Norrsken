import { readFile } from "node:fs/promises";
import { Ajv2020 } from "ajv/dist/2020.js";
import type { MotionSpec } from "./types.ts";

const SCHEMA_URL = new URL("../../schema/motion-scene.schema.json", import.meta.url);

export class MotionSpecValidationError extends Error {
  constructor(details: string) {
    super(`Invalid MotionSpec: ${details}`);
    this.name = "MotionSpecValidationError";
  }
}

async function loadValidator() {
  const schema: object = JSON.parse(await readFile(SCHEMA_URL, "utf8"));
  return new Ajv2020({ allErrors: true, strict: false }).compile<MotionSpec>(schema);
}

export async function parseMotionSpec(json: string): Promise<MotionSpec> {
  let value: unknown;
  try {
    value = JSON.parse(json);
  } catch (error) {
    throw new MotionSpecValidationError(`not JSON (${(error as Error).message})`);
  }
  const validate = await loadValidator();
  if (!validate(value)) {
    const details = (validate.errors ?? []).map((e) => `${e.instancePath || "/"} ${e.message}`);
    throw new MotionSpecValidationError(details.join("; "));
  }
  return value;
}
