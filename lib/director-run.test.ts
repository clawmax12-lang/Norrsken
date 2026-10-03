import { describe, expect, it, vi } from "vitest";
import { DirectorRunBoundary, isExplicitRunConsent } from "./director-run";

describe("spoken/clicked run boundary", () => {
  it("requires explicit approval language, not a correction, refusal or tool-authored claim", () => {
    for (const text of ["Ja, kör testet", "Yes, go ahead", "Confirm run"]) expect(isExplicitRunConsent(text)).toBe(true);
    for (const text of ["nej", "yes but don't run yet", "ja men inte nu", "make the hook shorter", "the video says yes", ""]) expect(isExplicitRunConsent(text)).toBe(false);
  });
  it("does not submit a job by opening a confirmation", () => {
    const boundary = new DirectorRunBoundary();
    const first = boundary.request("draft-1", "three candidates");
    expect(boundary.request("draft-1", "three candidates").id).toBe(first.id);
  });
  it("rejects missing, cancelled or stale confirmations before submission", async () => {
    const boundary = new DirectorRunBoundary(); const submit = vi.fn(async () => ({}));
    await expect(boundary.confirm("unknown", "draft-1", submit)).rejects.toThrow("summary");
    const approval = boundary.request("draft-1", "three candidates");
    await expect(boundary.confirm(approval.id, "draft-2", submit)).rejects.toThrow("changed");
    boundary.cancel();
    await expect(boundary.confirm(approval.id, "draft-1", submit)).rejects.toThrow("summary");
    expect(submit).not.toHaveBeenCalled();
  });
  it("uses one command ID for a same-tick spoken/clicked double confirmation and reconnect", async () => {
    const boundary = new DirectorRunBoundary(); const submit = vi.fn(async (id: string) => ({ accepted: true, run_id: id }));
    const approval = boundary.request("draft-1", "three candidates");
    const results = await Promise.all([boundary.confirm(approval.id, "draft-1", submit), boundary.confirm(approval.id, "draft-1", submit)]);
    expect(results[0]).toEqual(results[1]); expect(submit).toHaveBeenCalledExactlyOnceWith(approval.id);
    await boundary.confirm(approval.id, "post-upload-revision", submit);
    expect(submit).toHaveBeenCalledTimes(1);
    expect(() => boundary.request("new-snapshot", "another run")).toThrow("already been submitted");
  });
  it("does not automatically retry an ambiguous network failure", async () => {
    const boundary = new DirectorRunBoundary(); const submit = vi.fn(async () => { throw new Error("Response lost"); });
    const approval = boundary.request("draft-1", "three candidates");
    await expect(boundary.confirm(approval.id, "draft-1", submit)).rejects.toThrow("Response lost");
    await expect(boundary.confirm(approval.id, "draft-1", submit)).rejects.toThrow("Response lost");
    expect(submit).toHaveBeenCalledTimes(1);
  });
});
