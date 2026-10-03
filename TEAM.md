# Preflight — shared team board

**Product baseline:** [PRD v1.4](PRD.md). **Platform:** desktop-browser flow-canvas web product; no iOS/SwiftUI or native client. **Demo:** female Gemini voice is mandatory FR-16/P0. **Repository:** https://github.com/clawmax12-lang/Norrsken. **Product owner:** William.

This document tracks coordination and implementation evidence. It does not redefine the product. Update it when claiming work, handing off a change, resolving a blocker or integrating a pull request. Blank ownership is intentional: technical names and progress were not supplied in the PRD.

## Start a task in Git or Conductor

1. Open a workspace attached to **clawmax12-lang/Norrsken**, based on the latest `origin/main`. A directory cloned inside another project's sandbox does not change that Conductor workspace's project association.
2. Read [AGENTS.md](AGENTS.md), its required PRD sections and this board. Existing chats must explicitly reread the new baseline; do not assume older chat context updates automatically.
3. Check `git status` and fetch current remote state. If your branch has local work, integrate upstream changes without discarding it. Do not reset or force-push a shared branch.
4. Claim a requirement below with a named owner and workspace/branch. Share that claim with the team before overlapping work starts. Keep it visible on the shared board; a claim left only in an unpublished branch cannot coordinate teammates.
5. List the files/components you will change. Coordinate changes to shared schemas, orchestration, dependency manifests and lockfiles with their current owner.
6. Implement against the PRD acceptance criteria. Open a small PR with FR IDs and verification evidence. Update this board at handoff and after integration.

Suggested first message for any existing or new agent session:

> Read AGENTS.md, then PRD.md §15, §8, §9, §10 and §12, then TEAM.md. PRD v1.4 makes the flow canvas, first-entry/persistent brain and female Gemini narration core demo requirements. Reuse the brain once-built; genuine neural data is still required for activation. For UI/brain/voice also read docs/design/README.md, OPUS_BRAIN_BRIEF.md and CANVAS_VOICE_BRIEF.md. Work only on my assigned IDs, preserve existing backend/frontend work and agree shared contracts before editing them. Do not remove execution caps or claim completed tests from prototype graph nodes.

## Ownership

Fill in real people rather than assigning all work to an unnamed agent. Record a workspace/branch so teammates can locate the work.

| Area | Requirement IDs | Owner | Workspace / branch / owned files |
| --- | --- | --- | --- |
| Product decisions | Scope, priority, PRD changes | William | — |
| Brief intake and tablehopp fixture | FR-01 | William / Codex (voice Director, PR #2 merged to main) + Backend team (intake API) | `williu16/voice-hackathon-brainstorming` · voice Director UI, brief contracts, Gemini Live session route; Backend: Hackathon Project Overview |
| Template and renderer | FR-03 | Backend team (Mihir's workspace agents) | [Hackathon Project Overview](conductor://workspace?id=35a48d23-f284-4204-b9cb-8d44dc06bfa8); render/composer in progress |
| TRIBE worker | FR-04 (TRIBE) | Backend team (Mihir's workspace agents) | Same workspace; upstream vendored on `Mihir-Bhargav/hackathon-project-overview`; worker being built, live GPU evidence not verified |
| Agent, Gemini, Condense | FR-02, FR-04 (panel), FR-05, FR-06, FR-10 | Backend team (Mihir's workspace agents) | Same workspace; contracts/LLM/simulators/scoring being integrated |
| Web canvas and results | FR-07 | William U. / Dashboard agent | [Dashboard](conductor://workspace?id=6e7c2346-1d02-4ca4-b560-17b77aba0c1c) / `williu16/preflight-swiftui-dashboard`; preserve its app shell/graph work |
| Persisted jobs and export | FR-08, FR-09 | Backend team + Dashboard consumer | Backend owns activity/API/artifacts; canvas and voice consume agreed events |
| Brain viewer and Preflight sequence | FR-12, FR-14, FR-15 | Claude Opus 5.5 (implementation); William (product review) | [3D Brain — Opus 5.5](conductor://workspace?id=e14af4c4-eada-4c17-bc3b-42cd2ef08dcd) / `conductor/3d-brain-opus-55`; reusable viewer/scene and minimal web integration. Owned files: `app/brain/**`, `components/brain/**`, `lib/brain/**`, `public/brain/**`, `scripts/brain/**`, `tests/brain/**`; shared touches: one nav link in `app/page.tsx`, `three` in `package.json`/lockfile, `test` script, `allowImportingTsExtensions` in `tsconfig.json`. See docs/design/OPUS_BRAIN_BRIEF.md. FR-15 remains gated P1. |
| Female Gemini voice and orb | FR-16; optional Live intake | William U. / Voice workspace agent (scope handoff pending) | [Voice Hackathon Brainstorming](conductor://workspace?id=987f2949-3647-4e9a-a202-04e6d2c1d023); currently design/research, no real speech acceptance yet |
| Integration and release | Shared contracts, clean-clone run, final demo path | Unassigned | — |
| Demo video and pitch | PRD §14.4–§14.6 | William | — |

## Requirement tracker

Source requirements and full acceptance criteria: [PRD §8](PRD.md#8-functional-requirements). The [timestamped audit](docs/status/2026-10-03-build-audit.md) distinguishes agent-reported local work from integrated acceptance. A PRD requirement or a working session is not a completed feature.

Statuses: `unclaimed` → `in_progress` → `in_review` → `done`. Use `blocked` with a reason. Use `dropped` only for an explicitly permitted conditional cut, with the decision and evidence recorded below. `done` means integrated into the shared branch with acceptance evidence, not merely working in someone's workspace.

| ID | Requirement | Priority / gate | Owner | Status | Branch / PR / acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Brief intake and fixture | P0 | William / Codex | in_review | `williu16/voice-hackathon-brainstorming` · [PR #2](https://github.com/clawmax12-lang/Norrsken/pull/2) — voice-native intake, typed fallback, approved-folder shelf, storyboard and persisted brief implemented. `npm run typecheck`, `npm run lint`, 6 tests and production build pass; API smoke test persisted 3 PNGs + `brief.json`; 1440 px browser screenshot in `.context/preflight-director.png`. Live call remains unverified because `GEMINI_API_KEY` is not configured in this workspace. |
| FR-02 | Three creative concepts | P0 | Backend team | in_progress | Planner/LLM being built; no real-provider acceptance verified |
| FR-03 | Three rendered MP4s | P0 | Backend team | in_progress | Renderer/composer being built; research render is not the three-variant AC |
| FR-04 | Simulators and Gemini fallback | P0 | Backend team | in_progress | TRIBE/Gemini panel adapters being built; live GPU/result not verified |
| FR-05 | Deterministic score and rank | P0 | Backend team | in_progress | Agent reports local scoring checks/69 tests; not merged/integrated acceptance |
| FR-06 | Timestamped explanations | P0 | Backend team | in_progress | Same local handoff, no end-to-end real evidence verified |
| FR-07 | Flow canvas, results and synced playback | P0 | Dashboard + brain integration | in_progress | Canvas prototype on branch/preview; actual backend binding/brain not integrated |
| FR-08 | Four export files | P0 | Backend team | in_progress | API/export implementation underway; four real exports not verified |
| FR-09 | Live persisted activity log | P0 | Backend team | in_progress | Orchestrator handoff reports 222 tests with fakes; global check/integration pending |
| FR-10 | Gemini via Condense, measured savings | P0 | Backend team | in_progress | Provider adapters underway; audio/Live routing and genuine savings unverified |
| FR-12 | Reusable interactive brain and dock | P0 anatomy/dock; genuine response gated | Opus 5.5 | in_review | [PR #3](https://github.com/clawmax12-lang/Norrsken/pull/3), `conductor/3d-brain-opus-55`. Anatomy/dock/controls verified in headless Chrome (SwiftShader); activity only with labelled MOCK. Genuine-data AC and MacBook performance unverified. |
| FR-14 | Entry and analysis Preflight sequence | P0 entry; genuine analysis gated | Opus 5.5 | in_review | [PR #3](https://github.com/clawmax12-lang/Norrsken/pull/3). Entry once/session → dock, Skip, reduced motion verified on gray anatomy; analysis focus verified only with MOCK/no-data preview. Genuine-run analysis and a genuine demo example unverified (none exist). |
| FR-16 | Female Gemini narration and orb | P0, owner-confirmed | Voice owner (handoff pending) | unclaimed | Voice design/research exists; no implemented real TTS acceptance verified |
| FR-11 | One revision of the winner | P1: all applicable P0 pass | — | unclaimed | — |
| FR-15 | A/B and brain difference view | P1: all applicable P0 pass | Opus 5.5 (queued) | unclaimed | Shared component/time/camera groundwork in FR-12; P1 implementation awaits gate |
| FR-13 | Historical backtest | P1: P0 pass and real historical data exists | — | unclaimed | — |

P2 stays outside today's build. The broader validation programme also has the explicit prerequisite in PRD §13; do not silently start it as part of the MVP.

## Integration and acceptance handoff

### Current handoffs

| Date | Scope | Owner / branch | Status and evidence | Remaining work |
| --- | --- | --- | --- | --- |
| 3 Oct 2026 | TypeScript web dashboard shell; FR-01 entry point and §12.6 visual tokens | Codex / `williu16/preflight-swiftui-dashboard` | In review. Added a responsive app shell with sidebar/top bar, priority-first overview, workflow, empty recent-brief state and new-preflight entry surface. `npm run build` passed on Next.js 16.3.8, including strict TypeScript validation; desktop and 390 px mobile layouts were visually checked. | Dashboard only. Brief persistence and every render, simulator, score, result, and export acceptance criterion remain unimplemented. No FR is marked done. |
| 3 Oct 2026 | FR-12/FR-14 reusable brain companion (entry → dock ⇄ expanded, analysis focus); FR-15 groundwork only | Claude Opus 5.5 / [3D Brain — Opus 5.5](conductor://workspace?id=e14af4c4-eada-4c17-bc3b-42cd2ef08dcd) / `conductor/3d-brain-opus-55` / [PR #3](https://github.com/clawmax12-lang/Norrsken/pull/3) / preview https://norrsken-w11.conductor.show/brain (Conductor access required) | In review. Changed: `app/brain/**`, `components/brain/**`, `lib/brain/**`, `public/brain/**` (fsaverage5 + Desikan-Killiany in TRIBE vertex order, FreeSurfer licence; original head mesh), `scripts/brain/**`, `tests/brain/**`, `docs/design/BRAIN_COMPANION.md`; shared touches: nav link in `app/page.tsx`, `three`/`@types/three` + `test` script, `tsconfig` `allowImportingTsExtensions`, `app/icon.svg`, README run steps, one proposed PRD §16 row. Evidence: `npm run build`, `npx tsc --noEmit`, `npm test` 19/19; headless Chrome 1440×900 SwiftShader on dev and `next start`: entry once/session + Skip + reduced motion, dock/expand state retention, orbit/zoom/reset, region card, surfaces/hemispheres, keys/scrub, video-master sync (generated test MP4), fullscreen, analysis focus + Skip, `?sim=off`, ingestion/validation, command channel, MOCK refused in production, no console/WebGL errors. | Genuine TRIBE data, a genuine demo example and MacBook/GPU performance unverified (activity seen only as labelled MOCK). Needs owner agreement on `meta.cortical` v0 (TRIBE worker) and the events/commands seam (Dashboard, Voice/Live). Not wired into the Dashboard canvas. Based on Dashboard `62ad654` and docs `f0c38e2`; PRD v1.5 not yet merged. FR-15 P1 not started. |

Documentation task **DOC-WEB** (clarifies FR-01, FR-07, FR-08, FR-09, FR-12 and FR-14): Codex owns the explicit web-platform decision and matching onboarding/agent guidance in [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1) on `docs/tribe-foundation`. Status: `in_review` (not yet integrated). Files: `PRD.md`, `README.md`, `AGENTS.md`, `TEAM.md`, `docs/source/README.md`. The web clarification landed in v1.2 (the current editable PRD is v1.4); that change retained all original 15 IDs/AC, local links passed and the original v1.1 PDF checksum is unchanged. No application code was changed.

Documentation task **DOC-TRIBE** (supports FR-04, FR-12 and FR-14): Codex owns the README explanation and upstream quickstart on branch `docs/tribe-foundation`. Status: `in_review` (not yet integrated). Files: `README.md` and this handoff entry. Verified against upstream commit `af58661791a351a448a489042a28f6c37e1c14b7`; local links, Python/shell example syntax and whitespace checks pass. GPU installation/inference was not run. This does not claim ownership or completion of the TRIBE worker or brain-viewer implementation.

Documentation task **DOC-BRAIN** (supports FR-12/FR-14/FR-15 and model roles in §9.1): Codex owns the tracked visual-reference package and Opus implementation brief on `docs/tribe-foundation`, [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1). Status: `in_review` (not yet integrated). Files: `docs/design/`, `PRD.md`, `README.md`, `AGENTS.md`, `TEAM.md`, `docs/source/README.md`. All three original images and the MP4 are copied without modification; byte comparisons and SHA-256 checks pass. PRD v1.3 adopts the visual/reuse decisions; all 15 FR IDs and original sections remain, 42 local document/media links and anchors pass, whitespace checks pass, and the original v1.1 PDF checksum is unchanged. Dashboard's temporary Vercel preview is recorded and checked (HTTP 200 plus browser screenshot); it is not a completed brain feature. Opus's code implementation is a separate assignment, not completed by this documentation work. No application tests or GPU inference were run on this documentation branch.

Implementation task **BRAIN-WEB** (FR-12/FR-14; FR-15 queued P1): product-owner-requested Claude Opus 5.5 is running in [its isolated Conductor workspace](conductor://workspace?id=e14af4c4-eada-4c17-bc3b-42cd2ef08dcd&session=be40ac16-08d6-4ce4-999f-7e69ea8d4912), branch `conductor/3d-brain-opus-55`, based on the existing Dashboard web implementation. Launch verified on 3 Oct 2026: workspace ready, session working, model `opus-5-5-1m` resolved to `claude-opus-5-5[1m]`; initial task delivered and current docs/references being read/integrated. Scope: reusable mesh/materials/controls, data adapter, sync/fullscreen and conditional intro; no runtime video-generation API integration or replacement of the GPU worker. No brain PR, preview or implementation AC has passed yet. Opus must preserve Dashboard run instructions/ownership while integrating PR #1, then record its own build/browser evidence and handoff here. Do not mark the feature done merely because the agent has started.

Documentation task **DOC-CANVAS-VOICE** (FR-07/FR-09/FR-12/FR-14/new FR-16): Codex owns PRD v1.4, the new original canvas reference, aligned shared docs, integration brief and build-status audit on `docs/tribe-foundation`, [PR #1](https://github.com/clawmax12-lang/Norrsken/pull/1). Status: `in_review` (not integrated). The owner explicitly confirmed female Gemini narration as P0, then proposed the standalone growing orb. Backend/application files, dependency manifests, runtime credentials and other agents' branches are not modified. Checks: all 19 original sections and FR-01–FR-16 with 16 AC blocks; 60 local links/anchors; byte/hash verification of the new reference and unchanged original PDF/assets; whitespace and credential-pattern checks; public canvas HTTP/browser inspection; documented registry/provider references. No paid model or GPU calls, app tests or voice acceptance run in this docs branch. This is a direction/status handoff, not completed provider/GPU/voice implementation.

**Coordination warning:** `origin/main` was still the initial v1.1 documentation commit at this audit; PR #1 is open. Existing workspaces do not automatically adopt v1.4. Integrate the current docs non-destructively and preserve their actual application run instructions before claiming shared-baseline synchronization. Older Design System/Results/Activity/Brief sessions produced SwiftUI artifacts before the web decision; they are idle, off the current architecture and not web acceptance evidence. See the audit for exact sources.

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
| 12:30 — TRIBE | One real clip completes; capture environment, duration and real output artifact | Backend team; evidence pending |
| 12:30 — renderer | One 15 s, 1080x1920, 30 fps MP4 renders through the template | Backend team; implementation proof pending |
| 12:30 — voice | Real female Gemini TTS playback; account/model and Condense routing recorded | Voice owner handoff/acceptance pending |
| P0 complete | FR-01–FR-10, anatomy/entry/dock FR-12/FR-14, voice FR-16 and applicable genuine-data AC; clean-clone end-to-end evidence | Pending |
| 17:45 — code freeze | Demo path verified; remaining cuts recorded per PRD | Pending |
| 18:00–18:40 — recording | Two-minute recording of the real product, as specified in PRD | Pending |
| 18:45 — planned submission | Public repo, README and recording ready; team/platform requirements checked | Pending |

If live TRIBE fails its gate, record the result and apply the Gemini-only fallback. Per v1.4 keep canvas, gray anatomy/entry/dock and mandatory voice, without falsely claiming neural AC passed. Genuine precomputed examples must be disclosed and separated from the run; do not silently bypass the live go/no-go. If voice is unavailable, explicitly report the unmet FR-16/P0; a glow/orb is not a substitute for Gemini speech.

## Open items from the PRD

| Item | Current evidence / question | Next action |
| --- | --- | --- |
| Repository URL and visibility | URL is filled in. GitHub reported PRIVATE at import on 3 Oct 2026; PRD requires public. | Repository owner to resolve visibility before submission. No visibility change was made during documentation setup. |
| Exact submission time | PRD says verify 19:00 vs 19:19; planned submission is 18:45. | Confirm on the hackathon platform and record the source. |
| GPU / TRIBE feasibility | GPU source and actual latency/VRAM are unverified; §11 itself asks for model-card verification. | Assign TRIBE owner; run the go/no-go and record evidence. |
| Template style | Modern SaaS launch video reference in PRD; no selected template implementation. | Renderer owner + William to choose one family. |
| Runtime model keys and finalization | Owner reports a Gemini key is available; deployment/account/TTS access is not yet verified. Coding-agent Opus is available; runtime Opus API/Condense routing and budget remain unverified. | Keep all keys server-side and out of Git/messages; use only verified provider routes. A changed final asset must be re-simulated, per PRD §9.1. |
| Voice provider/transport | Google's docs list Gemini 3.8 Flash TTS; voice workspace is exploring Live intake. No working speech demo was observed. | Deliver P0 TTS narration/orb; verify Condense audio route. Optional direct Live needs supported transport or an approved documented exception. |
| Batch capacity | Canvas prototype displays large branching claims, but real test throughput/cost is unknown. | Keep three-video execution cap; agree explicit hypothesis/render/inference budget and queue/pruning before increasing it. |
| Lunch time | Unclear in the opening talk per PRD. | Confirm only if needed for team scheduling. |
| Technical ownership and registration | Names absent from §14.3; team/platform registration not verified here. | Fill ownership and confirm participant registration. |

## Implementation clarifications to resolve

These are gaps to clarify during implementation, not changes to the supplied requirements.

| Affected IDs | Question | Status |
| --- | --- | --- |
| FR-05 | What goal-aligned scoring rule, normalization, simulator weighting and tie rule make ranking deterministic? Neural activity alone is not a validated success score. | Open — document the actual rule in code, README and §16. |
| FR-04, FR-05 | What confidence label applies when only Gemini is available? The PRD defines agreement/disagreement, but not the single-simulator case. | Open — resolve before claiming fallback acceptance. |
| FR-07, FR-12, FR-14, FR-16 | How do the canvas and voice consume brain entry/dock/selection state without duplicate selection state? | Proposed: `BrainCompanion` props plus `preflight:brain` events (incl. `selection.changed`) and `preflight:brain-command` commands in [BRAIN_COMPANION.md](docs/design/BRAIN_COMPANION.md); awaiting Dashboard and Voice owner agreement. |
| FR-04, FR-07, FR-12, FR-14 | How do mesh/atlas identifiers, timestamps, region series and cortical samples reach the viewer through the shared SimulationResult boundary? | Proposed: `meta.cortical` v0 (fsaverage5, nilearn left-then-right, `times_s`, `hemodynamic_alignment`, one value source) in [BRAIN_COMPANION.md](docs/design/BRAIN_COMPANION.md) / PR #3; awaiting TRIBE worker owner agreement. |
| FR-03, FR-05, FR-08 | How are rankings and winner/runner-up exports handled if render retries leave fewer than two successful variants? | Open — preserve visible failures; do not invent an output. |

## Changes to this baseline

Update product requirements in PRD.md and append the decision to §16. Update this board for owners/status/evidence and README for actual run instructions. Keep the original PDF unchanged. Earlier advisor briefs under `.context/` are historical and are not team requirements.

## Current handoff

- **FR-01 / [PR #2](https://github.com/clawmax12-lang/Norrsken/pull/2) on `williu16/voice-hackathon-brainstorming`:** Next.js vertical slice adds secure ephemeral Gemini Live sessions (`gemini-3.8-live`, `Kore`), interruptible PCM audio, transcripts, typed fields, explicit local-folder selection, five inspectable Director tools, screenshot upload and schema-validated `data/projects/{project_id}/brief.json` persistence.
- **Verification:** `npm run typecheck`; `npm run lint`; `npm test` (6/6); `npm run build`; `npm audit --omit=dev` (0 vulnerabilities); browser GET and 1440 px screenshot; API upload/save smoke test. No real Gemini request was claimed because the server has no `GEMINI_API_KEY`.
- **Next owner:** configure a Tier 3 AI Studio key in `.env.local`, verify microphone permission, barge-in, input/output transcripts and all five tool calls in current desktop Chrome. Planning/render/TRIBE remain separate unclaimed requirements; no simulated output is present in this slice.
