import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ctaStartFrame, sceneWindows } from "./timeline.ts";
import type { CompositionSpec } from "../spec/types.generated.ts";

const spec: CompositionSpec = {
  variant_id: "A",
  fps: 30,
  duration_frames: 450,
  theme: { background: "#f5f5f7", foreground: "#1d1d1f", accent: "#5b5bd6", font_family: "Inter" },
  scenes: [
    {
      start_frame: 0,
      end_frame: 360,
      text: "Hook",
      source_field: "one_liner",
      screenshot: "a.png",
      layout: "device_center",
      transition_in: "fade",
    },
    {
      start_frame: 360,
      end_frame: 450,
      text: "End",
      source_field: "product_name",
      screenshot: "b.png",
      layout: "device_center",
      transition_in: "fade",
    },
  ],
  cta: "Acme",
  cta_source_field: "product_name",
  wordmark: "Acme",
  headline: "Hook",
  headline_source_field: "one_liner",
};

describe("end card timeline", () => {
  it("locks the last 3 seconds at 30 fps", () => {
    assert.equal(ctaStartFrame(spec), 360);
    const windows = sceneWindows(spec);
    assert.equal(windows.length, 1);
    assert.equal(windows[0]?.from, 0);
  });
});
