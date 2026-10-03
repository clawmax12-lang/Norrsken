# Preflight — shared team board

**Product baseline:** [PRD v1.5](PRD.md). **Platform:** desktop-browser web product; no iOS/SwiftUI or native client. **Repository:** https://github.com/clawmax12-lang/Norrsken. **Product owner:** William.

This document tracks coordination and implementation evidence. It does not redefine the product. Update it when claiming work, handing off a change, resolving a blocker or integrating a pull request. Blank ownership is intentional: technical names and progress were not supplied in the PRD.

## Start a task in Git or Conductor

1. Open a workspace attached to **clawmax12-lang/Norrsken**, based on the latest `origin/main`. A directory cloned inside another project's sandbox does not change that Conductor workspace's project association.
2. Read [AGENTS.md](AGENTS.md), its required PRD sections and this board. Existing chats must explicitly reread the new baseline; do not assume older chat context updates automatically.
3. Check `git status` and fetch current remote state. If your branch has local work, integrate upstream changes without discarding it. Do not reset or force-push a shared branch.
4. Claim a requirement below with a named owner and workspace/branch. Share that claim with the team before overlapping work starts. Keep it visible on the shared board; a claim left only in an unpublished branch cannot coordinate teammates.
5. List the files/components you will change. Coordinate changes to shared schemas, orchestration, dependency manifests and lockfiles with their current owner.
6. Implement against the PRD acceptance criteria. Open a small PR with FR IDs and verification evidence. Update this board at handoff and after integration.

Suggested first message for any existing or new agent session:

> Read AGENTS.md, then PRD.md §15, §8, §9, §10 and §12, then TEAM.md. PRD v1.3 supersedes earlier brainstorming: Preflight is a web platform, not an iOS/SwiftUI app; the interactive brain is built once and reused with genuine per-video data. For brain/design work also read docs/design/README.md and OPUS_BRAIN_BRIEF.md. Work only on my assigned requirement IDs. Report the scope, dependencies and acceptance criteria before implementing, and keep shared contracts coordinated with their owners.

## Ownership

Fill in real people rather than assigning all work to an unnamed agent. Record a workspace/branch so teammates can locate the work.

| Area | Requirement IDs | Owner | Workspace / branch / owned files |
| --- | --- | --- | --- |
| Product decisions | Scope, priority, PRD changes | William | — |
| Brief intake, canvas and Live Director | FR-01, FR-07, FR-09, FR-16 | William / Codex | `williu16/fr-16-canvas-live` · canvas shell/composer, shared draft contracts, Gemini Live tools, Next API routes, package/README/PRD/TEAM. Preserves backend and brain-owner files. |
| Template and renderer | FR-03 | Unassigned | — |
| TRIBE worker | FR-04 (TRIBE) | Unassigned | — |
| Agent, Gemini, Condense | FR-02, FR-04 (panel), FR-05, FR-06, FR-10 | Unassigned | — |
| Web app, results, export and log | FR-07, FR-08, FR-09 | Unassigned | — |
| Brain viewer and Preflight sequence | FR-12, FR-14, FR-15 | Claude Opus 5.5 (implementation); William (product review) | [3D Brain — Opus 5.5](conductor://workspace?id=e14af4c4-eada-4c17-bc3b-42cd2ef08dcd) / `conductor/3d-brain-opus-55`; reusable viewer/scene and minimal web integration. See docs/design/OPUS_BRAIN_BRIEF.md. FR-15 remains gated P1. |
| Integration and release | Shared contracts, clean-clone run, final demo path | Unassigned | — |
| Demo video and pitch | PRD §14.4–§14.6 | William | — |

## Requirement tracker

Source requirements and full acceptance criteria: [PRD §8](PRD.md#8-functional-requirements). No implementation evidence has been registered at this documentation bootstrap. A PRD requirement is not a completed feature.

Statuses: `unclaimed` → `in_progress` → `in_review` → `done`. Use `blocked` with a reason. Use `dropped` only for an explicitly permitted conditional cut, with the decision and evidence recorded below. `done` means integrated into the shared branch with acceptance evidence, not merely working in someone's workspace.

| ID | Requirement | Priority / gate | Owner | Status | Branch / PR / acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Brief intake and fixture | P0 | William / Codex | in_review | Original intake in merged PR #2; canvas integration on `williu16/fr-16-canvas-live` adds the shared typed/voice brief and approved-folder shelf. Unit/build/browser checks pass; real Gemini call remains unverified in this workspace. |
| FR-02 | Three creative concepts | P0 | — | unclaimed | — |
| FR-03 | Three rendered MP4s | P0 | — | unclaimed | — |
| FR-04 | Simulators and Gemini fallback | P0 | — | unclaimed | — |
| FR-05 | Deterministic score and rank | P0 | — | unclaimed | — |
| FR-06 | Timestamped explanations | P0 | — | unclaimed | — |
| FR-07 | Canvas/results UI and synced playback | P0 | William / Codex | in_progress | `williu16/fr-16-canvas-live` implements the primary pan/zoom A/B/C canvas, selected scene detail and honest proposed/no-data states. Real render/result binding, leaderboard, player and curves remain. |
| FR-08 | Four export files | P0 | — | unclaimed | — |
| FR-09 | Live persisted activity log | P0 | William / Codex + backend owner | in_progress | Canvas exposes an honest job state and confirmation-gated idempotency key. SSE event binding remains blocked on a deployed canonical project/orchestrator seam; no progress is simulated. |
| FR-10 | Gemini via Condense, measured savings | P0 | — | unclaimed | — |
| FR-12 | Interactive 3D brain | Conditional P0: TRIBE go/no-go | Opus 5.5 | in_progress | `conductor/3d-brain-opus-55`; assignment started, no acceptance evidence yet |
| FR-14 | Preflight sequence | Conditional P0: FR-12 | Opus 5.5 | in_progress | Same isolated assignment; genuine-data/intro AC not yet verified |
| FR-11 | One revision of the winner | P1: all applicable P0 pass | — | unclaimed | — |
| FR-15 | A/B and brain difference view | P1: all applicable P0 pass | Opus 5.5 (queued) | unclaimed | Shared component/time/camera groundwork in FR-12; P1 implementation awaits gate |
| FR-13 | Historical backtest | P1: P0 pass and real historical data exists | — | unclaimed | — |
| FR-16 | Integrated two-way Gemini Live Director | P0 | William / Codex | in_review | `williu16/fr-16-canvas-live` · [PR #6](https://github.com/clawmax12-lang/Norrsken/pull/6) — Live transport now sits in the shared canvas composer; validated revisioned A/B/C tools, typed fallback, real input/output levels, transcripts, mute/disconnect and explicit Run confirmation implemented. `npm run typecheck`, `npm run lint`, 12 tests, build and production audit pass; 1440×1000 browser screenshot checked. Real provider reply/interruption/spoken edit remains an acceptance gate because no key is present in this workspace. |

P2 stays outside today's build. The broader validation programme also has the explicit prerequisite in PRD §13; do not silently start it as part of the MVP.

## Integration and acceptance handoff

Documentation task **DOC-WEB** (clarifies FR-01, FR-07, FR-08, FR-09, FR-12 and FR-14): Codex owns the explicit web-platform decision and matching onboarding/agent guidance in [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1) on `docs/tribe-foundation`. Status: `in_review` (not yet integrated). Files: `PRD.md`, `README.md`, `AGENTS.md`, `TEAM.md`, `docs/source/README.md`. The web clarification landed in v1.2 (the current editable PRD is v1.3); all 15 requirement IDs/AC remain, local links and version references pass checks, and the original v1.1 PDF checksum is unchanged. No application code was changed.

Documentation task **DOC-TRIBE** (supports FR-04, FR-12 and FR-14): Codex owns the README explanation and upstream quickstart on branch `docs/tribe-foundation`. Status: `in_review` (not yet integrated). Files: `README.md` and this handoff entry. Verified against upstream commit `af58661791a351a448a489042a28f6c37e1c14b7`; local links, Python/shell example syntax and whitespace checks pass. GPU installation/inference was not run. This does not claim ownership or completion of the TRIBE worker or brain-viewer implementation.

Documentation task **DOC-BRAIN** (supports FR-12/FR-14/FR-15 and model roles in §9.1): Codex owns the tracked visual-reference package and Opus implementation brief on `docs/tribe-foundation`, [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1). Status: `in_review` (not yet integrated). Files: `docs/design/`, `PRD.md`, `README.md`, `AGENTS.md`, `TEAM.md`, `docs/source/README.md`. All three original images and the MP4 are copied without modification; byte comparisons and SHA-256 checks pass. PRD v1.3 adopts the visual/reuse decisions; all 15 FR IDs and original sections remain, 42 local document/media links and anchors pass, whitespace checks pass, and the original v1.1 PDF checksum is unchanged. Dashboard's temporary Vercel preview is recorded and checked (HTTP 200 plus browser screenshot); it is not a completed brain feature. Opus's code implementation is a separate assignment, not completed by this documentation work. No application tests or GPU inference were run on this documentation branch.

Implementation task **BRAIN-WEB** (FR-12/FR-14; FR-15 queued P1): product-owner-requested Claude Opus 5.5 is running in [its isolated Conductor workspace](conductor://workspace?id=e14af4c4-eada-4c17-bc3b-42cd2ef08dcd&session=be40ac16-08d6-4ce4-999f-7e69ea8d4912), branch `conductor/3d-brain-opus-55`, based on the existing Dashboard web implementation. Launch verified on 3 Oct 2026: workspace ready, session working, model `opus-5-5-1m` resolved to `claude-opus-5-5[1m]`; initial task delivered and current docs/references being read/integrated. Scope: reusable mesh/materials/controls, data adapter, sync/fullscreen and conditional intro; no runtime video-generation API integration or replacement of the GPU worker. No brain PR, preview or implementation AC has passed yet. Opus must preserve Dashboard run instructions/ownership while integrating PR #1, then record its own build/browser evidence and handoff here. Do not mark the feature done merely because the agent has started.

For each task, record:

- Requirement IDs, owner, branch/PR and changed components.
- Producer/consumer contract changes, environment requirements and other owners affected.
- AC checked, actual commands/results, screenshots or artifact references, plus limitations.
- What is ready for the next owner and what remains blocked.

Keep the simplified contracts in PRD §10.3 aligned across all components. Record implementation choices in PRD §16 and reflect approved contract changes there. Do not create a competing specification in a workspace note.

## Go/no-go and release gates

The authoritative schedule, cut order and pitch are in [PRD §14](PRD.md#14-hackathon-execution). Times below are copied from that event schedule; confirm the submission deadline on the platform.

| Gate | Required evidence | Decision / status |
| --- | --- | --- |
| 12:30 — TRIBE | One real clip completes; capture environment, duration and real output artifact | Pending; owner unassigned |
| 12:30 — renderer | One 15 s, 1080x1920, 30 fps MP4 renders through the template | Pending; owner unassigned |
| P0 complete | All applicable FR-01–FR-10 plus conditional FR-12/FR-14 AC pass; clean-clone run and end-to-end duration recorded | Pending |
| 17:45 — code freeze | Demo path verified; remaining cuts recorded per PRD | Pending |
| 18:00–18:40 — recording | Two-minute recording of the real product, as specified in PRD | Pending |
| 18:45 — planned submission | Public repo, README and recording ready; team/platform requirements checked | Pending |

If TRIBE fails its gate, record the result and apply the PRD's Gemini-only fallback. FR-12/FR-14 are dropped as specified, not falsely marked passed. Any proposed use of precomputed genuine outputs must follow the PRD disclosures and have its scope recorded; do not use it to silently bypass the documented go/no-go.

## Open items from the PRD

| Item | Current evidence / question | Next action |
| --- | --- | --- |
| Repository URL and visibility | URL is filled in. GitHub reported PRIVATE at import on 3 Oct 2026; PRD requires public. | Repository owner to resolve visibility before submission. No visibility change was made during documentation setup. |
| Exact submission time | PRD says verify 19:00 vs 19:19; planned submission is 18:45. | Confirm on the hackathon platform and record the source. |
| GPU / TRIBE feasibility | GPU source and actual latency/VRAM are unverified; §11 itself asks for model-card verification. | Assign TRIBE owner; run the go/no-go and record evidence. |
| Template style | Modern SaaS launch video reference in PRD; no selected template implementation. | Renderer owner + William to choose one family. |
| Runtime model keys and finalization | Gemini key is to be supplied later. Coding-agent Opus is available in Conductor; runtime Opus API/Condense routing, credentials and budget remain unverified. | Keep explicit not-configured states; Gemini remains the P0 path. A changed final asset must be re-simulated, per PRD §9.1. |
| Lunch time | Unclear in the opening talk per PRD. | Confirm only if needed for team scheduling. |
| Technical ownership and registration | Names absent from §14.3; team/platform registration not verified here. | Fill ownership and confirm participant registration. |

## Implementation clarifications to resolve

These are gaps to clarify during implementation, not changes to the supplied requirements.

| Affected IDs | Question | Status |
| --- | --- | --- |
| FR-05 | What goal-aligned scoring rule, normalization, simulator weighting and tie rule make ranking deterministic? Neural activity alone is not a validated success score. | Open — document the actual rule in code, README and §16. |
| FR-04, FR-05 | What confidence label applies when only Gemini is available? The PRD defines agreement/disagreement, but not the single-simulator case. | Open — resolve before claiming fallback acceptance. |
| FR-04, FR-07, FR-12, FR-14 | How do mesh/atlas identifiers, timestamps, region series and cortical samples reach the viewer through the shared SimulationResult boundary? | Open — agree between simulator and viewer owners. |
| FR-03, FR-05, FR-08 | How are rankings and winner/runner-up exports handled if render retries leave fewer than two successful variants? | Open — preserve visible failures; do not invent an output. |

## Changes to this baseline

Update product requirements in PRD.md and append the decision to §16. Update this board for owners/status/evidence and README for actual run instructions. Keep the original PDF unchanged. Earlier advisor briefs under `.context/` are historical and are not team requirements.

## Current handoff

- **FR-01/FR-07/FR-09/FR-16 / [PR #6](https://github.com/clawmax12-lang/Norrsken/pull/6) on `williu16/fr-16-canvas-live`:** replaces the standalone Director screen with a minimal black dotted flow canvas. Exactly three proposed A/B/C paths contain five 3-second editable scenes; proposed nodes are explicitly not rendered. The bottom composer owns Gemini Live, typed fallback, captions, actual mic/output levels, mute and disconnect. Voice/click/typed operations share `CanvasDraft`, reject stale revisions and source-less scene copy, persist browser state plus `draft.json` in writable Node deployments, and open confirmation rather than auto-starting jobs.
- **Verification:** `npm run typecheck`; `npm run lint`; `npm test` (12/12); `npm run build`; `npm audit --omit=dev` (0 vulnerabilities); browser HTTP 200 and 1440×1000 screenshot at `.context/preflight-canvas-live.png`; draft PUT/GET smoke passed and stale revision returned 409; disconnected Run returned the intended honest 503. Real Gemini audio was not tested because no Google key is available to this cloud process.
- **Preview:** `https://temporary-agile-redwood-3fj586n.vercel.app` returned HTTP 200 with `Preflight Canvas`; anonymous deployment expires after about 60 minutes and has no inherited environment variables, so it demonstrates the canvas but not Live voice.
- **Remaining integration:** Vercel needs `GOOGLE_API_KEY` in the same project/environment and a redeploy. Durable server draft storage needs an adapter; Vercel function filesystems are not durable. The FastAPI service must expose a canonical editable-draft/project seam plus deployed `PREFLIGHT_API_URL` before the canvas may claim queued jobs/SSE milestones/results. Brain owner files were not changed; the canvas currently shows `No brain data`.

- **FR-01 / [PR #2](https://github.com/clawmax12-lang/Norrsken/pull/2) on `williu16/voice-hackathon-brainstorming`:** Next.js vertical slice adds secure ephemeral Gemini Live sessions (`gemini-3.8-live`, `Kore`), interruptible PCM audio, transcripts, typed fields, explicit local-folder selection, five inspectable Director tools, screenshot upload and schema-validated `data/projects/{project_id}/brief.json` persistence.
- **Verification:** `npm run typecheck`; `npm run lint`; `npm test` (6/6); `npm run build`; `npm audit --omit=dev` (0 vulnerabilities); browser GET and 1440 px screenshot; API upload/save smoke test. No real Gemini request was claimed because the server has no `GEMINI_API_KEY`.
- **Next owner:** configure a Tier 3 AI Studio key in `.env.local`, verify microphone permission, barge-in, input/output transcripts and all five tool calls in current desktop Chrome. Planning/render/TRIBE remain separate unclaimed requirements; no simulated output is present in this slice.
