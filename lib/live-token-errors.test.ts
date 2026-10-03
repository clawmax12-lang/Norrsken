import { describe, expect, it } from "vitest";
import { LIVE_TOKEN_ERRORS, liveTokenFailure, liveTokenMessage } from "./live-token-errors";

describe("safe Live token diagnostics", () => {
  it.each([[401, "auth_rejected"], [403, "auth_rejected"], [404, "model_unavailable"], [429, "rate_limited"], [500, "provider_unavailable"]])("classifies provider HTTP %s without forwarding its message", (status, code) => {
    const result = liveTokenFailure({ status, message: "MOCK_secret_request_url" });
    expect(result.code).toBe(code); expect(JSON.stringify(result)).not.toContain("MOCK_secret");
    expect(result.status).toBe(status === 429 ? 429 : 502);
  });
  it("does not mistake timeouts/network errors for an account/model diagnosis", () => {
    expect(liveTokenFailure(new Error("private"))).toEqual({ code: "provider_unavailable", error: LIVE_TOKEN_ERRORS.provider_unavailable, status: 502 });
  });
  it("only displays allowlisted codes, never arbitrary server/proxy strings", () => {
    expect(liveTokenMessage({ code: "auth_rejected" }, 502)).toBe(LIVE_TOKEN_ERRORS.auth_rejected);
    expect(liveTokenMessage({ code: "__proto__" }, 502)).toBe(LIVE_TOKEN_ERRORS.provider_unavailable);
    expect(liveTokenMessage({ code: "private_request_url" }, 503)).toBe(LIVE_TOKEN_ERRORS.not_configured);
  });
});
