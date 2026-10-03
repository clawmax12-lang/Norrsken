# Opus 5.5 — browser brain implementation brief

**Product:** Preflight, desktop-browser web platform, PRD v1.6. **Requested agent:** Claude Opus 5.5. **Scope:** FR-12 and FR-14; FR-15 only after all applicable P0 acceptance criteria pass. Read [AGENTS.md](../../AGENTS.md), [PRD.md](../../PRD.md) §15/§8/§9/§10/§12, [TEAM.md](../../TEAM.md), the entire [visual reference baseline](README.md), [canvas/voice integration brief](CANVAS_VOICE_BRIEF.md) and [clean-flow layout](CLEAN_FLOW_DESIGN.md) before implementing.

## Outcome

Build the complete interactive brain experience in the existing Next.js/React/TypeScript frontend. The supplied anatomical brains and head silhouettes are the quality reference. The end result must make the relationship between the video, cortical response, time and selected region immediately visible in a browser.

Start from the existing Dashboard web branch, inspect its current layout and preserve its navigation/brief flow. Own the brain component and its scene code; do not overwrite another owner's dashboard, results, pipeline or worker files. Add only the necessary routing/integration surface and describe it in the handoff.

**v1.4 handoff:** Dashboard is now building the flow canvas. Your reusable viewer must support entry hero → persistent corner dock → expanded selected-variant analysis/fullscreen with shared selection/time. Quality of anatomy, materials and purposeful cinematic framing is important: match the original brain references, not a generic blob or icon. The new canvas screenshot defines workspace structure, not brain geometry. Preserve Dashboard's canvas work and coordinate the integration seam; do not rebuild its graph or the voice owner's service.

**v1.5 integration update:** two-way female Gemini Live is mandatory FR-16/P0, owned by the existing Voice workspace. Agree selection/project/variant/scene/time and entry/dock events with Dashboard/Voice so validated spoken storyboard changes update shared state. Preserve anatomy quality and exact-video evidence; a changed draft/video cannot keep another artifact's brain response. Keep the standalone voice orb separate from the brain; do not implement a second speech service or scheduler. TTS-only is no longer P0 acceptance.

**v1.6 design update:** FLORA/reference 08 is the owner's exact main-layout target: black dotted open canvas, narrow floating left tools and compact corner actions. Preserve your anatomy/dock/adapter work while coordinating the shell with Dashboard. Use supplied Redaction/warm orange-red identity; no radial universe, lime theme or panel-heavy Director landing. Brain stays top-left below project controls, with hover/keyboard pin; actual milestone → roughly three-second slower camera/text → resume, without changing video/sample time. Voice owner integrates both [orb and prompt beam](DIRECTOR_VISUALS.md), reusing actual Live input/output state; no competing audio service.

## Build once, bind data repeatedly

This is a one-time product-development assignment, not an LLM-generated brain per user or video. Build a reusable typed viewer component, share/cache immutable geometry and atlas assets, and keep each instance's activity data separate. An A/B view duplicates the component, not anatomy generation or model inference. Playback, orbit and scrubbing must not invoke Gemini, Opus or TRIBE.

Your Conductor coding-agent role is separate from the planned runtime Opus final-video composition in PRD §9.1. Do not build that video pipeline, connect billable model calls or wait for a Gemini key to implement the mesh/controls. Implement the honest no-data viewer now; integrate genuine response data when the worker contract is available.

## Mesh, materials and data

- Integrate a real `fsaverage5` cortical mesh, including normal/inflated surfaces and correct hemisphere/vertex mapping. Record where the geometry and atlas come from and their licensing/attribution. A plausible sculpted brain with incompatible vertices cannot display TRIBE values accurately.
- Opus owns the rendering code: neutral gray anatomical material, lighting, depth, restrained silhouette, activity shader, selection effects, camera and animation. Use the project's web stack/three.js; do not substitute a screenshot or looping video for an interactive brain.
- Consume the agreed `SimulationResult` boundary. Coordinate the mesh IDs, vertex order, atlas mapping and segment times with the worker/results owners before changing shared contracts. Do not implement a second provider-specific neuroscience API inside the UI.
- Use real cortical values and atlas-backed region series when supplied. Interpolate the 1 Hz values for smooth presentation; preserve the actual source timestamps. Label them predicted cortical/fMRI response, not measured EEG "brain waves".
- With no data, the full mesh/controls may be developed, but show **No brain data**, no active meters, no invented curves or changing activation. Precomputed output must belong to the displayed video and carry the required label.

## FR-12 — interactive viewer and dock (P0)

- A/B/C variant selector; Normal/Inflated surface; Closed/Open hemispheres.
- The reference-quality anatomical brain is the core asset: detailed folds, restrained silhouette and convincing profile/depth. Keep the code/geometry reusable; avoid a per-run generative scene.
- Drag orbit, wheel zoom, double-click reset and a useful default profile framing.
- Select a region and show its atlas-derived name, fixed hand-checked "known for" description, current time and the scene actually visible at that time.
- One source of truth for time: video, mesh, curves and scrubber follow the same playback position. Implement space to play/pause, arrows to step one second and F for fullscreen.
- Fullscreen is stage-ready: large brain, small floating video, bottom controls, visible legend/time and region information.
- Add persistent corner mode identifying variant, time and data mode, with Expand/return-to-dock. Do not recreate geometry or trigger inference when moving between views. Gray anatomy remains available if live TRIBE is off; actual activity remains conditional on genuine data.
- Keep the result recommendation accessible. The spectacle cannot hide which variant the user should test next.

## FR-14 — entry and analysis Preflight sequence (P0)

Implement first-entry brain reveal/orbit/region focus → corner dock → canvas once per browser session, with Skip/reduced motion and explicit replay. Camera/material motion can run on gray anatomy. Before a user run, colored waves require a genuine video-matched example with visible "Demo example · precomputed" disclosure; no such bundle means "No brain data", not random response.

For genuine run data, preserve PRD §12.2's analysis beats: dim → assemble → watch → lock on → hand over to the canvas inspector/corner dock, once per run. Preload actual results. Missing live TRIBE keeps anatomy/entry/dock but follows the no-data/Brain-sim-off rules. The two-way female Gemini Live Director is mandatory FR-16, implemented by the voice owner; expose entry/completion/selection events without adding a competing speech service here.

## FR-15 — compare and difference (P1)

When the P0 gate permits it, two variants show synchronized video times and matched camera framing. Use a consistent activity normalization and visible shared legend; independent auto-scaling can make an unchanged response look different. A true difference view displays B minus A only for compatible mesh mappings and aligned timestamps, with a diverging legend.

These compare predicted variants, not actual/predicted measurements. More activation is not inherently a better ad. Explain the change separately from the goal-aligned recommendation.

## Verification and handoff

- Verify the app build using the current project's actual scripts and inspect the browser for console errors. Keep README run steps correct.
- Exercise empty/no-data, genuine-data, scrub, variant change, region click, camera reset, fullscreen, Skip and reduced-motion paths. If genuine data is unavailable, clearly report which AC remain unverified; do not use a test fixture as the demo's scientific output.
- Capture screenshots/video in the workspace's `.context/` and share a browser preview. Check a desktop viewport at least 1440 px wide; record performance on available hardware without claiming a MacBook test that was not run.
- Keep the work in its own branch and open a small PR with FR IDs, verification evidence and any shared-contract decisions. Do not merge or redeploy the existing Dashboard without coordination.
- Update TEAM.md with the workspace/branch, changed components, preview, remaining TRIBE dependency and handoff. A browser renderer does not imply the GPU worker, ranking or entire product is complete.
