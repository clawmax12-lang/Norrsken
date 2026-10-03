// MOCK provider: validates server configuration and sanitization, not Live acceptance.
import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "./route";

const provider = vi.hoisted(() => ({ create: vi.fn(), options: vi.fn() }));
vi.mock("@google/genai", async original => ({
  ...await original<typeof import("@google/genai")>(),
  GoogleGenAI: class { constructor(options: unknown) { provider.options(options); } authTokens = { create: provider.create }; },
}));
function request(id: string) {
  return new NextRequest("http://localhost/api/live-token", { method: "POST", headers: { host: "localhost", origin: "http://localhost", "x-forwarded-for": id } });
}
afterEach(() => { vi.unstubAllEnvs(); vi.restoreAllMocks(); });
describe("Live token route (MOCK)", () => {
  it("uses the ephemeral-token v1alpha endpoint and a scoped one-use token", async () => {
    vi.stubEnv("GOOGLE_API_KEY", "MOCK_server_only");
    provider.create.mockResolvedValueOnce({ name: "MOCK_ephemeral", expireTime: "later" });
    const response = await POST(request("endpoint"));
    expect(response.status).toBe(200);
    expect(provider.options).toHaveBeenLastCalledWith({ apiKey: "MOCK_server_only", httpOptions: { apiVersion: "v1alpha" } });
    expect(provider.create.mock.calls.at(-1)?.[0].config.uses).toBe(1);
    expect(response.headers.get("Cache-Control")).toBe("no-store");
    expect(await response.json()).toMatchObject({ token: "MOCK_ephemeral", model: "gemini-3.8-live" });
  });
  it("reports safe credential diagnostics without logging provider keys/URLs", async () => {
    vi.stubEnv("GOOGLE_API_KEY", "MOCK_server_only");
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    provider.create.mockRejectedValueOnce({ status: 403, message: "MOCK_secret_request_url" });
    const response = await POST(request("auth"));
    expect(response.status).toBe(502);
    const body = await response.json();
    expect(body.code).toBe("auth_rejected");
    expect(JSON.stringify([body, log.mock.calls])).not.toContain("MOCK_secret");
  });
});
