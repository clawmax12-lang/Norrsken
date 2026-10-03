// MOCK backend only: no provider requests and no real credentials.
import { NextRequest } from "next/server";
import { afterEach, expect, it, vi } from "vitest";
import { POST } from "./route";

const command = { command_id: "finish-12345678", confirmed: true, variant_id: "B", source_video_sha256: "b".repeat(64) };
const context = { params: Promise.resolve({ projectId: "proj-1" }) };
function request(body: unknown = command, origin = "https://preflight.example") {
  return new NextRequest("https://preflight.example/api/projects/proj-1/finalization", {
    method: "POST", headers: { "Content-Type": "application/json", origin }, body: JSON.stringify(body),
  });
}
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

it("forwards only validated approval and lineage, never a permanent API key", async () => {
  vi.stubEnv("PREFLIGHT_API_URL", "https://backend.example/");
  vi.stubEnv("ANTHROPIC_API_KEY", "MOCK_server_secret");
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "queued" }), { status: 202 }));
  vi.stubGlobal("fetch", fetchMock);
  const response = await POST(request(), context);
  expect(response.status).toBe(202);
  expect(fetchMock.mock.calls[0][0]).toBe("https://backend.example/api/projects/proj-1/finalization");
  expect(fetchMock.mock.calls[0][1].headers["Idempotency-Key"]).toBe(command.command_id);
  expect(JSON.stringify(fetchMock.mock.calls)).not.toContain("MOCK_server_secret");
  expect(response.headers.get("Cache-Control")).toBe("no-store");
});

it("rejects unconfirmed, arbitrary-code and cross-origin requests without calling the backend", async () => {
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  for (const r of [request({ ...command, confirmed: false }), request({ ...command, code: "arbitrary" }), request(command, "https://evil.example")]) {
    expect((await POST(r, context)).status).toBe(400);
  }
  expect(fetchMock).not.toHaveBeenCalled();
});

it("reports an unconnected backend explicitly", async () => {
  vi.stubEnv("PREFLIGHT_API_URL", "");
  expect((await POST(request(), context)).status).toBe(503);
});
