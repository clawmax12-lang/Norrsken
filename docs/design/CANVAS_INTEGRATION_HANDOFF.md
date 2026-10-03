# Canvas integration — brain motion and Live Director

Product-owner direction, 3 Oct 2026: **ElevenLabs is a UI reference only; Gemini Live remains mandatory two-way voice.** This handoff records requested interaction and inspected seams, not completed acceptance or permission to overwrite/merge another branch. [PRD.md](../../PRD.md) remains the specification; [TEAM.md](../../TEAM.md) tracks evidence.

**v1.7 update:** [PRODUCT_RESET_HANDOFF.md](PRODUCT_RESET_HANDOFF.md) records the existing-video-first decision and current browser defects. It supersedes this older merge snapshot and screenshots-first/always-bottom-orb examples. Baseline/candidate artifact/clip migration is required; preserve owners and actual runtime run instructions.

**Latest design direction, PRD v1.6:** [FLORA and reference 08](README.md#reference-08--flora-primary-product-layout) supersede the earlier shell references. Use a black dotted open canvas, narrow floating left tools, compact corner actions, Redaction/warm orange-red identity and readable media/storyboard/pretest branches. Both [standalone orb and prompt beam](DIRECTOR_VISUALS.md) are requested, preserving existing real Gemini Live/audio/tool logic. See [CLEAN_FLOW_DESIGN.md](CLEAN_FLOW_DESIGN.md) for the relay-ready frontend brief. This does not change the backend contracts or authorize automatic merges.

## Voice brief to relay

> Build the female two-way Gemini Live Director inside the existing Canvas, not as another app. The user can talk, interrupt, ask why, select a storyboard/scene and request a source-backed pre-render edit. Tools update the same validated persisted draft and visible Canvas state. Confirm the bounded run before paid jobs. Use a standalone growing ThinkingOrb, no enclosing card, matched transcripts and accessible mute/stop/disconnect. Long-lived keys stay server-side. Actual backend events and tested evidence drive progress/verdict; never invent brain response or completed tests. ElevenLabs is visual reference only. Agree shared draft/event/data seams with Dashboard, backend and Opus; preserve their working code.

Full requirements: [CANVAS_VOICE_BRIEF.md](CANVAS_VOICE_BRIEF.md), PRD FR-16/§12.9. Read docs PR #1's baseline, not only main's older PRD.

## Requested brain motion

- Persistent brain **top-left**, leaving navigation/Canvas tools usable. Hover enlarges; click/keyboard can pin/expand detail. Preserve variant/time and cached geometry.
- Brisk purposeful camera/orbit motion while real backend work runs → meaningful actual milestone triggers roughly **three seconds of slower detail/focus with text** → return to work motion. No fabricated milestones or repeating takeovers without new events.
- Job-only beat: real render/simulate status, not a made-up "planning region". Camera/halo/status can animate; cortex stays gray without genuine results.
- Neural detail: atlas-backed region/sample from the exact selected video's genuine TRIBE result, with scene/sample time. Demo examples stay separate. More activation is not automatically a better video.
- Slowdown means **camera choreography**, not silently changing video speed, neural timestamps or GPU work. Manual inspection wins. Bound/deduplicate focus/audio queues, respect reduced motion/pause/keyboard and never call a model on hover/orbit.

This refines the existing persistent dock; it does not promote P1 comparison/revision, increase the three-video budget or claim implementation.

## One shared state

```text
Backend persisted events + actual results
                    ↓
         One project/run/evidence store
           ↙            ↓            ↘
     Canvas nodes   Brain companion   Gemini Live context
```

Canvas owns selection/draft; spoken and typed tools use the same validated operations. Brain is presentation, not another scheduler. Audio level is never cortical data.

## Inspected backend interface

Source: backend branch `Mihir-Bhargav/hackathon-project-overview` at `8970609`, not a verified deployment.

- `POST /api/briefs`: multipart intake and canonical project creation.
- `POST /api/projects/{project_id}/run`: background start; returns 503 without injected run service.
- `GET /api/projects/{project_id}/log`: SSE `activity`, numeric `id`, `Last-Event-ID`/`from` replay, terminal `end`. Share one subscription/store, deduplicate project/event ID and close on terminal state.
- Event fields: `at`, `step`, `status`, `message`, optional `variant_id`/`duration_s`. Status is `started/succeeded/failed/skipped`; do not invent percentages/neural completion.
- `GET /api/projects/{project_id}/results`: available concepts/renders/simulations/ranking/report/file URLs; absent evidence stays unavailable.

## Open seams to agree with owners

1. **Runnable backend:** inspected `create_app()` defaults to `run_service=None`. Supply the real wired pipeline/deployment, not unit-test fakes.
2. **Editable draft:** inspected Pipeline runs plan → render automatically; inspected routes lack persisted concept-edit/pre-render approval. Voice's local storyboard must update the real rendered concept and share one project/storage.
3. **Brain adapter:** backend `SimulationResult.brain` points to little-endian float16 `activity.npy`/`groups.json`; viewer PR #3 proposes `meta.cortical` v0 JSON/base64/raw float32. Agree a server-side adapter/safe same-origin artifact route; `.npy` is not raw float32.
4. **Scientific mapping:** both use fsaverage5/left-then-right in principle, but worker groups are Destrieux2009 and viewer picking/reductions use Desikan-Killiany. Keep names/groups explicit or agree a checked mapping. Preserve video hash, timestamps/order; worker says lag is already compensated, so do not shift five seconds again.
5. **Real voice:** merged Voice PR reports no configured Gemini/Condense/TRIBE integration or real Live round trip. Configure secrets server-side and verify speech/interruption/tools; no keys in handoffs.

Opus PR #3 proposes controlled variant selection, project/run IDs and `onEvent`, plus `preflight:brain` selection/lifecycle and `preflight:brain-command` controls. These are presentation seams, not job events/authorization.

## Merge snapshot and next integration PR

- Voice [PR #2](https://github.com/clawmax12-lang/Norrsken/pull/2) merged at 11:59 UTC; real Live acceptance unverified.
- Brain [PR #3](https://github.com/clawmax12-lang/Norrsken/pull/3) is open/conflicting and carries an older Dashboard shell, not the latest Canvas. Preserve main Voice/latest Canvas when reconciling routes/CSS/manifests/tests.
- Backend `8970609` is pushed; no backend PR/merge at this check. Coordinator last reported a session limit. Pushed code is not integrated runtime evidence.
- Docs [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1) is open. v1.5 says no Condense Live exception; merged PR #2 separately records a narrow direct-Live exception/older version. Reconcile this policy/version divergence explicitly with the product owner; this handoff approves no new exception.

Agree one integration owner: latest Canvas → embed Voice/BrainCompanion → shared draft/selection/events → real backend/artifact adapter → verified Live editing and brief → three videos → pretest → verdict/export. Do not auto-merge conflicting branches or replace each other's apps.

Minimum proof: real reply/interruption → persisted spoken edit visible in Canvas → confirmed Run → actual SSE milestone across Canvas/brain/voice → three-second focus without altering playback → matching genuine neural data or honest no-data → evidence-backed verdict question → export. Record actual provider/routing/artifacts/checks and unmet criteria; screenshots/fake tests cannot prove this path.
