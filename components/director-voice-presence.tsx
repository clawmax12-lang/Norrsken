"use client";

import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";
import { DirectorOrb } from "@/components/director-orb";

import type { useLiveDirector } from "@/hooks/use-live-director";
import { directorOrbState } from "@/lib/director-presence";

type Director = Pick<ReturnType<typeof useLiveDirector>,
  "state" | "error" | "isSpeaking" | "isProcessing" | "isMuted" | "isMicPaused" |
  "liveDirectorText" | "liveUserText" | "toggleMute" | "setMicPaused">;

export function VoiceIcon() {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 10v4m4-7v10m4-13v16m4-13v10m4-7v4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg>;
}

export function DirectorVoicePresence({ open, director, paused, anchorRef, onClose, onRetry, onTranscript }: {
  open: boolean; director: Director; paused: boolean;
  anchorRef: RefObject<HTMLButtonElement | null>;
  onClose: () => void; onRetry: () => void; onTranscript: () => void;
}) {
  const [pushToTalk, setPushToTalk] = useState(false);
  const presenceRef = useRef<HTMLDivElement>(null);
  const orbRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const place = () => {
      const anchor = anchorRef.current?.getBoundingClientRect();
      const presence = presenceRef.current?.getBoundingClientRect();
      const orb = orbRef.current;
      if (!anchor || !presence || !orb) return;
      orb.style.setProperty("--voice-origin-x", `${anchor.x + anchor.width / 2 - presence.x - orb.offsetLeft - orb.offsetWidth / 2}px`);
      orb.style.setProperty("--voice-origin-y", `${anchor.y + anchor.height / 2 - presence.y - orb.offsetTop - orb.offsetHeight / 2}px`);
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [anchorRef, open, director.error, director.liveDirectorText, director.liveUserText, pushToTalk]);
  useEffect(() => {
    if (!open) return;
    const escape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [onClose, open]);

  const connected = director.state === "listening";
  const label = director.isSpeaking ? "Director speaking" : director.isProcessing ? "Working on your canvas"
    : connected ? director.isMicPaused ? "Microphone paused" : "Listening"
    : director.state === "requesting" ? "Allow microphone access" : director.state === "connecting" ? "Connecting to Gemini Live"
    : director.state === "error" ? "Could not connect" : "Conversation ended";
  const orbState = director.isMicPaused && !director.isSpeaking && !director.isProcessing ? "breathing"
    : directorOrbState(director.state, director.isSpeaking, director.isProcessing);
  const caption = director.liveDirectorText || director.liveUserText;

  return <section id="director-voice-mode" className={`voice-session ${open ? "is-open" : ""}`} aria-label="Live voice conversation" aria-hidden={!open} inert={!open}>
    <div className="voice-presence" ref={presenceRef}>
      <div className="voice-orb" ref={orbRef} data-speaking={director.isSpeaking}>
        <DirectorOrb state={orbState} label={label} paused={paused || !open || director.state === "idle" || director.state === "error"} />
      </div>
      <div className="voice-status" role="status">{label}{director.isMuted && <span> · speaker muted</span>}</div>
      {caption && <button className="voice-caption" onClick={onTranscript}>{caption}</button>}
      {director.error && <p className="voice-error" role={open ? "alert" : undefined}>{director.error}</p>}
      <div className="voice-actions">
        {connected && <>
          <button aria-label={director.isMuted ? "Unmute Director" : "Mute Director"} aria-pressed={director.isMuted} onClick={director.toggleMute} title={director.isMuted ? "Unmute speaker" : "Mute speaker"}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />{director.isMuted ? <path d="m16 9 5 6m0-6-5 6" stroke="currentColor" strokeWidth="1.5" /> : <path d="M15 8c3 2 3 6 0 8m3-11c5 4 5 10 0 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />}</svg>
          </button>
          <button aria-label={pushToTalk ? "Use open microphone" : "Use push-to-talk"} aria-pressed={pushToTalk} onClick={() => { setPushToTalk(!pushToTalk); director.setMicPaused(!pushToTalk); }} title={pushToTalk ? "Use open microphone" : "Use push-to-talk in a noisy room"}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3ZM6 11v1a6 6 0 0 0 12 0v-1M12 18v3m-4 0h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />{director.isMicPaused && <path d="m4 4 16 16" stroke="currentColor" strokeWidth="1.5" />}</svg>
          </button>
        </>}
        {!connected && (director.state === "error" || director.state === "idle") && <button className="voice-retry" onClick={onRetry}>Try again</button>}
        <button className="voice-close" onClick={onClose} aria-label="End voice conversation" title="End conversation · Esc"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg></button>
      </div>
      {connected && pushToTalk && <button className="voice-hold"
        onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); director.setMicPaused(false); }}
        onPointerUp={() => director.setMicPaused(true)} onPointerCancel={() => director.setMicPaused(true)}
        onKeyDown={(event) => { if (event.key === " " || event.key === "Enter") { event.preventDefault(); director.setMicPaused(false); } }}
        onKeyUp={(event) => { if (event.key === " " || event.key === "Enter") director.setMicPaused(true); }}
        onBlur={() => director.setMicPaused(true)}>Hold to talk</button>}
      <small className="voice-privacy">{connected ? pushToTalk ? "Microphone sends only while you hold to talk." : "Microphone stays on until you pause or end the conversation." : "Voice starts only with your permission."}</small>
    </div>
  </section>;
}
