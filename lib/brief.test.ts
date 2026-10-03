import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { briefSchema } from "./brief";

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

  it("rejects invented overlong one-line copy", () => {
    expect(briefSchema.safeParse({ ...fixture, one_liner: "x".repeat(141) }).success).toBe(false);
  });
});
