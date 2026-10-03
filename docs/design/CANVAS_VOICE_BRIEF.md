# Canvas, persistent brain and female voice — integration brief

Authoritative scope: [PRD v1.4](../../PRD.md) §8/§9.2/§12. This is an implementation handoff, not a second product specification. Visuals: [all supplied references](README.md). Execution evidence: [status audit](../status/2026-10-03-build-audit.md) and [TEAM.md](../../TEAM.md).

## Target experience

Entry brain hero → dock in a corner → prompt/validated brief on a flow canvas → connected storyboard/variant/job nodes → actual pretest evidence → recommended tested export. A female Gemini voice narrates actual work throughout, represented by a standalone orb without a surrounding card, enlarging while speaking. The brain and voice are persistent companions; node selection drives their context. The finished video remains the outcome.

Keep the dark sidebar/top bar, pan/zoom, fit-to-flow, readable lineage and bottom prompt. A zoomed-out tree and focused individual scene should both be understandable. Large-graph virtualization is permitted; fake completed-test counts or a “+47” badge standing in for generated evidence are not. Proposed/example nodes must be distinguishable from actual rendered/tested artifacts.

## Ownership seams

| Owner / existing workspace | Owns | Consumes / exposes |
| --- | --- | --- |
| Dashboard | Canvas shell, graph interactions, prompt/brief surface, result inspector | Real project/variant/job IDs and events; slot for brain/voice companions |
| Opus 5.5 — Frontend + 3d brain | Anatomical renderer, materials, camera, entry/dock/expand, video-time binding | Genuine SimulationResult adapter, selection/time; no graph scheduler or speech service |
| Voice workspace | Female Gemini TTS, event-grounded narration, captions, audio queue and glow | Actual backend/entry events; mute/stop; optional later Live intake |
| Backend team | Planning, rendering, simulators, ranking, persisted activity and export | Typed contracts/events and exact-video results; budget/concurrency enforcement |

Do not replace each other's working shell/branches, duplicate API clients or fork contracts. Agree event IDs/transport, node lineage and video-hash/result mapping before wiring them. Keep each task independently reviewable, then integrate via small PRs. A change in this document does not automatically retask existing sessions.

## Required voice output, not merely an animated microphone

The owner explicitly requires a female Gemini voice for today's demo: **FR-16/P0**. Start with actual `gemini-3.8-flash-tts` speech after key/model/Condense-route verification. Audition a supported female-sounding preset. Speech text is grounded in real entry/job/verdict state, concise and cinematic; do not imitate a film character or claim an uncompleted result.

## Orb-first assistant avatar

Use [ThinkingOrb](https://libraries.dev/orbs.html) as the preferred assistant visual, no enclosing panel/card. Registry verified `thinking-orbs` v0.3.2, MIT, React ≥18 and no listed runtime dependencies. Supported presets are 64 and 20, not arbitrary sizes. Keep captions/transcript and mute/stop in separate accessible UI; visual minimalism cannot hide the listening/privacy or stop-audio controls.

```bash
npm install thinking-orbs@0.3.2
```

```tsx
import { ThinkingOrb } from 'thinking-orbs';

<ThinkingOrb state={orbState} size={64} dark paused={reduceMotion} />
```

Map actual service/agent state to a supported animation (for example connecting, composing, working; breathing when idle). `listening` is reserved for an actually enabled mic, not the assistant talking. The package has no microphone/audio-level input. Implement speech growth as a smooth wrapper transition from playback state, or a subtle scale driven by our real output analyser, paused/reduced with reduced motion. Keep idle small and speaking larger without blocking the canvas or rebuilding a large graph each audio frame. Do not invent a `speaking` orb prop or imply it synthesizes speech.

The orb is primary; the optional prompt glow below should not become a second competing large avatar.

## Optional prompt glow

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
  theme="dark"
  paused={reduceMotion}
>
  <ChatInput />
</VoiceBeam>
```

`level` is actual amplitude normalized to 0–1; it is not a fake progress meter. Use `processing` for a pending job/TTS request, not as evidence of neural response. Bind synthesis/playback through a bounded queue, deduplicate event IDs, cancel stale progress when the verdict arrives and preserve captions/mute/stop. Audio must not stall the video pipeline.

`useMicrophone`/`stream` belongs only to explicitly enabled input. If supplied, `stream` overrides `level`; do not bind a microphone stream and claim the glow visualizes the assistant's audio. Mic mode requires HTTPS/localhost, a user gesture and permission; release tracks on stop/unmount. Web Audio/playback also needs an initial user interaction under browser policies. An output-only TTS demo does not need a microphone.

## Optional Live intake is a separate integration

The Voice workspace is exploring conversational brief intake. Gemini Live has a separate WebSocket/model/token lifecycle from TTS. No silent first-visit microphone activation is possible; require the initial permission interaction, visible listening state and explicit confirmation to start expensive jobs. Use server-held secrets and scoped ephemeral tokens if connecting a browser directly.

Condense audio/Live support remains unverified. Do not silently bypass FR-10: verify transport or ask the product owner for a documented exception. Deliver mandatory event-grounded TTS first; full-duplex voice intake is P1, not necessary for FR-16 acceptance.

## Brain honesty and reuse

Entry, corner and fullscreen share the licensed fsaverage5 geometry and viewer code. Docking changes presentation, not anatomy or inference. Only genuine per-video TRIBE samples change heat/region curves. Before the first run, a genuine disclosed example can provide colored response; otherwise show gray anatomy and "No brain data". An audio waveform/glow cannot masquerade as cortical response.

"Realtime" means actual job events plus immediate playback/scrub response on stored data. Queued jobs do not have results yet. Large branching plans do not mean thousands of neural tests have run. Today the real execution cap is still three videos/one P1 revision; expanded batches need an approved budget, measured throughput and bounded queue/pruning.

## Handoff checks

- Preserve backend contracts and workers; no broad formatting or changes to another owner's in-progress files.
- Verify build/browser, canvas controls, entry Skip/reduced motion, dock/expand without losing selection/time, empty/error/precomputed modes and actual event-driven updates.
- Verify real Gemini audio, chosen voice, matched captions, state-driven orb/speech enlargement, optional output-amplitude glow, mute/stop, provider failure and no exposed keys. A CSS orb/glow/system speech cannot satisfy real Gemini speech acceptance.
- Record real-data versus MOCK tests separately. Do not claim live GPU, batch throughput or end-to-end acceptance from a screenshot or test fake.
- Update TEAM.md/README with PR, preview, checked commands, verified provider routing and remaining dependencies. Never include credentials in handoffs.
