# Brain companion — implementation and integration seam (FR-12, FR-14)

Implementation notes for the reusable browser brain built by Claude Opus 5.5 on `conductor/3d-brain-opus-55`. [PRD.md](../../PRD.md) stays authoritative; this file documents what exists and the **proposed** contracts other owners consume. Nothing here is agreed with the TRIBE worker, canvas or voice owners until they confirm it (record that in TEAM.md and PRD §16).

## What is built

| Piece | Files | Notes |
| --- | --- | --- |
| Anatomy assets | `public/brain/fsaverage5/*`, `public/brain/head/*`, `scripts/brain/*` | fsaverage5 pial + inflated, sulc/curv, Desikan-Killiany labels, TRIBE vertex order. Original head silhouette. Provenance: [`public/brain/ATTRIBUTION.md`](../../public/brain/ATTRIBUTION.md). |
| Shared geometry | `lib/brain/assets.ts`, `lib/brain/geometry.ts` | Loaded once per session (one manifest + one 0.9 MB binary), geometry built once and cached; every view reuses the same `BufferGeometry`. |
| Renderer | `lib/brain/scene.ts`, `lib/brain/materials.ts`, `lib/brain/head.ts`, `lib/brain/activityTexture.ts` | Sculpted gray cortex (sulcal shading, cavity, facet normals, camera-locked studio light + rim), thresholded heat overlay, atlas-outlined selection, normal↔inflated morph, closed/open hemispheres. Each bound result is packed once into a float texture; playback/orbit/variant change only update uniforms. |
| Time | `lib/brain/clock.ts`, `lib/brain/timeline.ts` | One `PlaybackClock` for video, mesh, curves and scrubber; the attached video is master while playing. |
| Data boundary | `lib/brain/contract.ts`, `lib/brain/adapter.ts`, `lib/brain/atlas.ts` | PRD `SimulationResult` + proposed `meta.cortical` v0, strict validation, shared display scale, region/group reduction, fixed "known for" list. |
| Experience | `components/brain/*` | `BrainCompanion` with entry hero → corner dock ⇄ expanded analysis/fullscreen; `EntrySequence`; `PreflightSequence` (analysis focus); `Timeline`; `RegionCard`. |
| Route | `app/brain/page.tsx` | `/brain` harness: canvas placeholder, local loaders, URL parameters, emitted-event log. The real canvas lives on the Dashboard branch. |

## Presentation modes (PRD v1.4 §12.2/§12.3)

One mounted `BrainScene` moves between modes via CSS; anatomy is never rebuilt and variant, time, surface and selection persist.

- **entry** — first arrival once per browser session (`sessionStorage["preflight.entry.played"]`), ~12 s: wireframe-to-shaded reveal inside the head, slow orbit, camera push into the right superior temporal gyrus (fixed atlas region, labelled as anatomy), pull back, dock. Skip always visible; reduced motion uses fades and static framing. Replay is explicit.
- **dock** — 372×266 px corner view showing variant, video time, nearest genuine sample time, data mode chip, Expand and Replay. Orbit and region click still work.
- **expanded** — the full analysis view: stage with bottom pills (Variant · Surface · View), floating video, meters, legend, timeline with curves, region card; F for stage-ready fullscreen, Esc returns to the dock.
- **analysis focus** — PRD §12.2 beats (dim → assemble → watch → lock on → hand over), at most once per run (`localStorage["preflight.analysis.played:<runId>"]`), only auto-started for this run's genuine data, ending in the dock.

## Embedding API (for the Dashboard canvas)

```tsx
import { BrainCompanion } from "@/components/brain/BrainCompanion"; // relative import in this repo

<BrainCompanion
  projectId={project.id}
  runId={run.id}                      // analysis focus plays once per run id
  results={run.simulationResults}     // SimulationResult[] from the backend; non-cortical ones are ignored
  concepts={run.concepts}             // CreativeConcept[]: variant_id + scenes for "what is on screen"
  videos={{ A: urlA, B: urlB, C: urlC }} // the exact analyzed MP4s
  brainSim={tribeAvailable ? "available" : "off"}
  demoExample={exampleBundle}         // optional, see below
  selectedVariant={selectedNode.variantId}   // canvas owns selection
  onSelectVariant={(v) => selectCanvasNode(v)}
  onEvent={(e) => voiceAndCanvasBus.publish(e)}
/>
```

Without `harness`, the component renders no top bar or canvas; it shows the entry fullscreen, then docks in the corner over the host, and the expanded view is a fixed overlay. Install note: it needs `three` (already added to `package.json` on this branch).

### Events out — `onEvent` and `window` `"preflight:brain"` (`lib/brain/events.ts`)

| Event | When | Typical consumer |
| --- | --- | --- |
| `entry.started` `{replay, dataMode}` / `entry.region_focus` `{region}` / `entry.completed` `{skipped}` | Entry lifecycle | Voice welcome timing; canvas reveal after completion |
| `analysis.started` / `analysis.lock_on` `{region, time_s}` / `analysis.completed` `{skipped}` | Analysis focus | Voice can narrate the genuine lock-on; canvas reveals the result inspector on completion |
| `mode.changed` `{mode}` | entry / dock / expanded | Canvas layout |
| `variant.selected`, `region.selected` | User changes | Canvas node highlight |
| `selection.changed` `{selection}` | Variant/region/mode/data change, seek, pause — never per frame | Voice "what am I looking at" context |

`selection` = `{ projectId, runId, variant, time_s, sample_time_s, scene: {index, t_start, t_end, text} | null, region: {hemi, atlasName, name} | null, dataMode, mode }`. `dataMode` ∈ `none | sim_off | demo_example | genuine | genuine_precomputed | mock`, so narration can never present anatomy, a demo example or a MOCK fixture as the user's tested result.

### Commands in — `window` `"preflight:brain-command"`

`select_variant {variant}`, `seek {time_s}`, `play`, `pause`, `set_mode {mode: "dock" | "expanded"}`, `select_region {hemi, atlasName}`, `clear_region`, `replay_entry`. Intended for the canvas, or for the voice owner **after the user confirms** a change. In controlled use the canvas keeps selection state and passes `selectedVariant`; the brain reports requests through `onSelectVariant` rather than holding a competing copy. The brain contains no speech, Live, scheduling or inference code; voice/orb audio is never cortical activity.

## Proposed cortical payload — `SimulationResult.meta.cortical` (v0, not yet agreed)

Top-level PRD §10.3 keys are unchanged; TRIBE's arrays travel in `meta.cortical`:

```json
{
  "variant_id": "A", "simulator": "tribe_v2", "version": "<checkpoint/config revision>", "hz": 1,
  "series": {}, "events": [], "precomputed": false,
  "meta": {
    "video": { "url": "/runs/<id>/A.mp4", "duration_s": 15, "sha256": "<exact analyzed bytes>" },
    "cortical": {
      "schema": "preflight.cortical.v0",
      "mesh": "fsaverage5",
      "vertex_order": "nilearn-fsaverage5:left-then-right",
      "n_vertices": 20484,
      "n_timesteps": 15,
      "times_s": [0, 1, 2, "…"],
      "hemodynamic_alignment": "stimulus_time",
      "units": "predicted BOLD (model units)",
      "values_url": "/runs/<id>/A.cortical.f32"
    }
  }
}
```

- Values are TRIBE's `preds` (`[n_timesteps][20484]`), row-major, unmodified, as exactly one of `values` (JSON rows), `values_f32_b64` (little-endian float32) or `values_url` (same-origin raw float32, recommended: 15 × 20,484 × 4 B ≈ 1.2 MB).
- `times_s[i]` is the video time sample *i* describes, from TRIBE's returned segments. Set `hemodynamic_alignment` to `stimulus_time` if the worker already compensated the hemodynamic lag (upstream documents ~5 s) and `acquisition_time` otherwise, so nobody shifts twice. The viewer does not shift.
- The adapter rejects (never repairs) a wrong mesh/order/vertex count, non-increasing or mismatched times, non-finite values or multiple/missing value sources, and reports the reason.
- `precomputed: true` is shown as "Precomputed". `meta.mock: true` is reserved for test fixtures and always renders a MOCK banner.

**Demo example (first arrival, before the user's run):** same format with `precomputed: true` and `meta.demo_example = { title, video_url, scenes? }` naming the genuine example video. Anything else is rejected. It is labelled "Demo example · precomputed" and disappears as soon as the run has cortical data. No such bundle exists in the repository today, so the entry runs on gray anatomy with "No brain data".

## Presentation rules (implementation choices, PRD §15 rule 8)

- **Interpolation:** linear between genuine samples; the edge sample is held for at most one sample period; beyond that no activity is drawn. Source timestamps are shown (region card, dock, sample table).
- **Display scale:** one scale for all variants shown together: `vmax` = 99th percentile of positive values pooled across bound variants, threshold = 35 % of `vmax`; values below threshold and all non-positive values stay gray. Not a score.
- **Regions:** Desikan-Killiany (34 regions per hemisphere) for picking, cards and lock-on; TRIBE's own ROI helpers use HCP-MMP1, which is too fine for a hand-checked list. Meter groups: Visual (pericalcarine, cuneus, lingual, lateral occipital, fusiform, inferior temporal), Auditory (transverse and superior temporal), Language (pars opercularis/triangularis/orbitalis, banks of STS, middle temporal), both hemispheres, vertex-weighted means. Group/lock-on values are deterministic reductions of the bound values.
- **Words:** "predicted cortical (fMRI-like) response", never EEG, emotion, desire, buying intent or attention guarantees; a unit test guards the known-for list.

## Verification status (3 Oct 2026, cloud VM)

Checked: `npm run build`, `npx tsc --noEmit`, `npm test` (19 tests); headless Chrome 1440×900 with SwiftShader software WebGL — entry hero/dock, expanded view, orbit/zoom/double-click reset, region click, surface and hemisphere toggles, arrows/space/scrub, video-master sync with a locally generated test MP4, fullscreen, analysis focus, Skip, reduced motion, `?sim=off`, URL/file ingestion and validation errors; no console or WebGL errors on these paths. Activity rendering was exercised **only with the visibly labelled MOCK fixture**.

Not verified: genuine TRIBE output (none available), a genuine demo-example bundle, real-GPU/MacBook performance (SwiftShader only), integration into the Dashboard canvas or voice service, FR-15 compare/difference (P1, not started beyond shared clock/camera/scale interfaces).
