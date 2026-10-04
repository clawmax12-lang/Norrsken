import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { cropLayer, largestLayer, productRect, punchIn } from "./crop.ts";
import { PRODUCT_ZONE, TYPE_ZONE } from "../composition/tokens.ts";

describe("cropLayer", () => {
  it("places a bbox as a crop of the full frame, not an empty fill", () => {
    const crop = cropLayer([0.1, 0.2, 0.5, 0.4], 1080, 1920);
    assert.ok(crop);
    assert.equal(crop.box.left, 108);
    assert.equal(crop.box.top, 384);
    assert.equal(crop.box.width, 540);
    assert.equal(crop.box.height, 768);
    assert.equal(crop.image.left, -108);
    assert.equal(crop.image.top, -384);
    assert.equal(crop.image.width, 1080);
    assert.equal(crop.image.height, 1920);
  });

  it("letterboxes a landscape source instead of stretching it to the portrait stage", () => {
    const crop = cropLayer([0.1, 0.2, 0.5, 0.4], 1080, 1920, 16 / 9);
    assert.ok(crop);
    assert.equal(crop.box.left, 108);
    assert.ok(crop.box.top > 384);
    assert.ok(crop.image.height < 1920);
  });

  it("drops degenerate boxes instead of drawing a placeholder", () => {
    assert.equal(cropLayer([0.1, 0.2, 0.01, 0.4], 1080, 1920), null);
  });
});

describe("punchIn", () => {
  it("keeps the product band strictly below the type band", () => {
    const dest = productRect();
    assert.ok(dest.top >= TYPE_ZONE.top + TYPE_ZONE.height);
    assert.equal(dest.top, PRODUCT_ZONE.top);
  });
  it("covers the product band with the hero bbox instead of letterboxing the whole photo", () => {
    const dest = productRect();
    const crop = punchIn([0.27, 0.16, 0.44, 0.58], 16 / 9, dest);
    assert.ok(crop);
    assert.equal(crop.box.top, dest.top);
    assert.equal(crop.box.height, dest.height);
    assert.ok(crop.box.top >= 500);
    assert.ok(crop.image.width > dest.width);
  });

  it("picks the largest layer as the hero", () => {
    const hero = largestLayer([
      { bbox_norm: [0.1, 0.1, 0.1, 0.1] as const },
      { bbox_norm: [0.2, 0.2, 0.5, 0.4] as const },
    ]);
    assert.deepEqual(hero?.bbox_norm, [0.2, 0.2, 0.5, 0.4]);
  });
});
