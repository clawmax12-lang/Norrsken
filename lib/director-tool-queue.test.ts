import { describe, expect, it, vi } from "vitest";
import { DirectorToolQueue } from "./director-tool-queue";

describe("Live tool queue", () => {
  it("serializes scene selection and dependent edits across concurrent messages", async () => {
    const order: string[] = [];
    let resolve!: () => void;
    const first = new Promise<void>((done) => { resolve = done; });
    const queue = new DirectorToolQueue();
    const selection = queue.execute({ id: "1", name: "select_scene" }, async () => { order.push("selection started"); await first; order.push("selection saved"); return { saved: true }; });
    const edit = queue.execute({ id: "2", name: "edit_scene_copy" }, async () => { order.push("edit saved"); return { saved: true }; });
    await Promise.resolve();
    expect(order).toEqual(["selection started"]);
    resolve(); await Promise.all([selection, edit]);
    expect(order).toEqual(["selection started", "selection saved", "edit saved"]);
  });
  it("deduplicates a repeated tool call, including while in flight", async () => {
    const queue = new DirectorToolQueue();
    const handler = vi.fn(async () => ({ saved: true }));
    const call = { id: "same", name: "record_decision", args: { choice: "opening" } };
    expect(await Promise.all([queue.execute(call, handler), queue.execute(call, handler)])).toEqual([{ output: { saved: true } }, { output: { saved: true } }]);
    expect(handler).toHaveBeenCalledTimes(1);
    expect(await queue.execute({ ...call, args: { choice: "different" } }, handler)).toHaveProperty("error");
    expect(handler).toHaveBeenCalledTimes(1);
  });
  it("honors cancellation and disconnect before side effects", async () => {
    const queue = new DirectorToolQueue();
    const handler = vi.fn(async () => ({}));
    queue.cancel(["cancelled"]);
    expect(await queue.execute({ id: "cancelled", name: "edit_scene_copy" }, handler)).toHaveProperty("cancelled", true);
    queue.close();
    expect(await queue.execute({ id: "closed", name: "confirm_run" }, handler)).toHaveProperty("cancelled", true);
    expect(handler).not.toHaveBeenCalled();
  });
  it("returns failure instead of success on persistence errors", async () => {
    const result = await new DirectorToolQueue().execute({ id: "failed", name: "edit_scene_copy" }, async () => { throw new Error("Server save failed"); });
    expect(result).toEqual({ error: "Server save failed" });
  });
  it("refuses anonymous calls and redacts sensitive transport errors", async () => {
    const queue = new DirectorToolQueue();
    const handler = vi.fn(async () => { throw new Error("Credential Bearer secret-token"); });
    expect(await queue.execute({ name: "confirm_run" }, handler)).toHaveProperty("error");
    expect(handler).not.toHaveBeenCalled();
    expect((await queue.execute({ id: "bad", name: "update_brief" }, handler)).error).not.toContain("secret-token");
  });
});
