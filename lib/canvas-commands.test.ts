import { describe, expect, it } from "vitest";

import { isGroundedCopy, normalizeGoal, parseTypedCommand } from "./canvas-commands";

describe("normalizeGoal", () => {
  it("maps loose phrasing onto the four supported goals", () => {
    expect(normalizeGoal("Sign-ups")).toBe("signups");
    expect(normalizeGoal("app downloads")).toBe("downloads");
    expect(normalizeGoal("awareness")).toBe("understand");
    expect(normalizeGoal("buy now")).toBe("purchase");
  });

  it("rejects goals outside the brief contract", () => {
    expect(normalizeGoal("go viral")).toBeNull();
  });
});

describe("isGroundedCopy", () => {
  const source = "Book a table at the best restaurants in Stockholm";

  it("accepts copy taken from the confirmed source", () => {
    expect(isGroundedCopy("best restaurants in Stockholm", source)).toBe(true);
    expect(isGroundedCopy("Stockholm restaurants, book!", source)).toBe(true);
  });

  it("rejects copy that adds claims the source does not contain", () => {
    expect(isGroundedCopy("Free tables in Stockholm", source)).toBe(false);
    expect(isGroundedCopy("anything", "")).toBe(false);
  });
});

describe("parseTypedCommand", () => {
  it("parses brief fields", () => {
    expect(parseTypedCommand("product is tablehopp")).toEqual({ kind: "brief", field: "product_name", value: "tablehopp" });
    expect(parseTypedCommand("one-liner: Book tables fast")).toEqual({ kind: "brief", field: "one_liner", value: "Book tables fast" });
    expect(parseTypedCommand("audience is diners")).toEqual({ kind: "brief", field: "audience", value: "diners" });
    expect(parseTypedCommand("goal is downloads")).toEqual({ kind: "brief", field: "goal", value: "downloads" });
  });

  it("parses storyboard edits and run", () => {
    expect(parseTypedCommand("select b scene 2")).toEqual({ kind: "select", variant: "B", scene: 2 });
    expect(parseTypedCommand("use description as copy")).toEqual({ kind: "use-copy", field: "one_liner" });
    expect(parseTypedCommand("move scene 2 to 1")).toEqual({ kind: "move", from: 2, to: 1 });
    expect(parseTypedCommand("  run preflight ")).toEqual({ kind: "run" });
  });

  it("returns null for open-ended requests", () => {
    expect(parseTypedCommand("make it punchier")).toBeNull();
  });
});
