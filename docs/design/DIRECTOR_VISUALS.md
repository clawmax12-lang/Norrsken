# Gemini Director — Preflight orb and voice beam

Owner-requested presentation in [PRD v1.6](../../PRD.md) FR-16/§12.9. **Use both Libraries.dev packages**, adapted to our minimal FLORA-style black canvas and warm orange-red identity. Gemini Live remains the mandatory two-way voice provider.

## Ready-to-relay implementation prompt

> Add thinking-orbs@0.3.2 and voice-glow@0.2.1 to our existing React app. Preserve useLiveDirector, its secure session, microphone, interruption, transcripts and validated tools. Use a standalone 64px ThinkingOrb above the bottom prompt, no card/panel; theme="dark", color="#FF5A36". Grow its wrapper smoothly to about 96px only during actual audible assistant playback. Connecting/listening/thinking states come from real lifecycle, not timers. Wrap the prompt with a restrained warm VoiceBeam; customize orange-red lobe/band colors and freeze hue drift. Output beam uses actual assistant-output amplitude; user-input amplitude may react only in explicitly labeled listening mode. Do not call a second useMicrophone or request permission on mount. Keep captions, visible mic state, Enable Live, output mute and stop/disconnect separately accessible. Stop speech growth/output beam immediately on interruption, mute and disconnect. Respect reduced motion/background tabs. Preserve shared Canvas selection/draft/job state and confirmed bounded jobs. Verify real audio binding and publish an updated preview; an animation does not prove Live conversation works.

## Install and exact API

In the application owner's branch, using its existing package manager:

```bash
npm install thinking-orbs@0.3.2 voice-glow@0.2.1
```

Registry and published type definitions checked on 3 Oct 2026. Both packages are MIT and require React ≥18; voice-glow also requires ReactDOM ≥18. No listed runtime dependencies. Preserve lockfile changes in the actual app, not a parallel package manifest in this docs branch.

The copied usage is slightly behind the published Orb API: **v0.3.2 uses `theme="dark"`, not `dark`**, and supports `color` tint. Use actual exported `OrbState`; `speaking` is not a library animation state. Use `composing` with our own speaking-growth wrapper. The 64 and 20 presets are hand-tuned; our larger visual is a modest wrapper scale, not an invented `size={96}`. The beam accepts custom `colors`, `bandColors` and `staticColors`.

The [controlled React example](examples/DirectorPresence.tsx) and [theme CSS](preflight-theme.css) implement this presentation seam. They are not imported by an application on this docs branch and contain no speech API, microphone acquisition, model calls or job scheduler. The owner must bind real state, add the packages, import the CSS/apply `.preflight-theme`, and verify the integrated browser behavior.

## Real-state mapping

| Actual state | Orb | Size / beam |
| --- | --- | --- |
| Disconnected / error | Paused breathing + written status | 64px, beam off |
| Opening a real session | Connecting | 64px; no fake audio |
| Mic permission granted and actively listening | Listening | 64px; existing input meter can drive labeled input beam |
| Waiting on an actual agent/tool response | Working | 64px; processing beam |
| Assistant audio actually playing | Composing | Smooth 64→96px wrapper; output analyser drives beam |
| Interrupted / muted / stopped | Actual new state | Cancel speech growth/stale output immediately |

The current inspected main at `89338e1` exposes `useLiveDirector().level` from **microphone RMS**. It does not expose assistant playback state/output analyser. Do not rename that input meter as assistant output. Voice owner must expose independent `inputLevel`, `outputLevel`, actual `isSpeaking`, `micActive`, `isThinking` and output-mute/session state from the existing audio graph. Account for scheduled playback rather than the arrival of text or audio chunks. Route PCM sources through the existing output analyser/gain; interruption/disconnect must cancel queued sources and clear output state. Do not create another microphone or AudioContext just for an effect.

The example takes normalized level getters so audio does not rerender the whole canvas every frame. Supply real 0–1 RMS/envelope measurements; silence is zero, not a random animation. It displays generic phase status; host keeps real captions/transcripts, controls and errors outside the visual. Host must bind `paused` to reduced-motion, hidden-tab and manual visual-pause state using the existing lifecycle; it freezes presentation, not jobs or audio.

## Acceptance

Verify visible warm-tinted orb/beam, standalone layout, actual listening versus output, speaking-growth start/end, processing from real work, immediate interruption/mute/disconnect, denied mic/error/offline, reduced motion and background-tab pause. Check keyboard controls and transcript availability. UI test fixtures may assert phases but do not establish real Gemini Live/provider acceptance. Only an actual two-way conversation, interruption and persisted storyboard/tool flow can pass FR-16.
