import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { lerpPath } from "./pathMorph.ts";

describe("lerpPath", () => {
  it("interpolates matching polygon commands", () => {
    const mid = lerpPath("M 0 0 L 10 0 Z", "M 0 0 L 20 0 Z", 0.5);
    assert.equal(mid, "M 0 0 L 15 0 Z");
  });

  it("does not invent a morph when commands differ", () => {
    const from = "M 0 0 L 10 0 Z";
    const to = "M 0 0 C 1 2 3 4 5 6";
    assert.equal(lerpPath(from, to, 0.2), from);
    assert.equal(lerpPath(from, to, 0.8), to);
  });
});
