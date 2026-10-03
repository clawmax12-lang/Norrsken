# Gemini Director — Preflight orb and voice beam

Owner-requested presentation in [PRD v1.7](../../PRD.md) FR-16/§12.9. Use **both** packages. Standalone orb is **large/central during conversation**, **small near the bottom when inactive**, not only a 64→96 bottom pulse. Localized multicolor beam is permitted; UI/brain remains neutral/orange-red. Gemini Live is the mandatory provider. Read [the correction handoff](PRODUCT_RESET_HANDOFF.md).

## Ready-to-relay implementation prompt

> Preserve useLiveDirector, secure session, mic/audio graph, interruption, transcripts and validated tools. Use thinking-orbs@0.3.2 + voice-glow@0.2.1. Same standalone Orb with theme="dark", warm color, no panel: smoothly move/enlarge centrally (~224–280 px presentation) during actual user/assistant conversation or intentional focus, then dock small near the bottom when inactive. Use supported 64 preset with wrapper; do not invent speaking/level props. Enabled mic is not audible conversation. Post-gain output analyser drives assistant beam/pulse; input RMS is separate/labeled. Localized multicolor beam is allowed, not rainbow UI/brain. Actual lifecycle/tool work drives processing. No second mic/AudioContext, permission on mount or model on hover. Captions/privacy/mute/stop/disconnect stay reachable; interruption/mute clears stale output immediately. Respect reduced motion/background tabs. Main flow is existing-video baseline → grounded candidate edits → retest; migrate contracts with owners and never invent evidence. Verify ACTUAL ROUTE and real conversation/tools, publish fresh preview.

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
| Opening a real session | Connecting | Dock or explicit foreground focus; no fake audio |
| Mic enabled but silent | Listening | Small bottom dock; visible mic state |
| Actual user speech / intentional conversation focus | Listening | Large central wrapper; input meter is clearly labeled |
| Waiting on an actual conversational/tool response | Working | Central while engaged; processing from real work |
| Assistant audio actually playing | Composing | Large central wrapper; post-gain output analyser drives beam |
| Interrupted / muted / stopped | Actual new state | Cancel speech growth/stale output immediately |

The current inspected main at `89338e1` exposes `useLiveDirector().level` from **microphone RMS**. It does not expose assistant playback state/output analyser. Do not rename that input meter as assistant output. Voice owner must expose independent `inputLevel`, `outputLevel`, actual `isSpeaking`, `micActive`, `isThinking` and output-mute/session state from the existing audio graph. Account for scheduled playback rather than the arrival of text or audio chunks. Route PCM sources through the existing output analyser/gain; interruption/disconnect must cancel queued sources and clear output state. Do not create another microphone or AudioContext just for an effect.

The controlled example takes normalized level getters and host-supplied `conversationActive`; host derives engagement from actual speech/conversation intent, not merely an open mic. Placement/central scale are a logged presentation choice, not a neural signal. Host supplies captions/transcripts/controls/errors and binds reduced-motion/hidden-tab/manual pause; visuals do not start/stop jobs or audio. The example is still **not imported in an app**; code alone does not establish deployed acceptance.

## Acceptance

Verify visible warm-tinted orb/beam, standalone layout, actual listening versus output, speaking-growth start/end, processing from real work, immediate interruption/mute/disconnect, denied mic/error/offline, reduced motion and background-tab pause. Check keyboard controls and transcript availability. UI test fixtures may assert phases but do not establish real Gemini Live/provider acceptance. Only an actual two-way conversation, interruption and persisted storyboard/tool flow can pass FR-16.
