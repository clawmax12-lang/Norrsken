# Preflight — clean black flow canvas

Approved owner direction, 3 Oct 2026. Implements [PRD v1.6 §12](../../PRD.md#12-ui-and-the-analysis-intro); this brief does not change pipeline scope. **Primary design reference: [FLORA](https://flora.ai/) and the owner's [FLORA workspace screenshot, reference 08](README.md#reference-08--flora-primary-product-layout).** References [06/07](README.md#references-06-and-07--clean-flows-and-dark-canvas) remain supporting flow references. The old radial/sidebar layout is superseded, not the brain anatomy references.

## Design in one sentence

A quiet black dotted workspace where real product screenshots become readable storyboard branches, playable videos, simulated comparisons and one clear launch recommendation — with a cinematic brain and a conversational Director as companions.

## Main layout

- Full-viewport `#0A0A0A` canvas; faint neutral dot grid about 24 px apart. Preserve generous open space and fit the initial three lanes to the desktop viewport.
- Top-left: small Preflight/project identity; brain companion sits below it with room for hover/pin enlargement. No permanent navigation sidebar or full-width dashboard header.
- Top-right: compact actual run/status/actions; Export becomes available only with real files. Do not copy account, share or template-management features from the reference.
- Left-center: a narrow floating vertical tool pill, approximately 48–56 px wide (add/upload, assets, select, pan, fit/search). This is a lightweight tool rail on the canvas, not a navigation sidebar. Only implement actions the product actually supports.
- Bottom-center: a compact prompt with the customized VoiceBeam. The standalone Director orb sits just above/alongside it, with separate captions and accessible mic/mute/stop controls. No giant chat card.
- Bottom-left: zoom/fit controls. On-demand inspector for the selected brief, storyboard, result or transcript; close it without losing canvas position or selection.
- Bottom-right: small queue/activity control if backed by real job state, not a persistent log panel or an invented active-job count.

Match FLORA's spatial hierarchy, light-touch chrome, open black dot grid and content-first cards. Use Preflight branding/Redaction/orange-red; do not import FLORA's logo or generated marketing assets. The survey visible in the supplied screenshot, upgrade/share/team features and external Claude/ChatGPT/Grok launch buttons are not our product scope. Empty state is our own short upload/Enable Live invitation, disappearing as actual source nodes arrive. The homepage is visual inspiration, not a request to build an extra marketing site today.

## Branches, not a radial universe

```text
                     ┌─ Storyboard A → Video A → Pretest A ─┐
Product + sources ───┼─ Storyboard B → Video B → Pretest B ─┼─ Recommendation → Export
                     └─ Storyboard C → Video C → Pretest C ─┘
```

Use left-to-right curved connectors and vertically spaced A/B/C lanes. A storyboard card contains its 4–6 source-backed scenes; expanding it reveals detail rather than spawning many unrelated videos. The pretest contains actual TRIBE/Gemini evidence, including unavailable states. This is simulated comparison; live audience A/B confirmation and P1 synchronized brain difference are separate.

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

The interface is predominantly neutral. No lime theme, rainbow panels, always-glowing borders, constant particle storms or walls of telemetry. High-tech polish comes from excellent transitions and truthful interactions. The UI accent is separate from the brain's scientifically normalized heat/difference scales.

## Cinematic companions

Opus builds the reusable brain once. Entry → top-left dock → hover/pin/expand. Actual meaningful milestone → approximately three seconds of slower camera/detail with concise text → resume. Manual inspection wins; reduced motion keeps information without camera rushes. Do not slow the video or invent neural activity while work runs.

The Director uses both requested Libraries.dev effects, adapted to our warm palette. Details, exact package APIs and a controlled integration example are in [DIRECTOR_VISUALS.md](DIRECTOR_VISUALS.md). Gemini Live remains the two-way voice provider; these packages provide only presentation.

## Frontend handoff and acceptance

Dashboard owns the shell/graph; Voice owns Live/audio/tool lifecycle; Opus owns anatomy/dock/adapters. Preserve their services, assets, API clients and event contracts. Implement the shell around one shared draft/selection/run store, not three competing apps. No automatic PR merges.

At 1440 px wide, verify: readable three-lane initial flow; no permanent sidebar; quiet dark dots; warm restrained selection; Redaction loaded; node selection/pan/zoom/fit; on-demand evidence and reachable verdict/export; brain enlargement does not obscure actions; orb/glow follow real audio/work; keyboard focus, captions, mic/mute/stop and reduced motion work. Check empty, queued, failed and unavailable states as well as actual results. Capture the new preview separately from old prototype screenshots.

Relay to the existing frontend owner:

> Read PR #1's PRD v1.6 and docs/design/CLEAN_FLOW_DESIGN.md + DIRECTOR_VISUALS.md. FLORA (flora.ai and reference 08) is William's exact primary layout target: black dotted canvas, narrow floating left tools, compact corner controls and readable left-to-right source → A/B/C storyboard → video → pretest → verdict branches. Replace the radial/sidebar/panel-heavy shell. Use the supplied Redaction WOFF2 files and orange-red tokens. Embed the existing Opus top-left brain and Gemini Live orb/beam; preserve all existing Live, draft, source, backend and job logic. No FLORA branding/survey/external-agent buttons, extra mic/service, fake neural response or unbounded runs. Verify desktop interactions, real visual-state binding and publish a fresh preview. Coordinate overlapping integration files before editing.
