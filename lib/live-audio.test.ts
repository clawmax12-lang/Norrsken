import { describe, expect, it, vi } from "vitest";

import { normalizedRms, outputVisualState, stopQueuedPlayback } from "./live-audio";

describe("Gemini Live audio presentation", () => {
  it("normalizes measured samples without inventing activity", () => {
    expect(normalizedRms(new Float32Array())).toBe(0);
    expect(normalizedRms(new Float32Array([0, 0, 0]))).toBe(0);
    expect(normalizedRms(new Float32Array([0.5, -0.5]), 2)).toBe(1);
  });

  it("shows output only while a source is audible and unmuted", () => {
    const output = new Float32Array([0.1, -0.1, 0.1, -0.1]);
    expect(outputVisualState(output, 1, false)).toMatchObject({ isSpeaking: true });
    expect(outputVisualState(output, 0, false)).toEqual({ level: 0, isSpeaking: false });
    expect(outputVisualState(output, 1, true)).toEqual({ level: 0, isSpeaking: false });
  });

  it("stops and discards the full scheduled queue even if one source already ended", () => {
    const first = { stop: vi.fn() };
    const ended = { stop: vi.fn(() => { throw new Error("already ended"); }) };
    const last = { stop: vi.fn() };
    const queue = new Set([first, ended, last]);

    stopQueuedPlayback(queue);

    expect(first.stop).toHaveBeenCalledOnce();
    expect(ended.stop).toHaveBeenCalledOnce();
    expect(last.stop).toHaveBeenCalledOnce();
    expect(queue.size).toBe(0);
  });
});
