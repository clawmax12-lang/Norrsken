// @vitest-environment jsdom
// MOCK persisted job states, never a real Opus/render/Gemini acceptance test.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { FinalVideoFinish } from "./final-video-finish";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
const props = { apiBase: "/preflight-api", projectId: "proj-1", variantId: "B", sourceHash: "b".repeat(64) };
const completed = {
  command_id: "finish-12345678", status: "done", opus_attempts: 1, error: null, brain_sim: false,
  files: { video: "/api/projects/proj-1/finalization/video", report: "/api/projects/proj-1/finalization/report" },
  usage: { model: "claude-opus-5-5", route: "condense/anthropic", input_tokens: 100, output_tokens: 200 },
};

it("opening and cancelling confirmation cannot start a paid job", async () => {
  const fetchMock = vi.fn().mockResolvedValue(new Response("null"));
  vi.stubGlobal("fetch", fetchMock);
  render(<FinalVideoFinish {...props} />);
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  fireEvent.click(screen.getByRole("button", { name: "Finish with Opus" }));
  expect(screen.getByRole("button", { name: "Confirm paid finish" })).toBeDefined();
  fireEvent.click(screen.getByRole("button", { name: "Keep original" }));
  expect(fetchMock.mock.calls.every(([, init]) => init?.method !== "POST")).toBe(true);
});

it("explicit confirmation sends only the approved winner/hash and exposes distinct final evidence", async () => {
  let done = false;
  const fetchMock = vi.fn().mockImplementation((_url, init) => {
    if (init?.method === "POST") { done = true; return Promise.resolve(new Response(JSON.stringify(completed), { status: 202 })); }
    return Promise.resolve(new Response(done ? JSON.stringify(completed) : "null"));
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<FinalVideoFinish {...props} />);
  fireEvent.click(screen.getByRole("button", { name: "Finish with Opus" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirm paid finish" }));
  await screen.findByRole("link", { name: "Finished MP4" });
  const sent = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
  expect(JSON.parse(sent![1].body)).toMatchObject({ confirmed: true, variant_id: "B", source_video_sha256: props.sourceHash });
  expect(screen.getByText(/ranking above still belongs to the original/)).toBeDefined();
  expect(screen.getByRole("link", { name: "Final evidence (JSON)" }).getAttribute("href")).toContain("/finalization/report");
});

it("keeps a missing backend credential visible after refreshing empty status", async () => {
  const fetchMock = vi.fn().mockImplementation((_url, init) => Promise.resolve(new Response(init?.method === "POST" ? JSON.stringify({ error: { message: "ANTHROPIC_API_KEY is not set on the backend" } }) : "null", { status: init?.method === "POST" ? 503 : 200 })));
  vi.stubGlobal("fetch", fetchMock);
  render(<FinalVideoFinish {...props} />);
  fireEvent.click(screen.getByRole("button", { name: "Finish with Opus" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirm paid finish" }));
  await screen.findByRole("alert");
  await waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(3));
  expect(screen.getByRole("alert").textContent).toContain("ANTHROPIC_API_KEY");
});
