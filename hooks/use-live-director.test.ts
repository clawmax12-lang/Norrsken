// @vitest-environment jsdom
// MOCK transport/audio graphs: regression coverage, not real Gemini Live acceptance.
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { LiveServerMessage } from "@google/genai";
import { useLiveDirector } from "./use-live-director";

type Callbacks = { onmessage: (message: LiveServerMessage) => void; onerror: () => void; onclose: () => void };
const provider = vi.hoisted(() => ({ connect: vi.fn() }));
vi.mock("@google/genai", async (original) => ({ ...await original<typeof import("@google/genai")>(), GoogleGenAI: class { live = { connect: provider.connect }; } }));

const sources: Array<{ start: ReturnType<typeof vi.fn>; stop: ReturnType<typeof vi.fn>; connect: ReturnType<typeof vi.fn>; buffer?: AudioBuffer; onended?: () => void }> = [];
const contexts: MockAudioContext[] = [];
const captures: MockWorklet[] = [];
const callbacks: Callbacks[] = [];
const sessions: Array<{ close: ReturnType<typeof vi.fn>; sendRealtimeInput: ReturnType<typeof vi.fn>; sendClientContent: ReturnType<typeof vi.fn>; sendToolResponse: ReturnType<typeof vi.fn> }> = [];
let operations: string[];
let getUserMedia: ReturnType<typeof vi.fn>;

class MockAudioContext {
  state = "running"; sampleRate = 48_000; currentTime = 0; destination = {};
  audioWorklet = { addModule: vi.fn(async () => undefined) };
  resume = vi.fn(async () => { operations.push("resume output"); });
  close = vi.fn(async () => { this.state = "closed"; });
  createGain = vi.fn(() => ({ gain: { value: 1, setValueAtTime: vi.fn() }, connect: vi.fn() }));
  createAnalyser = vi.fn(() => ({ fftSize: 1024, smoothingTimeConstant: 0, connect: vi.fn(), getFloatTimeDomainData: (values: Float32Array) => values.fill(0) }));
  createMediaStreamSource = vi.fn(() => ({ connect: vi.fn() }));
  createBuffer = vi.fn((channels: number, length: number, rate: number) => ({ duration: length / rate, getChannelData: () => new Float32Array(length) }));
  createBufferSource = vi.fn(() => {
    const source = { start: vi.fn(), stop: vi.fn(), connect: vi.fn(), buffer: undefined, onended: undefined };
    sources.push(source); return source;
  });
  constructor() { contexts.push(this); }
}
class MockWorklet {
  port = { onmessage: null as ((event: MessageEvent<ArrayBuffer>) => void) | null };
  disconnect = vi.fn(); connect = vi.fn();
  constructor() { captures.push(this); }
}
function mockStream() {
  const track = { enabled: true, stop: vi.fn() };
  return { stream: { getTracks: () => [track], getAudioTracks: () => [track] } as unknown as MediaStream, track };
}
function emit(message: unknown, index = callbacks.length - 1) {
  callbacks[index].onmessage(message as LiveServerMessage);
}

beforeEach(() => {
  sources.length = contexts.length = captures.length = callbacks.length = sessions.length = 0; operations = [];
  const stream = mockStream();
  getUserMedia = vi.fn(async () => { operations.push("request mic"); return stream.stream; });
  vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
  vi.stubGlobal("AudioContext", MockAudioContext); vi.stubGlobal("AudioWorkletNode", MockWorklet);
  vi.stubGlobal("requestAnimationFrame", vi.fn(() => 1)); vi.stubGlobal("cancelAnimationFrame", vi.fn());
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ token: "MOCK_ephemeral" }) })));
  provider.connect.mockReset();
  provider.connect.mockImplementation(async (args: { callbacks: Callbacks }) => {
    callbacks.push(args.callbacks);
    const session = { close: vi.fn(), sendRealtimeInput: vi.fn(), sendClientContent: vi.fn(), sendToolResponse: vi.fn() };
    sessions.push(session); return session;
  });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("Live session/audio regressions (MOCK)", () => {
  it("resumes output before awaiting permission, starts one graph and bounds duplicate starts", async () => {
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await Promise.all([result.current.start(), result.current.start()]); });
    expect(operations).toEqual(["resume output", "request mic"]);
    expect(contexts).toHaveLength(1); expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(provider.connect).toHaveBeenCalledTimes(1); expect(result.current.state).toBe("listening");
    expect(sessions[0].sendClientContent.mock.calls[0][0].turns).toContain("PROJECT_SNAPSHOT");
  });

  it("connects real-output PCM sources to the playback gain, never directly to a mic meter", async () => {
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await result.current.start(); });
    await act(async () => emit({ data: btoa(String.fromCharCode(0, 32, 0, 224)) }));
    expect(contexts[0].createBuffer).toHaveBeenCalledWith(1, 2, 24_000);
    expect(sources[0].connect).toHaveBeenCalledWith(contexts[0].createGain.mock.results[0].value);
    expect(sources[0].start).toHaveBeenCalledOnce();
    await act(async () => emit({ serverContent: { interrupted: true } }));
    expect(sources[0].stop).toHaveBeenCalledOnce(); expect(result.current.isSpeaking).toBe(false);
  });

  it("accumulates captions even when the provider does not set finished", async () => {
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await result.current.start(); });
    await act(async () => emit({ serverContent: { outputTranscription: { text: "Hej " } } }));
    await act(async () => emit({ serverContent: { outputTranscription: { text: "välj B" } } }));
    expect(result.current.liveDirectorText).toBe("Hej välj B");
    await act(async () => emit({ serverContent: { turnComplete: true } }));
    expect(result.current.transcript.at(-1)?.text).toBe("Hej välj B");
  });

  it("microphone gate stops transmission, remains distinct from output mute and resumes", async () => {
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await result.current.start(); });
    act(() => result.current.setMicPaused(true));
    const samples = new Float32Array(2048).fill(.1).buffer;
    act(() => captures[0].port.onmessage?.({ data: samples } as MessageEvent<ArrayBuffer>));
    expect(sessions[0].sendRealtimeInput).toHaveBeenCalledExactlyOnceWith({ audioStreamEnd: true });
    expect(result.current.isMuted).toBe(false);
    act(() => result.current.setMicPaused(false));
    act(() => captures[0].port.onmessage?.({ data: samples } as MessageEvent<ArrayBuffer>));
    expect(sessions[0].sendRealtimeInput.mock.calls.at(-1)?.[0].audio.mimeType).toBe("audio/pcm;rate=16000");
  });

  it("late close from an old session cannot release a reconnected microphone/output graph", async () => {
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await result.current.start(); });
    await act(async () => { await result.current.stop(); });
    await act(async () => { await result.current.start(); });
    await act(async () => callbacks[0].onclose());
    expect(result.current.state).toBe("listening"); expect(contexts[1].close).not.toHaveBeenCalled();
    expect(sessions[1].close).not.toHaveBeenCalled();
  });

  it("denied permission and server configuration failures stay visible, not a silent idle state", async () => {
    getUserMedia.mockRejectedValueOnce(new DOMException("denied", "NotAllowedError"));
    const { result } = renderHook(() => useLiveDirector({ onToolCall: async () => ({}) }));
    await act(async () => { await result.current.start(); });
    expect(result.current.state).toBe("error"); expect(result.current.error).toContain("permission");
    vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) } as Response);
    await act(async () => { await result.current.start(); });
    expect(result.current.error).toContain("GOOGLE_API_KEY"); expect(result.current.state).toBe("error");
  });

  it("tool failure cancels dependent calls instead of falsely acknowledging an edit", async () => {
    const onToolCall = vi.fn(async () => { throw new Error("Server save failed"); });
    const { result } = renderHook(() => useLiveDirector({ onToolCall }));
    await act(async () => { await result.current.start(); });
    await act(async () => emit({ toolCall: { functionCalls: [{ id: "1", name: "select_scene" }, { id: "2", name: "edit_scene_copy" }] } }));
    await waitFor(() => expect(sessions[0].sendToolResponse).toHaveBeenCalledOnce());
    expect(onToolCall).toHaveBeenCalledTimes(1);
    expect(sessions[0].sendToolResponse.mock.calls[0][0].functionResponses[1].response.cancelled).toBe(true);
  });
});
