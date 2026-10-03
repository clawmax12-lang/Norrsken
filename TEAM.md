# Preflight — shared team board

**Product baseline:** [PRD v1.1](PRD.md). **Repository:** https://github.com/clawmax12-lang/Norrsken. **Product owner:** William.

This document tracks coordination and implementation evidence. It does not redefine the product. Update it when claiming work, handing off a change, resolving a blocker or integrating a pull request. Blank ownership is intentional: technical names and progress were not supplied in the PRD.

## Start a task in Git or Conductor

1. Open a workspace attached to **clawmax12-lang/Norrsken**, based on the latest `origin/main`. A directory cloned inside another project's sandbox does not change that Conductor workspace's project association.
2. Read [AGENTS.md](AGENTS.md), its required PRD sections and this board. Existing chats must explicitly reread the new baseline; do not assume older chat context updates automatically.
3. Check `git status` and fetch current remote state. If your branch has local work, integrate upstream changes without discarding it. Do not reset or force-push a shared branch.
4. Claim a requirement below with a named owner and workspace/branch. Share that claim with the team before overlapping work starts. Keep it visible on the shared board; a claim left only in an unpublished branch cannot coordinate teammates.
5. List the files/components you will change. Coordinate changes to shared schemas, orchestration, dependency manifests and lockfiles with their current owner.
6. Implement against the PRD acceptance criteria. Open a small PR with FR IDs and verification evidence. Update this board at handoff and after integration.

Suggested first message for any existing or new agent session:

> Read AGENTS.md, then PRD.md §15, §8, §9, §10 and §12, then TEAM.md. PRD v1.1 supersedes earlier brainstorming. Work only on my assigned requirement IDs. Report the scope, dependencies and acceptance criteria before implementing, and keep shared contracts coordinated with their owners.

## Ownership

Fill in real people rather than assigning all work to an unnamed agent. Record a workspace/branch so teammates can locate the work.

| Area | Requirement IDs | Owner | Workspace / branch / owned files |
| --- | --- | --- | --- |
| Product decisions | Scope, priority, PRD changes | William | — |
| Brief intake and tablehopp fixture | FR-01 | Unassigned | — |
| Template and renderer | FR-03 | Unassigned | — |
| TRIBE worker | FR-04 (TRIBE) | Unassigned | — |
| Agent, Gemini, Condense | FR-02, FR-04 (panel), FR-05, FR-06, FR-10 | Unassigned | — |
| Web app, results, export and log | FR-07, FR-08, FR-09 | Unassigned | — |
| Brain viewer and Preflight sequence | FR-12, FR-14, FR-15 | Unassigned | — |
| Web dashboard shell | FR-01 entry point, §12.6 visual tokens | Codex | Dashboard workspace / `williu16/preflight-swiftui-dashboard`; `app/*.tsx`, `app/*.css` |
| Integration and release | Shared contracts, clean-clone run, final demo path | Unassigned | — |
| Demo video and pitch | PRD §14.4–§14.6 | William | — |

## Requirement tracker

Source requirements and full acceptance criteria: [PRD §8](PRD.md#8-functional-requirements). No implementation evidence has been registered at this documentation bootstrap. A PRD requirement is not a completed feature.

Statuses: `unclaimed` → `in_progress` → `in_review` → `done`. Use `blocked` with a reason. Use `dropped` only for an explicitly permitted conditional cut, with the decision and evidence recorded below. `done` means integrated into the shared branch with acceptance evidence, not merely working in someone's workspace.

| ID | Requirement | Priority / gate | Owner | Status | Branch / PR / acceptance evidence |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Brief intake and fixture | P0 | — | unclaimed | — |
| FR-02 | Three creative concepts | P0 | — | unclaimed | — |
| FR-03 | Three rendered MP4s | P0 | — | unclaimed | — |
| FR-04 | Simulators and Gemini fallback | P0 | — | unclaimed | — |
| FR-05 | Deterministic score and rank | P0 | — | unclaimed | — |
| FR-06 | Timestamped explanations | P0 | — | unclaimed | — |
| FR-07 | Results UI and synced playback | P0 | — | unclaimed | — |
| FR-08 | Four export files | P0 | — | unclaimed | — |
| FR-09 | Live persisted activity log | P0 | — | unclaimed | — |
| FR-10 | Gemini via Condense, measured savings | P0 | — | unclaimed | — |
| FR-12 | Interactive 3D brain | Conditional P0: TRIBE go/no-go | — | unclaimed | — |
| FR-14 | Preflight sequence | Conditional P0: FR-12 | — | unclaimed | — |
| FR-11 | One revision of the winner | P1: all applicable P0 pass | — | unclaimed | — |
| FR-15 | A/B and brain difference view | P1: all applicable P0 pass | — | unclaimed | — |
| FR-13 | Historical backtest | P1: P0 pass and real historical data exists | — | unclaimed | — |

P2 stays outside today's build. The broader validation programme also has the explicit prerequisite in PRD §13; do not silently start it as part of the MVP.

## Integration and acceptance handoff

### Current handoffs

| Date | Scope | Owner / branch | Status and evidence | Remaining work |
| --- | --- | --- | --- | --- |
| 3 Oct 2026 | TypeScript web dashboard shell; FR-01 entry point and §12.6 visual tokens | Codex / `williu16/preflight-swiftui-dashboard` | In review. Added a responsive app shell with sidebar/top bar, priority-first overview, workflow, empty recent-brief state and new-preflight entry surface. `npm run build` passed on Next.js 16.3.8, including strict TypeScript validation; desktop and 390 px mobile layouts were visually checked. | Dashboard only. Brief persistence and every render, simulator, score, result, and export acceptance criterion remain unimplemented. No FR is marked done. |

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
