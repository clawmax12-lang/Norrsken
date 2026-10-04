import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseCliArgs } from "./args.ts";

describe("parseCliArgs", () => {
  it("defaults to the Showcase composition", () => {
    const options = parseCliArgs(["--spec", "/tmp/a.json", "--out", "/tmp/a.mp4"]);
    assert.equal(options.compositionId, "PreflightVideo");
    assert.equal(options.entry, undefined);
  });

  it("accepts an opt-in motion composition without changing required flags", () => {
    const options = parseCliArgs([
      "--spec",
      "/tmp/m.json",
      "--out",
      "/tmp/m.mp4",
      "--composition-id",
      "PreflightMotion",
      "--entry",
      "src/motion/index.ts",
    ]);
    assert.equal(options.compositionId, "PreflightMotion");
    assert.equal(options.entry, "src/motion/index.ts");
  });
});
