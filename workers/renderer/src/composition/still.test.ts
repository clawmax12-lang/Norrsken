import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { DEVICE } from "./tokens.ts";
import { MAX_UPSCALE, coverLayout, focusOf, focusTransform, isPhoneAspect, regionAspect, stageTransform } from "./still.ts";

describe("product still", () => {
  it("keeps a phone frame for portrait screenshots only", () => {
    assert.equal(isPhoneAspect(0.46), true);
    assert.equal(isPhoneAspect(DEVICE.phoneMaxAspect), true);
    assert.equal(isPhoneAspect(16 / 9), false);
  });

  it("decides phone or window from the shown region, not the whole mockup", () => {
    const mockup = { width: 1066, height: 756 };
    assert.equal(isPhoneAspect(regionAspect(mockup, null)), false);
    assert.equal(isPhoneAspect(regionAspect(mockup, [0.37, 0.1, 0.27, 0.79])), true);
  });

  it("covers the box with exactly the crop region, centred", () => {
    const layout = coverLayout({ width: 1000, height: 500 }, [0.5, 0, 0.25, 1], 500, 1000);
    assert.equal(layout.scale, 2);
    assert.equal(layout.left, -1000);
    assert.equal(layout.top, 0);
    assert.equal(layout.width, 2000);
  });

  it("drifts slowly, but not at all when the source is already enlarged to the cap", () => {
    assert.equal(stageTransform(1, null, 1), "scale(1.050)");
    assert.equal(stageTransform(1, null, MAX_UPSCALE), "scale(1.000)");
  });
});

describe("focus punch-in", () => {
  const box = [0.1, 0.6, 0.4, 0.2] as const;

  it("shows the whole screen first, then zooms and holds", () => {
    assert.deepEqual(focusTransform(0, box), { scale: 1, x: 0, y: 0 });
    const end = focusTransform(1, box);
    assert.ok(Math.abs(end.scale - 0.85 / 0.5) < 1e-9);
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
    assert.equal(focusTransform(1, [0, 0, 0.8, 0.8]).scale, 1.15);
  });

  it("never zooms so far that the focus region is cut", () => {
    const wide = [0, 0.17, 0.91, 0.37] as const;
    const { scale, x } = focusTransform(1, wide);
    const visibleLeft = 0.5 - x - 0.5 / scale;
    const visibleRight = 0.5 - x + 0.5 / scale;
    assert.ok(visibleLeft <= wide[0] + 1e-9 && visibleRight >= wide[0] + wide[2] - 1e-9);
  });

  it("never zooms a small source past the upscale cap", () => {
    assert.equal(focusTransform(1, box, 1.3).scale, 1.3);
    assert.equal(focusTransform(1, box, 0.8).scale, 1);
    assert.match(stageTransform(1, box, 1.6), /^scale\(1\.250\)/);
  });

  it("accepts only four fractions", () => {
    assert.deepEqual(focusOf([0.1, 0.2, 0.3, 0.4]), [0.1, 0.2, 0.3, 0.4]);
    assert.equal(focusOf(null), null);
    assert.equal(focusOf([0.1, 0.2, 0.3]), null);
    assert.equal(focusOf([0.1, 0.2, 1.3, 0.4]), null);
    assert.equal(focusOf([0.1, 0.2, 0, 0.4]), null);
  });
});
