import { describe, expect, it } from "vitest";

import { publicErrorMessage, readJson, SERVER_UNREACHABLE } from "./public-error";

describe("readJson", () => {
  it("returns the parsed body", async () => {
    expect(await readJson(new Response('{"status":"queued"}'))).toEqual({ status: "queued" });
  });

  it("turns a tunnel error page into a readable error", async () => {
    const page = new Response("<html>Error 1033 Cloudflare Tunnel error</html>", { status: 530 });
    expect(await readJson(page)).toEqual({ error: SERVER_UNREACHABLE });
  });
});

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
