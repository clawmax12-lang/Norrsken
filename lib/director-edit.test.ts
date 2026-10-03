import { describe, expect, it } from "vitest";
import { createCanvasDraft } from "./canvas-draft";
import { assertEditableScene } from "./director-edit";

describe("pre-render edit boundary", () => {
  it("locks confirmed/queued content even before a backend concept status arrives", () => {
    expect(() => assertEditableScene(createCanvasDraft("test"), "A-scene-1", true)).toThrow("confirmed run");
  });
  it("requires the real selected scene", () => {
    const draft = createCanvasDraft("test");
    expect(() => assertEditableScene(draft, "B-scene-1")).toThrow("Select");
    expect(() => assertEditableScene(draft, "A-scene-1")).not.toThrow();
  });
  it.each(["rendering", "rendered", "tested", "failed"] as const)("does not patch a %s concept in place", (status) => {
    const draft = createCanvasDraft("test"); draft.concepts[0].status = status;
    expect(() => assertEditableScene(draft, "A-scene-1")).toThrow("locked");
  });
});
