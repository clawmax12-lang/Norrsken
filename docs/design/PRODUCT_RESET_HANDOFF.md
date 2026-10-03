# Preflight — existing-video product and live UI correction

Owner-approved direction, 3 Oct 2026. [PRD v1.7](../../PRD.md) is authoritative. This handoff is implementation work to do, not deployed acceptance. Read [TEAM.md](../../TEAM.md) and preserve teammate ownership.

## The product, unambiguously

A company/e-commerce brand uploads its **existing video**. We pretest the original, analyze its image/audio/text/timing alongside genuine TRIBE predictions, turn specific observations into grounded edit hypotheses, create candidate cuts, retest those exact videos and deliver a recommended cut with an original comparison.

Screenshots are optional supporting assets, **not the primary intake**. The old “generate a launch video from 3–6 screenshots” decision and exclusion of existing-video editing are superseded. Three generated candidates, one template family and the 15-second candidate-export target remain today's bounded scope, with one original baseline. An additional winner revision and synchronized dual-brain/difference view remain P1. No unlimited batches.

TRIBE predicts cortical/fMRI response, not measured EEG frequencies or proven consumer psychology/buying intent. Creative improvement is a hypothesis; show the actual comparison under a documented objective and report no improvement when appropriate. Do not promise a “best video” in the real world from higher activation. Real audience retention/conversion validation remains necessary.

## The actual required experience

1. **Entry:** seamless full-viewport cinematic anatomical brain. Deliberate orbit/region shots, sculptural material/light and minimal text. No scroll animation, raw viewer card, old Run/composer overlay or page scroll. Hide/inert host controls. Skip must work before mesh loading and if WebGL fails. Reduced motion uses static framing/fades.
2. **Handover:** the **same renderer**, not a second generated asset, moves smoothly top-left and rotates quietly. Hover/keyboard pin reveals detail. Real backend milestones can trigger roughly three seconds of slower camera/text, then resume. Manual pause/reduced motion wins; camera motion never alters video/sample time.
3. **Canvas:** [FLORA/reference 08](README.md#reference-08--flora-primary-product-layout), black dots, open space, minimal floating tools, supplied Redaction and orange-red accents. Empty state invites a video upload. Then playable Original → actual baseline analysis → A/B/C edit/storyboard/video/retest lanes → comparison/recommendation/export. No wall of empty scenes before a source exists.
4. **Voice:** female two-way Gemini Live, real conversation/interruption/tools, **same standalone ThinkingOrb large/central during engaged conversation, small near the bottom when inactive**. Both requested Libraries.dev packages are required. Localized multicolor VoiceBeam can react to real speech; no rainbow UI/brain. Captions, mic/privacy, mute, stop/disconnect stay reachable separately.
5. **Activity:** warm red/orange cortical response comes only from genuine exact-video TRIBE data. A colored intro needs a genuine matched disclosed example, not a looping reference video or fabricated waves. Gray “No brain data” / “Brain sim off” is honest until data exists. Audio and job progress never become cortical response.

## Concrete browser findings, not another moodboard

At 1440×1000, using real routes in isolated checkouts and a fresh Chrome context:

| Surface | Verified observation | Required correction |
| --- | --- | --- |
| Brain branch `8e02f13`, actual `/` | Entry brain stage is full viewport, but old Director Run dock overlays it; document height is 1411 px. After entry the 196×148 top-left brain sits over lime/panel-heavy DirectorStudio. | Brain owns entry isolation/scroll/Skip/materials; Canvas owner replaces the old host. A passing injected FLORA fixture does not fix the root. |
| PR #6 `c548786`, local root and public preview | Black dotted card flow, no page scroll; real brain absent, only placeholder. Empty scene cards shown before input. Small ~55 px orb near bottom-left of composer, not a central conversation presence. | Embed brain once outside pan/zoom; clean empty state, central↔bottom orb, migrate video intake/lineage. |
| PR #6 audio at `c548786` | Output level/isSpeaking are set at PCM arrival before scheduled playback. | Use post-gain playback analyser and actual playback window; immediately cancel/clear on interruption/mute/disconnect. Later Voice transcript reports a correction; verify the pushed replacement separately. |
| Public canvas preview | HTTP 200; UI/brief inspector exercised. No proof of configured Live, render, GPU simulation or baseline upload. | Real provider and end-to-end acceptance still required. |
| New PR #6 `fa27aea`, actual local root | Brain and Redaction are now integrated; 46 tests, lint/typecheck pass. **Actual pointer click on Skip fails**: top-right host Run intercepts pointer events. Orb remains bottom-only (64→96), input still screenshots. | Fix entry stacking/inertness in brain + host. Implement central conversation presence/video-first migration; automated unit success is not browser acceptance. |

Further browser checks on `fa27aea`: ordinary reload correctly stays docked; explicit replay reopens entry. Canvas has no page scroll, but floating header/tool/composer controls remain over the brain, and Skip is genuinely blocked. Missing initial draft produces `/api/projects/launch-draft/draft` 404 responses. Enable Live reports `Requested device not found` on this headless machine; no real microphone conversation or provider acceptance can be claimed. No billable jobs were confirmed.

The team subsequently merged PR #6 to main `a36670f`; the reviewer did not merge it. The findings above apply to its inspected head `fa27aea`. Source integration is not video-first/Live/TRIBE acceptance. Brain PR #3 and docs PR #1 need non-destructive reconciliation with current main; keep actual run instructions.

Protected brain preview `https://norrsken-w11.conductor.show/` returns HTTP 401 without login. We did not bypass authentication; the exact pushed source was run locally. The older public canvas tested was `https://temporary-agile-redwood-3fj586n.vercel.app/`, a temporary deployment, not a stable production link. Browser screenshots/results are saved in the reviewer's `.context/`; these are diagnostic evidence, not design-baseline images or scientific data.

## Ready-to-relay prompt for the Canvas / Voice owner

> Read PRD v1.7 and docs/design/PRODUCT_RESET_HANDOFF.md, CLEAN_FLOW_DESIGN.md, DIRECTOR_VISUALS.md. William clarified the product: company uploads an EXISTING VIDEO → baseline pretest/analysis → three grounded edit hypotheses → new cuts → exact-output retests → recommendation with original comparison. Screenshots-first is superseded. Preserve useLiveDirector, secure tokens, interruption, transcripts, validation, persisted revisions and confirmed/idempotent jobs; do not build a second app. Coordinate source-video upload/artifact/clip/time contracts with Backend before migrating intake/tools. Do not map Original to A or reuse its predictions for changed bytes.
>
> Actual UI: FLORA black dotted canvas, Redaction, minimal floating chrome, quiet empty video-upload state. Mount one Opus CanvasBrain/BrainCompanion OUTSIDE the transformed flow plane. Seamless fullscreen entry hides/inerts host UI and locks scroll; Skip/loading/error/reduced motion all work; same brain docks top-left. Use thinking-orbs@0.3.2 (theme="dark", supported 64 preset with wrapper, no invented speaking/level prop) and voice-glow@0.2.1. SAME orb moves/enlarges to the CENTER during actual user/assistant conversation or intentional focus, then shrinks/docks near BOTTOM when inactive, no surrounding card. Enabled mic alone is not engagement. Keep mic/privacy/captions/mute/stop/disconnect reachable. Beam may be localized multicolor, not rainbow panels. Output is measured AFTER gain during real scheduled playback, not PCM arrival or mic RMS. Processing reflects real pending tools/session work. No second mic/AudioContext; no permission on mount. Interruption/mute/disconnect cancels queued output/visual speech immediately.
>
> Verify the ACTUAL ROOT, not browser-injected layout: fresh entry→dock→canvas, ordinary reload versus replay, Skip before assets, WebGL failure, reduced motion, keyboard/pan/zoom/fit, video intake and source/output timeline mapping, real two-way reply/interruption, validated persisted visible edit, confirmed Run and real shared events. Orange/red neural animation requires genuine exact-video TRIBE data or disclosed matched intro example; no random waves. No guaranteed retention/purchases. Publish a fresh preview and distinguish tests/screenshots from real Live/GPU/end-to-end evidence. Coordinate overlaps; do not auto-merge another PR.

The controlled [DirectorPresence example](examples/DirectorPresence.tsx) now exposes `conversationActive` and a localized multicolor/warm palette; its [CSS](preflight-theme.css) demonstrates center/bottom positioning. These are owned handoff assets, **not integrated app code**. Port the seam into the real owner branch using actual lifecycle/audio state and verify crispness of the larger 64-preset wrapper.

## Backend and brain seams that must actually change

- Existing intake requires 3–6 screenshots; renderer concepts use screenshot paths; original/source-clip support is not proved by accepting `.mp4` in a file picker. Validate media server-side, persist canonical artifact/hash/duration and provide playable source storage.
- Plan after real baseline analysis (or honestly labeled Gemini-only fallback). Keep original input times distinct from candidate output times; edits/cropping/audio changes require new artifacts and new tests.
- Extend shared contracts/versioning for original versus A/B/C, source clip lineage and baseline comparison. Brain currently accepts A/B/C; never silently relabel Original as A. Worker, scoring, results, voice/tools and UI must agree the migration.
- `/api/briefs`, `/api/projects/{id}/run`, `/log` SSE and `/results` are the actual merged backend seams. Local Voice IDs are not FastAPI IDs. Feed brain/voice one canonical project/selection/evidence store; do not fork schedulers or fake milestones.
- Default backend composition root was not wired to a real run service at the previous check; confirmed Run could return 503. Require actual configured service/GPU/provider evidence, not test fakes.
- Preserve durable storage, uploaded-source privacy and server-only keys. Do not put customer media, keys/tokens, raw audio, model weights or generated run artifacts in Git. Preserve the original source PDF, licensed fonts and reference images.

## Ownership and release gate

Opus owns brain/render/entry/dock; Canvas owns graph/intake/selection; Voice owns Live/audio/tools; Backend owns contracts/media/pipeline/scoring/evidence. Codex owns this synchronized specification/audit, not their in-progress application files. The concrete Opus correction was delivered to its existing session. Direct Voice/Canvas messaging is restricted by Conductor's other-member ChatGPT-plan access; **its owner must relay this prompt**, not bypass that restriction.

Unmerged PRs or a handoff are not team-wide completion. Publish proof from a clean-clone real route and explicitly list unmet original upload, real conversation, exact-video response, baseline comparison and export acceptance. Keep docs PR #1's divergence/conflicts visible until reconciled with current main while preserving its actual run instructions.
