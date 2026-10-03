import { describe, expect, it } from "vitest";

import { DIRECTOR_INSTRUCTION, directorTools, LIVE_MODEL } from "./director";

describe("Preflight Director contract", () => {
  it("uses the adopted low-latency Live model", () => {
    expect(LIVE_MODEL).toBe("gemini-3.8-live");
  });

  it("declares unique inspectable tools", () => {
    const names = directorTools.map((tool) => tool.name);
    expect(new Set(names).size).toBe(names.length);
    expect(names).toEqual([
      "update_brief",
      "search_assets",
      "select_asset",
      "inspect_asset",
      "select_scene",
      "edit_scene_copy",
      "set_scene_asset",
      "reorder_scene",
      "record_decision",
      "request_run_confirmation",
    ]);
  });

  it("forbids unsupported TRIBE claims during intake", () => {
    expect(DIRECTOR_INSTRUCTION).toContain("Do not cite TRIBE");
    expect(DIRECTOR_INSTRUCTION).toContain("Never invent");
    expect(DIRECTOR_INSTRUCTION).toContain("creative rationale");
  });
});
