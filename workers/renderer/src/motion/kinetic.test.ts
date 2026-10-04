import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { canAnimateIn, lineLandFrame, SPEECH_LEAD_S, splitWords } from "./kinetic.ts";

describe("kinetic line cadence", () => {
  it("lands the whole line after the speech lead", () => {
    assert.equal(lineLandFrame(60), Math.round(SPEECH_LEAD_S * 60));
  });

  it("refuses an in-animation when the shot is shorter than the hold window", () => {
    assert.equal(canAnimateIn(60, 60), false);
    assert.equal(canAnimateIn(180, 60), true);
  });

  it("splits source text into words without inventing any", () => {
    assert.deepEqual(splitWords("Sell anything online"), ["Sell", "anything", "online"]);
  });
});
