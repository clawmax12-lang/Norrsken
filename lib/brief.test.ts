import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { applyBriefFieldInput, briefSchema } from "./brief";

describe("briefSchema", () => {
  const fixture = JSON.parse(
    readFileSync(path.join(process.cwd(), "fixtures", "tablehopp", "brief.json"), "utf8"),
  );

  it("accepts the committed tablehopp fixture", () => {
    expect(briefSchema.parse(fixture)).toEqual(fixture);
  });

  it("requires 3 to 6 screenshots", () => {
    expect(briefSchema.safeParse({ ...fixture, screenshots: ["one.png", "two.png"] }).success).toBe(false);
    expect(
      briefSchema.safeParse({ ...fixture, screenshots: Array.from({ length: 7 }, (_, index) => `${index}.png`) }).success,
    ).toBe(false);
  });

  it("defaults missing render_mode to showcase", () => {
    const { render_mode, ...rest } = fixture;
    expect(render_mode).toBe("showcase");
    expect(briefSchema.parse(rest).render_mode).toBe("showcase");
  });

  it("rejects invented overlong one-line copy", () => {
    expect(briefSchema.safeParse({ ...fixture, one_liner: "x".repeat(141) }).success).toBe(false);
  });
});

describe("applyBriefFieldInput", () => {
  it("keeps a trailing space while typing so words are not glued together", () => {
    expect(applyBriefFieldInput("product_name", "Sell anything ", "live")).toBe("Sell anything ");
    expect(applyBriefFieldInput("one_liner", "Sell anything online", "live")).toBe("Sell anything online");
  });

  it("trims only at commit so Run still stores clean source words", () => {
    expect(applyBriefFieldInput("product_name", "Sell anything ", "commit")).toBe("Sell anything");
    expect(applyBriefFieldInput("goal_note", "  Start selling today  ", "commit")).toBe("Start selling today");
  });

  it("rejects copy that exceeds the confirmed field cap", () => {
    expect(() => applyBriefFieldInput("one_liner", "x".repeat(141), "live")).toThrow(/140/);
  });
});
