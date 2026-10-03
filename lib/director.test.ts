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
      "get_project_context",
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
      "confirm_run",
    ]);
  });

  it("forbids unsupported TRIBE claims during intake", () => {
    expect(DIRECTOR_INSTRUCTION).toContain("Do not cite TRIBE");
    expect(DIRECTOR_INSTRUCTION).toContain("Never invent");
    expect(DIRECTOR_INSTRUCTION).toContain("creative rationale");
  });

  it("prioritizes real context, Swedish conversation, explicit consent and asynchronous runs", () => {
    expect(DIRECTOR_INSTRUCTION).toContain("including Swedish");
    expect(DIRECTOR_INSTRUCTION).toContain("at most one useful question");
    expect(DIRECTOR_INSTRUCTION).toContain("existing video");
    expect(DIRECTOR_INSTRUCTION).toContain("capability flags");
    expect(DIRECTOR_INSTRUCTION).toContain("An ID is not consent");
    expect(directorTools.find((tool) => tool.name === "confirm_run")?.behavior).toBe("NON_BLOCKING");
  });
});
