import { describe, expect, it } from "vitest";

import { impactStory } from "./impact-story";

describe("impact story", () => {
  it("states the three problems a launch founder actually has", () => {
    expect(impactStory.problems.map((problem) => problem.title)).toEqual([
      "One chance",
      "Spend, then learn",
      "Nothing carries over",
    ]);
  });

  it("keeps the live case on the known tablehopp launch", () => {
    expect(impactStory.liveCase.product).toBe("tablehopp");
    expect(impactStory.liveCase.when).toBe("7 Oct 2026");
    expect(impactStory.liveCase.status).toMatch(/does not invent/i);
  });

  it("describes agreement as the confidence rule and refuses a sales forecast", () => {
    expect(impactStory.verdict.rule).toMatch(/two simulated viewers/i);
    expect(impactStory.verdict.rule).toMatch(/not a forecast/i);
    expect(impactStory.verdict.lanes).toEqual(["A", "B", "C"]);
  });

  it("contains no measured lift", () => {
    const text = JSON.stringify(impactStory);
    expect(text).not.toMatch(/\d+\s*%/);
    expect(text).not.toMatch(/go viral|predicts sales|times more/i);
  });
});
