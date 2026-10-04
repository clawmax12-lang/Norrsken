# Preflight · Product Requirements Document

**Version:** 1.7.1 · **Date:** 3 Oct 2026 · **Status:** Hackathon build ({Tech: Europe} Agentic AI Hack, Norrsken Stockholm)

**Owner:** William (product) · **Tech owners:** see §14.3 and [TEAM.md](TEAM.md)

**Repository:** https://github.com/clawmax12-lang/Norrsken

**Built with (PRD plan):** Claude Opus 5.5 as the coding agent · Gemini · Condense · TRIBE v2 (Meta FAIR, research use)

> This is the team's canonical, editable product specification. It supersedes earlier brainstorming and advisor briefs. The baseline was imported from the complete, 20-page [Preflight PRD v1.1.pdf](docs/source/Preflight-PRD-v1.1.pdf), which is preserved unchanged; see [source provenance](docs/source/README.md). Versions 1.2–1.7.1 incorporate subsequent product-owner decisions in §16. Actual implementation progress lives in [TEAM.md](TEAM.md), not in these requirements.

**What changed in 1.7.1 — integrated release:** preserve v1.7’s approved existing-video product direction while adopting the owner’s later bottom-only voice correction and FR-17 Opus finalization. Voice replaces the bottom prompt with the transparent composing orb and warm viewport-border glow; no central/full-screen voice takeover or white circle. Opus finishes one explicitly confirmed tested winner and retests the exact final MP4. The currently implemented intake remains screenshots/brief, not original-video analysis; the v1.7 schema/pipeline migration is a target, not a deployed capability. See TEAM.md for deployment and provider acceptance evidence. Historical change notes do not override this correction.

**What changed in 1.7 — existing video first:** William explicitly clarifies that a company uploads its **current video**. Preflight pretests the original, connects its video/audio/text/timing and genuine predicted neural response to edit hypotheses, creates bounded improved candidates, retests those exact outputs and recommends the best-ranked asset with an original comparison. This supersedes the screenshots-first launch-founder MVP and the historical decision not to edit existing videos. Companies/e-commerce marketers are primary; screenshots are optional supporting evidence. Today's existing three-candidate, single-template, 15-second export limits remain, plus one source baseline; additional tested-winner iteration stays P1. Entry is full-viewport cinema without host panels/scrolling, then the same brain docks top-left. The Gemini Live orb is bottom-docked while voice replaces the prompt, returning to the prompt when disabled; a localized multicolor voice beam is permitted. Predicted cortical response is not EEG frequency, proof of buying intent or guaranteed retention. Shared backend/Voice contracts require migration; this is an approved target, **not deployed acceptance**. See §8–§12 and the [implementation correction handoff](docs/design/PRODUCT_RESET_HANDOFF.md). Older change notes below are historical.

**What changed in 1.6:** William selects **[FLORA](https://flora.ai/) and the supplied FLORA workspace screenshot as the primary product design reference**, replacing the radial tiny-node prototype and panel-heavy interface with a minimal black dotted canvas and spacious left-to-right card-based branching flows. Use a narrow floating left tool rail, small top-left project identity, compact top-right actions and bottom prompt/Director presence; no permanent navigation sidebar or large idle chat panel. Earlier ElevenLabs-style images remain supporting flow references. Redaction is the shared identity font; orange-red is the restrained UI accent. Both requested Libraries.dev effects are required presentation: standalone speaking-growth `ThinkingOrb` plus audio-reactive prompt `VoiceBeam`, adapted to Preflight, not new speech services. High-tech mission control comes from purposeful brain/job/voice interaction, not dense HUD decoration. The existing hover/pin brain and roughly three-second milestone focus are clarified without changing the video/neural clock. See §8/§12, the [clean-flow design brief](docs/design/CLEAN_FLOW_DESIGN.md), [Director visuals](docs/design/DIRECTOR_VISUALS.md) and §16. Three videos, source traceability, real evidence, mandatory two-way Live and P1 comparison/revision gates are unchanged. This is an approved target, not a claim that it is already deployed; historical notes below remain intact.

**What changed in 1.5:** William explicitly confirmed **two-way Gemini Live as mandatory FR-16/P0**. A female-sounding creative Director must listen, respond, handle interruption and help select/change the actual source-grounded storyboard through validated tools and visible canvas updates. TTS-only narration, a prerecorded conversation or text-only mode cannot pass this requirement. Captions, the standalone speaking-growth orb, explicit job confirmation, secure credentials and event-grounded progress/verdict remain required. Gemini Live uses a separate model/session transport from TTS; verify the proposed `gemini-3.8-live` model/account and Condense compatibility. No Condense exception has been approved. Pre-render storyboard editing is P0; revising a tested winner remains FR-11/P1, and the three-video cap is unchanged. The v1.4 notes/log below are historical and their optional-Live scope is superseded. See §8/§9/§10/§12.9/§14/§16.

**What changed in 1.4:** the primary workspace is a pan/zoom flow canvas, not a dashboard of disconnected screens. First arrival opens a cinematic 3D brain intro, then the same brain docks persistently in a corner while storyboard branches and actual job status populate the canvas. The new supplied canvas image joins the tracked visual baseline. **A female Gemini voice is mandatory P0 (new FR-16), explicitly confirmed by the product owner**, with event-grounded narration, captions and mute. Visual direction is a standalone `ThinkingOrb`, without a surrounding card, enlarging during speech; `voice-glow` is a complementary prompt effect, not another required voice engine. Gemini TTS is distinct from optional two-way Gemini Live voice intake. Brain anatomy/entry/dock remain P0 even without GPU inference; response animation still requires genuine data. Large-scale experimentation is the architecture direction, not proof of 50×50×50 completed tests or approval to remove today's three-video/budget cap. See §8, §9.2, §12 and §16.

**What changed in 1.3:** all three supplied images and the original motion reference are adopted as the shared [visual baseline](docs/design/README.md). Claude Opus 5.5 builds the interactive browser brain once; the same renderer/geometry is reused across users and A/B views with different simulation data, not generated per customer. §9.1 separates this development task from the desired runtime roles: Gemini for the variant/analysis loop and Opus for final motion-graphics composition. Runtime Opus is planned, not connected or a new P0 requirement. FR-12/FR-14 remain conditional P0 and FR-15 remains P1. See §10.5, §12.1 and §16.

**What changed in 1.2:** Preflight is explicitly a standard, browser-based web platform. The full product journey, including the 3D viewer, runs in a desktop browser. It is not an iOS app and must not be implemented in SwiftUI or as an Xcode/native-client project. The 1080x1920 videos are exported assets, not a mobile-app platform requirement. See §7.5, §10, §15 and §16.

**What changed in 1.1:** new §12 UI with the analysis intro (the "Preflight sequence") and the interactive 3D brain viewer; brain viewer and intro moved to P0 (conditional on TRIBE running); A/B compare mode added; repo and build info added; timeline and owners updated.

## 0. How to read this document

- **Humans:** read §1 to §7 (why, who, journey). Builders continue with §8 to §14.
- **AI coding agents:** read §15 (Rules for AI agents) first, then §8 (requirements) and §10 (architecture). Every requirement has an ID, a priority and acceptance criteria (AC). Build all P0 before touching any P1.
- **Labels:** `[FACT]` verified · `[ASSUMPTION]` not yet verified · `[DECISION]` decided by the team today.
- **Priorities:** P0 = must exist for the demo · P1 = do if P0 is done · P2 = after the hackathon.

## 1. TL;DR

**Preflight is a web platform accessed through a URL in a desktop browser.** No native app is installed. Existing company videos are the main input; confirmed product facts and optional assets ground the edits.

Companies have videos but do not know which moments to improve before spending on distribution. Preflight pretests the original with TRIBE v2 and a Gemini viewer panel, proposes timestamped edit hypotheses, renders three improved candidate cuts and pretests them again. It delivers a recommended tested cut, comparison to the original, reasons and a runner-up for real audience testing. “Improved” is the creative objective, not a guaranteed measured outcome.

The product feels like a creative mission-control workspace: full-viewport brain cinema → FLORA-like black dotted experiment canvas, with the same rotating brain top-left and a two-way female Gemini Live Director. Her standalone orb is bottom-docked while enabled and replaced by the prompt when disabled. Spoken and typed edits share validated canvas state. The original → analyze → edit → retest → recommend loop delivers the finished-video outcome.

## 2. Working backwards

### 2.1 Press release (the day we launch)

**Preflight: test the video you have, create the next cut with evidence**

Companies change hooks, reveal order and pacing by intuition, then spend on distribution to find out whether the new cut works.

Upload your existing video, confirm product facts, audience and goal. Preflight analyzes the original, proposes three grounded editing hypotheses, creates and retests candidate videos, then recommends a cut with timestamped evidence and the original baseline. Target latency remains unverified; recommendations need real-world validation.

> "I was about to pay for my app's launch video and had no way of knowing which style would work. I wanted to know before I paid, not after." (William, founder of tablehopp and Preflight)

### 2.2 Customer FAQ

- **Where do I use Preflight?** Open the web platform in your desktop browser. No iOS app, App Store installation or native client is required.
- **What do I need?** Your existing video, confirmed product facts, your goal (for example purchases), and your audience. Screenshots/product images are optional supporting sources.
- **How long does it take?** Target under 10 minutes for three tested videos.
- **Does it guarantee results?** No. It ranks versions by simulated viewer response so you only spend real money testing the strongest ones. Confirm with a live A/B test.
- **What is the brain view?** A research model (TRIBE v2 from Meta FAIR) that predicts the average human brain response to video, audio and language, second by second. It is one of several simulated viewers.
- **Will it make things up about my product?** No. Every word and screen in the video comes from what you provided.

### 2.3 Internal FAQ

- **Why generate videos at all?** `[DECISION — v1.7]` Customers need an actionable new cut, not only a report. The original is baseline/source material; edited candidates must be retested.
- **Why not only generate?** Generation is becoming a commodity. Knowing which version works is the scarce part. Generation plus pretest is the product.
- **TRIBE v2 is non commercial. How is this a business?** `[FACT]` TRIBE v2 is CC BY-NC 4.0. We use it for research and this hackathon. The commercial path is our own audience model trained on outcome data (simulated response paired with real A/B results).
- **What must be true for this company to exist?** Simulated pretesting must pick the real winner more often than chance and more often than an LLM alone. See §13 and the validation plan.

## 3. Problem

### 3.1 Problem statement

When a company has a video ready, it needs to know what to change and which alternative deserves a real audience test. Editing and evaluation are disconnected: it changes hooks, order or pacing by intuition, then spends to learn whether that helped. There is no quick, traceable loop from an observed moment to an edit hypothesis, new artifact and comparable pretest.

### 3.2 Evidence

| Claim | Status |
| --- | --- |
| tablehopp (William's app) launches 7 Oct and needs a launch video. William collected reference videos, most were rejected, and he was about to pay for production without knowing which style would work. | `[FACT]` (founder's own case) |
| Ad pretesting is an established paid category (for example Kantar, Neurons, System1 appear in comparisons). Companies pay to know before they spend. | `[FACT]` |
| Early stage startups need a demo video for most launches and cannot pay an agency every time. | `[ASSUMPTION]` |
| They would pay for a pretested video. | `[ASSUMPTION]` |
| Simulated viewer response correlates with real video performance. | `[ASSUMPTION]` critical, unproven |

### 3.3 Alternatives today

| Alternative | What it gives | What it lacks |
| --- | --- | --- |
| Agency or freelancer | High quality | Weeks, expensive, one version, untested |
| DIY screen recording tools | Fast, cheap | Looks amateur, untested |
| AI video generators | Many variants | No idea which one works |
| Ad testing platforms | Tests | No asset, built for larger brands and slower studies |
| Live A/B test on Meta or TikTok | Real data | Costs money and days per variant |

## 4. Users

**Primary persona: the company / e-commerce marketer with an existing video.** A small brand's founder, marketer or creative team wants to improve an ad/product video before the next spend. Success is a useful tested candidate and a defensible real-world experiment, not a neural-metric promise of purchases.

**Secondary:** agencies and app/SaaS founders with an existing product/demo video. Screenshots-only generation is a supporting/later path, not the primary intake.

**Anti personas (we do not design for them):** big brands with research departments, creators chasing entertainment virality, anyone who wants a guarantee.

**Job to be done:** "When I already have a video, help me understand what to change, create a stronger candidate and show the pretest evidence so I can choose what to test with real customers."

## 5. User journey

### 5.1 Today

| Stage | What they do | Pain |
| --- | --- | --- |
| 1. Trigger | Existing video needs improvement | "What should we change?" |
| 2. Diagnose | Retention/ad data or opinions | Symptoms without a concrete editing experiment |
| 3. Re-edit | Agency or DIY changes hook/order/pacing | Time, money and uncertain rationale |
| 4. Choose | Gut feeling, ask friends | No real signal |
| 5. Publish and boost | Pay for ads, wait days | Money spent before knowing |
| 6. Learn | Rarely | Next launch starts from zero |

### 5.2 With Preflight

| Stage | What happens | User sees |
| --- | --- | --- |
| 1. Trigger | "Improve this video" | Full-viewport brain entry → same brain docks top-left; explicit Enable Live |
| 2. Intake | Upload existing video; confirm facts, goal and audience | Playable Original, validated intake, bottom-docked composing orb, interruption/transcripts |
| 3. Agent at work (target under 8 min) | Pretest original → 3 grounded edit hypotheses → render candidates → retest exact outputs | Readable original/analysis/A-B-C branches, real jobs and brain; inactive voice docks near bottom |
| 4. Verdict | Best-ranked candidate, reasons and comparison to original | Timestamped evidence, synced video/curves/brain; no invented uplift |
| 5. Export | Winner plus runner up plus launch brief | Downloads |
| 6. Launch and learn (V1) | Live A/B results flow back | Model gets better per launch |

### 5.3 Moments of truth

1. **The videos must look good enough to post.** If not, the test is meaningless. Quality of the template matters more than the number of variants.
2. **The verdict must feel credible.** Always show why, with timestamps, never a bare score.
3. **It must be fast.** If it takes longer than making a video yourself, it fails.

Journey rule: the user never sees "TRIBE output". They see: which video, why, what next.

## 6. Product principles

1. **Decision over data.** Every screen leads to "launch this one".
2. **Show the why.** Every ranking comes with timestamped reasons.
3. **Honest uncertainty.** Show a confidence label. Never say "will go viral" or "predicts sales".
4. **Truth in the video.** Only use claims and screens the customer provided. No invented features, numbers, logos or testimonials.
5. **Fast beats perfect.** Under 10 minutes end to end.
6. **Model agnostic.** Every viewer simulator sits behind one interface. TRIBE is one viewer, not the product.

## 7. Scope

### 7.1 Hackathon MVP (today)

Full-viewport brain entry → FLORA canvas + existing-video intake → confirmed original pretest → 3 edit hypotheses → Gemini Live storyboarding/refinement → confirmed render of 3 candidates from source clips/assets using one template family → retest → ranking, original comparison and export. The same brain docks top-left; voice replaces the bottom prompt with the bottom-docked composing orb while enabled. Cortical animation requires genuine data. P1: synchronized dual-brain/difference view and an additional tested-winner iteration. Execution remains bounded: one original plus three generated candidates, not unlimited edits.

### 7.2 V1 (only after validation, see §13)

Ad account connection, launch live A/B tests, ingest real results, brand kit, more templates, backtest mode.

### 7.3 Moonshot

A simulated audience for all content: every launch video, ad, trailer and landing page is tested on simulated people before it meets real ones. Every customer's real results train our own audience model. AI made making content free; Preflight owns knowing what works.

### 7.4 Non goals (today)

- Screenshots-only generation as a second primary onboarding path (v1.7 supersedes the historical exclusion of existing-video editing)
- Text-to-video footage generation (use original video clips/audio and real supporting assets within the one-template composition family)
- Accounts, auth, payments, teams
- Publishing to social platforms
- More than one template family
- Mobile layout, multi language UI
- Native iOS, iPadOS, Android or desktop clients; SwiftUI and Xcode application targets

### 7.5 Product platform (required)

`[DECISION — v1.2]` Preflight is a conventional web product, delivered through a URL and used in a desktop browser. The brief form, agent activity, video previews, results, interactive 3D brain, Preflight sequence and exports are all part of that web experience.

The frontend uses web technology as proposed in §10.1. Orchestration, video rendering and GPU inference run in backend services/workers; end users do not need a local Python environment, GPU or development tools to use the deployed product.

**Platform acceptance:** the complete MVP journey from brief intake to downloading the winner and runner up can be used through the browser without installing a native client. iOS, SwiftUI, Xcode, the iOS SDK and Simulator are not part of the Preflight application build or demo workflow.

**Input/output distinction:** tablehopp and other customer apps may be mobile apps. Their screenshots and the 1080x1920 vertical video outputs do not make Preflight a mobile app. Desktop web remains the hackathon target; mobile layout is still outside today's scope.

## 8. Functional requirements

### P0

#### FR-01 Brief intake

**Inputs:** one existing company video (MP4 for the demo); product name; one-line description (max 140 chars); goal (sign ups / downloads / understand the product / purchase, plus optional free text); audience; optional supporting images/screenshots, brand color and logo. A screenshot folder is not mandatory.

**AC:** upload/drop yields a playable Original node; server validates container/file and configured size/duration limits, records stable artifact ID, SHA-256, actual duration/dimensions/fps and canonical project ID. Invalid input has a clear error. Brief/source metadata persist against §10.3's migrated schema. Provide a genuine existing-video fixture with rights/provenance; the tablehopp screenshot fixture is supporting/historical, not video-intake acceptance. Confirm Run before billable analysis/render/test jobs.

#### FR-02 Creative plan

After the original pretest, produce exactly 3 candidate-edit concepts. Each has a distinct hypothesis about a timestamped original moment (hook/reveal order/pacing), hook text (max 8 words), 4 to 6 scenes with source-video clip or optional asset references, grounded on-screen text, CTA and 15-second target duration. Clearly separate creative rationale, Gemini observations and genuine TRIBE evidence.

**AC:** concepts validate against the migrated schema; hypotheses differ; edits link to real source moments and label actual evidence used. Clip in/out ranges are valid and map to candidate output times. Every claim traces to confirmed facts or a verified source transcript/asset. No invented neural rationale if TRIBE is unavailable.

#### FR-03 Render

Each candidate renders to MP4, 1080x1920, 15 s, 30 fps, using original-video clips/audio and optional supporting assets within one composition/template family. Keep today's output target without falsely relabeling the original duration or silently destroying source framing/audio.

**AC:** 3 MP4s render with no manual step; render time logged per video; a failed render is retried once, then marked failed without stopping the run.

#### FR-04 Pretest (simulate)

Pretest the original baseline first, then every rendered candidate with TRIBE v2 and a Gemini viewer panel (3 personas from the audience). Keep evidence against each artifact's exact bytes/model/config and original/candidate role.

**AC:** one `SimulationResult` per original/candidate per simulator, matching migrated schema and actual hash/duration. Never reuse the original prediction for an edited video. TRIBE output is genuine live or visibly disclosed precomputed exact-video data. If unavailable, complete with Gemini only and "Brain sim off"; edits are labeled Gemini/creative hypotheses, not neural optimization.

#### FR-05 Score and rank

A goal aligned score per variant, a ranking, and a confidence label (High if simulators agree on the winner, Low if they disagree).

**AC:** same inputs give the same ranking; scoring/confidence and baseline comparison rules are documented in code/README, including duration/time-normalization. More activation is not a quality score. Report no improvement if no candidate improves the documented pretest objective; never invent uplift or guarantee real-world performance.

#### FR-06 Explain

For each variant, 2 to 4 reasons, each tied to a timestamp and to what is on screen at that moment (hold moments and drop moments).

**AC:** every reason references a real scene/source clip within the actual artifact duration. Original moment → edit hypothesis → candidate outcome is traceable; source and output timestamps stay distinct after cuts/reordering.

#### FR-07 Flow canvas and results UI

Browser-based flow canvas: playable Original + brief → baseline analysis → edit-hypothesis/storyboard branches → rendered candidates → retests → original comparison/recommendation/export. Use readable media cards with left-to-right curved branches on a near-black dotted canvas. Empty state shows a short video-upload invitation, not a prepopulated wall of empty scenes. Selection reveals an on-demand evidence inspector, player, synced curves and recommendation. No permanent sidebar, raw brain box or oversized idle chat panel. See §12.4/§12.10.

**AC:** canvas pan/zoom, fit-to-flow and node selection work in the desktop browser; the default view shows readable source/storyboard/media cards and A/B/C lineage with minimal floating controls on the black dotted canvas; rendered/tested nodes have real artifact/result links and visible status; graph branches show lineage and the selected storyline; curves follow scrubbing; verdict accessible without scrolling on a 1440 px wide screen; corner brain and voice dock do not obscure core controls. Typography/accent follow §12.6, dense evidence appears on demand and keyboard focus remains visible. Prototype-only or untested nodes are explicitly labeled and never counted as completed tests. No native client is required.

#### FR-08 Export

Download recommended candidate MP4, runner-up MP4, `report.json`, and a Markdown launch brief. Report/brief include the original baseline, edit lineage and genuine before/after evidence; unsupported improvement is stated, not invented.

**AC:** all four files download and open.

#### FR-09 Agent activity log

Visible persisted steps: source intake/baseline pretest, plan edits, render, retest, score, explain, each with actual status/duration. Canvas, brain choreography and Live context use these same events.

**AC:** log updates live during a run and is saved with the project; the canvas and voice use this same source of job truth, including retry/failure/unavailable states. A reconnect does not duplicate completed nodes or narration, and no progress percentage/completed-test count is invented.

#### FR-10 Partner tech

Gemini for planning, viewer panel and explanations. All LLM calls go through Condense. Show token savings in the UI.

**AC:** savings number visible on the results screen. This is required for eligibility (at least two partner technologies).

#### FR-12 Interactive 3D brain viewer

**P0 viewer/anatomy/dock; genuine neural animation is conditional on available TRIBE data.** Build the fsaverage5 brain inside a head silhouette once and reuse it for the entry, persistent corner view and expanded analysis. With genuine results, predicted activity is synced to video playback. Controls and behaviour as specified in §12.3. This v1.4 split supersedes dropping the entire viewer when live GPU inference is unavailable.

**AC:** the reusable anatomical viewer and persistent corner dock work without a Gemini/GPU call; orbit, zoom, region click, expand/dock and scrub work; the dock identifies the selected variant and actual playback/sample time. Activity comes from real TRIBE results only; without data show "No brain data" with gray anatomy, never generated/random activity. Unavailable live inference shows "Brain sim off"; any genuine sample shown instead is visibly "Demo example · precomputed", not the current run. Playback runs smoothly in a desktop browser on a recent MacBook; record actual hardware used for verification.

#### FR-14 Entry intro and analysis focus, the "Preflight sequence"

**P0 entry intro, depends on FR-12.** First arrival opens seamless full-viewport 10–15 second rotating brain cinema, with deliberate region camera shots; no scroll-controlled reveal, host panel overlay or raw viewer box. Then the same renderer docks top-left and reveals the canvas. Genuine results can drive the analysis focus §12.2, once per run.

**AC:** fresh entry fills the viewport, locks page scroll and hides/inerts host controls; loading/error cannot flash a small raw viewer. Skip works before/after geometry loading and on WebGL failure. Entry runs once per session with explicit Replay; reduced motion uses fades/static framing. Completion/Skip preserves the same renderer/selection/time in the top-left dock with quiet continuous rotation subject to manual pause/reduced motion. Colored entry response requires a genuine matched example labeled "Demo example · precomputed"; otherwise gray anatomy + "No brain data". Analysis only uses the run's genuine exact-video results, once per run. No fake waves.

#### FR-16 Two-way female Gemini Live Director

**Placement — v1.6.2:** the button is inside the bottom text bar. Enabling voice replaces the prompt with reference 10's neutral composing orb in the bottom dock, transparent on black; no white substrate, central/full-screen overlay, backdrop or canvas dimming. Keep the same silhouette even when disconnected, with a paused visual and honest status rather than a loading ring. The warm audio-reactive VoiceBeam is anchored on the viewport's bottom border beneath the orb. Orb amplitude/deformation and beam react simultaneously to actual playback; listening input is separate and cannot drive assistant speech growth. Canvas controls remain usable. End/Escape restores the text bar/focus and releases the microphone.

**P0, explicitly required by William for the hackathon demo.** An original female-sounding Gemini Live creative Director listens and responds in a real two-way conversation, helps choose/refine the storyboard and explains actual agent transitions and evidence-backed conclusions. Tone: concise, capable, cinematic mission control, not an imitation of a copyrighted character's voice. Required visuals are a standalone state-driven `ThinkingOrb`, growing during actual assistant speech without a surrounding card, and `VoiceBeam` from `voice-glow` along the prompt's bottom edge, adapted to our orange-red palette. Neither library supplies speech or Live transport. See §12.9.

**AC:** after an explicit Enable Live gesture and mic permission in HTTPS/localhost, the user can speak, hear a real Gemini Live reply, interrupt assistant playback and receive a reply to the interruption without stale audio continuing. Input/output transcripts match the exchange; the chosen female-sounding preset is auditioned and documented in README. Demonstrate spoken selection of a real storyboard/scene and at least one source-grounded pre-render edit through validated tools: the persisted concept/draft and canvas update visibly, preserve FR-01/FR-02 constraints and report actual success/failure. Explicit confirmation of the summarized run is required before generation/render/pretest jobs; no duplicate job on reconnect/repeated tool call. Live welcome, an actual job milestone and an evidence-backed verdict are demonstrated; statements never invent completed tests, counts, emotion or guaranteed outcomes. Orb state/scale follows the real connection/mic/work/output audio; any amplitude glow is real, not random. Mute, stop/disconnect, mic release, captions and typed fallback work; jobs do not wait for audio, and missing credentials/quota/connection failures are visible. Long-lived keys stay server-side, with scoped short-lived tokens or a secure proxy for browser Live; provider/model/routing evidence is recorded. TTS-only narration, prerecorded dialogue, a reactive orb or text-only fallback does not pass FR-16. Editing a tested winner remains FR-11/P1; any changed video invalidates its old test evidence.

### Owner-prioritized release extension

#### FR-17 Finish the selected winner with runtime Opus

After the original run reaches DONE, Results offers **Finish with Opus** for its tested winner. Separate explicit confirmation binds the job to the winner ID and source video SHA-256; opening/selecting/downloading is free of inference. Opus chooses shot duration, layout and transitions only, within the existing 4–6-shot, 450-frame template. Keep text, source fields, screenshots, order, brand and CTA unchanged. This limited motion finalization is not FR-11's creative revision.

**AC:** server-only `ANTHROPIC_API_KEY` plus `CONDENSE_API_KEY` on the Python renderer host; native Messages via Condense, no direct fallback/model substitution. One final asset per project; output capped at 4,096 tokens by default (configuration ceiling 8,192). No automatic Opus retry; a failed/uncertain call needs another explicit confirmation and at most two attempts in total. Atomic composition/render/audio/simulation checkpoints and a per-project cross-process lock prevent duplicate purchases on resume/concurrent requests. Reject stale approval/changed source assets. Add local music/SFX if enabled, without expanding the unapproved direct-TTS exception. Require matching Gemini evidence for the exact final MP4 hash; optional TRIBE unavailable is **Final brain sim off**. Never inherit the original ranking/brain data or promise improvement. Original artifacts/results/four exports remain; final MP4 and `final_report.json` download separately with lineage, actual model/route/token counts and matching new evidence. Missing provider/backend, quota, failed rendering/testing and exhausted budgets are explicit and resumable where safe. A completed file that changes fails download validation. Live provider/render acceptance remains required before calling the deployed feature complete.

### P1

#### FR-11 Iterate the winner

One revision round aimed at the winner's weakest second, re-render, re-test, show the delta.

**AC:** before/after score and curve shown.

#### FR-15 A/B compare and difference view

Two variants side by side with synced playback, plus a difference view on the brain (where variant B is more or less active than A).

**AC:** both videos and brains stay in sync while scrubbing; the difference view uses a diverging color scale with a legend.

#### FR-13 Backtest mode

Upload 2 or more historical videos plus which one won in real life; Preflight ranks them blind; show hit or miss.

**AC:** only shown if real historical data exists; never with invented results.

### P2

Screen recording input, brand kit, more templates, ad account connection, live A/B launch, outcome ingestion. Voice moved out of P2 into FR-16/P0 in v1.4; v1.5 requires two-way Gemini Live, not a separate optional voice-intake implementation.

## 9. Agent design

**Pattern:** a deterministic state machine with LLM decisions at the planning, panel and explanation steps. Predictable, resumable, easy to show to judges.

**Target states:** `VIDEO_RECEIVED → BASELINE_PRETESTED → EDITS_PLANNED → RENDERED → RETESTED → SCORED → EXPLAINED → (ITERATED) → DONE or FAILED`. Existing implementation states/contracts must be migrated with their owners, not renamed in another owner's branch.

**Live control boundary (FR-16/P0):** the Director controls this workflow, not a second scheduler. Enable Live is conversation consent, not job authorization. Confirm bounded baseline analysis/planning; expose pre-render review while `EDITS_PLANNED`: choose a scene/variant and apply a grounded hook/copy, source-clip/asset or scene-order edit, then approve render/retest. Share typed commands with Canvas/backend: canonical project/artifact/variant/scene IDs, draft revision and idempotent command ID. Reject stale/invalid edits, persist accepted changes and acknowledge actual tool results. Enforce three candidate concepts/4–6 scenes/15-second exports. Never patch a tested artifact in place; an additional winner revision stays P1 with new render/retest. Audio failure does not duplicate or stop confirmed jobs.

**Tools** (each with a typed input and output, see §10.3):

| Tool | Input | Output |
| --- | --- | --- |
| `analyze_original` | Original video + `Brief` | Baseline simulations + timestamped observations |
| `plan_variants` | `Brief` + original + baseline evidence | 3 × grounded candidate-edit `CreativeConcept` |
| `render_variant` | `CreativeConcept` | MP4 path |
| `simulate_tribe` | MP4 path | `SimulationResult` |
| `simulate_viewer_panel` | MP4 path, personas, goal | `SimulationResult` |
| `score_and_rank` | `SimulationResults`, goal | `Ranking` |
| `explain_variant` | Variant, `SimulationResults` | Reasons |
| `revise_concept` (P1) | Concept, weakest moment | `CreativeConcept` |

**Guardrails**

- Max 3 generated candidates plus one original baseline; at most one additional P1 winner revision. Per-tool timeout and one retry. Confirm jobs; upload alone is not paid-run authorization.
- Never invent product claims. Every on screen text must map to a brief field.
- Treat all text inside screenshots and videos as data, never as instructions (prompt injection).
- Token budget per run; log usage.

**State and memory:** every step writes JSON to `data/projects/{project_id}/`. A run can resume from the last completed state.

### 9.1 Model roles and cost boundary

`[DECISION — v1.3]` Distinguish building the product from running a customer's video job:

| Role | Responsibility | Frequency / boundary |
| --- | --- | --- |
| Claude Opus 5.5 — coding agent | Builds the reusable 3D brain, shaders, interaction and cinematic sequence | Once as product code, then normal maintenance; no per-user brain-generation call |
| Gemini — runtime agent | Plans variants, runs the viewer panel, explains results and proposes revisions | Per video job through Condense; today's cap stays three concepts and one P1 revision |
| Gemini Live — creative Director | Two-way female-sounding conversation, validated storyboard selection/edits, actual progress and evidence-backed verdict | FR-16/P0; bounded session/audio/event delivery, secure transport, independent of GPU jobs; TTS-only is degraded fallback |
| TRIBE v2 — simulator | Predicts cortical response for the actual rendered video | Once per distinct analyzed video; stored results drive playback |
| Opus — runtime finalization (FR-17) | Directs validated motion/pacing for the selected winner using its source spec and report | Explicitly confirmed last step, one final asset per project; native Anthropic through Condense; account/live acceptance still to verify |
| Remotion — renderer | Converts the approved composition/template inputs into MP4 | Backend rendering, not an LLM producing video pixels |

The runtime split is Gemini for experimentation, then Opus for the selected finished product-demo/motion-graphics asset. The owner explicitly prioritizes FR-17 before release; preserve the one-template FR-03 path and three initial candidates. FR-17 motion finishing is separately consented and re-tested, not FR-11 creative revision or proof that outstanding P0 requirements passed. Do not introduce unlimited variants or a second template family.

Provider documentation checked 3 Oct confirms `claude-opus-5-5` and Condense `POST /anthropic/v1/messages` with native structured JSON. Actual account access/latency still require a live check. Conductor's coding-agent label is not itself an inference API contract. A Gemini key does not authenticate Claude. FR-17's asynchronous job has its own persisted `finalization/record.json` lifecycle, separate from the completed original run. Record actual model/route/input/output tokens separately; do not claim unmeasured savings/pricing. See [deployment instructions](backend/README.md#runtime-opus-final-video-fr-17).

If finalization changes the content or timing of a tested video, re-render and re-simulate those exact bytes before attaching a tested verdict or brain response to the export. Keep the original winner/runner-up artifacts and results traceable; never reuse a candidate's prediction for a changed final asset. Replaying, orbiting or opening an A/B view does not trigger new LLM or TRIBE inference.

### 9.2 Experiment graph and scale

`[DECISION — v1.4]` The canvas projects the workflow; it is not a second job scheduler. Each hypothesis, storyboard, rendered asset and test result keeps stable IDs, parent lineage, source traceability and status. Node selection and connecting a visual edge do not themselves authorize a paid render, inference or publication.

Separate **hypothesis nodes** from **rendered videos** and **completed neural simulations**. A hook/storyboard needs a playable render before TRIBE can evaluate it; Gemini-authored text or a thumbnail is not a neural result. Selection, ranking and explanations consume the actual stored evidence, not the number of nodes on screen.

The user's “at scale” direction is bounded experimentation: queue/prune candidates, enforce worker concurrency/rate limits/timeouts and cache identical video/config hashes. v1.7 adds the original baseline to the existing three-generated-candidate budget; one additional winner revision stays P1. No unlimited full renders, inferred test counts or unmeasured capacity. Higher batch limits need owner/backend budget approval and measured throughput.

Large visual trees may use viewport virtualization/level-of-detail and staged layout while retaining actual nodes/edges and lineage. A node must be inspectable when zoomed in; a “+47” badge is not evidence that 47 hypotheses were generated or tested. If the product shows a prototype/example tree, the whole graph and its claims stay visibly prototype/untested. Present this as **simulated comparison/pretest**, not a live randomized audience A/B experiment.

### 9.3 Sound for the exported videos

`[DECISION — sound addendum]` After picture render, every rendered variant gets a soundtrack **before** simulated viewers watch it, so ranking covers the mixed file.

- **What is added.** Gemini text-to-speech narration (default voice `Leda`, a youthful feminine ad voice; Live Director stays `Kore`), a synthesized 120 BPM music bed and synthesized effects placed on scene changes. Music and effects are generated in code, not sampled, so there are no licensing questions. Everything is mixed to about -14 LUFS with a true peak at or below -1 dBTP, **measured on the encoded file**.
- **Narration.** Gemini TTS speaks source-backed on-screen copy (and the end-card headline/CTA). Lines that cannot fit their scene window are trimmed; a failed TTS call degrades to music/effects only for that cut.
- **The picture is never re-encoded.** ffmpeg copies the video stream (`-c:v copy`), so the exported picture is byte-identical to the rendered one.
- **What the verdict covers.** Simulated viewers watch the **mixed** cut when mixing succeeded (`videos/{id}.final.mp4`). The silent picture stays at `videos/{id}.mp4`. Both hashes are kept in `sound/{id}.json`. If mixing is skipped, the panel watches the silent render.
- **Degrades, never fails.** If narration fails, the cut has music and effects only and says why. If ffmpeg is unavailable the variant is exported silent and the activity log shows the step as skipped.
- **Routing exception (FR-10).** Narration calls Gemini's TTS model directly, not through Condense: Condense documents only text chat routes, and each call carries one on-screen line, so there is nothing to compress. This is a logged exception that the product owner must confirm; narration token usage is recorded in `sound/{id}.json`, separate from the Condense ledger.
- **Cost bound.** At most three rendered videos per run, one TTS call per distinct line, cached on disk by text, voice and model, so a resumed run does not pay twice.

## 10. Architecture

**Platform decision:** this is a standard web application with a browser frontend and backend services/workers. The following web stack is the implementation direction. Do not create an iOS/SwiftUI application or an Xcode project; the user-facing product and 3D experience belong in the browser.

### 10.1 Components

| Component | Responsibility | Suggested tech |
| --- | --- | --- |
| Web frontend (desktop browser) | Flow canvas, brief, job events, entry/analysis sequence, persistent brain, results, voice dock, export | Next.js, TypeScript, Tailwind, three.js; project-compatible graph rendering |
| API and orchestrator | State machine, tools, storage | Python, FastAPI |
| Renderer | Motion graphics template driven by concept JSON | Remotion (check its license for commercial use later) |
| TRIBE worker | Runs TRIBE v2 on a GPU and returns `SimulationResult` | Python on a GPU with 40 GB+ VRAM |
| Viewer panel | Gemini watches each video as 3 personas | Gemini API via Condense |
| Live Director service and playback | Two-way audio/transcripts, validated storyboard commands, actual job context, interruption and session lifecycle | Gemini Live (proposed `gemini-3.8-live`, verify model/account/transport), secure token service or proxy, browser Web Audio, `thinking-orbs` and `voice-glow` |

Use the actual orchestrator's persisted events as the common input to canvas progress and the Live Director's context. Agree the delivery mechanism (SSE, WebSocket or polling), event IDs and artifact/result identifiers with its owner; this PRD does not claim that a deployed streaming endpoint exists yet. Live's audio/session transport is separate from job event delivery. Tools call agreed application commands and return actual validated results; long jobs acknowledge accepted/queued, then report completion via persisted events. Audio is off the critical render/simulation path. A graph library or standalone voice prototype is not a reason to replace the existing backend contracts or Dashboard shell.

### 10.2 Simulator interface

Every simulator implements one function: video in, `SimulationResult` out. Scoring and UI only read `SimulationResult`. Adding or removing a simulator must not require changes in scoring or UI code.

### 10.3 Data contracts (JSON, simplified)

**Target contract migration:** the examples below add original-video/artifact/clip fields. Current merged code still has screenshots-only intake and A/B/C-only identifiers. Backend, Canvas, Voice and brain owners must agree and implement migration/versioning together. These examples do not make new routes or schemas available; never pretend the original is candidate A or attach its results to another artifact.

**Brief**

```json
{
  "project_id": "str",
  "product_name": "str",
  "one_liner": "str<=140",
  "source_video": {
    "artifact_id": "original-id",
    "path": "server-owned path",
    "sha256": "hex",
    "duration_s": 15,
    "width": 1080,
    "height": 1920,
    "fps": 30
  },
  "screenshots": ["optional supporting asset path"],
  "goal": "signups|downloads|understand|purchase",
  "goal_note": "str?",
  "audience": "str",
  "brand_color": "#hex?",
  "logo": "path?"
}
```

**CreativeConcept**

```json
{
  "variant_id": "A|B|C",
  "hypothesis": "str",
  "baseline_artifact_id": "original-id",
  "evidence_refs": [{ "artifact_id": "original-id", "t": 3, "kind": "creative|gemini_panel|tribe_v2" }],
  "hook": "str<=8 words",
  "scenes": [
    {
      "t_start": 0,
      "t_end": 3,
      "source_clip": { "artifact_id": "original-id", "in_s": 3, "out_s": 6 },
      "screenshot": "optional supporting asset path",
      "text": "str",
      "source_field": "brief field this text comes from"
    }
  ],
  "cta": "str",
  "duration_s": 15
}
```

**SimulationResult**

```json
{
  "variant_id": "original|A|B|C",
  "artifact_id": "exact analyzed artifact id",
  "video_sha256": "hex",
  "simulator": "tribe_v2|gemini_panel",
  "version": "str",
  "hz": 1,
  "series": { "name": [0.0] },
  "events": [{ "t": 3, "type": "hold|drop", "label": "str" }],
  "precomputed": false,
  "meta": {}
}
```

**Ranking**

```json
{
  "order": ["C", "A", "B"],
  "scores": { "A": 0.0 },
  "confidence": "high|low",
  "rule": "str"
}
```

**Report**

```json
{
  "winner": "C",
  "runner_up": "A",
  "reasons": { "C": [{ "t": 2, "text": "str" }] },
  "next_time": ["str"],
  "baseline_comparison": { "original_artifact_id": "original-id", "candidate_artifact_id": "candidate-id", "rule": "documented comparison rule", "improved_under_rule": false },
  "token_savings": { "tokens_saved": 0, "percent": 0 }
}
```

### 10.4 Secrets and repo

- Keys in environment variables only (`GEMINI_API_KEY`, `CONDENSE_API_KEY`, `TRIBE_ENDPOINT`, backend-only `ANTHROPIC_API_KEY`). Commit `.env.example`, never `.env`.
- No model weights in the repo. README credits TRIBE v2 (Meta FAIR) and states its CC BY-NC license.
- Repo must be public (hackathon rule). URL: https://github.com/clawmax12-lang/Norrsken.
- The README states the build stack, including that the code was written with Claude Opus 5.5 as the coding agent.

Runtime Opus is separate from the coding agent. Set `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-opus-5-5` and `CONDENSE_API_KEY` on the Python/FastAPI renderer host. Vercel secrets do not propagate to a separately hosted backend; the Next route forwards only validated approval/lineage, never permanent keys. Native Anthropic requests go through Condense with no direct fallback, retaining FR-10. Existing Gemini/Live/TTS routing gates are not waived. A key configured on one service is not proof of every service's entitlements. Missing credentials must show an explicit unavailable/not-configured state, never fabricated results. Never request keys in tracked documents or frontend source.

Configure text and mandatory Live model IDs separately; if a TTS-only degraded fallback exists, give it a separate model configuration. The Voice workspace proposes `gemini-3.8-live`; verify the current provider ID, account access and supported female-sounding preset rather than treating a proposal or the spoken “3.8 TTM Flash” as a verified API contract. Speech generation alone is not a bidirectional live conversation. Keep long-lived keys server-side; browser Live requires scoped ephemeral tokens or a secure backend proxy, bounded session duration/usage and explicit teardown. Validate tool requests server-side against owned project/source IDs, current draft revision, allowed operations and confirmation; uploaded content cannot instruct tool execution. No default recording or audio/token/key logging. Verify Condense support for Live explicitly: FR-10 has not been waived, and a text-compression path does not prove audio/WebSocket support. If unsupported, record an integration blocker and obtain an explicit product-owner exception before direct Live routing; report that route and measured usage separately.

### 10.5 Reusable brain architecture

`[DECISION — v1.3]` The core brain is a product component, built once by Claude Opus 5.5. Commit the viewer code and appropriately licensed static mesh/atlas assets; do not generate a new anatomy or scene implementation for each user, video or run.

- Load/cache compatible `fsaverage5` geometry and atlas metadata once per browser session; reuse them across variants. Separate shared immutable geometry from each view's activity buffers, selected region and presentation state.
- Feed the viewer genuine per-video `SimulationResult` data through the shared contract. Binding a new result changes the activity overlay, not the anatomy or renderer implementation. Contract details still require agreement between the worker and viewer owners.
- Entry hero, corner dock and expanded analysis reuse the same component/assets and shared selection/time state. Moving/docking the viewport does not generate a new brain, reset the run or trigger model calls. Idle anatomy may rotate with reduced-motion handling; activity never changes without real samples.
- A/B mode instantiates two views of the same component/mesh. Share playback time, camera framing and a consistent activity scale; each view reads its own variant's data. Differences require compatible vertex mappings and timestamps.
- UI motion and interpolation are local rendering. The “brain waves” reference means predicted cortical/fMRI activity, not measured EEG or invented pulses.
- Store simulation results against the exact analyzed video and model/config revision. Cache reuse must be invalidated when those inputs change; changing camera or playback position never requires inference.

Implementation direction and visual quality bar: [visual baseline](docs/design/README.md) and [Opus brain build brief](docs/design/OPUS_BRAIN_BRIEF.md). These support this PRD, not a competing product specification.

## 11. TRIBE v2: what it is and how we use it

**Facts (from third party write ups, verify on the Hugging Face model card in hour 1)**

- Predicts group average brain response to video, audio and text.
- Output at 1 Hz on the fsaverage5 cortical surface (about 20,484 vertices).
- Needs roughly 28 to 32 GB VRAM. A T4 is not enough.
- License CC BY-NC 4.0: research and non commercial use.

**How we use it**

- Run each variant once and store the result. Playback in the UI is synced to the stored result, so it looks live.
- Reduce vertices to a few region groups (for example visual, auditory, language) using a standard atlas, and show those as curves.

**Rules**

- No emotion, desire or buying intent read from brain regions. Region cards describe what a region is known for, nothing more.
- Never claim TRIBE predicts retention, virality or sales.
- If TRIBE does not run by 12:30, it is dropped from live runs. In v1.5 keep the required canvas, anatomy/entry/dock and two-way Live Director; show "Brain sim off" and no invented activity. Genuine disclosed example/precomputed data is separate from that run and cannot turn a failed live gate into a pass.

## 12. UI and the analysis intro

### 12.1 Design direction

- **Feeling:** minimal, high-tech creative mission control. A quiet black workspace with a cinematic brain/voice moment; every number on screen is real and readable. The owner's Tony Stark reference describes interaction quality, not an imitation of film branding, voice or a wall of HUD panels.
- **Restraint:** minimum interface, complete capability. The [Specific supporting reference](docs/design/README.md#reference-09--specific-restraint-and-readable-connections) and owner's Sana-like direction clarify the existing minimalism: prioritize current content/state and one contextual primary action; reveal logs, editors and detailed evidence on demand. Do not hide active mic/privacy, stop/mute, errors, confirmation or scientific data labels. See [progressive disclosure](docs/design/CLEAN_FLOW_DESIGN.md#minimum-interface-complete-capability). FLORA remains the main shell target.
- **Primary layout:** full-viewport black dotted canvas, using [FLORA and reference 08](docs/design/README.md#reference-08--flora-primary-product-layout) as the primary target and the [clean-flow design brief](docs/design/CLEAN_FLOW_DESIGN.md). Spacious source/storyboard/media cards branch left-to-right through A/B/C renders, actual pretests and the recommendation. A narrow floating left tool rail, small top-left project identity, compact top-right actions and bottom-centered prompt/Director presence replace the permanent sidebar/top-bar shell. Evidence/brief/transcript panels open on demand. FLORA supersedes references 05–07 for the shell; earlier images still inform branching and original brain references still set anatomy quality. Do not copy its branding, onboarding survey, third-party assistant launchers or unrelated features.
- **Reference:** all three original images and the motion clip supplied by the product owner, now committed in the [visual baseline](docs/design/README.md): black background, a dark head silhouette in profile, a sculptural light gray brain mesh, activity in a red to yellow heat scale, readable timeline and rounded segmented controls. Match their anatomical depth and cinematic quality with an actual interactive 3D renderer, not a screenshot or prerecorded substitute. Do not copy Meta branding.
- **Ownership and reuse:** Claude Opus 5.5 builds the complete browser brain experience under the [implementation brief](docs/design/OPUS_BRAIN_BRIEF.md). Build the renderer once and reuse it as specified in §10.5. A/B instances share the anatomy and controls, not simulation values. FR-15 remains P1.
- **Rule:** the cinema is the wrapper, the decision is the content. Every screen still ends in "launch this one".

### 12.2 Entry intro and analysis focus: the "Preflight sequence" (FR-14)

**Entry, before intake:** on fresh arrival, a seamless 10–15 second full-viewport hero reveals the brain/silhouette, orbits and deliberately visits anatomical regions, pulls back and docks the **same** renderer top-left as the canvas appears. No page scrolling, old host/composer/Run overlay, raw viewer card or pre-load dock flash. Lock scroll and keep underlying controls inert until completion/Skip. Skip survives slow/failed geometry/WebGL; reduced motion keeps static framing/fades. No backend job or mic starts on mount. Enable Live requires a gesture/permission; silent entry remains usable but does not pass FR-16.

Red/orange/yellow “waves” before the user's run require genuine precomputed predictions for a specific example video, visibly labeled **Demo example · precomputed**, with its provenance/video available. Without that bundle, show gray anatomy and **No brain data**, using lighting/camera motion for the entry. Never portray a prerecorded/reference animation or fabricated pulse as the user's simulated response. The original reference images are inspiration, not analysis data.

**Analysis focus, when genuine results are ready:** reuse the renderer for the following beats once per run. Its handover now returns to the canvas, not a separate dashboard page.

| Beat | Time | What happens on screen |
| --- | --- | --- |
| 1. Black out | 0 to 1.5 s | Screen dims to black. The variant video shrinks into a floating frame on the left. Small mono text: "Running simulated viewers · Variant A". |
| 2. Assemble | 1.5 to 4 s | Head silhouette fades in. The brain builds from a thin wireframe into the shaded gray mesh while slowly rotating to a side view. |
| 3. Watch | 4 to 9 s | Video plays with exact-video predicted response interpolated between genuine 1 Hz samples. Quiet visible activity legend/timeline; detailed region curves appear intentionally, not as decorative HUD telemetry. |
| 4. Lock on | 9 to 12 s | At the strongest moment, the camera pushes in on the most active region. An info card slides in: region group, what it is known for (one line), timestamp, and what is on screen at that second (for example "0:03 · product screen appears"). |
| 5. Hand over | 12 to 15 s | Camera pulls back. The brain returns to its persistent corner dock; the selected result node, verdict and evidence inspector are revealed on the canvas. |

**Always:** a Skip button top right; reduced motion setting replaces the camera moves with fades; a small "precomputed" label if the TRIBE results were computed ahead of time.

Entry plays once per session; analysis focus once per run. Explicit replay is allowed. Live audio never blocks Skip, canvas access or result availability.

### 12.3 Interactive brain viewer (FR-12)

Bottom controls, as segmented pills like the reference:

| Control | Options | Behaviour |
| --- | --- | --- |
| Variant | A · B · C | Switch which variant's response is shown. This replaces the reference's "True / Predicted", because we only have predicted data and our job is comparing variants. |
| Surface | Normal · Inflated | Inflated unfolds the brain so activity hidden in folds becomes visible. |
| View | Closed · Open | Open splits the two hemispheres apart to show the inner surfaces. |
| Mode (P1) | Activity · Difference | Difference shows where the selected variant is more (warm) or less (cool) active than variant A. |

**Interaction**

- Drag to orbit, scroll to zoom, double click to reset the camera.
- Click a region to open its info card (same content rules as §12.5).
- Scrubbing the timeline moves video, brain and curves together.
- Keyboard: space play or pause, left and right arrows step one second, F fullscreen.

**Fullscreen mode:** brain centered and large, video as a small floating frame, controls at the bottom, info cards on the right. This is the mode for the demo video and the stage.

**Persistent corner mode:** the brain remains top-left while the canvas pans/zooms, separated from project controls. Hover enlarges; click/keyboard can pin/expand, with a clear return to dock. Show selected variant, sample/video time, data mode and Expand. During actual work, purposeful brisk camera motion can pause into roughly three seconds of slower focus plus concise text at a new meaningful backend milestone, then resume. Job-only focus uses camera/halo/status, never a fabricated active brain region; genuine neural focus must be atlas-backed and exact-video matched. Slow the camera, not video playback, neural timestamps or GPU work. Deduplicate/bound focus events; manual inspection, pause and reduced motion take precedence. New results become available through actual backend events; neural playback reads stored samples at 1 Hz with visual interpolation. “Realtime” describes live job updates and responsive presentation, not continuous fMRI measurement or a new GPU inference at every animation frame. While queued/running and without results, keep gray anatomy and truthful progress; once a result is ready, bind it to the matching selected video.

### 12.4 Screens

1. **Entry hero:** rotating brain intro and Enable Live/female-voice welcome, then the brain docks and reveals the workspace.
2. **Canvas intake and original review:** short video-upload invitation on an otherwise quiet canvas. Uploaded Original becomes a playable source node; confirm product facts/audience/goal, then Run baseline analysis. Conversation uses the bottom-docked composing orb; no empty fabricated storyboard tree before intake.
3. **Canvas at work:** Original → actual baseline analysis → grounded edit hypotheses/storyboards → candidate videos → retests; selected path highlighted. Persistent top-left brain, bottom idle voice dock and accessible persisted log. Typed/spoken edits use the same validated draft.
4. **Canvas results:** recommended candidate plus original comparison, leaderboard/evidence inspector, selected video/time-aligned curves/brain, actual Condense savings. Verdict reachable at 1440 px; real-world uplift is not claimed.
5. **Compare (P1):** inspect two variant nodes with synchronized video/brain/difference view; return without losing canvas position.
6. **Export:** chosen tested asset and runner-up, report and launch-brief downloads remain the four FR-08 files. Graph complexity must not bury them.

### 12.5 Info card rules

- Region names come from a standard atlas, grouped into a few groups (for example visual, auditory, language).
- "Known for" text comes from a fixed, hand checked list in the repo, not from free LLM text.
- What is on screen comes from the concept's scene data at that timestamp.
- Never emotion, desire, attention guarantees or buying intent.

### 12.6 Visual tokens

- Background near black (`#0A0A0A`), subtle neutral dots spaced about 24 px apart. Cards/floating controls dark gray (`#151515`) with 1 px borders (`#2A2A2A`), restrained radii and shallow shadows; generous negative space. The grid is decorative, not data.
- Brain base light gray. Activity heat scale dark red → orange → yellow, with a threshold so low activity stays gray (like the reference).
- Difference view: diverging scale, warm for more, cool for less, legend always visible.
- Primary text warm off-white (`#F3EFE9`), secondary text gray (`#ABA7A2`). Shared UI accent orange-red (`#FF5A36`) for selection, the active path and primary action; inactive connections remain muted. Use dark text on filled accent buttons (small white text fails normal-text contrast). No lime/green brand theme, rainbow cards, full-screen bloom or constant glowing borders. Status is written/icon-labeled, not color alone.
- Use the supplied Redaction font for product identity, headings and card titles; Redaction20 is a restrained large-display option, not weight 20. Keep existing readable sans for dense controls/transcripts and mono for timestamps. Self-host the supplied licensed WOFF2 files; include their original OFL/copyright. The [font handoff](public/fonts/redaction/README.md) and opt-in [theme stylesheet](docs/design/preflight-theme.css) provide shared assets, not a deployed application change. These exact tokens/selective font uses are implementation choices under the owner's approved direction.
- Segmented controls: rounded pills, dark gray background, active option filled lighter.

### 12.7 Performance

- Target smooth playback on a recent MacBook. fsaverage5 is about 10,000 vertices per hemisphere, which is light for three.js.
- Preload all variants' brain data before the intro starts. First paint of Results under 2 seconds after the intro.
- For entry without run data, preload only the licensed mesh and any genuine disclosed example bundle. Do not wait for unstarted GPU jobs. In analysis focus, preload the actual chosen results before animating.
- Large graph rendering uses viewport virtualization/level-of-detail. Brain and voice visualizers yield when hidden, pause on background tabs and respect reduced motion. Record hardware and node count; do not advertise unmeasured “at scale” or a smooth 125,000-node DOM.

### 12.8 Words

**We use:** simulated viewers, brain sim, pretest, winner, why, launch brief.

**We never use:** "TRIBE output", "will go viral", "predicts sales", "reads emotions", "mind reading".

### 12.9 Two-way Live Director, orb and glow (FR-16)

**Latest bottom-dock layout — v1.6.2:** voice mode replaces the bottom prompt, not the canvas. Show reference 10's neutral gray Libraries.dev composing orb at the bottom, compact captions and separate mute/end controls. No white background, full-screen voice surface, dimming or surrounding card; source/storyboard/brain/console interaction stays available. A native-resolution 160 px orb (136 px on short viewports) reuses the tuned 64 composing geometry in every phase: real phase changes cadence/status, not avatar identity. Actual post-gain output amplitude drives smooth growth and wave deformation; mute/interruption/disconnect resets immediately. The warm `VoiceBeam` is anchored to the viewport's bottom border beneath the orb, independent of the controls, and reacts to the same audio. Closing restores the prompt and its voice-button focus; reduced motion freezes orb motion/growth and beam travel. This supersedes the v1.6.1 controls-beam and earlier central-orb clarifications.

**Required experience:** real two-way Gemini Live, not narration-only TTS. After Enable Live and mic permission, the user can ask questions, hear replies, interrupt, choose a storyboard/scene and ask for a source-grounded pre-render change that updates the actual canvas/draft. Verify the proposed `gemini-3.8-live` model/account and audition a supported female-sounding preset (the Voice workspace proposes Kore; not yet verified). Use an original mission-control personality, not a clone of JARVIS or an actor. The Director can recommend and explain a tradeoff, but respects an explicit user choice within safety/source/budget constraints.

**Conversation and commands:** show input/output transcripts and actual connecting/listening/working/speaking/error states. Interruption stops queued assistant audio immediately and feeds the next user turn; do not replay interrupted/stale speech. Route typed and spoken commands to the same validated application state (§9), persist accepted changes and report the tool result, not merely “done” in speech. Selecting/changing a storyboard is P0 before rendering; a tested-winner revision remains P1. Filling fields/selecting nodes is not job authorization: summarize the current run and require an explicit confirmed Run action, clicked/typed or acknowledged spoken command. Reject invalid/stale/source-inventing commands and deduplicate execution on reconnect.

**Actual work context:** consume the same persisted events/evidence as the canvas. Deduplicate event IDs, bound pending audio/context, suppress stale progress after the verdict and never narrate every graph node. Speak concise welcome, actual job milestones/unavailable states and why the selected result was recommended; allow follow-up questions. Label future intentions as future intentions. Long jobs do not occupy a blocking Live tool call: report accepted/queued then use persisted completion events. An audio/provider failure is separate from a failed video job; preserve typed operation but report FR-16 as unmet if the real two-way path fails. Stop/mute is immediate and audio/mic never restarts against the user's preference. TTS-only/text-only mode is degraded fallback, not a passing demo.

**Required orb-first visual direction:** a standalone [Libraries.dev Orb](https://libraries.dev/orbs.html), package `thinking-orbs` (registry v0.3.2 checked on 3 Oct 2026, MIT, React ≥18), is the assistant's visible identity. No enclosing chat card, bordered panel or bulky controls around the orb. It grows smoothly when the assistant speaks; captions/transcript and mute/stop remain accessible separately. Use the tuned 64 preset and a presentation wrapper for larger speaking scale, with reduced-motion/performance checks. Verified v0.3.2 uses `theme="dark"` and supports an optional `color` tint; use our warm accent, not an invented `dark` or `level` prop. States such as composing/working/connecting reflect actual job/service state; listening is only shown while a permitted microphone is actually live. Speech-responsive scale requires our own actual playback state/analyser binding, not microphone amplitude or queued text. See the [controlled visual example](docs/design/DIRECTOR_VISUALS.md).

**Required prompt glow:** [Libraries.dev Voice](https://libraries.dev/voice.html), package `voice-glow` (registry v0.2.1 checked on 3 Oct 2026, MIT, React/ReactDOM ≥18). `VoiceBeam` wraps the prompt with a restrained bottom-edge beam, customized warm lobe/band colors and no rainbow hue drift. For assistant speech, drive `level` from the actual output audio's Web Audio analyser (0–1); `processing` reflects actual pending agent/session work. During explicit listening, input amplitude may be displayed as clearly labeled input, never assistant speech. A mic `stream` overrides `level` and visualizes user input, not the assistant's output meter. A glow/orb is not speech synthesis, speech recognition, Live transport or neural activity. Share the explicitly enabled microphone capture with the Live owner rather than creating competing mic sessions/large visualizers; do not call another `useMicrophone` in this UI layer.

**Browser safety:** output audio and mic acquisition require an appropriate user gesture; microphone additionally requires HTTPS/localhost and permission. Never silently enable a mic on first visit. Show listening/privacy state; release tracks/audio nodes and close the Live session on disconnect/unmount. Avoid recording by default and keep long-lived keys out of the client. Provide captions, distinct mute/stop/disconnect controls, reduced-motion behavior and plain-input fallback. Verify denied permission, disconnect/reconnect, expired token, quota and tool failure without falsely reporting a successful command.

**Provider gate:** Live uses its own model/session transport, not the TTS endpoint or a visual library. Verify key/project/model access and Condense Live support, or obtain/document a product-owner routing exception before a direct Live path. This v1.5 scope decision does not waive FR-10. Record the actual route, tested voice/model, session/budget controls and remaining provider blockers in README/TEAM; never include secrets.

Technical handoff: [Canvas and voice integration brief](docs/design/CANVAS_VOICE_BRIEF.md). This PRD remains authoritative.

### 12.10 Canvas evidence and job binding

Use one readable left-to-right graph: Original/brief → baseline evidence → three candidate edit/storyboard/video/pretest lanes → original comparison/recommendation/export. Empty intake does not show a wall of empty scenes. Source/output IDs, clip ranges, actual durations and hashes preserve lineage; simplified distant zoom cannot replace evidence. Pan/zoom/fit/selection explain the whole experiment and individual scene. Visual original/candidate evidence comparison is P0; synchronized dual-brain/difference remains FR-15/P1, not a live audience experiment.

Agree with backend owners how node IDs map to project/variant/job IDs, persisted event IDs and video hashes. Reuse the existing state machine and `SimulationResult` contracts; a client-side timer or graph animation cannot declare a backend transition complete. A/B selection uses compatible stored results. Preserve rerender/resimulation traceability when a final Opus composition changes the video (§9.1).

Show status per node: proposed/untested, queued, running, completed, failed or unavailable as supported by actual events. A displayed mock/prototype tree remains separated from the real run, visibly labeled across the graph and voice. Do not claim many experiments merely because a connector tree is large. Default actual run scope is §9.2; extended batch execution requires an explicit budget/throughput decision, not only this visual reference.

## 13. Metrics and validation

**Hackathon success**

- All P0 acceptance criteria pass.
- Full run with 3 variants in under 10 minutes.
- 2 minute demo video recorded with the real product.
- Public repo with a README that lets someone run it.

**Product metrics (after validation)**

- Time to verdict.
- Share of runs that end in an export.
- Backtest hit rate: how often Preflight picks the real winner of historical A/B tests, compared with 50% (chance) and with Gemini alone. This is the number the company lives or dies on.
- Live agreement rate: how often the pretest winner also wins the live A/B test.
- Paying customers.

**Validation plan (logged, not started until tablehopp has a paying customer)** Collect 20 to 50 historical A/B tests with known winners from 5 small companies, run backtest mode, and compare the hit rate against chance and Gemini alone.

## 14. Hackathon execution

### 14.1 Rules (from the opening talk; verify on the platform)

- Submit by 19:00 (heard as "nineteen past seven", check the platform).
- Public GitHub repo, code written today.
- 2 minute demo video: you using the product and explaining it. No AI style presentation.
- Use at least 2 of the 3 partner technologies. Our plan: Gemini and Condense. Ask Metrix if they have GPUs.
- Team of 1 to 5, everyone registered on the platform and in the team.
- Judging: 50% technical, 30% creativity, 20% real problem. Top 5 go to a 5 minute live final.

### 14.2 Timeline (from 12:00)

| Time | Milestone |
| --- | --- |
| 12:00 | Idea locked. Owners assigned. Repo public. Team on platform. Gemini key. Condense form. Brain viewer work starts in parallel (mesh, controls, empty state, no data needed yet). |
| 12:30 | Go/no-go: TRIBE runs on one clip; template renders one video; a real two-way female Gemini Live exchange and interruption work, with model/account/Condense routing recorded. |
| 14:00 | FR-01 to FR-03: brief, plan, 3 rendered videos. Canvas intake/lineage, brain entry/dock and FR-16 spoken storyboard selection/edit/confirmed Run work. |
| 15:30 | FR-04 to FR-06: simulate, score, explain. First real TRIBE data shown in the brain viewer. |
| 16:30 | FR-07 to FR-10: results UI, export, log, Condense. |
| 17:15 | FR-14 genuine-data analysis focus and FR-16 actual milestone, spoken verdict/follow-up, interruption/reconnect/tool/error paths verified. Then P1: compare view, iterate winner. |
| 17:45 | Code freeze. |
| 18:00 to 18:40 | Record the 2 minute video (3 takes), finish README. |
| 18:45 | Submit. |

**Cut order if late:** batch expansion/runtime Opus finalization, then winner iteration, compare/difference and elaborate camera moves (keep entry/dock with fades). If live TRIBE fails at 12:30, drop live neural inference and show the documented Gemini-only fallback; keep the required canvas, gray anatomy/entry/dock and two-way Live Director. Any real disclosed example is separate from the run. Never cut brief → 3 videos → pretest → winner or silently demote FR-16 to TTS-only narration/fake animation. If Live cannot run, explicitly report the unmet P0 and obtain a product-owner scope decision.

### 14.3 Owners (fill in now)

The source PRD leaves technical owners blank. Assign and maintain the live assignments in [TEAM.md](TEAM.md); these areas come from the PRD.

| Area | Owner |
| --- | --- |
| Template and renderer (FR-03) | Unassigned — see TEAM.md |
| TRIBE worker (FR-04) | Unassigned — see TEAM.md |
| Agent, Gemini, Condense (FR-02, 05, 06, 10) | Unassigned — see TEAM.md |
| Web app, results and export (FR-07, 08, 09) | Unassigned — see TEAM.md |
| Brain viewer and Preflight sequence (FR-12, 14, 15) | Unassigned — see TEAM.md |
| Flow canvas and female Gemini voice (FR-07, 09, 16) | See Dashboard/Voice workspaces in TEAM.md; coordinate with brain and backend owners |
| Demo video and pitch | William |

### 14.4 Two minute demo script

- **0:00** "Our company already has this video. What should we change before the next spend?" Full-viewport brain entry → top-left dock → FLORA canvas; Enable Live and hear a real female reply. Example predictions are disclosed.
- **0:15** Upload a genuine existing video; play Original and confirm facts/audience/goal. Run baseline analysis; discuss a real timestamp, interrupt and refine a grounded candidate edit on the actual canvas. Confirm render/retest; fast-forward waiting only with disclosure. Orb replaces the bottom prompt while voice is enabled.
- **0:40** Genuine results populate the canvas. Expand the persistent brain and show a video-aligned region/timestamp; analysis focus if available. Distinguish actual tests from untested hypotheses.
- **1:20** Ask the Live Director why this variant won; hear an evidence-backed answer with timestamps. Show evidence and iteration delta if built; never claim retention/sales prediction.
- **1:45** Show original-versus-candidate evidence and export. "This is the cut we will test with real customers." Mention Gemini, Condense and TRIBE; do not claim proven lift.

### 14.5 Five minute final (if top 5)

Problem (40 s) → live demo (2 min 30) → how it works, the agent and the simulator interface (50 s) → moonshot (30 s) → close: "AI made making videos free. Knowing which one works is the new bottleneck."

### 14.6 Judge Q&A

- **Isn't this a TRIBE wrapper?** TRIBE is one of the simulated viewers behind a common interface. The product is the agent that plans, makes, tests and decides. Turn the brain sim off and it still works.
- **Does it predict sales?** No. It pretests so you only spend real money on the strongest versions. Our first proof point after today is the backtest against real historical A/B results.
- **TRIBE is non commercial?** Correct. It is research use today. The commercial path is our own model trained on simulated response paired with real outcomes.
- **Why would someone pay?** Companies already pay for ad pretesting. We do it for small teams in minutes, and we deliver the finished video.
- **What stops Meta?** Meta has the outcomes but sells the testing. A neutral pretest that saves spend is not their incentive. This is our reasoning, not a proven fact.

## 15. Rules for AI coding agents

1. Read §15, then §8, §9, §10, §12. Build in requirement ID order. No P1 until every P0 acceptance criterion passes.
2. Never mock TRIBE or simulation output in the demo path. Mocks are allowed only in tests and must show a visible "MOCK" banner if rendered in the UI.
3. Never invent product claims, numbers, logos or testimonials in generated videos. Every on screen text needs a `source_field`.
4. Keep simulators behind the interface in §10.2. Adding a simulator must not change scoring or UI code.
5. Secrets only in environment variables. No model weights in the repo.
6. Small, runnable commits. Keep the README "How to run" section correct after every change.
7. Definition of done: acceptance criteria pass, the app runs from a clean clone using README steps, and there are no console errors on the demo path.
8. When unsure, choose the simpler option and write the choice in the decision log (§16).
9. The brain viewer may be built before data exists, but must then show the "No brain data" empty state. Never fill it with random or generated activity.
10. Primary coding agent for this repo: Claude Opus 5.5. Keep this PRD in the repo root as `PRD.md` and update the decision log when a requirement changes.
11. Build Preflight as the browser-based web platform specified in §7.5 and §10. Do not scaffold Swift, SwiftUI, an Xcode project or a native client. References to a customer's mobile app, screenshots or vertical videos describe input/output, not Preflight's implementation platform.
12. Read the shared visual baseline before changing the brain experience. Opus 5.5 owns its implementation; keep the reusable mesh/renderer separate from per-video data and from any planned runtime Opus video-composition calls (§9.1/§10.5). No random “brain waves”, no per-user regeneration of the brain.
13. PRD v1.7 makes existing company video → baseline analysis → improved candidate → retest the main product, superseding screenshots-first/existing-video exclusions. Keep the FLORA canvas, full-viewport entry/top-left same-brain dock and bottom-prompt/bottom-orb two-way Gemini Live presentation. TTS-only/fake dialogue/glow cannot pass Live. Coordinate migration/ownership; a new spec is not shipped acceptance or a Condense exception.
14. Apply the clean-flow design in §12 and its shared brief: near-black dotted canvas, readable left-to-right media/storyboard branches, minimal floating chrome, Redaction identity and restrained orange-red accents. Preserve existing application logic/contracts when changing the shell. New layout references supersede the old radial/sidebar layout, not the anatomical brain baseline.

## 16. Decision log

The original entries below are retained for provenance. **v1.7 explicitly supersedes their screenshots-first output, exclusion of editing existing videos and later-only e-commerce scope.** Later decisions are appended; update affected requirements/version/change notes together.

| Date | Decision | Why |
| --- | --- | --- |
| 3 Oct | B2B: startups and companies, not creators | Companies have money metrics and already pay to pretest |
| 3 Oct | Output is generated motion graphics product demos | Customers pay for the asset; polishing a weak existing video does not fix it |
| 3 Oct | We do not edit customers' existing videos | Same reason |
| 3 Oct | TRIBE v2 is used for analysis inside the pretest, as one of at least two simulators | Strong signal, but research only and must not be the product |
| 3 Oct | Pretest selects, live A/B confirms | Honest about what simulation can and cannot prove |
| 3 Oct | Rejected: creator focus, AI editing of base videos, chief of staff agent | Weaker money metric, does not fix weak content, off track |
| 3 Oct, 12:00 | The interactive 3D brain viewer and the analysis intro are part of the core demo (P0 if TRIBE runs) | Strongest creativity moment (30% of judging); makes the pretest visible |
| 3 Oct, 12:00 | Variant toggle replaces "True / Predicted" from the reference viewer | We only have predicted data; our job is comparing variants |
| 3 Oct, v1.2 | Preflight is a standard web platform accessed in a desktop browser, not an iOS/SwiftUI or other native app. The full user journey and 3D experience are web-based; vertical videos remain export assets. Applies to FR-01, FR-07, FR-08, FR-09, FR-12 and FR-14, and §7.5/§10/§15. | Explicit product-owner clarification; prevents agents and teammates from choosing a native-app architecture based on earlier workspace context or customer app screenshots. |
| 3 Oct, v1.3 | Adopt all three supplied images and the original motion clip as tracked visual references. Claude Opus 5.5 builds the complete interactive brain once; reuse its mesh/renderer with each video's genuine TRIBE data and synchronized A/B instances. FR-12/FR-14 stay conditional P0, FR-15 stays P1. Applies to §10.5/§12/§15. | Explicit product-owner direction: reference-quality 3D that reveals how the system works, with a shared baseline across team workspaces and no per-user brain-generation expense. |
| 3 Oct, v1.3 | Separate coding-agent Opus from desired runtime roles: Gemini for variants/analysis, Opus for the selected finished motion-graphics composition, Remotion for MP4 rendering and TRIBE for neural prediction. Runtime Opus remains planned until credentials, provider routing, budget and API model are verified; it does not add a P0 gate. Changed final videos must be re-simulated. Applies to FR-02/FR-03/FR-04/FR-10/FR-11 and §9.1/§10.4. | Captures the product owner's generation/cost direction without claiming the API exists in the app, conflating Gemini with neural simulation, or presenting a candidate's result as evidence for a different exported video. |
| 3 Oct, v1.4 | Adopt the new flow-canvas image; make a connected pan/zoom storyline/experiment canvas the main workspace with entry brain intro and persistent corner brain. FR-07/FR-09/FR-12/FR-14 and §5/§7/§10/§12 updated. Anatomy/entry/dock remain P0; actual neural animation still needs genuine data and live TRIBE keeps its gate. | Product owner is refining the interface while frontend/backend builds proceed; replaces disconnected dashboard screens and allows a truthful first-visit experience before the user's predictions exist. |
| 3 Oct, v1.4 | Female Gemini voice is mandatory demo P0, explicitly confirmed by William. Add FR-16; event-grounded TTS welcome/progress/verdict plus captions/mute. Orb-first direction: standalone `ThinkingOrb`, no enclosing card, grows during actual speech; prompt `voice-glow` is optional. Move narration out of P2; full two-way Live is a separate P1 extension. | Product owner's explicit wow-moment and visual direction, aligned with Gemini sponsor use. This is our requirement, not a verified event rule that voice is compulsory; an animation is not a voice engine. |
| 3 Oct, v1.4 | Keep “realtime” as real job events plus synchronized presentation of stored predictions. Large-scale branching is an architecture direction; three full videos/one P1 revision remain the default until batch budget/GPU throughput are approved. Separate proposed nodes from rendered/tested artifacts. | Prevents visual prototype scale from being mistaken for 125,000 genuine neural tests and prevents unapproved exponential cost. |
| 3 Oct, v1.5 | William explicitly confirmed two-way Gemini Live as FR-16/P0, superseding v1.4's TTS minimum/optional Live. Require listening/replies/interruption, transcripts, validated source-backed storyboard selection/pre-render editing with visible persisted canvas changes, explicit Run confirmation and actual progress/verdict. Preserve female original voice, standalone orb, secure session lifecycle and event truth. Update §5/§7/§8/§9/§10/§12.9/§14/§15. | Owner requires the interactive creative Director for the wow-moment demo; narration-only does not satisfy it. Three-video cap and FR-11/P1 tested-winner revision remain. Model/account/Condense Live transport are still unverified; this does not approve a routing exception or claim implementation acceptance. |
| 3 Oct, v1.6 | Adopt FLORA and the owner's FLORA workspace screenshot as the primary product-layout reference; earlier two clean-flow/dark-dot images remain supporting references. Use black dotted canvas, narrow floating left tool rail, compact corner actions and readable source/storyboard/render/pretest/result branches. Adopt Redaction/orange-red identity and require both standalone speaking-growth ThinkingOrb and restrained prompt VoiceBeam. Keep top-left hover/pin brain and actual milestone → roughly three-second slower camera/text → resume choreography. Exact tokens/selective fonts/effect tuning are logged implementation choices. Applies to FR-07/FR-09/FR-12/FR-14/FR-16 and §12/§15. | Explicit owner corrections: "exakt denna design" at flora.ai, minimal black dotted high-tech product, and both Libraries.dev visuals adapted for us. Preserve cinematic anatomy and real backend/voice logic; no fictional response, unlimited tests, FLORA branding/features or provider change. Gemini Live remains two-way P0. |
| 3 Oct, v1.6 quality clarification | Add the owner's Specific screenshot as a supporting reference and make "minimum interface, complete capability" explicit: contextual primary action, details on demand, persistent safety/evidence controls. Sana-like restraint describes the desired feel. FLORA remains the primary shell; no new feature/platform/provider scope or AC removed. Applies to §12 and existing UI requirements. | Owner emphasizes professional UI/UX and subtraction, not feature deletion. Prevents the additional reference from reintroducing a permanent sidebar or hiding necessary controls under the guise of minimalism. |
| 3 Oct, v1.7 | William clarifies existing company/e-commerce video as primary input: baseline pretest → grounded edit hypotheses → candidate renders/retests → original comparison/recommended export. Supersede screenshots-first and the historical existing-video exclusion. Full-viewport cinematic entry must hide/inert host UI and lock scroll before same-brain top-left docking. Gemini Live orb is large/central during conversation, small/bottom when inactive; localized multicolor beam is permitted. Applies to FR-01–FR-09/FR-12/FR-14/FR-16 and §1–§12/§14/§15. | Explicit owner correction after reviewing the live interface. Preserve bounded three-candidate/one-template/15-second exports, add one original baseline, keep additional winner iteration and dual-brain difference P1. Coordinate schema migration and report actual evidence; no guaranteed retention/psychology/frequency claims, fake waves or automatic merges. |

| 3 Oct, v1.6 implementation | Reuse Gemini Live's single microphone and `AudioContext`; measure assistant output after its gain node, discard queued playback on interruption/mute/disconnect, and bind the one canvas brain to a project id only after the backend accepts that project. | Keeps voice visuals tied to audible playback, prevents a second capture/service, and prevents local draft ids or audio amplitude from becoming false brain/job evidence. Applies to FR-07/FR-12/FR-16. |
| 3 Oct, FR-16 implementation clarification | Latest owner gesture: voice is a button inside the text bar; explicit click opens a large central standalone orb, End/Escape returns it smoothly to that button and disconnects. Use the library's public engine at native resolution for the large orb, its supported 20 preset in the active button, and real-audio VoiceBeam. Expose actual host capabilities, serialized tools and one snapshot-bound spoken/clicked run command. | Makes the owner's FLORA/minimalism direction and required two-way voice usable without a permanently floating side avatar or blurry bitmap. The supplied builder guide requires voice-first operation; see docs/VOICE_FIRST_ACCEPTANCE.md. This branch is based on main's v1.6 implementation; the owner's broader video-first v1.7 baseline remains in pending docs PR #1 and is not silently implemented by changing the voice prompt. |
| 3 Oct, v1.6.1 / FR-16 placement correction | Voice button inside the bottom prompt → fairly large standalone orb **at the bottom, instead of the prompt** → End/Escape restores the prompt and disconnects. Adopt reference 10's neutral gray Libraries.dev orb. No full-screen voice view, canvas dimming or surrounding card. Implementation uses native 160 px canvas (136 px on short viewports) with the library's tuned 64 geometry, restrained warm beam and compact controls/captions. | Explicit owner correction of the preceding central-orb interpretation. Keeps canvas interaction primary and Gemini Live functional; no audio/provider/backend/brain scope change. |
| 3 Oct, v1.6.2 / FR-16 orb and floor | Reference 10 is the library's composing sash: preserve it instead of a breathing/loading ring, even when disconnected. Actual assistant output amplitude drives both orb growth/deformation and a warm VoiceBeam anchored at the screen's bottom border, like a floor beneath the orb. The briefly requested white circle is withdrawn; transparent orb on black. Honest phase labels/paused disconnected visuals, compact controls and existing audio/job/brain contracts remain. | Owner reports mismatched orb and connection failure in the preview, then clarifies the simultaneous floor effect and withdraws the white substrate. No new microphone/service. Main token probe passes; protected Preview needs separate provider/configuration verification. Pin token issuance to the SDK-documented v1alpha API and emit only allowlisted error categories; do not claim this proves the Preview root cause or a real conversation. |
| 3 Oct, sound addendum | Add narration (Gemini TTS, voice `Kore`), a synthesized music bed and effects to the exported winner and runner-up after the pretest; the picture stream is copied unchanged; the verdict covers the silent render and the launch brief says so; narration bypasses Condense (logged exception, owner to confirm). Applies to FR-08 and §9.3. | The owner wants finished ads with audio. Keeping the tested silent render and the sound cut as separate, hashed files keeps the pretest claim honest. |
| 3 Oct, v1.6.3 / FR-17 FINAL-OPUS | William: “CONNECT OPUS FIRST WITH THE LAST STEP”. Connect runtime Opus only to one explicitly confirmed winner motion-finalization job. Opus recipe → existing Remotion template → local music/SFX → exact-final-byte Gemini/available-TRIBE pretest → separate final MP4/evidence. Preserve original candidates/ranking/export and existing voice/audio owners' work. Docs verify `claude-opus-5-5` and Condense's native Anthropic route; configure keys on the Python host, never forward Vercel secrets. Cap output/attempts and persist checkpoints/locks. | Makes the requested expensive final step executable without pretending that Opus generates video pixels, reusing a different video's brain data, widening creative scope or silently approving the existing direct-TTS exception. Code/tests are not evidence of live account/deployment success; those gates remain explicit. |
| 3 Oct, v1.7.1 release reconciliation | Integrate the existing-video product target from PR #1, newer anatomical entry/dock from PR #3 and voice/Opus from PR #11; PR #4 is superseded by the current canvas, asset inspection and server-key compatibility. Later owner corrections win: voice replaces the bottom prompt with the transparent composing orb and warm bottom-border beam, never a central takeover. | Explicit owner request to resolve all PRs and deploy. Current implementation still uses screenshot intake; video-first migration and genuine Live/Opus/TRIBE acceptance remain separately reported gates. Preserve current source/audio/privacy/consent boundaries and teammate work. |
| 3 Oct, FR-05/FR-07 report display | Retain backend ranking and confidence. Display raw mean goal-fit × 100 only for complete Gemini-panel-only runs; mixed neural/panel and missing-series runs retain relative scores. Gaps below five panel points are a close-call UI heuristic, not statistical significance. Admin launch examples are illustrative, not measured results. | Release review prevents averaging unlike neural/panel scales or claiming observed retention from simulated hold/drop events. No scoring algorithm or scientific validation claim is changed. |
| 4 Oct, narration voice | Ad narration uses Gemini prebuilt `Leda` (calm youthful feminine) instead of `Kore`. Live Director stays `Kore`. Strip clipped TTS tails and fade speech edges so the last phoneme does not rasp. Applies to §9.3. | Local demo: Kore sounded androgynous/firm; TTS clips ended in a near-full-scale burst. Keeps the female-ad requirement without changing the Live preset. |
| 4 Oct, brief spaces / motion | Trim brief text fields on blur/commit, not each keystroke. Surface `goal_note` as optional CTA copy. Planner `plan-v4` opens problem-first on audience/one-liner then product, and uses goal_note for the end card when present. Same template family: Ken Burns on screenshots, fade-in hook, 20-frame transitions, caption overlay on the device. Screenshots stay bitmaps — no invented UI graph animation. Applies to FR-01/FR-02/FR-03. | Concatenated on-screen words (“Sellanythingonline”) came from live `.trim()`; the Shopify-style motion notes fit Ken Burns/transitions without a second template or unsourced claims. |
| 4 Oct, two-track motion (local) | Opt-in `render_mode` (`showcase` default vs `generative_motion`). Mode 2 is a parallel 60 fps / 900-frame Remotion composition, not the default FR-03 template. Showcase stays 1080×1920 30 fps one family. Failed/low-confidence extraction falls back to Showcase in the same run. Labels still follow `source_field` grounding. Local Cursor experiment; not published. | Pixel-exact screenshots remain the pretest picture unless the operator opts in. Avoids silently redrawing customer UI. |
| 4 Oct, video engine pacing | Lock the last 3.0 s as the end card at both 30 fps and 60 fps; text in 0.6 s then hold; soundtrack follows the spec that was actually rendered; CTA copy is `goal_note` / `one_liner` / `product_name` plus optional uploaded logo. Planner `plan-v5`. Mode 2 stays fail-closed. Opus/FR-17 not in this change. Applies to FR-03/FR-02/§9.3. | Launch A showed 1 s dark CTA at 60 fps, mid-word kinetic type, and VO from the Showcase hook. Seconds, not frame constants. |
| 4 Oct, P0 picture/sound contract | Reserved type band + punch-in of the largest UI bbox (Mode 2 no longer letterboxes the whole 16:9 photo in the middle). Overlay type wraps; never ellipsizes. Mode 2 only when every variant can compose, otherwise all Showcase. Mix narration/music on all rendered variants before the Gemini panel. CTA copy still never invents words; empty `goal_note` stays product name. Opus/FR-17 untouched. Applies to FR-03/FR-04/§9.3. | Owner asked for watchable, goal-locked 15 s films in one run. Mixed Mode 1/2 ranking and silent pretest were hiding craft failures. |
| 4 Oct, stacked picture bands | Overlay type and the product occupy two clipped bands with a 40 px gap (type 220–500, product from 540). Max two overlay lines. Device is fitted inside the product band; animation cannot cross the gap. Same rule in Showcase and Mode 2. Applies to FR-03. | Launch videos put the headline and the device in the same vertical span. |
| 4 Oct, Leda retry | Gemini TTS 429 retries twice with backoff; variants mix one at a time so identical lines hit the disk cache; a line that still cannot fit is trimmed to its window instead of silencing the voice. Music-only remains only when every line fails. Applies to §9.3. | Latest launch-draft mix logged `narration unavailable... 429` and dropped Leda. |
| 4 Oct, motion-ad standard track | Showcase opens on a type-only hook, then product scenes. Landscape screenshots fill the product band without a second device frame and zoom 1.00–1.16; portrait screenshots keep one phone frame. Planner `plan-v6` rejects adjacent screenshot repeats and identical A/B/C sequences. Panel `panel-v2` lowers goal_fit when the moment addresses someone other than the brief audience. Copy stays source-backed. Condense and TRIBE stay optional and off. Opus/FR-17 untouched. Applies to FR-02/FR-03/FR-04. | The default path was a slideshow of the same screens reordered, with a tablet frame around landscape mockups. Motion ads have to hold without those two providers. |
## 17. Open questions

- v1.7 video-intake migration: agree validated upload size/duration/container limits, clip/audio/crop handling, canonical original/artifact IDs, durable source storage and baseline-versus-candidate time normalization with backend/Canvas/Voice/brain owners. Existing screenshot schemas/routes are not video acceptance. Demo exports retain 15 s/1080x1920/30 fps until explicitly changed; use a genuine compatible clip and report limitations.

- Public repo URL to paste into the header and §10.4. **Repository import update:** URL filled in as https://github.com/clawmax12-lang/Norrsken; visibility was PRIVATE when checked on 3 Oct 2026. Public visibility remains outstanding; see TEAM.md.
- Exact submission time (19:00 or 19:19).
- GPU source for TRIBE (sponsors, Metrix, Colab, cloud).
- Template style. Reference: modern SaaS launch videos (for example the Lovable 2.0 launch video).
- Lunch time (unclear in the opening talk).
- Runtime Opus finalization: verify API model availability, Condense routing, server credentials, exact budget/latency and whether it fits today's P1 timebox. Coding-agent availability in Conductor alone does not resolve these.
- Voice P0: scope is resolved as two-way Gemini Live (FR-16), not TTS-only. Verify proposed Live model/account access, audition the female-sounding preset, agree typed tool/draft/event contracts and session/cost bounds, and verify Condense Live transport or obtain an explicit approved routing exception. No key material belongs in this document.
- Batch scale: approve limits/pruning/GPU concurrency/cost/latency before increasing today's one-original/three-generated-candidate budget.
- Shared UI/job integration: agree event IDs/transport, artifact hashes and the cortical adapter payload; merge current baseline so older branches do not continue on v1.1.

## 18. Glossary

- **Pretest:** testing video variants on simulated viewers before spending on real ads.
- **Simulated viewer:** any model that predicts how people respond to a video (TRIBE v2, Gemini panel).
- **Brain sim:** TRIBE v2's predicted average brain response.
- **Preflight sequence:** the entry brain reveal/dock and, with genuine run data, the 10–15 second analysis focus.
- **Canvas:** connected source/storyboard/variant/test/result nodes with lineage and actual evidence, not a count of executed jobs by itself.
- **Realtime:** live job status and responsive playback of available predictions; not measured live EEG or inference per animation frame.
- **Live Director / voice companion:** mandatory female-sounding two-way Gemini Live assistant for storyboard selection/pre-render editing and actual progress/verdict; TTS-only is degraded fallback, not P0 acceptance.
- **Launch brief:** exported Markdown with which video to post, which to A/B test, and what to change next time.
- **Backtest:** running Preflight on historical A/B tests with known winners to measure its hit rate.
