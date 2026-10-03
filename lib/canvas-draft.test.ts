import { describe, expect, it } from "vitest";

import { canvasDraftSchema, createCanvasDraft, reorderScenes, replaceScene } from "./canvas-draft";

describe("canvas draft", () => {
  it("starts with exactly three five-scene concepts", () => {
    const draft = createCanvasDraft("project-one");
    expect(draft.concepts.map((concept) => concept.variant_id)).toEqual(["A", "B", "C"]);
    expect(draft.concepts.every((concept) => concept.scenes.length === 5 && concept.duration_s === 15)).toBe(true);
  });

  it("requires a source field for visible copy", () => {
    const draft = createCanvasDraft("project-one");
    expect(() => replaceScene(draft, "A-scene-1", { text: "Unverified claim" })).toThrow();
  });

  it("increments revisions for valid source-backed edits and reorders", () => {
    const draft = replaceScene(createCanvasDraft("project-one"), "A-scene-1", { text: "Real description", source_field: "one_liner" });
    const reordered = reorderScenes(draft, "A", 1, 2);
    expect(reordered.revision).toBe(2);
    expect(reordered.concepts[0].scenes[1].text).toBe("Real description");
    expect(canvasDraftSchema.parse(reordered)).toEqual(reordered);
  });
});
