import { describe, expect, it } from "vitest";

import { getGoogleApiKey } from "./google-api-key";

describe("Google API key configuration", () => {
  it("prefers GOOGLE_API_KEY", () => {
    expect(getGoogleApiKey({ GOOGLE_API_KEY: "google-key", GEMINI_API_KEY: "legacy-key" })).toBe("google-key");
  });

  it("keeps GEMINI_API_KEY as a backwards-compatible fallback", () => {
    expect(getGoogleApiKey({ GEMINI_API_KEY: "legacy-key" })).toBe("legacy-key");
  });

  it("ignores empty values", () => {
    expect(getGoogleApiKey({ GOOGLE_API_KEY: " ", GEMINI_API_KEY: "" })).toBeUndefined();
  });
});
