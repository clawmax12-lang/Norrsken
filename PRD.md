# Preflight · Product Requirements Document

**Version:** 1.6.2 · **Date:** 3 Oct 2026 · **Status:** Hackathon build ({Tech: Europe} Agentic AI Hack, Norrsken Stockholm)

**Owner:** William (product) · **Tech owners:** see §14.3 and [TEAM.md](TEAM.md)

**Repository:** https://github.com/clawmax12-lang/Norrsken

**Built with (PRD plan):** Claude Opus 5.5 as the coding agent · Gemini · Condense · TRIBE v2 (Meta FAIR, research use)

**What changed in 1.6.2:** reference 10 is the Libraries.dev **composing** dotted sash, not the breathing ring. Preserve that orb silhouette through all connection states, paused with an honest label when disconnected. Its growth and wave deformation follow actual post-gain assistant amplitude, not merely a boolean speech flag. In voice mode the required warm `VoiceBeam` sits on the **viewport's bottom border, like a floor beneath the orb**, not around the controls. Both react simultaneously to the existing audio graph. The owner withdrew the briefly requested white circular background: orb stays transparent on black. Bottom-only placement, captions, privacy/mute/end, reduced motion, Gemini Live and all backend/brain contracts are unchanged. See §16.

**What changed in 1.6.1:** the owner corrects FR-16's placement: the voice button stays inside the bottom text bar; enabling voice **replaces that bar with a fairly large standalone orb at the bottom**, not a central/full-screen surface. No canvas dimming, backdrop, card or modal. Keep the canvas usable, compact captions/mute/end and the real-audio beam; closing restores the prompt and keyboard focus. The latest supplied gray Libraries.dev orb is [reference 10](docs/design/references/10-voice-orb-bottom.png). This supersedes the earlier central-orb implementation clarification without changing Gemini Live, jobs, the brain or the separate video-first migration.

> This is the team's canonical, editable product specification. It supersedes earlier brainstorming and advisor briefs. The baseline was imported from the complete, 20-page [Preflight PRD v1.1.pdf](docs/source/Preflight-PRD-v1.1.pdf), which is preserved unchanged; see [source provenance](docs/source/README.md). Versions 1.2–1.6 incorporate the product owner's web-platform, reusable-brain, canvas, voice and clean-flow design decisions, documented below and in §16. Actual implementation progress lives in [TEAM.md](TEAM.md), not in these requirements.

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

**Preflight is a web platform accessed through a URL in a desktop browser.** Users do not install an iOS app or any other native client. The web platform is the product; customers' apps and screenshots are input material.

Startups need a demo video for every launch, but agencies take weeks and nobody knows which version will actually work until after they have posted and paid for ads. Preflight's agent turns your product into several motion graphics demo videos, pretests them on simulated viewers (TRIBE v2 brain simulation plus a Gemini viewer panel), and hands you the winner, why it won, and the runner up for a live A/B test.

The product feels like a creative mission-control workspace: a cinematic brain on entry, an explorable storyboard/experiment canvas, a persistent brain companion and a two-way female Gemini Live Director. Talk to her to select/refine the storyboard and ask about actual progress and the verdict; confirmed tool changes are visible on the canvas. These make the generation → pretest → decision loop understandable; they do not replace the finished-video outcome.

## 2. Working backwards

### 2.1 Press release (the day we launch)

**Preflight: launch videos that are tested before anyone sees them**

Startups launching a product today either pay an agency and wait weeks, or make a video themselves. Either way they only find out if it works after it is posted and the ad budget is spent.

Preflight changes that. Upload a few screenshots of your product, say what you want viewers to do, and in minutes Preflight's agent produces three motion graphics demo videos, each built on a different idea of what will make viewers act. It plays every version to simulated viewers, including a simulation of the human brain's response, and tells you which one to launch, why, and which one to A/B test against it.

> "I was about to pay for my app's launch video and had no way of knowing which style would work. I wanted to know before I paid, not after." (William, founder of tablehopp and Preflight)

### 2.2 Customer FAQ

- **Where do I use Preflight?** Open the web platform in your desktop browser. No iOS app, App Store installation or native client is required.
- **What do I need?** 3 to 6 screenshots of your product, one sentence on what it does, your goal (for example sign ups), and who it is for.
- **How long does it take?** Target under 10 minutes for three tested videos.
- **Does it guarantee results?** No. It ranks versions by simulated viewer response so you only spend real money testing the strongest ones. Confirm with a live A/B test.
- **What is the brain view?** A research model (TRIBE v2 from Meta FAIR) that predicts the average human brain response to video, audio and language, second by second. It is one of several simulated viewers.
- **Will it make things up about my product?** No. Every word and screen in the video comes from what you provided.

### 2.3 Internal FAQ

- **Why generate videos at all?** `[DECISION]` Customers pay for a finished asset, not a report. Polishing a weak existing video does not fix it, so we generate from the product itself.
- **Why not only generate?** Generation is becoming a commodity. Knowing which version works is the scarce part. Generation plus pretest is the product.
- **TRIBE v2 is non commercial. How is this a business?** `[FACT]` TRIBE v2 is CC BY-NC 4.0. We use it for research and this hackathon. The commercial path is our own audience model trained on outcome data (simulated response paired with real A/B results).
- **What must be true for this company to exist?** Simulated pretesting must pick the real winner more often than chance and more often than an LLM alone. See §13 and the validation plan.

## 3. Problem

### 3.1 Problem statement

When a startup launches something, it needs a video that makes people understand the product and act. Today it cannot afford agency quality for every launch, and it has no way of knowing which version works before posting and paying. So it ships one video based on gut feeling and learns nothing for next time.

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

**Primary persona: the launch week founder.** Founder or first marketer at a 1 to 20 person startup (app or SaaS). No motion designer. Launches on LinkedIn, X, Instagram, TikTok, often with a small paid boost. Success means sign ups or downloads from the launch.

**Secondary (later):** e-commerce marketers, small agencies producing for several clients.

**Anti personas (we do not design for them):** big brands with research departments, creators chasing entertainment virality, anyone who wants a guarantee.

**Job to be done:** "When I am about to launch, help me ship a demo video I am confident in, so the launch brings users and I do not waste the launch moment or ad money."

## 5. User journey

### 5.1 Today

| Stage | What they do | Pain |
| --- | --- | --- |
| 1. Trigger | Launch date is set | "We need a video" panic |
| 2. Find a style | Scroll reference videos | Most references feel wrong, hours lost |
| 3. Make it | Agency (weeks, cost) or DIY (amateur) | Time, money, quality |
| 4. Choose | Gut feeling, ask friends | No real signal |
| 5. Publish and boost | Pay for ads, wait days | Money spent before knowing |
| 6. Learn | Rarely | Next launch starts from zero |

### 5.2 With Preflight

| Stage | What happens | User sees |
| --- | --- | --- |
| 1. Trigger | "We launch Wednesday" | Cinematic brain entry, then the brain docks; explicit Enable Live action starts the female Director |
| 2. Brief (2 min) | Uploads screenshots, one sentence, goal, audience; talks with the Director to select/refine the storyboard | Validated brief and actual storyboard changes on the canvas; listening/responding, interruption and transcripts |
| 3. Agent at work (under 8 min) | Agent plans 3 hypotheses, renders 3 videos, runs simulated viewers | Branching storyboard/experiment nodes, live job status, captions/voice and persistent brain |
| 4. Verdict | Winner, why, where other variants differ in the simulation | Verdict/leaderboard on the canvas, synced video/curves/brain and optional focus sequence using genuine data |
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

Brain entry → flow canvas + brief → agent plans 3 variants → two-way female Gemini Live Director selects/refines the storyboard with the user → confirmed render of 3 motion graphics videos (one template) → pretest with TRIBE v2 and Gemini panel → ranking with reasons → export, with a persistent reusable brain and Live conversation throughout. Neural animation requires genuine data. P1: synchronized A/B/difference view and one iteration on the tested winner. Scalable branching experiments are the longer-term architecture; today's number of actual rendered/tested videos is still bounded.

### 7.2 V1 (only after validation, see §13)

Ad account connection, launch live A/B tests, ingest real results, brand kit, more templates, backtest mode.

### 7.3 Moonshot

A simulated audience for all content: every launch video, ad, trailer and landing page is tested on simulated people before it meets real ones. Every customer's real results train our own audience model. AI made making content free; Preflight owns knowing what works.

### 7.4 Non goals (today)

- Editing customers' existing videos `[DECISION]`
- Text to video generative models (no generated footage, only motion graphics from real screens)
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

**Inputs:** product name; one line description (max 140 chars); 3 to 6 screenshots (PNG or JPG); goal (sign ups / downloads / understand the product / purchase, plus optional free text); audience (free text); optional brand color and logo.

**AC:** form validates required fields; brief saved as `brief.json` matching schema §10.3; a fixture brief for tablehopp exists in `/fixtures`.

#### FR-02 Creative plan

The agent produces exactly 3 concepts. Each concept has: a hypothesis (for example problem first, outcome first, product first), hook text (max 8 words), 4 to 6 scenes, screenshot per scene, on screen text per scene, CTA, duration 15 s.

**AC:** output validates against `CreativeConcept` schema; the 3 hypotheses are different; every text claim can be traced to the brief (agent stores the source field for each claim).

#### FR-03 Render

Each concept renders to MP4, 1080x1920, 15 s, 30 fps, using one motion graphics template driven by the concept data.

**AC:** 3 MP4s render with no manual step; render time logged per video; a failed render is retried once, then marked failed without stopping the run.

#### FR-04 Pretest (simulate)

Every variant runs through the simulators: TRIBE v2 (brain sim) and Gemini viewer panel (3 personas derived from the audience field).

**AC:** one `SimulationResult` per variant per simulator, matching schema; TRIBE results in the demo are real model output (live or precomputed, and if precomputed, disclosed in UI and README); if TRIBE is unavailable the run still completes with Gemini only and the UI shows "Brain sim off".

#### FR-05 Score and rank

A goal aligned score per variant, a ranking, and a confidence label (High if simulators agree on the winner, Low if they disagree).

**AC:** same inputs give the same ranking; confidence rule documented in code and README.

#### FR-06 Explain

For each variant, 2 to 4 reasons, each tied to a timestamp and to what is on screen at that moment (hold moments and drop moments).

**AC:** every reason has a timestamp inside the video length and references a real scene from the concept.

#### FR-07 Flow canvas and results UI

Browser-based flow canvas: brief/source nodes → storyboard/concept branches → rendered variants → simulation/result nodes → recommendation/export. Use spacious, readable media/storyboard cards with left-to-right curved tree branches on a near-black dotted canvas, not a radial cloud of tiny dots. Selecting a node opens its evidence without losing the graph; an on-demand results inspector contains the leaderboard, video player, per-second synced curves and verdict card ("Launch C. A/B test it against A."). No permanent sidebar or oversized idle chat panels. See §12.4 and §12.10.

**AC:** canvas pan/zoom, fit-to-flow and node selection work in the desktop browser; the default view shows readable source/storyboard/media cards and A/B/C lineage with minimal floating controls on the black dotted canvas; rendered/tested nodes have real artifact/result links and visible status; graph branches show lineage and the selected storyline; curves follow scrubbing; verdict accessible without scrolling on a 1440 px wide screen; corner brain and voice dock do not obscure core controls. Typography/accent follow §12.6, dense evidence appears on demand and keyboard focus remains visible. Prototype-only or untested nodes are explicitly labeled and never counted as completed tests. No native client is required.

#### FR-08 Export

Download winner MP4, runner up MP4, `report.json`, and a Markdown launch brief (which to post, which to A/B test, what to change next time).

**AC:** all four files download and open.

#### FR-09 Agent activity log

Visible step by step log: plan, render, simulate, score, explain, each with status and duration.

**AC:** log updates live during a run and is saved with the project; the canvas and voice use this same source of job truth, including retry/failure/unavailable states. A reconnect does not duplicate completed nodes or narration, and no progress percentage/completed-test count is invented.

#### FR-10 Partner tech

Gemini for planning, viewer panel and explanations. All LLM calls go through Condense. Show token savings in the UI.

**AC:** savings number visible on the results screen. This is required for eligibility (at least two partner technologies).

#### FR-12 Interactive 3D brain viewer

**P0 viewer/anatomy/dock; genuine neural animation is conditional on available TRIBE data.** Build the fsaverage5 brain inside a head silhouette once and reuse it for the entry, persistent corner view and expanded analysis. With genuine results, predicted activity is synced to video playback. Controls and behaviour as specified in §12.3. This v1.4 split supersedes dropping the entire viewer when live GPU inference is unavailable.

**AC:** the reusable anatomical viewer and persistent corner dock work without a Gemini/GPU call; orbit, zoom, region click, expand/dock and scrub work; the dock identifies the selected variant and actual playback/sample time. Activity comes from real TRIBE results only; without data show "No brain data" with gray anatomy, never generated/random activity. Unavailable live inference shows "Brain sim off"; any genuine sample shown instead is visibly "Demo example · precomputed", not the current run. Playback runs smoothly in a desktop browser on a recent MacBook; record actual hardware used for verification.

#### FR-14 Entry intro and analysis focus, the "Preflight sequence"

**P0 entry intro, depends on FR-12's reusable renderer.** First arrival opens a 10–15 second rotating brain/camera sequence, then docks the brain and reveals the canvas. When genuine pretest results are ready, the same renderer may run the data-grounded analysis focus sequence from §12.2, once per run.

**AC:** entry plays once per browser session (explicit Replay permitted); Skip is always visible; reduced motion uses fades/static framing; completion/Skip reaches the canvas and leaves the brain docked with its state preserved. Before the user's first run, any colored response must come from a genuine video-matched example labeled "Demo example · precomputed"; no example means gray anatomy and "No brain data". The run's analysis sequence only uses that run's genuine results, plays at most once per run and hands back to the canvas results inspector. No fake waves while waiting for inference.

#### FR-16 Two-way female Gemini Live Director

**Placement — v1.6.2:** the button is inside the bottom text bar. Enabling voice replaces the prompt with reference 10's neutral composing orb in the bottom dock, transparent on black; no white substrate, central/full-screen overlay, backdrop or canvas dimming. Keep the same silhouette even when disconnected, with a paused visual and honest status rather than a loading ring. The warm audio-reactive VoiceBeam is anchored on the viewport's bottom border beneath the orb. Orb amplitude/deformation and beam react simultaneously to actual playback; listening input is separate and cannot drive assistant speech growth. Canvas controls remain usable. End/Escape restores the text bar/focus and releases the microphone.

**P0, explicitly required by William for the hackathon demo.** An original female-sounding Gemini Live creative Director listens and responds in a real two-way conversation, helps choose/refine the storyboard and explains actual agent transitions and evidence-backed conclusions. Tone: concise, capable, cinematic mission control, not an imitation of a copyrighted character's voice. Required visuals are a standalone state-driven `ThinkingOrb`, growing during actual assistant speech without a surrounding card, and `VoiceBeam` from `voice-glow` along the prompt's bottom edge, adapted to our orange-red palette. Neither library supplies speech or Live transport. See §12.9.

**AC:** after an explicit Enable Live gesture and mic permission in HTTPS/localhost, the user can speak, hear a real Gemini Live reply, interrupt assistant playback and receive a reply to the interruption without stale audio continuing. Input/output transcripts match the exchange; the chosen female-sounding preset is auditioned and documented in README. Demonstrate spoken selection of a real storyboard/scene and at least one source-grounded pre-render edit through validated tools: the persisted concept/draft and canvas update visibly, preserve FR-01/FR-02 constraints and report actual success/failure. Explicit confirmation of the summarized run is required before generation/render/pretest jobs; no duplicate job on reconnect/repeated tool call. Live welcome, an actual job milestone and an evidence-backed verdict are demonstrated; statements never invent completed tests, counts, emotion or guaranteed outcomes. Orb state/scale follows the real connection/mic/work/output audio; any amplitude glow is real, not random. Mute, stop/disconnect, mic release, captions and typed fallback work; jobs do not wait for audio, and missing credentials/quota/connection failures are visible. Long-lived keys stay server-side, with scoped short-lived tokens or a secure proxy for browser Live; provider/model/routing evidence is recorded. TTS-only narration, prerecorded dialogue, a reactive orb or text-only fallback does not pass FR-16. Editing a tested winner remains FR-11/P1; any changed video invalidates its old test evidence.

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

**States:** `BRIEF_RECEIVED → PLANNED → RENDERED → SIMULATED → SCORED → EXPLAINED → (ITERATED) → DONE or FAILED`

**Live control boundary (FR-16/P0):** the Director is a conversational control surface for this workflow, not a second scheduler. Enable Live opts into bounded conversation, not pipeline jobs. Confirm bounded planning before generating concepts; expose a pre-render review/confirmation checkpoint while `PLANNED`: select a scene/variant and apply a source-backed hook/copy, screenshot or scene-order change to the validated draft, then approve that draft for render/pretest. Agree typed command/result schemas with Dashboard/backend owners. Include project/variant/scene IDs, draft revision and idempotent command IDs; reject stale/invalid edits, persist accepted changes and acknowledge only completed tool results. Enforce the three-concept/4–6-scene/15-second contract. After rendering, never patch a tested artifact/result in place; the tested-winner revision stays FR-11/P1 with re-render/retest. Live connection state is separate from job state; losing audio does not stop or duplicate a confirmed job.

**Tools** (each with a typed input and output, see §10.3):

| Tool | Input | Output |
| --- | --- | --- |
| `plan_variants` | `Brief` | 3 × `CreativeConcept` |
| `render_variant` | `CreativeConcept` | MP4 path |
| `simulate_tribe` | MP4 path | `SimulationResult` |
| `simulate_viewer_panel` | MP4 path, personas, goal | `SimulationResult` |
| `score_and_rank` | `SimulationResults`, goal | `Ranking` |
| `explain_variant` | Variant, `SimulationResults` | Reasons |
| `revise_concept` (P1) | Concept, weakest moment | `CreativeConcept` |

**Guardrails**

- Max 3 variants and 1 revision per run. Per tool timeout. One retry.
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
| Opus — planned runtime finalization | Authors a validated motion-graphics composition for the selected final asset | A separately budgeted final-video step, not each candidate or brain-view render; not yet integrated |
| Remotion — renderer | Converts the approved composition/template inputs into MP4 | Backend rendering, not an LLM producing video pixels |

The product owner's desired runtime direction is Gemini for the scalable experimentation loop, followed by Opus for the finished product-demo/motion-graphics asset. For today's MVP, keep the existing one-template FR-03 path working; the additional runtime finalization integration is not a new mandatory P0 and any winner revision still follows FR-11/P1. Do not introduce unlimited variants or a second template family.

Before enabling runtime Opus, verify the provider's actual API model ID, Condense support, server-side credentials, per-run limits and latency. Conductor's coding-agent model ID is not an inference API contract. A Gemini key does not authorize or authenticate Claude calls. Log actual model usage/cost separately from browser rendering and TRIBE inference; do not claim unmeasured savings or pricing.

If finalization changes the content or timing of a tested video, re-render and re-simulate those exact bytes before attaching a tested verdict or brain response to the export. Keep the original winner/runner-up artifacts and results traceable; never reuse a candidate's prediction for a changed final asset. Replaying, orbiting or opening an A/B view does not trigger new LLM or TRIBE inference.

### 9.2 Experiment graph and scale

`[DECISION — v1.4]` The canvas projects the workflow; it is not a second job scheduler. Each hypothesis, storyboard, rendered asset and test result keeps stable IDs, parent lineage, source traceability and status. Node selection and connecting a visual edge do not themselves authorize a paid render, inference or publication.

Separate **hypothesis nodes** from **rendered videos** and **completed neural simulations**. A hook/storyboard needs a playable render before TRIBE can evaluate it; Gemini-authored text or a thumbnail is not a neural result. Selection, ranking and explanations consume the actual stored evidence, not the number of nodes on screen.

The user's “at scale” direction is bounded batch experimentation: queue candidates, apply configured worker concurrency/rate limits/timeouts, cache identical analyzed videos and prune/shortlist before expensive render/TRIBE/Opus steps. Default today remains FR-02/FR-03's three videos and one P1 revision until William and the backend owner approve an explicit batch budget and record throughput. Do not silently expand this to 50 full renders per node. Fifty choices at three depths means 125,000 possible paths, not 150 completed tests; neither the cost nor GPU capacity is yet verified.

Large visual trees may use viewport virtualization/level-of-detail and staged layout while retaining actual nodes/edges and lineage. A node must be inspectable when zoomed in; a “+47” badge is not evidence that 47 hypotheses were generated or tested. If the product shows a prototype/example tree, the whole graph and its claims stay visibly prototype/untested. Present this as **simulated comparison/pretest**, not a live randomized audience A/B experiment.

### 9.3 Sound for the exported videos

`[DECISION — sound addendum]` After a run is explained, the winner and the runner-up get a soundtrack, so the exported files are finished ads and not silent renders.

- **What is added.** Gemini text-to-speech narration (default voice `Kore`, the same female voice as the Live Director), a synthesized 120 BPM music bed and synthesized effects placed on scene changes. Music and effects are generated in code, not sampled, so there are no licensing questions. Everything is mixed to about -14 LUFS with a true peak at or below -1 dBTP, **measured on the encoded file**.
- **Narration says only what the video shows.** Each line is a scene's on-screen text (or the CTA), so it already carries a `source_field`. Nothing is added or paraphrased by a model.
- **The picture is never re-encoded.** ffmpeg copies the video stream (`-c:v copy`), so the exported picture is byte-identical to the rendered one.
- **What the verdict covers.** The simulated viewers and TRIBE analyzed the **silent** render. The sound cut is a different file, so the exported `winner.mp4` and `runner_up.mp4` are the sound cuts, `videos/{id}.mp4` stays the tested render, and the launch brief states that the ranking does not cover the audio. Both hashes are kept in `sound/{id}.json`. Re-simulating the sound cut (TRIBE also receives audio and speech) is the stricter option described in §9.1 and is not done today.
- **Degrades, never fails.** If narration fails, the cut has music and effects only and says why. If ffmpeg is unavailable the variant is exported silent and the activity log shows the step as skipped.
- **Routing exception (FR-10).** Narration calls Gemini's TTS model directly, not through Condense: Condense documents only text chat routes, and each call carries one on-screen line, so there is nothing to compress. This is a logged exception that the product owner must confirm; narration token usage is recorded in `sound/{id}.json`, separate from the Condense ledger.
- **Cost bound.** At most two videos per run, one TTS call per distinct line, cached on disk by text, voice and model, so a resumed run does not pay twice.

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

**Brief**

```json
{
  "project_id": "str",
  "product_name": "str",
  "one_liner": "str<=140",
  "screenshots": ["path"],
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
  "hook": "str<=8 words",
  "scenes": [
    {
      "t_start": 0,
      "t_end": 3,
      "screenshot": "path",
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
  "variant_id": "A",
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
  "token_savings": { "tokens_saved": 0, "percent": 0 }
}
```

### 10.4 Secrets and repo

- Keys in environment variables only (`GEMINI_API_KEY`, `CONDENSE_API_KEY`, `TRIBE_ENDPOINT`). Commit `.env.example`, never `.env`.
- No model weights in the repo. README credits TRIBE v2 (Meta FAIR) and states its CC BY-NC license.
- Repo must be public (hackathon rule). URL: https://github.com/clawmax12-lang/Norrsken.
- The README states the build stack, including that the code was written with Claude Opus 5.5 as the coding agent.

Runtime Opus is separate from the Conductor coding agent. If integrated, supply its credentials only on the server (for a direct Anthropic integration, `ANTHROPIC_API_KEY`) and configure the verified API model independently. All runtime LLM calls still follow FR-10's Condense requirement; unsupported provider routing is an integration blocker, not permission to silently bypass it. The product owner reports that a Gemini key is now available; this is not verification that it is configured in every workspace or has TTS/Live/GPU entitlements. Missing credentials must show an explicit unavailable/not-configured state, never fabricated results. Never request keys in tracked documents or frontend source.

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

**Entry, before the brief:** on first arrival this session, a 10–15 second hero reveals the shaded brain/silhouette, slowly orbits it, moves toward an atlas-backed region, then pulls back and docks the same brain in a corner as the canvas appears. No backend job or microphone starts on page load. A visible Enable Live action requests mic permission and unlocks the female Gemini conversation/welcome; the visual intro remains usable silently and skippable. The silent path is a fallback, not FR-16 acceptance.

Red/orange/yellow “waves” before the user's run require genuine precomputed predictions for a specific example video, visibly labeled **Demo example · precomputed**, with its provenance/video available. Without that bundle, show gray anatomy and **No brain data**, using lighting/camera motion for the entry. Never portray a prerecorded/reference animation or fabricated pulse as the user's simulated response. The original reference images are inspiration, not analysis data.

**Analysis focus, when genuine results are ready:** reuse the renderer for the following beats once per run. Its handover now returns to the canvas, not a separate dashboard page.

| Beat | Time | What happens on screen |
| --- | --- | --- |
| 1. Black out | 0 to 1.5 s | Screen dims to black. The variant video shrinks into a floating frame on the left. Small mono text: "Running simulated viewers · Variant A". |
| 2. Assemble | 1.5 to 4 s | Head silhouette fades in. The brain builds from a thin wireframe into the shaded gray mesh while slowly rotating to a side view. |
| 3. Watch | 4 to 9 s | The video plays in its frame. The brain lights up second by second with the predicted response (interpolated between the 1 Hz frames so it moves smoothly). Thin HUD lines connect three live meters (Visual, Auditory, Language) to their regions. A timeline under everything shows the scrubber moving. |
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
2. **Canvas intake and storyboard review:** prompt/brief/source uploads plus two-way Live conversation; completed brief becomes the root node. Spoken/typed selection and edits share the actual validated draft/canvas state. Keep FR-01 validation, not prompt text alone; confirm the summarized run before jobs start.
3. **Canvas at work:** connected storyboard/hook branches, rendered-video nodes and actual test states; selected path highlighted. Persistent corner brain, voice dock and accessible persisted activity log.
4. **Canvas results:** recommendation node plus leaderboard/evidence inspector; selected video, time-aligned curves and expanded brain; actual Condense savings; verdict reachable at 1440 px without canvas hunting.
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

Use one left-to-right branching graph with parent/child lineage rather than separate disconnected stage dashboards or a radial node universe. Connect brief assets to concepts, concepts to their renders, and renders to their exact simulation/ranking/export evidence. Fit the initial three concept lanes to the desktop viewport with readable cards, then allow pan/zoom and focused expansion. Show source media/hook/storyboard content, variant ID, actual state and relevant duration rather than indistinguishable tiny dots; at distant zoom simplify detail without replacing actual evidence. Pan/zoom/fit-to-flow and selection should explain both the full experiment tree and an individual scene. A branching hook can continue the same storyline; it is not necessarily a new full video or independent test. The visual A/B/C pretest comparison does not promote FR-15/P1 synchronized difference mode or claim a live randomized audience experiment.

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

- **0:00** "I'm launching my app tablehopp on Wednesday. I need a tested launch video." Show entry brain, Enable Live and a real female Gemini reply to the presenter, then dock into the canvas. Any example predictions are visibly disclosed.
- **0:15** Brief with real tablehopp screenshots/storyboard. Ask aloud to select a scene and change its hook using the brief; interrupt a reply and see the confirmed edit on the actual canvas. Confirm the summarized Run. Fast-forward waiting only with clear disclosure; show an actual job milestone.
- **0:40** Genuine results populate the canvas. Expand the persistent brain and show a video-aligned region/timestamp; analysis focus if available. Distinguish actual tests from untested hypotheses.
- **1:20** Ask the Live Director why this variant won; hear an evidence-backed answer with timestamps. Show evidence and iteration delta if built; never claim retention/sales prediction.
- **1:45** Export. "This is the video we launch on Wednesday." Mention Gemini, Condense, and TRIBE as one of the simulated viewers.

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
13. PRD v1.6 retains the canvas and two-way female Gemini Live Director core demo requirements. TTS-only narration, prerecorded dialogue, browser/system voice, a huge static tree or reactive glow cannot substitute for real conversation, validated visible storyboard edits or generation/testing. Distinguish entry example, real run data and test MOCK; do not retask other agents or bypass their ownership just because this document changed. Live scope approval is not a Condense routing exception.
14. Apply the clean-flow design in §12 and its shared brief: near-black dotted canvas, readable left-to-right media/storyboard branches, minimal floating chrome, Redaction identity and restrained orange-red accents. Preserve existing application logic/contracts when changing the shell. New layout references supersede the old radial/sidebar layout, not the anatomical brain baseline.

## 16. Decision log

The original entries below are retained from the supplied v1.1 PRD; later decisions are appended with their version. Append new decisions with their date, rationale and affected requirement IDs. Requirement changes must also update the relevant section and version/change notes in this document.

**Latest FR-16 placement, v1.6.1:** William rejected the central/full-screen voice view. Voice replaces the prompt at the bottom with a fairly large neutral Libraries.dev orb; canvas remains visible and interactive with no dimming. End/Escape restores the prompt. The earlier central-orb entry below is historical and superseded.

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
| 3 Oct, v1.6 implementation | Reuse Gemini Live's single microphone and `AudioContext`; measure assistant output after its gain node, discard queued playback on interruption/mute/disconnect, and bind the one canvas brain to a project id only after the backend accepts that project. | Keeps voice visuals tied to audible playback, prevents a second capture/service, and prevents local draft ids or audio amplitude from becoming false brain/job evidence. Applies to FR-07/FR-12/FR-16. |
| 3 Oct, FR-16 implementation clarification | Latest owner gesture: voice is a button inside the text bar; explicit click opens a large central standalone orb, End/Escape returns it smoothly to that button and disconnects. Use the library's public engine at native resolution for the large orb, its supported 20 preset in the active button, and real-audio VoiceBeam. Expose actual host capabilities, serialized tools and one snapshot-bound spoken/clicked run command. | Makes the owner's FLORA/minimalism direction and required two-way voice usable without a permanently floating side avatar or blurry bitmap. The supplied builder guide requires voice-first operation; see docs/VOICE_FIRST_ACCEPTANCE.md. This branch is based on main's v1.6 implementation; the owner's broader video-first v1.7 baseline remains in pending docs PR #1 and is not silently implemented by changing the voice prompt. |
| 3 Oct, v1.6.1 / FR-16 placement correction | Voice button inside the bottom prompt → fairly large standalone orb **at the bottom, instead of the prompt** → End/Escape restores the prompt and disconnects. Adopt reference 10's neutral gray Libraries.dev orb. No full-screen voice view, canvas dimming or surrounding card. Implementation uses native 160 px canvas (136 px on short viewports) with the library's tuned 64 geometry, restrained warm beam and compact controls/captions. | Explicit owner correction of the preceding central-orb interpretation. Keeps canvas interaction primary and Gemini Live functional; no audio/provider/backend/brain scope change. |
| 3 Oct, v1.6.2 / FR-16 orb and floor | Reference 10 is the library's composing sash: preserve it instead of a breathing/loading ring, even when disconnected. Actual assistant output amplitude drives both orb growth/deformation and a warm VoiceBeam anchored at the screen's bottom border, like a floor beneath the orb. The briefly requested white circle is withdrawn; transparent orb on black. Honest phase labels/paused disconnected visuals, compact controls and existing audio/job/brain contracts remain. | Owner reports mismatched orb and connection failure in the preview, then clarifies the simultaneous floor effect and withdraws the white substrate. No new microphone/service. Main token probe passes; protected Preview needs separate provider/configuration verification. Pin token issuance to the SDK-documented v1alpha API and emit only allowlisted error categories; do not claim this proves the Preview root cause or a real conversation. |
| 3 Oct, sound addendum | Add narration (Gemini TTS, voice `Kore`), a synthesized music bed and effects to the exported winner and runner-up after the pretest; the picture stream is copied unchanged; the verdict covers the silent render and the launch brief says so; narration bypasses Condense (logged exception, owner to confirm). Applies to FR-08 and §9.3. | The owner wants finished ads with audio. Keeping the tested silent render and the sound cut as separate, hashed files keeps the pretest claim honest. |

## 17. Open questions

- Public repo URL to paste into the header and §10.4. **Repository import update:** URL filled in as https://github.com/clawmax12-lang/Norrsken; visibility was PRIVATE when checked on 3 Oct 2026. Public visibility remains outstanding; see TEAM.md.
- Exact submission time (19:00 or 19:19).
- GPU source for TRIBE (sponsors, Metrix, Colab, cloud).
- Template style. Reference: modern SaaS launch videos (for example the Lovable 2.0 launch video).
- Lunch time (unclear in the opening talk).
- Runtime Opus finalization: verify API model availability, Condense routing, server credentials, exact budget/latency and whether it fits today's P1 timebox. Coding-agent availability in Conductor alone does not resolve these.
- Voice P0: scope is resolved as two-way Gemini Live (FR-16), not TTS-only. Verify proposed Live model/account access, audition the female-sounding preset, agree typed tool/draft/event contracts and session/cost bounds, and verify Condense Live transport or obtain an explicit approved routing exception. No key material belongs in this document.
- Batch scale: approve explicit hypothesis/render/simulation limits, pruning strategy, GPU concurrency, cost ceiling and measured latency before increasing today's three-video execution cap.
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
