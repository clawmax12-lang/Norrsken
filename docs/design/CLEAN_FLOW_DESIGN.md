# Preflight — clean black flow canvas

Approved owner direction, 3 Oct 2026. Implements [PRD v1.7 §12](../../PRD.md#12-ui-and-the-analysis-intro). [Existing-video correction](PRODUCT_RESET_HANDOFF.md) supersedes screenshots-first. **Primary reference: [FLORA](https://flora.ai/) / [reference 08](README.md#reference-08--flora-primary-product-layout).** References 06/07 support flows; original brain references still define anatomy.

## Design in one sentence

A quiet black dotted workspace where an existing company video becomes a baseline analysis, grounded edit branches, playable candidates, new pretests and one recommendation with an original comparison — accompanied by cinematic brain and Gemini Live.

## Minimum interface, complete capability

Owner principle: "Great design is achieved not when there is nothing more to add, but when there is nothing left to take away." Treat this as an editing discipline, not permission to remove required functionality. FLORA remains the layout target; the [Specific screenshot](README.md#reference-09--specific-restraint-and-readable-connections) and the owner's Sana-like direction reinforce quiet hierarchy, precise type and progressive disclosure.

The default view must answer **what am I making, what is happening, and what can I do next?** Prioritize the current content/selected path and one primary action appropriate to the stage. Full logs, transcripts, technical metadata, detailed reasons and advanced controls remain available on demand, with a clear return to the canvas. No panel opens merely to fill empty space.

| Context | Primary visible content / action | Detail on demand |
| --- | --- | --- |
| Empty project | Short existing-video upload/drop invitation, Enable Live; no empty scene tree | Validated facts/audience/goal and help |
| Storyboard review | Readable source/hook/scene cards and A/B/C choices; approve the bounded Run | Full scene editor, source traceability |
| Actual work | Real running node/status and current path | Persisted log, retries, durations |
| Result | Recommended video, short evidence-backed reason, runner-up and Export | Curves, full explanations, detailed brain analysis |

Compact status-only nodes can stay compact; show media where it helps recognize or compare content. Brain and voice are quiet companions at rest and expand for intentional interaction. Keep one accent hierarchy, consistent spacing/icons and readable neutral typography. Do not use extra badges, duplicated summaries, tooltips or glowing decoration to make the interface appear more sophisticated.

Minimalism must not hide active microphone/privacy state, mute/stop, failures, job confirmation, selected variant/time or no-data/precomputed labels. Required brain legends/evidence remain visible when their view is open. Details must work with click/keyboard, not hover alone. Every persistent element should justify itself through the current decision, navigation, safety or evidence; otherwise remove it or reveal it contextually.

## Main layout

- Full-viewport `#0A0A0A` canvas; faint neutral dot grid about 24 px apart. Preserve generous open space and fit the initial three lanes to the desktop viewport.
- Top-left: small Preflight/project identity; brain companion sits below it with room for hover/pin enlargement. No permanent navigation sidebar or full-width dashboard header.
- Top-right: compact actual run/status/actions; Export becomes available only with real files. Do not copy account, share or template-management features from the reference.
- Left-center: a narrow floating vertical tool pill, approximately 48–56 px wide (add/upload, assets, select, pan, fit/search). This is a lightweight tool rail on the canvas, not a navigation sidebar. Only implement actions the product actually supports.
- Bottom-center: compact prompt/VoiceBeam and small inactive Director orb. During engaged conversation, the same standalone orb moves/enlarges centrally; separate captions and mic/mute/stop controls remain reachable. No giant chat card; no second voice engine.
- Bottom-left: zoom/fit controls. On-demand inspector for the selected brief, storyboard, result or transcript; close it without losing canvas position or selection.
- Bottom-right: small queue/activity control if backed by real job state, not a persistent log panel or an invented active-job count.

Match FLORA's spatial hierarchy, light-touch chrome, open black dot grid and content-first cards. Use Preflight branding/Redaction/orange-red; do not import FLORA's logo or generated marketing assets. The survey visible in the supplied screenshot, upgrade/share/team features and external Claude/ChatGPT/Grok launch buttons are not our product scope. Empty state is our own short upload/Enable Live invitation, disappearing as actual source nodes arrive. The homepage is visual inspiration, not a request to build an extra marketing site today.

## Branches, not a radial universe

```text
                                      ┌─ Edit A → Video A → Retest A ─┐
Original + facts → Baseline analysis ──┼─ Edit B → Video B → Retest B ─┼─ Compare original → Recommend/export
                                      └─ Edit C → Video C → Retest C ─┘
```

Use left-to-right curved connectors and spaced A/B/C lanes after real intake/planning. Original is playable with actual duration; baseline evidence precedes edit hypotheses. Storyboards contain 4–6 grounded scenes/source clips, expanded on demand. Retest has exact-output TRIBE/Gemini evidence, including unavailable states. Source/output time mapping survives edits. Simulation comparison is not live audience A/B or P1 dual-brain difference.

Start with readable cards, roughly 220–280 px wide, 12–16 px radii and ample lane spacing. Source cards show real media; storyboard cards show the hook and scene strip; video cards open actual playable MP4s. Relevant metadata: variant ID, duration, hypothesis and written state. Proposed plans remain clearly untested. No tiny anonymous dots, fake score thumbnails, unsupported test counts or exploded 156-node initial view.

Inactive connectors are muted; the selected path uses restrained orange-red. An actual running node may have a subtle status/connector animation, never animation presented as a completed result. At distant zoom reduce card detail; zooming back restores the actual content and IDs.

## Identity and restraint

Shared ready-to-import assets: [Redaction font handoff](../../public/fonts/redaction/README.md) and [opt-in CSS tokens](preflight-theme.css). Import tokens into the existing frontend stylesheet and apply `.preflight-theme` to its root; do not replace another owner's stylesheet wholesale.

| Element | Token / treatment |
| --- | --- |
| Canvas / cards / border | `#0A0A0A` / `#151515` / `#2A2A2A` |
| Primary / secondary text | `#F3EFE9` / `#ABA7A2` |
| Selection, active path, primary action | `#FF5A36`, dark text on filled buttons |
| Identity, headings, storyboard titles | Clean Redaction; limited Redaction20 for large expressive text |
| Dense controls, forms, transcript | Existing readable sans; monospace for time/technical IDs |

Do not set tiny controls in heavily distressed Redaction variants. Orange-red on the canvas has about 6.38:1 contrast; off-white on the canvas about 17.28:1. Small white text on an orange-red fill is only about 3.10:1, so use dark text. Thin decorative borders do not replace visible focus rings. Exact dimensions/tokens are logged implementation choices, not new scientific claims.

Predominantly neutral: no lime, rainbow panels, constant glow/particle storms or telemetry walls. A localized multicolor **voice beam** is allowed by v1.7; not rainbow cards or cortical response. UI accent and scientific scales remain distinct.

## Cinematic companions

Opus builds once. Seamless full-viewport entry (host hidden/inert, scroll locked, Skip during loading) → same top-left dock → hover/pin/expand. Real milestone → three-second slower camera/detail/text → resume. Manual inspection/reduced motion wins. No invented neural activity or altered video/sample time. Intro color needs genuine disclosed matched example; absence is a data dependency.

The Director uses both requested Libraries.dev effects, adapted to our warm palette. Details, exact package APIs and a controlled integration example are in [DIRECTOR_VISUALS.md](DIRECTOR_VISUALS.md). Gemini Live remains the two-way voice provider; these packages provide only presentation.

## Frontend handoff and acceptance

Dashboard owns the shell/graph; Voice owns Live/audio/tool lifecycle; Opus owns anatomy/dock/adapters. Preserve their services, assets, API clients and event contracts. Implement the shell around one shared draft/selection/run store, not three competing apps. No automatic PR merges.

At 1440 px wide, verify: readable three-lane initial flow; no permanent sidebar; quiet dark dots; warm restrained selection; Redaction loaded; node selection/pan/zoom/fit; on-demand evidence and reachable verdict/export; brain enlargement does not obscure actions; orb/glow follow real audio/work; keyboard focus, captions, mic/mute/stop and reduced motion work. Check empty, queued, failed and unavailable states as well as actual results. Capture the new preview separately from old prototype screenshots.

Relay to the existing frontend owner:

> Read PRD v1.7, PRODUCT_RESET_HANDOFF.md, CLEAN_FLOW_DESIGN.md and DIRECTOR_VISUALS.md. Existing company video is main input: Original → baseline analysis → three candidate-edit/video/retest lanes → comparison/recommendation/export. FLORA reference08, black dots, Redaction, minimal floating tools/orange-red. Empty state is upload, not empty scenes. Embed the same Opus full-viewport-entry/top-left brain and Gemini Live orb (central conversation/bottom idle)/VoiceBeam. Preserve services but migrate contracts with owners; test ACTUAL ROUTE, not injected fixture, publish fresh preview. No fake response/results, extra mic, unlimited runs or automatic merges.
