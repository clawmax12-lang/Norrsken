# Brain companion — implementation and integration seam (FR-12, FR-14)

Implementation notes for the reusable browser brain built by Claude Opus 5.5 on `conductor/3d-brain-opus-55` ([PR #3](https://github.com/clawmax12-lang/Norrsken/pull/3)). [PRD.md](../../PRD.md) stays authoritative; this file documents what exists and the **proposed** seams other owners consume. Nothing here is agreed with the backend/TRIBE, canvas (Dashboard) or voice owners until they confirm it in TEAM.md and PRD §16.

Ownership: brain, dock, choreography and the read-only artifact adapter. Design baseline: PRD v1.6 / [CLEAN_FLOW_DESIGN.md](https://github.com/clawmax12-lang/Norrsken/blob/docs/tribe-foundation/docs/design/CLEAN_FLOW_DESIGN.md) on docs PR #1 (FLORA primary). This branch does not import the shell theme, fonts or Director visuals; those belong to the Dashboard and Voice owners. The canvas shell/graph (Dashboard), the Gemini Live Director, ThinkingOrb and VoiceBeam (Voice), and the API, workers and contracts (backend) belong to their owners and are not modified here.

## What is built

| Piece | Files | Notes |
| --- | --- | --- |
| Anatomy assets | `public/brain/fsaverage5/*`, `public/brain/head/*`, `scripts/brain/*` | fsaverage5 pial + inflated, sulc/curv, Desikan-Killiany labels, TRIBE vertex order (left 10,242 then right). Original head silhouette. Provenance and FreeSurfer licence: [`public/brain/ATTRIBUTION.md`](../../public/brain/ATTRIBUTION.md). |
| Shared geometry and renderer | `lib/brain/{assets,geometry,scene,materials,head,activityTexture}.ts` | Loaded and built once per session; each genuine result becomes one float texture. Playback, orbit, variant changes and mode changes only update uniforms/CSS. |
| Time | `lib/brain/{clock,timeline}.ts` | One `PlaybackClock` for video, mesh, curves and scrubber. With `hz`, sampling never interpolates across a gap in the producer's timestamps (silent stretches). |
| Data boundary | `lib/brain/{contract,adapter,atlas}.ts` | PRD `SimulationResult` + proposed `meta.cortical` (harness), strict validation, shared display scale, region and group reduction, fixed "known for" list. |
| Backend adapter (read-only) | `lib/brain/backend.ts`, `lib/brain/useBackendRun.ts` | Consumes the backend at `8970609` as it is: SSE log, results, `brain` artifact (float16 `.npy`, `groups.json`). No contract change. |
| Workload choreography | `lib/brain/workload.ts`, `components/brain/useDockChoreography.ts` | Spin/halo/status and ~3 s focus beats from real job events only. |
| Experience | `components/brain/*` | `CanvasBrain` (canvas slot), `BrainCompanion` (entry → dock ⇄ expanded/fullscreen), `EntrySequence`, `PreflightSequence` (analysis focus), `Timeline`, `RegionCard`. |
| Routes | `app/page.tsx` (one `<CanvasBrain />` beside main's `DirectorStudio`), `app/brain/page.tsx` (integration harness) | Main's voice route, API routes and components are unchanged. |

## Canvas integration slot

```tsx
import { CanvasBrain } from "@/components/brain/CanvasBrain";

<CanvasBrain
  projectId={backendProjectId}            // the backend project the canvas shows; omit to stay idle
  selectedVariant={selectedNode?.variant}   // canvas owns selection (controlled)
  onSelectVariant={(v) => selectCanvasNode(v)}
  onEvent={(e) => bus.publish(e)}           // same events as window "preflight:brain"
  entry                                     // once-per-session intro on this surface
/>
```

- `apiBase` defaults to `NEXT_PUBLIC_PREFLIGHT_API_BASE` (a public URL, not a secret). The backend's CORS already allows `http://localhost:3000`; other origins need its `CORS_ORIGINS` setting.
- **Placement and theme** are CSS variables on any ancestor; no brain code needs to change.
  - Compact dock: `--brain-dock-top`, `--brain-dock-left`, `--brain-dock-width`, `--brain-dock-height` (defaults 86 / 20 / 196 / 148 px).
  - Enlarged (hover/pin/focus beat): `--brain-dock-large-top`, `--brain-dock-large-left`, `--brain-dock-large-width`, `--brain-dock-large-height` (defaults: same top/left, 420×306). This lets it move clear of host tools.
  - `--brain-dock-surface` sets the dock background.
  - `--brain-dock-halo` is an RGB triplet for the workload halo. Keep it out of the red-yellow heat range so it is never read as cortical response.
- **PRD v1.6 FLORA layout** (identity top-left, ~52 px floating tool rail left-centre at about y 220–600 on a 1440×900 viewport). Recommended values: `--brain-dock-top: 64px; --brain-dock-left: 14px; --brain-dock-height: 140px; --brain-dock-large-left: 64px; --brain-dock-large-top: 64px`.
  - Checked in headless Chrome with a test-only ghost identity and rail. The compact dock (14–210 × 64–204) ends above the rail. The enlarged/pinned dock (64–484 × 64–370) and the callout to its right never overlap it.
- **v1.6 tokens:** when the host applies `.preflight-theme` (`docs/design/preflight-theme.css`), the dock picks up `--pf-accent` (focus ring, pinned border), `--pf-border`, `--pf-surface`, `--pf-radius-card`, `--pf-font-display` (callout title) and `--pf-font-mono`. Otherwise it falls back to neutral values. The UI accent never touches the cortical heat scale. Typography is inherited from the host; the brain loads no fonts.
- The component renders nothing in flow (`position: fixed` parts only), so the canvas layout is unaffected. With no `projectId`/API base it shows gray anatomy, a slow idle spin and no status line.
- `BrainCompanion` remains available for custom hosts (props: `bindings`, `scenesByVariant`, `videos`, `workload`, `consumeMilestone`, `dockCorner`, `results`, `concepts`, `demoExample`, `brainSim`, …).

## Dock interaction and workload choreography

| State | Trigger (real data only) | Presentation |
| --- | --- | --- |
| Idle | No running step | Slow spin (0.16 rad/s), compact 196×148 px dock |
| Working | An activity `started` without its finish | Brisk spin (0.85 rad/s), halo, status line `"<Step> · Variant X"` |
| Milestone focus | A live (≤30 s old on arrival) `succeeded` event for plan, render, simulate, score, explain or export | ~3 s: spin stops, dock enlarges, callout shows the backend message and duration. Region only for a simulate/score/explain/export event whose variant has a genuine TRIBE artifact: the strongest genuine region, its source sample time and the concept scene at that time. The beat waits up to 2.5 s for that variant's results to load. Otherwise a neutral detail view and, for result steps, "No region shown: no genuine brain data for this video yet." |
| Failed / ended | `failed` event, SSE `end` frame | Halo stops, status shows the backend failure message or "Run complete" |

- **Separation:** job events drive spin speed, halo, status line and camera; they never write cortical values or choose a region. Heat comes only from the bound artifact at the current playback time. A focus beat never seeks or changes playback speed, and the callout says so.
- **Keys:** space, arrows and F apply only in the expanded analysis view; the dock never captures host canvas keys (only Enter/Space/Esc while the dock itself is focused).
- **Control:** hover enlarges the dock. Click, or Enter/Space on the focused dock, pins it, and once pinned clicks select regions. Esc unpins. **Pause motion** stops spin and camera moves. Dragging the brain switches to manual control until **Resume motion**. Reduced motion keeps everything still; beats then show only the text and the region outline.
- **Bounded:** at most 2 queued beats, keeping the newest; SSE ids at or below the last applied are ignored on reconnect. Replayed history doesn't trigger beats.
- **Provenance always visible:** the compact dock shows a **MOCK**, **Demo example · precomputed** or **Precomputed** tag whenever activity is drawn.

## Events and commands

Events out (`onEvent` and `window` `"preflight:brain"`, `lib/brain/events.ts`):

- `entry.started`, `entry.region_focus`, `entry.completed`;
- `analysis.started`, `analysis.lock_on`, `analysis.completed`;
- `mode.changed`, `variant.selected`, `region.selected`;
- `workload.focus` — `{ step, variant, message, region | null, sample_time_s | null, dataMode | null }`, for voice narration of a real milestone;
- `selection.changed` — `{ projectId, runId, variant, time_s, sample_time_s, scene, region, dataMode, mode }`, sent on changes, seeks and pauses, never per frame.

`dataMode` ∈ `none | sim_off | demo_example | genuine | genuine_precomputed | mock`.

Commands in (`window` `"preflight:brain-command"`): `select_variant`, `seek`, `play`, `pause`, `set_mode` (`dock`/`expanded`), `select_region`, `clear_region`, `replay_entry`. For the voice owner after a user-confirmed storyboard change, or for the canvas. In controlled use the canvas keeps selection and passes `selectedVariant`.

**Voice (Gemini Live, ThinkingOrb, VoiceBeam).** These are the Voice owner's. The brain contains no speech, Live or microphone code and never reads audio levels. Main's `useLiveDirector().level` is microphone RMS, so neither the orb nor the brain can treat it as assistant speech. The Director can drive the brain with `preflight:brain-command` and narrate `workload.focus` / `analysis.lock_on` events. Orb/beam/audio are never cortical activity.

## Backend artifact adapter (read-only, proposed)

The backend `SimulationResult` (`8970609`) carries `video_sha256`, `duration_s`, `timestamps_s` and `brain: { mesh: "fsaverage5", n_vertices, activity_path, atlas, groups_path }`. The worker writes little-endian float16 `activity.npy` `[len(timestamps_s), 20484]` (left then right) and a Destrieux `groups.json`, and documents that its timestamps already compensate the 5 s hemodynamic lag. `loadBackendRun()`:

1. GET `/api/projects/{id}/results`.
2. Per variant, download `files["brain-activity"]` (and `files["brain-groups"]` when present) from the backend's allow-listed files route.
3. Parse `.npy` (`<f2`/`<f4`, C order).
4. **Reject, never repair** when:
   - the simulator isn't `tribe_v2`, or there is no brain artifact;
   - the mesh isn't fsaverage5 or the vertex count isn't 20,484;
   - the result's `video_sha256` differs from the render record;
   - timestamps aren't strictly increasing;
   - the array shape doesn't match the timestamps;
   - any value is non-finite.
5. Bind with timestamps unchanged (`alignment: "stimulus_time"`, no second lag shift), keeping `hz`, the hash and the worker groups.

**Atlases are kept distinct.** The worker's Destrieux groups (visual/auditory/language) drive the meters and curves, labelled `worker groups · <atlas>`. Region picking, cards and focus beats use the viewer's Desikan-Killiany labels, labelled as such. Neither is presented as the other.

**Still to agree with the backend owner:**
- whether this client-side adapter is acceptable or a server-side endpoint should serve a narrower payload;
- concept-scene timing for "on screen" text;
- the precomputed/demo bundle shape;
- how canvas node IDs map to project/variant/job IDs.

Observed blocker: `create_app` defaults to `run_service=None` (`POST /run` → 503), and there is no editable PLANNED checkpoint/API, so pre-render storyboard editing needs an agreed draft/approval seam (not a brain concern).

The earlier proposal `meta.cortical` v0 (float32 JSON/base64/URL, Desikan groups) remains supported only for the `/brain` harness and is superseded for backend data by the adapter above.

## Presentation rules (implementation choices, PRD §15 rule 8)

- **Interpolation:** linear between genuine samples; edge samples held for at most one period; with `hz`, gaps longer than 1.5 periods are not bridged. Source timestamps are shown in the dock, the region card and the sample table.
- **Display scale:** one scale per compared set (p99 of positive values pooled across variants; threshold 35 %). Values below threshold and non-positive values stay gray. It is not a score.
- **Words:** "predicted cortical (fMRI-like) response", never EEG, emotion, desire, buying intent or attention guarantees. A unit test guards the fixed known-for list.

## Verification status (3 Oct 2026, cloud VM, headless Chrome + SwiftShader, 1440×900)

- **Checks:** `npm run typecheck`, `npm run lint` and `npm test` (36 vitest tests: 30 brain, 6 voice) pass; `npm run build` passes; `npm audit --omit=dev` reports 0.
- **Previously verified views:** entry/dock/expanded/fullscreen, orbit/zoom/reset, regions, surfaces/hemispheres, keys/scrub, video-master sync, analysis focus, Skip, reduced motion, ingestion/validation.
- **Main route:**
  - the top-left dock beside the Director, hover enlarge, keyboard pin/unpin;
  - **the real backend app at `8970609` (uvicorn) streaming a scripted test activity log** through `/api/projects/{id}/log`:
    - working spin and halo;
    - three 3 s milestone beats with backend text;
    - a simulate beat with "No region shown";
    - failure → idle; clock unchanged.
  - **a MOCK-flagged TRIBE artifact served by the backend files route:**
    - float16 `.npy` adapted;
    - dock tag MOCK;
    - region beat on the strongest MOCK region at its sample time;
    - `workload.focus` event emitted.
  - No console errors.
- **Not verified:**
  - genuine TRIBE output;
  - a real backend run (no run service configured);
  - real Gemini Live audio or orb integration;
  - the Dashboard flow canvas (v1.6 design) integration;
  - MacBook/GPU performance;
  - FR-15 (P1).

### PRD v1.6 visual pass (3 Oct 2026)

**Removed or changed against the FLORA quality bar:**
- the blue pulsing workload halo is now a static neutral border with an accent status dot;
- the HUD corner brackets and the blurred glass panels are gone;
- brain titles use the host display face (Redaction through `--pf-font-display`).

**Embedded expanded view:**
- anatomy, video, timeline and region detail only; the canvas owns the verdict and variants;
- a visible **Back to canvas** button;
- "About this view" collapsed;
- expanding eases to the reference profile pose;
- the empty state is one line above the anatomy.

**Captured at 1440×900** on a test-only FLORA host simulation (`.context/v16-*.png`): docked, pinned, expanded no-data and selected region. No console errors.

**Remaining mismatches, not claimed as done:**
- The expanded view still uses boxed timeline/region panels rather than FLORA's floating minimal controls. Final shell styling should be agreed with Dashboard.
- Region outlines follow fsaverage5 mesh edges, so they look jagged at close range.
- The entry title uses the host face only when `.preflight-theme` is applied; this branch doesn't load the Redaction files (docs PR #1 owns them).
- Genuine activity has not been seen, because none exists.

### Minimum interface, complete capability (Specific/Sana-like editing pass)

**At rest:** the dock shows only the brain and one caption, `A · 0:00.0 · No brain data`. The caption carries variant, playback time and data mode, with MOCK as a red pill. While real work runs, a single status line is added.

**Enlarged (hover/pin/keyboard):**
- one primary action, **Expand**;
- quiet **Pause/Resume motion**;
- **Unpin** only when pinned.

Replay, Reset view and the duplicate data chip left the dock. Replay and Reset live under **More** in the expanded view; double-click reset still works.

**Expanded:**
- anatomy, controls and timeline;
- region details appear only after a region is clicked;
- the stage meters were removed because they repeated the timeline legend values;
- no empty "No variant video" frame;
- the no-data message appears once, as one line;
- "About this view" sits in the timeline footer on demand.

**Always visible:**
- selected variant, time and data mode;
- MOCK/precomputed labels;
- the legend whenever activity is drawn;
- Back to canvas, Fullscreen, and Variant/Surface/View controls.

Everything works by click and keyboard, not hover only.
