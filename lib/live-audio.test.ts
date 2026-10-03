import { describe, expect, it, vi } from "vitest";

import { normalizedRms, outputVisualState, Pcm16StreamEncoder, stopQueuedPlayback } from "./live-audio";

describe("Gemini Live audio presentation", () => {
  it.each([44_100, 48_000])("encodes exactly one second of %i Hz input at 16 kHz without chunk drift", (rate) => {
    const encoder = new Pcm16StreamEncoder(rate);
    let bytes = 0;
    for (let offset = 0; offset < rate; offset += 128) bytes += encoder.encode(new Float32Array(Math.min(128, rate - offset))).length;
    expect(bytes).toBe(32_000);
  });

  it("encodes signed-16 little-endian, clipping invalid/amplified samples safely", () => {
    const bytes = new Pcm16StreamEncoder(16_000).encode(new Float32Array([-1, 1, Number.NaN, 2, -2]));
    expect([...bytes]).toEqual([0, 128, 255, 127, 0, 0, 255, 127, 0, 128]);
  });
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
