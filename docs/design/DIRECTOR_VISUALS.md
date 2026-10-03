# Gemini Director — Preflight orb and voice beam

**Release reconciliation:** PRD v1.7.1 adopts the existing-company-video target from PR #1; the currently implemented intake remains screenshots/brief until the original-video migration is built. Later owner corrections govern voice: bottom prompt → transparent composing orb plus warm bottom-border beam → prompt on End/Escape. Do not restore older central/full-screen or white-background interpretations.

Owner-requested presentation in [PRD v1.7.1](../../PRD.md) FR-16/§12.9. **Use both Libraries.dev packages**, adapted to our minimal FLORA-style black canvas and warm orange-red identity. Gemini Live remains the mandatory two-way voice provider.

**Latest owner correction, 3 October:** clicking the voice button **inside the bottom text bar replaces the prompt with a fairly large orb at the bottom**. Reference 10 is the library's **composing sash**, not its breathing ring. Preserve that silhouette in every phase, with status/cadence from the actual session and a paused disconnected/error frame. Render the tuned 64 geometry at native 160 px resolution (136 px on short viewports). Real post-gain assistant amplitude drives scale and wave deformation; silence, mute and interruption reset speech growth. `VoiceBeam` sits at the **viewport's bottom border, like a floor under the orb**, driven simultaneously from the existing audio graph. The owner withdrew the white-circle request: transparent orb on black. No central/full-screen view, dimming, backdrop or card; canvas stays usable. End/Escape restores prompt/focus and releases mic. This supersedes v1.6.1's controls-beam and earlier central/side-orb directions. See [voice-first acceptance](../VOICE_FIRST_ACCEPTANCE.md).

## Ready-to-relay implementation prompt

> Preserve useLiveDirector, secure sessions, the single microphone/audio graph, interruption, transcripts and validated tools. Use thinking-orbs@0.3.2 and voice-glow@0.2.1. Voice starts inside the bottom prompt and replaces it with reference 10's fairly large neutral composing sash, transparent on black. Do not use a breathing/loading ring, white substrate, central/full-screen surface or dimmed canvas. Render the tuned 64 composing geometry at native 160 px (136 on short viewports); phase changes cadence and truthful status, not avatar identity. Bind scale and wobMul to a smooth actual post-gain output envelope, gated by audible playback; reset immediately on interruption/mute/disconnect and freeze under reduced motion. Place the warm VoiceBeam at the viewport's bottom border, like light rising from the floor under the orb, not around controls. Both effects react simultaneously to the same playback; explicit listening input stays distinct. Keep compact captions/mute/end/privacy and usable canvas. End/Escape releases mic and restores prompt/focus. No extra microphone/provider or fake audio/neural response. Verify bottom-border geometry, actual amplitude variation, silence/interruption/mute, error orb, reduced motion and prompt restoration; MOCK tests are not real Gemini Live acceptance.

## Install and exact API

In the application owner's branch, using its existing package manager:

```bash
npm install thinking-orbs@0.3.2 voice-glow@0.2.1
```

Registry and published type definitions checked on 3 Oct 2026. Both packages are MIT and require React ≥18; voice-glow also requires ReactDOM ≥18. No listed runtime dependencies. Preserve lockfile changes in the actual app, not a parallel package manifest in this docs branch.

The copied usage is slightly behind the published Orb API: **v0.3.2 uses `theme="dark"`, not `dark`**, and supports optional `color` tint. Our bottom orb keeps the default neutral dark-theme colors. Use actual exported `OrbState`; `speaking` is not a library animation state. Use `composing` with our own speaking-growth wrapper. The 64 and 20 presets are hand-tuned; the larger native-resolution dock uses the public engine's 64 geometry, not an invented `size={160}`. The beam accepts custom `colors`, `bandColors` and `staticColors`.

The older [controlled React example](examples/DirectorPresence.tsx) and [theme CSS](preflight-theme.css) illustrate the audio-state seam, not the corrected bottom-replaces-prompt layout. The current implementation is [DirectorVoicePresence](../../components/director-voice-presence.tsx), [DirectorOrb](../../components/director-orb.tsx) and [voice CSS](../../app/voice.css). These presentation components contain no microphone acquisition, provider calls or job scheduler; the host supplies the existing real state/audio controls.

## Real-state mapping

| Actual state | Orb | Size / beam |
| --- | --- | --- |
| Disconnected / error | Paused composing silhouette + written status | Bottom orb when open; floor beam off |
| Opening a real session | Same composing silhouette, connecting status | Native 160px; no fake audio |
| Mic permission granted and actively listening | Same silhouette, listening status | Input can drive labeled listening floor beam, not orb speech growth |
| Waiting on an actual agent/tool response | Same silhouette, working cadence/status | Native 160px; real processing floor beam |
| Assistant audio actually playing | Same composing silhouette | Actual output envelope drives scale/deformation and floor beam |
| Interrupted / muted / stopped | Actual new state/status | Cancel speech growth/stale output immediately |

The current inspected main at `89338e1` exposes `useLiveDirector().level` from **microphone RMS**. It does not expose assistant playback state/output analyser. Do not rename that input meter as assistant output. Voice owner must expose independent `inputLevel`, `outputLevel`, actual `isSpeaking`, `micActive`, `isThinking` and output-mute/session state from the existing audio graph. Account for scheduled playback rather than the arrival of text or audio chunks. Route PCM sources through the existing output analyser/gain; interruption/disconnect must cancel queued sources and clear output state. Do not create another microphone or AudioContext just for an effect.

The example takes normalized level getters so audio does not rerender the whole canvas every frame. Supply real 0–1 RMS/envelope measurements; silence is zero, not a random animation. It displays generic phase status; host keeps real captions/transcripts, controls and errors outside the visual. Host must bind `paused` to reduced-motion, hidden-tab and manual visual-pause state using the existing lifecycle; it freezes presentation, not jobs or audio.

## Acceptance

Verify a neutral orb with restrained warm beam at the bottom, hidden/inert prompt during voice, no dimming/backdrop and a still-interactive canvas. Check prompt/focus restoration, actual listening versus output, speaking-growth start/end, processing from real work, immediate interruption/mute/disconnect, denied mic/error/offline, reduced motion and background-tab pause. Check keyboard controls and transcript availability. UI test fixtures may assert phases but do not establish real Gemini Live/provider acceptance. Only an actual two-way conversation, interruption and persisted storyboard/tool flow can pass FR-16.
