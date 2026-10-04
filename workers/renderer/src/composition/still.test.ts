import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DEVICE } from "./tokens.ts";
import { focusOf, focusTransform, fullBleedStyle, isPhoneAspect, kenBurnsImageStyle } from "./still.ts";

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

describe("focus punch-in", () => {
  const box = [0.1, 0.6, 0.4, 0.2] as const;

  it("shows the whole screen first, then zooms and holds", () => {
    assert.deepEqual(focusTransform(0, box), { scale: 1, x: 0, y: 0 });
    const end = focusTransform(1, box);
    assert.ok(end.scale > 1.9 && end.scale <= 2);
    assert.deepEqual(focusTransform(0.9, box), end);
  });

  it("moves toward the focus region without revealing the image edge", () => {
    for (const t of [0.3, 0.5, 0.7, 1]) {
      const { scale, x, y } = focusTransform(t, box);
      const limit = 0.5 - 0.5 / scale;
      assert.ok(x >= 0 && x <= limit + 1e-9);
      assert.ok(y <= 0 && y >= -limit - 1e-9);
    }
  });

  it("zooms gently into a large region", () => {
    assert.equal(focusTransform(1, [0, 0, 0.9, 0.9]).scale, 1.15);
  });

  it("accepts only four fractions", () => {
    assert.deepEqual(focusOf([0.1, 0.2, 0.3, 0.4]), [0.1, 0.2, 0.3, 0.4]);
    assert.equal(focusOf(null), null);
    assert.equal(focusOf([0.1, 0.2, 0.3]), null);
    assert.equal(focusOf([0.1, 0.2, 1.3, 0.4]), null);
    assert.equal(focusOf([0.1, 0.2, 0, 0.4]), null);
  });
});
