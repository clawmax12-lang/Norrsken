# FR-16: voice-first acceptance

Source: the product owner's supplied **[External] Google DeepMind x Tech_Europe Stockholm Hackathon: Brief & Builder Guide**, seven pages, read on 3 October 2026. This is an implementation/verification note, not a second product specification.

## What changes the demo

- Page 1: voice is the primary interaction. If the experience is equally good with the mic unplugged, it does not pass the voice-first test. Name a real person and their concrete problem; demonstrate something enabled by recent capabilities.
- Pages 5–6: a generic chatbot with a microphone or voice wrapper scores poorly. Prove the interaction live. Combining two recent capabilities is recommended for novelty, not stated here as a separate strict eligibility condition.
- Page 6: keep the conversation responsive while heavy work executes asynchronously. The Director acknowledges a queued job, then consumes genuine progress/results; it does not announce completed simulations from a tool request.

## Current patch boundary

The owner wants an e-commerce brand's **existing video** analyzed, improved and retested. Original-video ingestion and exact-video evidence are a separate coordinated backend/canvas migration in docs PR #1/v1.7. Until connected, expose those capabilities as unavailable. Never make the Director claim it has watched a video, found a weak timestamp, run TRIBE or proven retention/sales uplift from the current screenshot-based intake.

Improve the implemented Live path now: current project context, concise language-matched conversation, ordered/deduplicated validated tools, source-grounded edits, truthful persistence failures, explicit spoken run confirmation using the same command as the button, accumulated captions, interrupt/reconnect cleanup and a microphone gate for the noisy venue. Do not add a second mic, pretend audio fixtures pass live acceptance, or change provider routing as a side effect.

Latest visual clarification: **voice button inside the text bar**. Explicit click opens a large central orb, End/Escape returns it to the button. `ThinkingOrb` uses its supported 20 preset in the active button; the expanded orb uses the package's public engine with the tuned 64 geometry painted at native resolution. No unsupported size prop, stretched low-resolution bitmap, avatar card or permanent side orb. `VoiceBeam` remains on the real input/output graph. The Live SDK explicitly requires `v1alpha` for ephemeral-token connections; this corrects transport configuration, not the unresolved Condense routing policy.

## Live acceptance: unplug the keyboard

With a real headset in the authenticated HTTPS deployment:

1. Enable Live. The Director uses already-confirmed project facts and asks only one useful missing question.
2. Speak Swedish, correct a fact and select B's opening scene. The actual canvas and confirmed fields change; a fresh context read reports the change.
3. Request a source-grounded copy edit. Reload to verify server persistence. Force a save failure separately: neither speech nor the tool may claim it was saved.
4. Interrupt a reply mid-sentence. No queued stale audio continues; the next turn answers the interruption.
5. Request the bounded run. Hear the summary, then say an explicit confirmation. This calls the same validated function as the Run button; repeated calls do not submit another command.
6. Show a real backend milestone and evidence-backed recommendation **only once the event/result consumer is connected**. No invented score, original analysis, brain activity or progress count.
7. Disconnect/reconnect and deny permission. The old session cannot release the new session's mic/audio or apply queued edits. Mute/stop remain accessible and captions remain readable.

## Document-supported, not account-verified

The guide lists `gemini-3.8-live` (default), `gemini-3.8-live-extended-thinking`, and `gemini-3.8-flash` for background reasoning. It does not prove our deployment has access. Keep the existing default until a real test supports changing it. Recorded transcription/word timings are a separate capability, not supplied by Live captions.

Page 6 specifies mono signed-16 little-endian 16 kHz PCM input and 24 kHz output, ephemeral browser credentials, HTTPS/localhost microphone permission and noisy-room headset/push-to-talk. Audio-only Live sessions have a 15-minute limit (audio+video two minutes); bound today's sessions rather than silently promise indefinite continuity. The patch keeps real-time transport on Live API and the existing single audio graph. Live directly uses Google's ephemeral-token WebSocket; Condense compatibility/owner approval remains an unresolved FR-10 gate, not waived by this guide.
