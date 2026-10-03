// @vitest-environment jsdom
// MOCK presentation state: not real Gemini Live/provider acceptance.
import { createElement, type ComponentProps } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DirectorVoicePresence } from "./director-voice-presence";

const visual = vi.hoisted(() => ({ orb: vi.fn(), beam: vi.fn() }));
vi.mock("@/components/director-orb", () => ({
  DirectorOrb: (props: { label: string }) => { visual.orb(props); return createElement("div", { role: "img", "aria-label": props.label }); },
}));
vi.mock("voice-glow", () => ({ VoiceBeam: (props: { children: React.ReactNode }) => { visual.beam(props); return props.children; } }));

type Props = ComponentProps<typeof DirectorVoicePresence>;
function fixture(): Props {
  return {
    open: true, paused: false, anchorRef: { current: null },
    onClose: vi.fn(), onRetry: vi.fn(), onTranscript: vi.fn(),
    director: {
      state: "listening", error: "", isSpeaking: false, isProcessing: false,
      isMuted: false, isMicPaused: false, liveDirectorText: "", liveUserText: "",
      toggleMute: vi.fn(), setMicPaused: vi.fn(),
      inputLevel: 0, outputLevel: 0,
    },
  };
}
afterEach(cleanup);
beforeEach(() => vi.clearAllMocks());

describe("Director voice presentation (MOCK)", () => {
  it("hides and disables the closed surface and makes Escape call the session teardown", () => {
    const props = fixture();
    const view = render(createElement(DirectorVoicePresence, props));
    fireEvent.keyDown(window, { key: "Escape" });
    expect(props.onClose).toHaveBeenCalledOnce();
    view.rerender(createElement(DirectorVoicePresence, { ...props, open: false }));
    const surface = view.container.querySelector("#director-voice-mode");
    expect(surface?.getAttribute("aria-hidden")).toBe("true");
    expect(surface?.hasAttribute("inert")).toBe(true);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(props.onClose).toHaveBeenCalledOnce();
  });

  it("keeps push-to-talk gated when reopening a session and releases it only during the hold", () => {
    const props = fixture();
    const view = render(createElement(DirectorVoicePresence, props));
    fireEvent.click(screen.getByRole("button", { name: "Use push-to-talk" }));
    const gate = vi.mocked(props.director.setMicPaused);
    gate.mockClear();
    view.rerender(createElement(DirectorVoicePresence, { ...props, open: false, director: { ...props.director, state: "idle" } }));
    view.rerender(createElement(DirectorVoicePresence, { ...props, open: true, director: { ...props.director, state: "connecting" } }));
    expect(gate).not.toHaveBeenCalled();
    view.rerender(createElement(DirectorVoicePresence, props));
    expect(gate).toHaveBeenCalledWith(true);
    const hold = screen.getByRole("button", { name: "Hold to talk" });
    fireEvent.keyDown(hold, { key: " " });
    expect(gate).toHaveBeenLastCalledWith(false);
    fireEvent.keyUp(hold, { key: " " });
    expect(gate).toHaveBeenLastCalledWith(true);
    fireEvent.blur(hold);
    expect(gate).toHaveBeenLastCalledWith(true);
  });

  it("uses actual playback for speech growth, not streaming captions, and keeps mute separate", () => {
    const props = fixture();
    const view = render(createElement(DirectorVoicePresence, { ...props, director: { ...props.director, liveDirectorText: "Caption before playback" } }));
    expect(view.container.querySelector(".voice-orb")?.getAttribute("data-speaking")).toBe("false");
    view.rerender(createElement(DirectorVoicePresence, { ...props, director: { ...props.director, isSpeaking: true } }));
    expect(view.container.querySelector(".voice-orb")?.getAttribute("data-speaking")).toBe("true");
    screen.getByRole("img", { name: "Director speaking" });
    fireEvent.click(screen.getByRole("button", { name: "Mute Director" }));
    expect(props.director.toggleMute).toHaveBeenCalledOnce();
    expect(props.director.setMicPaused).not.toHaveBeenCalled();
    view.rerender(createElement(DirectorVoicePresence, props));
    expect(view.container.querySelector(".voice-orb")?.getAttribute("data-speaking")).toBe("false");
  });

  it("shares actual output with the orb/floor beam, keeps mic separate and never creates a stream", () => {
    const props = fixture();
    const director = { ...props.director, isSpeaking: true, outputLevel: 0.4, inputLevel: 0.9 };
    const view = render(createElement(DirectorVoicePresence, { ...props, director }));
    expect(visual.orb.mock.calls.at(-1)?.[0].level()).toBe(0.4);
    const beam = visual.beam.mock.calls.at(-1)?.[0];
    expect(beam.level()).toBe(0.4); expect(beam.type).toBe("mobile"); expect(beam.stream).toBeUndefined();
    expect(view.container.querySelector(".voice-floor")?.getAttribute("aria-hidden")).toBe("true");
    view.rerender(createElement(DirectorVoicePresence, { ...props, director: { ...director, isSpeaking: false } }));
    expect(visual.orb.mock.calls.at(-1)?.[0].speaking).toBe(false);
    expect(visual.orb.mock.calls.at(-1)?.[0].level()).toBe(0.4); // orb gates this by actual playback
    expect(visual.beam.mock.calls.at(-1)?.[0].level()).toBe(0.9); // labeled listening input
    view.rerender(createElement(DirectorVoicePresence, { ...props, director: { ...director, isMuted: true, isMicPaused: true } }));
    expect(visual.orb.mock.calls.at(-1)?.[0].speaking).toBe(false);
    expect(visual.beam.mock.calls.at(-1)?.[0].level()).toBe(0);
    expect(visual.beam.mock.calls.at(-1)?.[0].active).toBe(false);
    expect(view.container.querySelector(".voice-floor")?.getAttribute("data-audio-active")).toBe("false");
  });
});
