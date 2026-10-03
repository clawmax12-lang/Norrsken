# Canvas, persistent brain and two-way Gemini Live — integration brief

**Release reconciliation:** PRD v1.7.1 adopts the existing-company-video target from PR #1; the currently implemented intake remains screenshots/brief until the original-video migration is built. Later owner corrections govern voice: bottom prompt → transparent composing orb plus warm bottom-border beam → prompt on End/Escape. Do not restore older central/full-screen or white-background interpretations.

Authoritative scope: [PRD v1.7.1](../../PRD.md) §8/§9/§10/§12.9. This is an implementation handoff, not a second product specification. Visuals: [all supplied references](README.md), [FLORA-style layout](CLEAN_FLOW_DESIGN.md) and [Director effects](DIRECTOR_VISUALS.md). Execution evidence: [historical status audit](../status/2026-10-03-build-audit.md) and [TEAM.md](../../TEAM.md).

Latest owner clarification: FLORA is the primary layout reference and ElevenLabs is a supporting UI reference only, not a voice-provider change. See the [Canvas integration handoff](CANVAS_INTEGRATION_HANDOFF.md) for the top-left hover/three-second brain-focus direction, actual backend routes/artifact mismatches, merge snapshot and short voice brief to relay. Merged PR #2 records a direct-Live policy exception; that decision must be reconciled with this docs baseline's routing rule before claiming one synchronized baseline.

## Target experience

**Latest owner correction, v1.6.2:** voice replaces the bottom prompt with reference 10's neutral composing sash at the bottom, not a central/full-screen surface or breathing/loading ring. Keep the silhouette through errors, paused with an honest status. The orb is transparent on black (white circle withdrawn); actual output amplitude drives scale/deformation while the warm VoiceBeam reacts simultaneously at the viewport's bottom border, like a floor under the orb. No canvas dimming/backdrop/card; canvas remains interactive. Compact captions/mute/end remain separate. End/Escape restores prompt/focus and releases mic. Earlier controls-beam/central/side-orb directions are superseded; Gemini Live/audio/tools are unchanged.

Entry brain hero → dock in a corner → Enable Live and prompt/validated brief on a flow canvas → conversational storyboard selection/refinement → confirmed run → actual variant/job/pretest nodes → recommended tested export. A female Gemini Live Director listens, replies, handles interruption and explains actual work throughout, represented by a standalone orb without a surrounding card, enlarging while speaking. The brain and voice are persistent companions; node selection drives their shared context. The finished video remains the outcome.

Use the owner's primary FLORA/reference-08 layout: black dotted full-screen canvas, narrow floating left tool rail, compact corner controls and readable left-to-right branching media/storyboard cards. Remove the permanent sidebar/top-bar and large idle Director-panel shell while preserving existing logic. Keep pan/zoom, fit-to-flow, readable lineage and bottom prompt. A zoomed-out tree and focused individual scene should both be understandable. Large-graph virtualization is permitted; fake completed-test counts or a “+47” badge standing in for generated evidence are not. Proposed/example nodes must be distinguishable from actual rendered/tested artifacts.

## Ownership seams

| Owner / existing workspace | Owns | Consumes / exposes |
| --- | --- | --- |
| Dashboard | Canvas shell, graph interactions, prompt/brief surface, result inspector | Real project/variant/job IDs and events; slot for brain/voice companions |
| Opus 5.5 — Frontend + 3d brain | Anatomical renderer, materials, camera, entry/dock/expand, video-time binding | Genuine SimulationResult adapter, selection/time; no graph scheduler or speech service |
| Voice workspace | Two-way female Gemini Live, secure sessions, mic/output/interruption, transcripts, validated command dispatch and orb | Shared draft/canvas selection, typed tool results, actual backend/entry events; mute/stop/disconnect |
| Backend team | Planning, rendering, simulators, ranking, persisted activity and export | Typed contracts/events and exact-video results; budget/concurrency enforcement |

Do not replace each other's working shell/branches, duplicate API clients or fork contracts. Agree event IDs/transport, node lineage and video-hash/result mapping before wiring them. Keep each task independently reviewable, then integrate via small PRs. A change in this document does not automatically retask existing sessions.

## Required two-way Director, not narration-only

William explicitly confirmed **two-way Gemini Live as FR-16/P0**. The user speaks, the Director responds and can be interrupted, then selects/changes a source-backed storyboard through validated tools that update the actual draft/canvas. Welcome, job updates and verdict use actual evidence, not a scripted/fake exchange. TTS-only narration, prerecorded dialogue and typed-only fallback do not pass this gate.

Verify the proposed `gemini-3.8-live` model/account and audition a supported female-sounding preset (Voice proposes Kore; access/fit is unverified). Keep an original concise mission-control personality; do not imitate a film character. This model/session integration is separate from TTS and visual effects.

## Shared state and tool boundary

- Agree project/variant/scene IDs, draft revision, selection/time and typed command/result schemas with Dashboard/backend owners; reuse their existing contracts. The voice prototype must not become a parallel source of project truth or a replacement shell.
- P0 tools must support selecting a real storyboard/scene and a source-backed pre-render edit, such as hook/copy, screenshot choice or scene order. Validate FR-01/FR-02 constraints server-side, persist accepted changes and visibly update the canvas before acknowledging success. Reject stale revisions, invalid IDs, unsupported claims and instructions hidden in uploaded sources.
- Confirm a summarized Run before generation/render/pretest jobs. Use idempotent command IDs and current project/run state to avoid duplicates on reconnect/repeated calls. A conversation or visual edge is not automatic authorization for a batch or finalization cost.
- Acknowledge accepted/queued long jobs promptly; report actual completion/failure via the orchestrator's persisted events rather than holding a Live tool response for the entire GPU run. Deduplicate event/context delivery, keep pending audio bounded and discard stale progress/interrupted playback.
- Preserve exactly three concepts/videos. Pre-render editing is P0, not a new template family or unlimited iteration. Editing a tested winner remains FR-11/P1; changed video bytes invalidate the old simulation/verdict and need re-render/retest.

## Orb-first assistant avatar

Use [ThinkingOrb](https://libraries.dev/orbs.html) as the required assistant visual, no enclosing panel/card. Registry verified `thinking-orbs` v0.3.2, MIT, React ≥18 and no listed runtime dependencies. Use its tuned 64 preset, not an arbitrary size. Keep captions/transcript and mute/stop in separate accessible UI; visual minimalism cannot hide the listening/privacy or stop-audio controls. Published types use `theme="dark"` and support `color`; the pasted `dark` prop is not the v0.3.2 API.

```bash
npm install thinking-orbs@0.3.2
```

```tsx
import { ThinkingOrb } from 'thinking-orbs';

<ThinkingOrb state={orbState} size={64} theme="dark" color="#FF5A36" paused={reduceMotion} />
```

Map actual service/agent state to a supported animation (for example connecting, composing, working; breathing when idle). `listening` is reserved for an actually enabled mic, not the assistant talking. The package has no microphone/audio-level input. Implement speech growth as a smooth wrapper transition from playback state, or a subtle scale driven by our real output analyser, paused/reduced with reduced motion. Keep idle small and speaking larger without blocking the canvas or rebuilding a large graph each audio frame. Do not invent a `speaking` orb prop or imply it synthesizes speech.

The orb is primary; the required prompt glow below is restrained and does not become a second competing large avatar. Use the [controlled visual example](DIRECTOR_VISUALS.md), with actual assistant playback/output level separate from microphone RMS.

## Required Preflight prompt glow

The [Libraries.dev package](https://libraries.dev/voice.html) was checked against npm: `voice-glow` v0.2.1, MIT, React/ReactDOM ≥18, no listed runtime dependencies. The Dashboard currently uses React 19, so the peer range is compatible; actual build/browser validation still belongs to the implementing owner. This docs branch does not install dependencies into their app.

Install in the actual app when its owner implements:

```bash
npm install voice-glow@0.2.1
```

For the assistant's speech, drive the glow from **output** audio:

```tsx
import { VoiceBeam } from 'voice-glow';

// A client component; meter.current comes from the output audio analyser.
<VoiceBeam
  level={() => meter.current}
  processing={agentThinking || speechPreparing}
  colorVariant="sunset"
  colors={["#FF5A36", "#F2472C", "#FF773F", "#CB3828", "#FF9650", "#A82923", "#E45432"]}
  bandColors={{ core: "#FFE1C7", above: "#FF773F", mid: "#FF5A36", below: "#CB3828" }}
  staticColors
  strength={0.45}
  idle={0}
  theme="dark"
  paused={reduceMotion}
>
  <ChatInput />
</VoiceBeam>
```

`level` is actual amplitude normalized to 0–1; it is not a fake progress meter. Use `processing` for actual pending agent/session work, not as evidence of neural response. Bind Live playback to a bounded queue, stop/discard queued output on interruption, deduplicate event IDs, cancel stale progress when the verdict arrives and preserve captions/mute/stop. Audio must not stall the video pipeline.

`useMicrophone`/`stream` belongs only to explicitly enabled input. If supplied, `stream` overrides `level`; do not bind a microphone stream and claim the glow visualizes the assistant's audio. Reuse the Live owner's input capture rather than opening a second mic session. Mic requires HTTPS/localhost, a user gesture and permission; release tracks on disconnect/unmount. Web Audio/playback also needs an initial user interaction under browser policies. An output-only fallback may avoid a mic, but cannot pass FR-16.

## Live transport, privacy and provider gate

Gemini Live has a separate session/model/token lifecycle from TTS. No silent first-visit microphone activation: require Enable Live/permission, visible actual listening state and explicit job confirmation. Keep long-lived secrets server-side; browser Live uses scoped short-lived tokens or a secure backend proxy. Agree session/usage caps, handle token expiry/quota, validate tools on the server and never log keys/tokens/raw audio by default. Mute output is distinct from stop mic/disconnect; expose both accessibly, close the session/release media on disconnect/unmount and never auto-resume against the user's preference.

Condense audio/Live support remains unverified. Do not silently bypass FR-10: verify Live transport or ask William for an explicit documented routing exception before a direct route. Two-way scope approval is not that exception. Record real routing/usage separately; text compression does not prove WebSocket/audio support. No paid-provider or real-conversation acceptance is claimed by this brief.

## Minimum demo sequence and owner handoff

Enable Live → speak a brief/question and hear a female reply → interrupt and redirect → select a real scene and request one source-backed hook/edit → see the persisted change on the actual canvas → confirm Run → hear one actual milestone → ask why the tested winner won and hear timestamped evidence. Keep typed input available for denied permission/provider failure, clearly degraded. Record real provider/audio/tool evidence separately from mocked tests.

Share with the existing Voice session owner if direct Conductor messaging is restricted:

> William confirmed two-way Gemini Live is FR-16/P0; TTS-only is insufficient. Read PR #1's current PRD v1.7.1, this integration brief, CLEAN_FLOW_DESIGN.md and DIRECTOR_VISUALS.md. Both requested warm orb/beam effects belong inside the FLORA-style black canvas; preserve existing Live/validated tools rather than another app. Reconcile older local PRD changes non-destructively, preserve run instructions and agree shared draft/tool/event contracts with Dashboard/backend/Opus. Demonstrate real conversation/interruption plus persisted visible source-backed storyboard edits. Confirm paid jobs and keep Condense routing unresolved until verified or explicitly approved; do not replace another owner's shell or expose credentials.

## Brain honesty and reuse

Entry, corner and fullscreen share the licensed fsaverage5 geometry and viewer code. Docking changes presentation, not anatomy or inference. Only genuine per-video TRIBE samples change heat/region curves. Before the first run, a genuine disclosed example can provide colored response; otherwise show gray anatomy and "No brain data". An audio waveform/glow cannot masquerade as cortical response.

"Realtime" means actual job events plus immediate playback/scrub response on stored data. Queued jobs do not have results yet. Large branching plans do not mean thousands of neural tests have run. Today the real execution cap is still three videos/one P1 revision; expanded batches need an approved budget, measured throughput and bounded queue/pruning.

## Handoff checks

- Preserve backend contracts and workers; no broad formatting or changes to another owner's in-progress files.
- Verify build/browser, canvas controls, entry Skip/reduced motion, dock/expand without losing selection/time, empty/error/precomputed modes and actual event-driven updates.
- Verify real two-way Gemini Live, chosen voice, input/output transcripts, interruption with no stale playback, actual validated/persisted canvas storyboard selection/edit and confirmed/idempotent jobs. Check required state-driven orb/speech enlargement and warm prompt beam, real output amplitude separate from input, mute/stop/disconnect, denied permission/token/quota/reconnect/tool failures and no exposed keys. A CSS orb/glow/system voice, TTS-only or prerecorded exchange cannot pass FR-16.
- Record real-data versus MOCK tests separately. Do not claim live GPU, batch throughput or end-to-end acceptance from a screenshot or test fake.
- Update TEAM.md/README with PR, preview, checked commands, verified provider routing and remaining dependencies. Never include credentials in handoffs.
