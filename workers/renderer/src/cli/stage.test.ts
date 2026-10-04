import { describe, it } from "node:test";
import assert from "node:assert/strict";
import type { CompositionSpec } from "../spec/types.generated.ts";
import { referencedAssets } from "./stage.ts";

const scene = (screenshot: string, backdrop?: string) => ({
  start_frame: 0,
  end_frame: 90,
  layout: "device_center" as const,
  screenshot,
  source_field: "one_liner" as const,
  text: "Sell anything online",
  transition_in: "cut" as const,
  backdrop: backdrop
    ? { kind: "image" as const, model: "test", path: backdrop, prompt: "bg", sha256: "0".repeat(64) }
    : null,
});

const spec = (partial: Partial<CompositionSpec> & Pick<CompositionSpec, "scenes">): CompositionSpec => ({
  variant_id: "A",
  duration_frames: 450,
  theme: { accent: "#f00", background: "#000", font_family: "Redaction", foreground: "#fff" },
  cta: "Shopify",
  cta_source_field: "product_name",
  wordmark: "Shopify",
  headline: "Sell anything online",
  headline_source_field: "one_liner",
  ...partial,
});

describe("referencedAssets", () => {
  it("stages screenshots and backdrops, not only the logo", () => {
    const listed = referencedAssets(
      spec({
        logo: "assets/logo.png",
        scenes: [
          scene("assets/one.jpg", "generated/bg.png"),
          scene("assets/one.jpg"),
          scene("assets/two.jpg"),
        ],
      }),
    );
    assert.deepEqual(listed.sort(), ["assets/logo.png", "assets/one.jpg", "assets/two.jpg", "generated/bg.png"].sort());
  });

  it("still stages screenshots when there is no logo", () => {
    const listed = referencedAssets(spec({ logo: null, scenes: [scene("assets/shot.jpg")] }));
    assert.deepEqual(listed, ["assets/shot.jpg"]);
  });
});
