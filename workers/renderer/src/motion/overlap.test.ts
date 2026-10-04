import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { OVERLAP_FRAMES, shotWindow } from "./overlap.ts";

describe("shotWindow", () => {
  it("extends a mid-film shot by twenty frames so it overlaps the next cut", () => {
    const window = shotWindow(180, 360, 900, OVERLAP_FRAMES);
    assert.equal(window.from, 180);
    assert.equal(window.duration, 180 + OVERLAP_FRAMES);
  });

  it("does not run past the 15-second end", () => {
    const window = shotWindow(880, 900, 900, OVERLAP_FRAMES);
    assert.equal(window.duration, 20);
  });
});
