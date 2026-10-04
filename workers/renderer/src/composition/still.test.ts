import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DEVICE } from "./tokens.ts";
import { fullBleedStyle, isPhoneAspect, kenBurnsImageStyle } from "./still.ts";

describe("product still", () => {
  it("keeps a phone frame for portrait screenshots only", () => {
    assert.equal(isPhoneAspect(0.46), true);
    assert.equal(isPhoneAspect(DEVICE.phoneMaxAspect), true);
    assert.equal(isPhoneAspect(16 / 9), false);
  });

  it("zooms a landscape still from 1 to 1.16 inside the product band", () => {
    assert.equal(fullBleedStyle(0).transform, "scale(1.000)");
    assert.equal(fullBleedStyle(1).transform, "scale(1.160)");
    assert.equal(fullBleedStyle(0).objectFit, "cover");
  });

  it("keeps the phone zoom inside the glass", () => {
    assert.equal(kenBurnsImageStyle(0).transform, "scale(1.080)");
    assert.equal(kenBurnsImageStyle(1).transform, "scale(1.120)");
  });
});
