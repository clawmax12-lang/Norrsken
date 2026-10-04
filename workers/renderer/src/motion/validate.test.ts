import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { parseMotionSpec } from "./validate.ts";

const FIXTURE = JSON.stringify({
  variant_id: "A",
  width: 1080,
  height: 1920,
  fps: 60,
  duration_frames: 900,
  theme: { background: "#f5f5f7", foreground: "#1d1d1f", accent: "#5b5bd6", font_family: "Inter" },
  shots: [
    {
      screenshot: "uploads/1.png",
      start_frame: 0,
      end_frame: 900,
      text: "Notes",
      source_field: "product_name",
      t_start: 0,
      t_end: 15,
      layers: [
        { id: "a", kind: "panel", bbox_norm: [0.1, 0.2, 0.5, 0.4], confidence: 0.9 },
        { id: "b", kind: "button", bbox_norm: [0.2, 0.7, 0.3, 0.08], confidence: 0.88 },
        { id: "c", kind: "icon", bbox_norm: [0.72, 0.18, 0.12, 0.08], confidence: 0.86 },
      ],
    },
  ],
  cta: "Notes",
  cta_source_field: "product_name",
  wordmark: "Notes",
  headline: "Notes",
  headline_source_field: "product_name",
  underlay: true,
});

describe("parseMotionSpec", () => {
  it("accepts a three-layer-capable 900-frame fixture", async () => {
    const spec = await parseMotionSpec(FIXTURE);
    assert.equal(spec.fps, 60);
    assert.equal(spec.duration_frames, 900);
    assert.equal(spec.shots[0]?.layers.length, 3);
    assert.equal(spec.underlay, true);
  });
});
