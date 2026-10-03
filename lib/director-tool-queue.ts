import type { FunctionCall } from "@google/genai";

export type DirectorToolResult = { output?: Record<string, unknown>; error?: string; cancelled?: boolean };
export type DirectorToolHandler = (call: FunctionCall) => Promise<Record<string, unknown>>;
export type DirectorUserTurn = { number: number; text: string; origin: "voice" | "typed" };

function safeError(error: unknown) {
  return (error instanceof Error ? error.message : "The canvas could not confirm this action.")
    .replace(/AIza[\w-]+/g, "[redacted]")
    .replace(/Bearer\s+\S+/gi, "Bearer [redacted]")
    .slice(0, 400);
}

/** Serialize across messages as well as within a burst. Never repeat a call ID. */
export class DirectorToolQueue {
  private tail: Promise<unknown> = Promise.resolve();
  private calls = new Map<string, { signature: string; result: Promise<DirectorToolResult> }>();
  private cancelled = new Set<string>();
  private closed = false;

  cancel(ids: string[]) { for (const id of ids) this.cancelled.add(id); }
  close() { this.closed = true; }

  execute(call: FunctionCall, handler: DirectorToolHandler): Promise<DirectorToolResult> {
    if (!call.id || !call.name) return Promise.resolve({ error: "Tool call must have an ID and name; no action was taken." });
    const id = call.id;
    const signature = JSON.stringify({ name: call.name, args: call.args ?? {} });
    const prior = this.calls.get(id);
    if (prior) return prior.signature === signature ? prior.result : Promise.resolve({ error: "Tool call ID was reused with different arguments; no action was taken." });
    if (this.calls.size >= 256) return Promise.resolve({ error: "Voice action limit reached. Reconnect before making more changes." });
    const result = this.tail.then(async (): Promise<DirectorToolResult> => {
      if (this.closed || this.cancelled.has(id)) return { cancelled: true, error: "Action cancelled before execution; read current project state." };
      try { return { output: await handler(call) }; }
      catch (error) { return { error: safeError(error) }; }
    });
    this.calls.set(id, { signature, result });
    this.tail = result;
    return result;
  }
}
