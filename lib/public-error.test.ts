import { describe, expect, it } from "vitest";

import { publicErrorMessage } from "./public-error";

describe("publicErrorMessage", () => {
  it("reads FastAPI {code, message} objects instead of crashing React", () => {
    expect(publicErrorMessage({ code: "internal_error", message: "invalid Brief" }, "fallback")).toBe("invalid Brief");
  });

  it("reads nested { error: { message } }", () => {
    expect(publicErrorMessage({ error: { code: "x", message: "Brief save failed." } }, "fallback")).toBe("Brief save failed.");
  });

  it("keeps a plain string", () => {
    expect(publicErrorMessage("Screenshot upload failed.", "fallback")).toBe("Screenshot upload failed.");
  });
});
