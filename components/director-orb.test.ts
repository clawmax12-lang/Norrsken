// @vitest-environment jsdom
// MOCK canvas/output meter. Browser/provider acceptance is recorded separately.
import { createElement, type ComponentProps } from "react";
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DirectorOrb } from "./director-orb";

const engine = vi.hoisted(() => ({ resolve: vi.fn(), frame: vi.fn(), paint: vi.fn() }));
vi.mock("thinking-orbs/engine", () => ({
  resolvePreset: engine.resolve, MODE_FRAMES: { ribbon: engine.frame }, paintFrame: engine.paint,
}));
const frames = new Map<number, FrameRequestCallback>();
let nextId = 0;
function step(time: number) {
  const [id, callback] = frames.entries().next().value!;
  frames.delete(id);
  act(() => callback(time));
}
const props: ComponentProps<typeof DirectorOrb> = {
  state: "listening", paused: false, label: "Listening", speaking: false, level: () => 0,
};
beforeEach(() => {
  vi.clearAllMocks(); frames.clear(); nextId = 0;
  engine.resolve.mockReturnValue({ mode: "ribbon", speed: 2.34, opts: { wobMul: 1 } });
  engine.frame.mockReturnValue({ dots: [], lines: [] });
  vi.spyOn(document, "hidden", "get").mockReturnValue(false);
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({ setTransform: vi.fn(), clearRect: vi.fn() } as unknown as CanvasRenderingContext2D);
  vi.spyOn(HTMLCanvasElement.prototype, "clientWidth", "get").mockReturnValue(160);
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => { frames.set(++nextId, callback); return nextId; });
  vi.stubGlobal("cancelAnimationFrame", (id: number) => frames.delete(id));
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("reference orb and real-output envelope (MOCK)", () => {
  it("keeps reference 10's composing silhouette even in a disconnected/error phase", () => {
    render(createElement(DirectorOrb, { ...props, state: "breathing", paused: true, label: "Could not connect" }));
    expect(engine.resolve).toHaveBeenCalledWith("composing", 64);
    expect(engine.paint.mock.calls[0][2]).toBe(true); // light ink; no white substrate
    expect(frames.size).toBe(0);
  });
  it("uses measured output amplitude, not a constant speaking scale, and resets on interruption", () => {
    let amplitude = 0;
    const level = () => amplitude;
    const view = render(createElement(DirectorOrb, { ...props, speaking: true, level }));
    const canvas = view.container.querySelector("canvas")!;
    step(1_000);
    expect(canvas.style.getPropertyValue("--voice-amplitude-scale")).toBe("1");
    amplitude = 0.8;
    for (let index = 0; index < 12; index++) step(1_016 + index * 16);
    expect(Number(canvas.style.getPropertyValue("--voice-amplitude-scale"))).toBeGreaterThan(1.1);
    expect(engine.frame.mock.calls.at(-1)?.[2].wobMul).toBeGreaterThan(1.8);
    view.rerender(createElement(DirectorOrb, { ...props, speaking: false, level }));
    step(1_300);
    expect(canvas.style.getPropertyValue("--voice-amplitude-scale")).toBe("1");
  });
  it("disables amplitude growth and animation for reduced motion/closed presentation", () => {
    const view = render(createElement(DirectorOrb, { ...props, paused: true, speaking: true, level: () => 1 }));
    expect(view.container.querySelector("canvas")?.style.getPropertyValue("--voice-amplitude-scale")).toBe("1");
    expect(frames.size).toBe(0);
  });
  it("preserves the animation position across phase changes and pauses instead of jumping", () => {
    const view = render(createElement(DirectorOrb, props));
    step(1_000); step(1_040);
    const before = engine.frame.mock.calls.at(-1)?.[1];
    view.rerender(createElement(DirectorOrb, { ...props, state: "composing" }));
    const after = engine.frame.mock.calls.at(-1)?.[1];
    expect(after).toBeGreaterThanOrEqual(before);
    view.rerender(createElement(DirectorOrb, { ...props, state: "composing", paused: true }));
    expect(engine.frame.mock.calls.at(-1)?.[1]).toBe(after);
  });
});
